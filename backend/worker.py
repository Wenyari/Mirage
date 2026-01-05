"""
Worker 异步任务处理入口
负责从密钥池执行队列中取任务并调用上游 API 执行

启动方式:
    python worker.py

工作流程:
1. 监听 queue:runnable 队列
2. 取出任务（已分配密钥）
3. 调用上游 API 执行任务
4. 轮询任务进度并更新到 Redis
5. 完成后释放密钥并触发下一个任务调度
"""
import json
import time
import logging
import requests
from datetime import datetime
from sqlalchemy import text
from app import create_app
from app.extensions import db
from app.models.task import Task
from app.services.key_manager import KeyManager
from app.adapters import get_adapter

# 创建 Flask 应用上下文
app = create_app()

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)


def get_redis():
    """获取 Redis 客户端"""
    from app.extensions import redis_client
    return redis_client


def execute_sql(sql, params=None):
    """
    使用独立连接执行 SQL，避免 session 缓存

    Args:
        sql: SQL 语句（text 对象）
        params: 参数字典

    Returns:
        执行结果（对于 SELECT）或 None（对于 UPDATE/INSERT）
    """
    with db.engine.connect() as conn:
        result = conn.execute(sql, params or {})
        conn.commit()
        return result


def query_sql(sql, params=None):
    """
    使用独立连接查询 SQL，返回结果

    Args:
        sql: SQL 语句（text 对象）
        params: 参数字典

    Returns:
        查询结果
    """
    with db.engine.connect() as conn:
        result = conn.execute(sql, params or {})
        return result.fetchone()  # 返回单行结果


def _should_refund_on_failure(fail_reason: str) -> bool:
    """
    判断任务失败时是否应该退款

    退款规则：
    - 用户责任（内容违规）：不退款
    - 系统责任（API错误、超时等）：退款

    Args:
        fail_reason: 失败原因文本

    Returns:
        bool: True 表示应该退款，False 表示不退款
    """
    if not fail_reason:
        return True  # 未知原因默认退款

    reason_lower = fail_reason.lower()

    # 内容违规关键词列表（用户责任，不退款）
    CONTENT_VIOLATION_KEYWORDS = [
        'content policy',
        'content violation',
        'policy violation',
        'safety',
        'unsafe',
        'inappropriate',
        'explicit',
        'violence',
        'violent',
        'sexual',
        'nsfw',
        'prohibited',
        'banned',
        'moderation',
        'restricted',
        'offensive',
        'harmful',
        'abuse',
        'illegal',
        'terms of service',
        'community guidelines',
        '违规',
        '违反'
    ]

    # 检查是否包含内容违规关键词
    for keyword in CONTENT_VIOLATION_KEYWORDS:
        if keyword in reason_lower:
            logger.info(f"Detected content violation keyword: '{keyword}' in reason: {fail_reason[:100]}")
            return False  # 内容违规，不退款

    # 其他情况（系统错误、超时、API故障等）默认退款
    logger.info(f"System error detected, will refund: {fail_reason[:100]}")
    return True


