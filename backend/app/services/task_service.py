"""
任务管理服务
负责任务的创建、提交、取消等业务逻辑
集成密钥池调度系统
"""
import json
import logging
import uuid
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from decimal import Decimal
from app.extensions import db
from app.models.task import Task
from app.models.user import User, MembershipConfig
from app.models.model import ModelConfig
from app.services.key_manager import KeyManager
from app.services.pay_service import check_and_deduct_balance, execute_refund

logger = logging.getLogger(__name__)


def get_redis():
    """获取 Redis 客户端"""
    from app.extensions import redis_client
    return redis_client


class TaskService:
    """任务服务"""

    @classmethod
    def submit_task(cls, user_id: int, task_data: dict):
        """
        提交新任务

        流程：
        1. 验证用户权限和余额
        2. 检查并发限制
        3. 扣除积分
        4. 创建任务记录
        5. 尝试获取密钥（快车道）或进入等待队列（慢车道）

        Args:
            user_id: 用户 ID
            task_data: 任务数据
                {
                    "model": "sora",
                    "prompt": "...",
                    "params": {...},
                    "input_file_url": "..."
                }

        Returns:
            dict: {"task_id": "...", "status": "...", "msg": "..."}

        Raises:
            ValueError: 业务错误（权限不足、余额不足等）
        """
        model_key = task_data.get('model')
        prompt = task_data.get('prompt')
        params = task_data.get('params', {})
        input_file_url = task_data.get('input_file_url')

        # 确保 input_file_url 是列表格式
        if input_file_url is not None:
            if isinstance(input_file_url, str):
                # 如果是单个字符串，转换为列表
                input_file_url = [input_file_url] if input_file_url else None
            elif isinstance(input_file_url, list):
                # 如果是列表，过滤掉空字符串
                input_file_url = [url for url in input_file_url if url] or None
            else:
                input_file_url = None

        print("task-dat::::::::::", task_data)
        # 1. 验证用户和模型配置
        user = User.query.get(user_id)
        if not user:
            raise ValueError("User not found")

        if user.status != 1:
            raise ValueError("User account is disabled")

        model_config = ModelConfig.query.filter_by(model=model_key, is_active=1).first()
        if not model_config:
            raise ValueError(f"Model {model_key} is not available")

        # 2. 验证用户等级权限
        membership = MembershipConfig.query.filter_by(level=user.level).first()
        tier_name = membership.name if membership else f"T{user.level}"

        if tier_name not in model_config.allowed_tiers:
            raise ValueError(f"Your membership tier ({tier_name}) cannot use this model")

        # 3. 计算费用
        cost = model_config.cost_per_call

        # 4. 检查并发限制
        if membership:
            concurrent_limit = membership.concurrent_limit
        else:
            concurrent_limit = 1

        current_processing = Task.query.filter_by(
            user_id=user_id,
            status='processing'
        ).count()

        if current_processing >= concurrent_limit:
            raise ValueError(f"Concurrent limit exceeded ({current_processing}/{concurrent_limit})")

        # 5. 生成任务 ID（需要在扣费前生成，用于流水记录）
        task_id = str(uuid.uuid4())

        # 6. 扣除积分（使用统一的 pay_service，优先扣除活动积分）
        try:
            # pass model_key so the transaction rows record which model was used
            check_and_deduct_balance(user_id, cost, task_id, model_key)
        except ValueError as e:
            raise ValueError(str(e))

        # 7. 创建任务记录
        from datetime import datetime
        from zoneinfo import ZoneInfo

        task = Task(
            id=task_id,
            user_id=user_id,
            model=model_key,
            prompt=prompt,
            input_file_url=input_file_url,
            params=params,
            status='pending',
            progress=0,
            cost_points=cost,
            created_at=datetime.now(ZoneInfo("Asia/Shanghai"))  # 显式设置创建时间
        )

        db.session.add(task)
        db.session.commit()

        logger.info(f"Task {task_id} created for user {user_id}, cost: {cost}")

        # 8. 构造任务 Payload
        payload = {
            "task_id": task_id,
            "user_id": user_id,
            "model": model_key,
            "params": params,
            "prompt": prompt,
            "input_file_url": input_file_url,
        }

        # 9. 尝试直接获取密钥（快车道）
        key, api_base = KeyManager.allocate_key(model_key)

        if key:
            # 有资源 -> 注入密钥 -> 进执行队列
            payload['key_id'] = key.id
            payload['api_base'] = api_base  # 使用分配的 api_base
            payload['api_key'] = key.key_secret

            get_redis().rpush(KeyManager.QUEUE_RUNNABLE, json.dumps(payload))
            msg = "Task is being processed"
            logger.info(f"Task {task_id} directly dispatched to runnable queue with key {key.id}")
        else:
            # 无资源 -> 进等待队列（慢车道）
            # 根据用户等级分流
            target_queue = KeyManager.QUEUE_VIP if user.level >= 3 else KeyManager.QUEUE_NORMAL

            get_redis().rpush(target_queue, json.dumps(payload))
            msg = "Task is in priority queue" if user.level >= 3 else "Task is in queue"
            logger.info(f"Task {task_id} added to {target_queue}")

        return {
            "task_id": task_id,
            "status": "pending",
            "msg": msg
        }

    @classmethod
    def cancel_task(cls, user_id: int, task_id: str):
        """
        取消任务（仅限排队中的任务）

        Args:
            user_id: 用户 ID
            task_id: 任务 ID

        Returns:
            dict: {"msg": "..."}

        Raises:
            ValueError: 业务错误
        """
        task = Task.query.get(task_id)

        if not task:
            raise ValueError("Task not found")

        if task.user_id != user_id:
            raise ValueError("Permission denied")

        if task.status != 'pending':
            raise ValueError("Only pending tasks can be cancelled")

        # 1. 尝试从 Redis 队列中移除任务
        removal_result = KeyManager.remove_task_from_queue(task_id)

        # 2. 如果任务在队列中且已分配密钥，释放密钥
        if removal_result['found'] and removal_result['key_id']:
            key_id = removal_result['key_id']
            logger.info(f"Task {task_id} had allocated key {key_id}, releasing it")
            # 释放密钥并触发下一个任务的调度
            KeyManager.release_key_and_dispatch(key_id)

        # 3. 修改任务状态为 cancelled（惰性删除）
        task.status = 'cancelled'
        task.progress = 0

        # 4. 退款（使用统一的 pay_service）
        execute_refund(user_id, float(task.cost_points), task_id, "User cancelled")

        db.session.commit()

        logger.info(f"Task {task_id} cancelled by user {user_id}, refunded {task.cost_points}, queue: {removal_result['queue']}")

        return {"msg": "Task cancelled successfully"}


    @classmethod
    def get_task_status(cls, user_id: int, task_id: str):
        """
        获取任务状态（支持实时进度和队列信息）

        Args:
            user_id: 用户 ID
            task_id: 任务 ID

        Returns:
            dict: 任务详情，如果是 pending 状态会附带队列信息

        Raises:
            ValueError: 业务错误
        """
        task = Task.query.get(task_id)

        if not task:
            raise ValueError("Task not found")

        if task.user_id != user_id:
            raise ValueError("Permission denied")

        task_dict = task.to_dict()

        # 如果任务正在执行，从 Redis 读取实时进度
        if task.status == 'processing':
            redis_progress = get_redis().get(f"task:progress:{task_id}")
            if redis_progress:
                task_dict['progress'] = int(redis_progress)

        # 如果任务还在排队，附带队列信息
        elif task.status == 'pending':
            user = User.query.get(user_id)
            is_vip = user.level >= 3 if user else False

            # 获取队列长度
            vip_count = get_redis().llen(KeyManager.QUEUE_VIP)
            normal_count = get_redis().llen(KeyManager.QUEUE_NORMAL)

            # 附加队列信息到返回数据
            task_dict['queue_info'] = {
                'user_queue': 'vip' if is_vip else 'normal',
                'position': vip_count if is_vip else normal_count,
                'vip_queue': vip_count,
                'normal_queue': normal_count
            }

        return task_dict

    @classmethod
    def get_task_history(cls, user_id: int, page: int = 1, size: int = 20):
        """
        获取任务历史记录

        Args:
            user_id: 用户 ID
            page: 页码
            size: 每页大小

        Returns:
            dict: {"list": [...], "total": ..., "page": ..., "size": ...}
        """
        pagination = Task.query.filter_by(user_id=user_id)\
            .order_by(Task.created_at.desc())\
            .paginate(page=page, per_page=size, error_out=False)

        return {
            "list": [task.to_dict() for task in pagination.items],
            "total": pagination.total,
            "page": page,
            "size": size
        }

    @classmethod
    def get_queue_status(cls, user_id: int):
        """
        获取队列排队状态

        Args:
            user_id: 用户 ID

        Returns:
            dict: {
                "vip_queue": 10,      # VIP 队列排队人数
                "normal_queue": 25,   # 普通队列排队人数
                "user_queue": "vip",  # 用户所在队列类型
                "user_position": 10   # 用户所在队列的排队人数
            }
        """
        # 获取用户信息以判断所属队列
        user = User.query.get(user_id)
        if not user:
            raise ValueError("User not found")

        # 获取队列长度
        vip_count = get_redis().llen(KeyManager.QUEUE_VIP)
        normal_count = get_redis().llen(KeyManager.QUEUE_NORMAL)

        # 判断用户所属队列（T4/T5 为 VIP，其他为普通）
        is_vip = user.level >= 4
        user_queue_type = "vip" if is_vip else "normal"
        user_position = vip_count if is_vip else normal_count

        return {
            "vip_queue": vip_count,
            "normal_queue": normal_count,
            "user_queue": user_queue_type,
            "user_position": user_position
        }

    @classmethod
    def get_available_models(cls, user_id: int):
        """
        获取所有模型列表，并标注当前用户是否可用

        Args:
            user_id: 用户 ID

        Returns:
            list: 所有模型列表，每个模型包含基本信息、价格配置和可用性标记
            [
                {
                    "key": "sora-2",
                    "name": "Sora-2",
                    "description": "...",
                    "cost_per_call": 100.00,
                    "is_available": false,        # 当前用户是否可用
                    "min_tier": "T3",             # 最低要求等级
                    "user_tier": "T1",            # 用户当前等级
                    "allowed_tiers": ["T3", "T4", "T5"],
                    ...
                }
            ]

        Raises:
            ValueError: 用户不存在
        """
        from app.models.model import Model, ModelConfig

        # 获取用户信息
        user = User.query.get(user_id)
        if not user:
            raise ValueError("User not found")

        # 获取用户等级对应的 tier 名称
        membership = MembershipConfig.query.filter_by(level=user.level).first()
        user_tier = membership.name if membership else f"T{user.level}"

        # 查询所有启用的模型及其配置
        models = db.session.query(Model, ModelConfig).join(
            ModelConfig, Model.key == ModelConfig.model
        ).filter(
            Model.enabled == 1,           # 模型已启用
            ModelConfig.is_active == 1    # 配置已激活
        ).all()

        # 返回所有模型，标注可用性
        result_models = []
        for model, config in models:
            model_dict = model.to_dict()

            # 添加价格信息
            model_dict['cost_per_call'] = float(config.cost_per_call)
            model_dict['allowed_tiers'] = config.allowed_tiers
            # 将配置中的 token_cost_config 与 params 一并返回
            try:
                model_dict['token_cost_config'] = config.token_cost_config
            except Exception:
                model_dict['token_cost_config'] = None
            try:
                model_dict['params'] = config.params
            except Exception:
                model_dict['params'] = None

            # 判断用户是否可用
            is_available = user_tier in config.allowed_tiers
            model_dict['is_available'] = is_available

            # 添加用户当前等级
            model_dict['user_tier'] = user_tier

            # 计算最低要求等级（从 allowed_tiers 中提取最小的）
            tier_levels = []
            for tier in config.allowed_tiers:
                # 提取 T1, T2... 中的数字
                if tier.startswith('T') and len(tier) > 1:
                    try:
                        tier_levels.append((int(tier[1:]), tier))
                    except ValueError:
                        pass

            if tier_levels:
                min_tier_level, min_tier_name = min(tier_levels)
                model_dict['min_tier'] = min_tier_name
            else:
                model_dict['min_tier'] = config.allowed_tiers[0] if config.allowed_tiers else None

            result_models.append(model_dict)

        # 按可用性排序：可用的在前，不可用的在后
        result_models.sort(key=lambda x: (not x['is_available'], x['cost_per_call']))

        return result_models

    @classmethod
    def cleanup_old_tasks(cls, days: int = 3) -> dict:
        """
        清理已完成超过指定天数的任务

        Args:
            days: 保留天数，默认3天

        Returns:
            dict: {
                'deleted': 删除的任务数量,
                'deleted_files': 删除的文件数量,
                'errors': 错误列表
            }
        """
        from app.services.storage_service import storage_service

        cutoff_time = datetime.now(ZoneInfo("Asia/Shanghai")) - timedelta(days=days)

        # 查询需要清理的任务（已完成且超过保留期）
        old_tasks = Task.query.filter(
            Task.finished_at.isnot(None),
            Task.finished_at < cutoff_time,
            Task.status.in_(['success', 'failed', 'cancelled'])
        ).all()

        deleted_count = 0
        deleted_files_count = 0
        errors = []

        logger.info(f"Found {len(old_tasks)} tasks to cleanup (older than {days} days)")

        for task in old_tasks:
            try:
                # 删除关联的文件（如果有）
                files_to_delete = []

                # 收集 input_file_url 中的文件
                if task.input_file_url and isinstance(task.input_file_url, list):
                    for url in task.input_file_url:
                        if url and isinstance(url, str):
                            # 从 URL 中提取对象键（去除协议和域名部分）
                            try:
                                from urllib.parse import urlparse
                                parsed = urlparse(url)
                                object_key = parsed.path.lstrip('/')  # 去掉开头的 /
                                if object_key:
                                    files_to_delete.append(object_key)
                            except Exception as e:
                                logger.warning(f"Failed to parse URL {url}: {e}")

                # 收集 result_url 中的文件
                # if task.result_url:
                #     try:
                #         object_key = task.result_url.split('/', 3)[-1] if '/' in task.result_url else None
                #         if object_key:
                #             files_to_delete.append(object_key)
                #     except Exception as e:
                #         logger.warning(f"Failed to parse result URL {task.result_url}: {e}")

                # 删除文件
                if files_to_delete:
                    delete_result = storage_service.delete_multiple_files(files_to_delete)
                    deleted_files_count += delete_result.get('deleted', 0)

                    if delete_result.get('errors'):
                        for error in delete_result['errors']:
                            errors.append({
                                'task_id': task.id,
                                'type': 'file_deletion',
                                'error': error
                            })

                # 删除任务记录
                db.session.delete(task)
                deleted_count += 1

            except Exception as e:
                error_msg = f"Failed to cleanup task {task.id}: {str(e)}"
                logger.error(error_msg)
                errors.append({
                    'task_id': task.id,
                    'type': 'task_deletion',
                    'error': str(e)
                })

        # 提交删除
        try:
            db.session.commit()
            logger.info(f"Cleanup completed: {deleted_count} tasks and {deleted_files_count} files deleted")
        except Exception as e:
            db.session.rollback()
            error_msg = f"Failed to commit cleanup: {str(e)}"
            logger.error(error_msg)
            errors.append({
                'type': 'commit',
                'error': str(e)
            })

        return {
            'deleted': deleted_count,
            'deleted_files': deleted_files_count,
            'errors': errors
        }

