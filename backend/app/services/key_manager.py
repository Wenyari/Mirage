"""
密钥池管理服务
负责密钥的分配、释放、熔断和任务调度
"""
import random
import json
import logging
from app.extensions import db
from app.models.model import ApiKey
from app.models.task import Task

logger = logging.getLogger(__name__)


class KeyManager:
    """密钥池管理器"""

    # Redis Key 前缀
    PREFIX_USAGE = "pool:usage:"           # 密钥使用计数
    PREFIX_COOLDOWN = "pool:cooldown:"     # 密钥熔断标记
    PREFIX_STATS = "pool:stats:calls:"     # 密钥调用统计
    QUEUE_VIP = "queue:waiting:vip"        # VIP 等待队列
    QUEUE_NORMAL = "queue:waiting:normal"  # 普通等待队列
    QUEUE_RUNNABLE = "queue:runnable"      # 可执行队列

    @classmethod
    def _get_redis(cls):
        """获取 Redis 客户端"""
        from app.extensions import redis_client
        return redis_client

    @classmethod
    def allocate_key(cls, model: str):
        """
        尝试获取一个可用的密钥

        逻辑：
        1. 查询支持该模型的所有启用密钥（通过 JOIN 多对多关联）
        2. 过滤掉熔断中的密钥
        3. 基于权重随机选择
        4. 原子性占用（检查并发限制）

        Args:
            model: 模型标识符（如 'sora', 'openai'）

        Returns:
            元组 (ApiKey对象, api_base) 或 (None, None)（无可用密钥）
        """
        # 1. 查询所有启用的密钥（通过 JOIN 多对多关联表）
        from app.models.model import Model, ApiKeyModel

        # 改为查询 ApiKey 和对应的 api_base
        candidates_with_base = db.session.query(ApiKey, ApiKeyModel.api_base)\
            .join(ApiKeyModel, ApiKey.id == ApiKeyModel.api_key_id)\
            .filter(
                ApiKeyModel.model == model,
                ApiKey.status == 1
            )\
            .all()

        # 2. 过滤掉熔断中的密钥
        valid = [(k, api_base) for k, api_base in candidates_with_base
                 if not cls._get_redis().get(f"{cls.PREFIX_COOLDOWN}{k.id}")]

        if not valid:
            logger.warning(f"No available keys for model: {model}")
            return None, None

        # 3. 权重随机选择（尝试多次）
        keys = [k for k, _ in valid]
        weights = [k.weight for k in keys]

        # 尝试次数 = 候选数（避免死循环）
        for _ in range(len(valid)):
            idx = random.choices(range(len(valid)), weights=weights, k=1)[0]
            selected, api_base = valid[idx]

            # 4. 原子性占用
            usage_key = f"{cls.PREFIX_USAGE}{selected.id}"
            current_usage = cls._get_redis().incr(usage_key)

            # 检查是否超过并发限制
            if current_usage <= selected.max_concurrency:
                # 成功占用，设置 TTL 并记录统计
                cls._get_redis().expire(usage_key, 86400)  # 24 小时过期
                cls._get_redis().incr(f"{cls.PREFIX_STATS}{selected.id}")
                logger.info(f"Allocated key {selected.id} for model {model}, usage: {current_usage}/{selected.max_concurrency}, api_base: {api_base}")
                return selected, api_base
            else:
                # 超限，回滚并继续尝试下一个
                cls._get_redis().decr(usage_key)
                logger.debug(f"Key {selected.id} is at full capacity, trying next...")
                continue

        logger.warning(f"All keys for model {model} are at full capacity")
        return None, None

    @classmethod
    def release_key_and_dispatch(cls, key_id: int):
        """
        释放密钥占用并触发事件分发

        这是核心调度方法，在 Worker 完成任务后调用
        会主动从等待队列中取出下一个任务并分配资源

        Args:
            key_id: 密钥 ID
        """
        # 1. 释放占用计数
        usage_key = f"{cls.PREFIX_USAGE}{key_id}"
        current = cls._get_redis().get(usage_key)

        if current and int(current) > 0:
            new_usage = cls._get_redis().decr(usage_key)
            logger.info(f"Released key {key_id}, current usage: {new_usage}")
        else:
            logger.warning(f"Attempted to release key {key_id} but usage was already 0")

        # 2. 触发事件驱动的任务分发
        cls._dispatch_next_task(key_id)

    @classmethod
    def _dispatch_next_task(cls, key_id: int):
        """
        调度器：从等待队列中取出任务并分配密钥

        优先级：VIP 队列 > 普通队列
        惰性取消：自动跳过已取消的任务
        递归填充：如果密钥还有空闲，继续调度

        Args:
            key_id: 密钥 ID
        """
        # 1. Double Check：确认密钥健康且有空闲
        key_obj = ApiKey.query.get(key_id)

        if not key_obj:
            logger.error(f"Key {key_id} not found in database")
            return

        # 检查是否在熔断中
        if cls._get_redis().get(f"{cls.PREFIX_COOLDOWN}{key_id}"):
            logger.info(f"Key {key_id} is in cooldown, skipping dispatch")
            return

        # 检查是否还有并发余额
        usage = cls._get_redis().get(f"{cls.PREFIX_USAGE}{key_id}")
        current_usage = int(usage) if usage else 0

        if current_usage >= key_obj.max_concurrency:
            logger.debug(f"Key {key_id} is at full capacity ({current_usage}/{key_obj.max_concurrency})")
            return

        # 2. VIP 插队逻辑：优先从 VIP 队列取任务
        raw_task = cls._get_redis().lpop(cls.QUEUE_VIP)
        if not raw_task:
            raw_task = cls._get_redis().lpop(cls.QUEUE_NORMAL)

        if not raw_task:
            logger.debug(f"No tasks waiting for key {key_id}")
            return

        # 3. 惰性取消检查
        task_data = json.loads(raw_task)
        task_id = task_data['task_id']

        # 查询数据库状态
        task_status = db.session.query(Task.status).filter_by(id=task_id).scalar()

        if task_status == 'cancelled':
            logger.info(f"Task {task_id} was cancelled, skipping and trying next")
            # 递归调用，继续处理下一个任务
            cls._dispatch_next_task(key_id)
            return

        # 4. 注入密钥信息并推送到执行队列
        # 再次占用（因为可能是从队列取出的新任务）
        usage_key = f"{cls.PREFIX_USAGE}{key_id}"
        current_usage = cls._get_redis().incr(usage_key)
        cls._get_redis().expire(usage_key, 86400)
        cls._get_redis().incr(f"{cls.PREFIX_STATS}{key_id}")

        # 注入密钥配置
        # 从关联表查询该密钥对应该模型的 api_base
        from app.models.model import ApiKeyModel
        model_key = task_data.get('model')

        api_key_model = db.session.query(ApiKeyModel)\
            .filter_by(api_key_id=key_obj.id, model=model_key)\
            .first()

        if api_key_model:
            api_base = api_key_model.api_base
        else:
            # 兜底使用默认 api_base
            logger.warning(f"No api_base found for key {key_id} and model {model_key}, using default")
            api_base = key_obj.api_base

        task_data['key_id'] = key_obj.id
        task_data['api_base'] = api_base
        task_data['api_key'] = key_obj.key_secret

        # 推送到执行队列
        cls._get_redis().rpush(cls.QUEUE_RUNNABLE, json.dumps(task_data))
        logger.info(f"Dispatched task {task_id} to runnable queue with key {key_id}")

        # 5. 如果还有并发余额，继续调度（填满为止）
        if current_usage < key_obj.max_concurrency:
            logger.debug(f"Key {key_id} still has capacity, continuing dispatch")
            cls._dispatch_next_task(key_id)

    @classmethod
    def mark_unhealthy(cls, key_id: int, reason: str, cooldown_seconds: int = 300):
        """
        触发密钥熔断

        Args:
            key_id: 密钥 ID
            reason: 熔断原因
            cooldown_seconds: 熔断时长（秒），默认 5 分钟
        """
        cooldown_key = f"{cls.PREFIX_COOLDOWN}{key_id}"
        cls._get_redis().setex(cooldown_key, cooldown_seconds, reason)

        # 记录错误统计
        cls._get_redis().incr(f"pool:stats:errors:{key_id}")

        logger.warning(f"Key {key_id} marked as unhealthy: {reason}, cooldown for {cooldown_seconds}s")

    @classmethod
    def get_key_status(cls, key_id: int):
        """
        获取密钥当前状态

        Returns:
            dict: 包含 usage, is_healthy, stats 等信息
        """
        key_obj = ApiKey.query.get(key_id)
        if not key_obj:
            return None

        usage = cls._get_redis().get(f"{cls.PREFIX_USAGE}{key_id}")
        is_in_cooldown = bool(cls._get_redis().get(f"{cls.PREFIX_COOLDOWN}{key_id}"))
        buffered_calls = cls._get_redis().get(f"{cls.PREFIX_STATS}{key_id}")
        buffered_errors = cls._get_redis().get(f"pool:stats:errors:{key_id}")

        return {
            'id': key_id,
            'models': [m.key for m in key_obj.models],  # 改为模型列表
            'current_usage': int(usage) if usage else 0,
            'max_concurrency': key_obj.max_concurrency,
            'is_healthy': not is_in_cooldown,
            'status': key_obj.status,
            'buffered_calls': int(buffered_calls) if buffered_calls else 0,
            'buffered_errors': int(buffered_errors) if buffered_errors else 0,
            'total_calls': key_obj.total_calls,
            'total_errors': key_obj.total_errors,
        }

    @classmethod
    def sync_stats_to_db(cls):
        """
        将 Redis 中的统计数据同步到 MySQL

        应该由定时任务调用（如每 5 分钟）
        """
        logger.info("Starting stats sync from Redis to MySQL")

        all_keys = ApiKey.query.all()
        synced_count = 0

        for key in all_keys:
            # 读取 Redis 缓冲的统计
            buffered_calls = cls._get_redis().get(f"{cls.PREFIX_STATS}{key.id}")
            buffered_errors = cls._get_redis().get(f"pool:stats:errors:{key.id}")

            if buffered_calls or buffered_errors:
                # 累加到数据库
                if buffered_calls:
                    key.total_calls += int(buffered_calls)
                    cls._get_redis().delete(f"{cls.PREFIX_STATS}{key.id}")

                if buffered_errors:
                    key.total_errors += int(buffered_errors)
                    cls._get_redis().delete(f"pool:stats:errors:{key.id}")

                synced_count += 1

        db.session.commit()
        logger.info(f"Stats sync completed, synced {synced_count} keys")
        return synced_count

    @classmethod
    def watchdog(cls):
        """
        看门狗任务：检测并修复队列死锁

        如果等待队列有积压，但存在空闲的密钥，主动触发调度
        应该由定时任务调用（如每 1 分钟）
        """
        logger.info("Watchdog checking for stuck tasks...")

        # 检查等待队列是否有任务
        vip_waiting = cls._get_redis().llen(cls.QUEUE_VIP)
        normal_waiting = cls._get_redis().llen(cls.QUEUE_NORMAL)

        if vip_waiting == 0 and normal_waiting == 0:
            logger.debug("No tasks waiting, watchdog idle")
            return 0

        logger.info(f"Tasks waiting: VIP={vip_waiting}, Normal={normal_waiting}")

        # 查找空闲密钥并触发调度
        all_keys = ApiKey.query.filter_by(status=1).all()
        dispatched = 0

        for key in all_keys:
            # 检查是否在熔断中
            if cls._get_redis().get(f"{cls.PREFIX_COOLDOWN}{key.id}"):
                continue

            # 检查是否有空闲
            usage = cls._get_redis().get(f"{cls.PREFIX_USAGE}{key.id}")
            current_usage = int(usage) if usage else 0

            if current_usage < key.max_concurrency:
                logger.info(f"Watchdog triggering dispatch for idle key {key.id}")
                cls._dispatch_next_task(key.id)
                dispatched += 1

        logger.info(f"Watchdog triggered {dispatched} dispatches")
        return dispatched

    @classmethod
    def remove_task_from_queue(cls, task_id: str):
        """
        从 Redis 队列中移除指定的任务

        检查所有队列（RUNNABLE, VIP, NORMAL），如果找到任务则移除。
        如果任务在 RUNNABLE 队列中（已分配密钥），返回 key_id 以便释放密钥。

        Args:
            task_id: 任务 ID

        Returns:
            dict: {
                'found': bool,           # 是否找到任务
                'queue': str,            # 任务所在队列名
                'key_id': int or None    # 密钥ID（如果已分配）
            }
        """
        redis_client = cls._get_redis()

        # 需要检查的队列列表
        queues_to_check = [
            cls.QUEUE_RUNNABLE,
            cls.QUEUE_VIP,
            cls.QUEUE_NORMAL
        ]

        for queue_name in queues_to_check:
            # 获取队列长度
            queue_len = redis_client.llen(queue_name)

            # 遍历队列中的所有任务
            for i in range(queue_len):
                # 获取队列中的第 i 个元素（但不移除）
                raw_payload = redis_client.lindex(queue_name, i)
                if not raw_payload:
                    continue

                try:
                    payload = json.loads(raw_payload)
                    if payload.get('task_id') == task_id:
                        # 找到任务，从队列中移除
                        # 使用 LREM 命令移除指定的元素
                        redis_client.lrem(queue_name, 1, raw_payload)

                        key_id = payload.get('key_id')
                        logger.info(f"Task {task_id} removed from queue {queue_name}, key_id: {key_id}")

                        return {
                            'found': True,
                            'queue': queue_name,
                            'key_id': key_id
                        }
                except (json.JSONDecodeError, KeyError) as e:
                    logger.warning(f"Failed to parse payload in queue {queue_name}: {e}")
                    continue

        # 未找到任务
        logger.info(f"Task {task_id} not found in any queue")
        return {
            'found': False,
            'queue': None,
            'key_id': None
        }