def process_task(payload):
    """
    处理单个任务

    Args:
        payload: 任务数据（从队列取出的 JSON）
            {
                "task_id": "...",
                "key_id": 123,
                "api_base": "https://...",
                "api_key": "sk-...",
                "params": {...},
                ...
            }
    """
    task_id = payload['task_id']
    key_id = payload['key_id']
    submit_endpoint = payload['api_base']  # 完整的提交端点地址
    api_key = payload['api_key']
    params = payload.get('params', {})

    # 【关键】根据 API Base 创建对应的适配器
    adapter = get_adapter(submit_endpoint)

    logger.info(f"Processing task {task_id} with key {key_id}")

    # 【关键修复】使用独立数据库连接，完全避开 session 缓存
    # Worker 长时间运行，session 缓存会导致查询失败
    # 1. 检查任务是否存在以及状态（使用新连接 + 原始 SQL）
    check_sql = text("SELECT status, user_id FROM tasks WHERE id = :task_id")
    result = query_sql(check_sql, {"task_id": task_id})

    if not result:
        logger.error(f"Task {task_id} not found in database")
        # 释放密钥
        KeyManager.release_key_and_dispatch(key_id)
        return

    current_status, user_id = result

    # 检查任务是否已被取消（懒删除模式）
    if current_status == 'cancelled':
        logger.info(f"Task {task_id} has been cancelled, skipping")
        # 释放密钥并触发下一个任务
        KeyManager.release_key_and_dispatch(key_id)
        return

    # 2. 更新任务状态为 processing（使用原始 SQL）
    update_sql = text("""
        UPDATE tasks
        SET status = 'processing', api_key_id = :key_id
        WHERE id = :task_id
    """)
    execute_sql(update_sql, {"task_id": task_id, "key_id": key_id})

    logger.info(f"Task {task_id} status updated to processing")

    try:
        # 2. 调用上游 API
        headers = {"Authorization": f"Bearer {api_key}"}

        # 处理特殊情况：查询路径与提交路径不同
        if '|' in submit_endpoint:
            submit_url, status_base = submit_endpoint.split('|')
        else:
            submit_url = submit_endpoint
            status_base = submit_endpoint

        logger.info(f"Submitting task to {submit_url}")

        # 构建符合上游 API 的请求体
        # 1. 处理 images 字段（必需）
        images = params.get('images')  # 优先使用 params 中的 images
        if not images:
            # 如果 params 中没有 images，尝试从 input_file_url 转换
            input_url = payload.get('input_file_url')
            if input_url:
                # 单个 URL 转为数组
                images = [input_url] if isinstance(input_url, str) else input_url
            else:
                # 如果都没有，使用空数组（某些 API 可能允许纯文本生成）
                images = []

        # 2. 构建完整请求体
        submit_payload = {
            "model": payload.get('model'),  # 必需：模型标识
            "prompt": payload.get('prompt', ''),  # 必需：提示词
            "images": images,  # 必需：图片列表
            **params  # 合并其他参数（aspect_ratio, duration, hd, watermark 等）
        }

        logger.info(f"Submitting task param: {params}")
        resp = requests.post(submit_url, headers=headers, json=submit_payload, timeout=30)

        # 错误处理
        if resp.status_code in [401, 403]:
            logger.error(f"Authentication error with key {key_id}: {resp.status_code}")
            KeyManager.mark_unhealthy(key_id, f"HTTP {resp.status_code} - Auth Error")
            raise Exception(f"Authentication failed: {resp.status_code}")

        if resp.status_code == 429:
            logger.warning(f"Rate limit exceeded for key {key_id}")
            KeyManager.mark_unhealthy(key_id, "Rate limit exceeded")
            raise Exception("Rate limit exceeded")

        if resp.status_code >= 400:
            logger.error(f"API error {resp.status_code}: {resp.text}")
            raise Exception(f"API error: {resp.status_code}")

        # 解析响应（使用适配器）
        response_data = resp.json()
        task_uuid = adapter.parse_submit_response(response_data)
        if not task_uuid:
            raise Exception("Failed to extract task ID from API response")

        logger.info(f"Task {task_id} submitted successfully, upstream ID: {task_uuid}")

        # 【关键】保存上游任务ID到数据库（使用独立连接）
        save_upstream_sql = text("""
            UPDATE tasks
            SET upstream_task_id = :upstream_task_id
            WHERE id = :task_id
        """)
        execute_sql(save_upstream_sql, {
            "task_id": task_id,
            "upstream_task_id": task_uuid
        })

        # 3. 轮询任务进度
        status_url = f"{status_base.rstrip('/')}/{task_uuid}"
        max_poll_time = 600  # 最长轮询时间 10 分钟
        poll_interval = 3    # 轮询间隔 3 秒
        start_time = time.time()

        while True:
            # 检查是否超时
            if time.time() - start_time > max_poll_time:
                raise Exception("Task polling timeout")

            time.sleep(poll_interval)

            # 查询状态
            logger.debug(f"Polling status for task {task_id}")
            check = requests.get(status_url, headers=headers, timeout=30)

            if check.status_code >= 400:
                logger.error(f"Status check error {check.status_code}: {check.text}")
                raise Exception(f"Status check failed: {check.status_code}")

            # 【使用适配器解析响应】
            raw_data = check.json()
            parsed = adapter.parse_status_response(raw_data)

            state = parsed['status']  # SUCCESS / FAILED / RUNNING
            progress = parsed['progress']  # 0-100 整数
            result_url = parsed['result_url']
            fail_reason = parsed['fail_reason']

            logger.info(f"Task {task_id} rawData:{raw_data} status: {state}, progress: {progress}%")

            # 写入 Redis 实时进度（只使用本地任务ID）
            if state == 'RUNNING':
                get_redis().setex(f"task:progress:{task_id}", 86400, progress)

            elif state == 'SUCCESS':
                # 任务成功（使用独立连接）
                success_sql = text("""
                    UPDATE tasks
                    SET status = 'success',
                        progress = 100,
                        result_url = :result_url,
                        finished_at = :finished_at
                    WHERE id = :task_id
                """)
                execute_sql(success_sql, {
                    "task_id": task_id,
                    "result_url": result_url,
                    "finished_at": datetime.now()
                })

                # 清理 Redis 进度
                get_redis().delete(f"task:progress:{task_id}")

                logger.info(f"Task {task_id} completed successfully, result: {result_url}")
                break

            elif state == 'FAILED':
                # 任务失败
                raise Exception(fail_reason or 'Unknown error')

    except Exception as e:
        # 任务失败处理（使用原始 SQL）
        logger.error(f"Task {task_id} failed: {str(e)}")

        fail_reason = str(e)[:255]  # 限制长度

        # 【智能退款逻辑】根据失败原因判断是否退款
        should_refund = _should_refund_on_failure(fail_reason)

        if should_refund:
            # 系统错误或非用户责任，进行退款
            # 先查询任务的 cost_points（使用独立连接）
            cost_sql = text("SELECT cost_points FROM tasks WHERE id = :task_id")
            cost_result = query_sql(cost_sql, {"task_id": task_id})

            if cost_result:
                refund_amount = cost_result[0]

                # 更新任务状态并退款（原子操作，使用独立连接）
                fail_with_refund_sql = text("""
                    UPDATE tasks t
                    JOIN users u ON u.id = :user_id
                    SET t.status = 'failed',
                        t.progress = 0,
                        t.fail_reason = :fail_reason,
                        t.finished_at = :finished_at,
                        u.balance = u.balance + :refund_amount
                    WHERE t.id = :task_id
                """)
                execute_sql(fail_with_refund_sql, {
                    "task_id": task_id,
                    "user_id": user_id,  # 之前从检查时获取的
                    "fail_reason": fail_reason,
                    "finished_at": datetime.now(),
                    "refund_amount": refund_amount
                })

                logger.info(f"Refunded {refund_amount} points to user {user_id} for task {task_id} (reason: {fail_reason[:50]})")
            else:
                logger.error(f"Cannot query cost for task {task_id}")
        else:
            # 用户责任（内容违规等），不退款，只更新任务状态（使用独立连接）
            fail_no_refund_sql = text("""
                UPDATE tasks
                SET status = 'failed',
                    progress = 0,
                    fail_reason = :fail_reason,
                    finished_at = :finished_at
                WHERE id = :task_id
            """)
            execute_sql(fail_no_refund_sql, {
                "task_id": task_id,
                "fail_reason": fail_reason,
                "finished_at": datetime.now()
            })

            logger.info(f"No refund for task {task_id} - user responsibility (reason: {fail_reason[:50]})")

        # 清理 Redis 进度
        get_redis().delete(f"task:progress:{task_id}")

    finally:
        # 【核心】释放密钥并触发下一个任务调度
        logger.info(f"Releasing key {key_id} for task {task_id}")
        KeyManager.release_key_and_dispatch(key_id)


def main():
    """主循环：监听执行队列"""
    logger.info("=" * 60)
    logger.info("AIGC Worker Started")
    logger.info(f"Listening on queue: {KeyManager.QUEUE_RUNNABLE}")
    logger.info("=" * 60)

    with app.app_context():
        while True:
            try:
                # 阻塞式取任务（超时 1 秒）
                raw_task = get_redis().blpop(KeyManager.QUEUE_RUNNABLE, timeout=1)

                if raw_task:
                    _, task_json = raw_task
                    payload = json.loads(task_json)

                    logger.info(f"Received task: {payload['task_id']}")

                    # 处理任务
                    process_task(payload)

            except KeyboardInterrupt:
                logger.info("Worker shutting down...")
                break

            except Exception as e:
                logger.error(f"Unexpected error in worker loop: {str(e)}", exc_info=True)
                time.sleep(1)  # 避免错误循环


if __name__ == '__main__':
    main()
