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
from zoneinfo import ZoneInfo
from sqlalchemy import text
from app import create_app
from app.extensions import db
from app.models.task import Task
from app.services.key_manager import KeyManager
from app.services.pay_service import execute_refund
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


def _sanitize_error_message(error_msg: str) -> str:
    """
    过滤错误信息，隐藏敏感信息，给用户友好的提示

    Args:
        error_msg: 原始错误信息

    Returns:
        str: 过滤后的用户友好错误信息
    """
    import re

    # 隐藏API域名
    error_msg = re.sub(r'https?://[^\s/]+', '[API服务]', error_msg)

    # 转换常见技术错误为用户友好信息
    error_mappings = {
        'Read timed out': '请求超时，请稍后重试',
        'Connection timed out': '网络连接超时，请稍后重试',
        'Connection failed': '网络连接失败，请稍后重试',
        'SSL error': '安全连接错误，请稍后重试',
        'DNS resolution failed': '网络连接错误，请稍后重试',
        'HTTPSConnectionPool': '网络请求失败，请稍后重试',
        'ConnectionError': '网络连接错误，请稍后重试',
        'Timeout': '请求超时，请稍后重试',
        '500': '服务器内部错误，请稍后重试',
        '502': '服务器网关错误，请稍后重试',
        '503': '服务器暂时不可用，请稍后重试',
        '504': '服务器响应超时，请稍后重试'
    }

    # 应用错误映射
    for tech_error, user_friendly in error_mappings.items():
        if tech_error.lower() in error_msg.lower():
            return user_friendly

    # 如果没有匹配到特定错误，返回通用错误信息
    if 'timeout' in error_msg.lower() or 'time out' in error_msg.lower():
        return '请求超时，请稍后重试'
    elif 'connection' in error_msg.lower():
        return '网络连接错误，请稍后重试'
    elif 'http' in error_msg.lower() or 'api' in error_msg.lower():
        return '服务暂时不可用，请稍后重试'
    else:
        # 对于未知错误，返回通用信息
        return '生成失败，请稍后重试'


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

        # 【使用适配器构造请求体】
        submit_payload = adapter.build_submit_payload(payload)

        logger.info(f"Submitting task payload: {submit_payload}")
        print(submit_url, headers, submit_payload)
        resp = requests.post(submit_url, headers=headers, json=submit_payload, timeout=300)
        print(resp)
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

        # 【关键分支】根据任务类型选择处理流程
        if adapter.is_async_task():
            # ========== 异步任务流程（视频生成等） ==========
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
            polling_config = adapter.get_polling_config()
            status_url_pattern = polling_config['status_url_pattern']
            status_url = status_url_pattern.format(
                base=status_base.rstrip('/'),
                task_id=task_uuid
            )
            max_poll_time = polling_config['max_timeout']
            poll_interval = polling_config['interval']
            start_time = time.time()

            while True:
                # 检查是否超时
                if time.time() - start_time > max_poll_time:
                    raise Exception("Task polling timeout")

                time.sleep(poll_interval)

                # 查询状态
                logger.debug(f"Polling status for task {task_id}")
                check = requests.get(status_url, headers=headers, timeout=300)

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
                        "finished_at": datetime.now(ZoneInfo("Asia/Shanghai"))
                    })

                    # 清理 Redis 进度
                    get_redis().delete(f"task:progress:{task_id}")

                    logger.info(f"Task {task_id} completed successfully, result: {result_url}")
                    break

                elif state == 'FAILED':
                    # 任务失败
                    raise Exception(fail_reason or 'Unknown error')

        else:
            # ========== 同步任务流程（图片生成/编辑等） ==========
            logger.info(f"Task {task_id} is synchronous, parsing result directly")

            # 1. 直接从提交响应中解析结果
            result = adapter.parse_sync_response(response_data)

            if not result.get('result_url'):
                logger.error(f"Sync task {task_id} has no result_url in response: {response_data}")
                raise Exception("No result found in synchronous response")

            # 2. 立即更新数据库为成功
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
                "result_url": result['result_url'],
                "finished_at": datetime.now(ZoneInfo("Asia/Shanghai"))
            })

            logger.info(f"Task {task_id} completed synchronously, result: {result['result_url']}")

    except Exception as e:
        # 任务失败处理（使用原始 SQL）
        logger.error(f"Task {task_id} failed: {str(e)}")

        fail_reason = _sanitize_error_message(str(e))[:255]  # 限制长度并过滤敏感信息

        # 【智能退款逻辑】根据失败原因判断是否退款
        should_refund = _should_refund_on_failure(fail_reason)

        if should_refund:
            # 系统错误或非用户责任，进行退款
            # 先查询任务的 cost_points 和 user_id
            cost_sql = text("SELECT cost_points, user_id FROM tasks WHERE id = :task_id")
            cost_result = query_sql(cost_sql, {"task_id": task_id})

            if cost_result:
                refund_amount, task_user_id = cost_result

                # 更新任务状态为失败
                fail_sql = text("""
                    UPDATE tasks
                    SET status = 'failed',
                        progress = 0,
                        fail_reason = :fail_reason,
                        finished_at = :finished_at
                    WHERE id = :task_id
                """)
                execute_sql(fail_sql, {
                    "task_id": task_id,
                    "fail_reason": fail_reason,
                    "finished_at": datetime.now(ZoneInfo("Asia/Shanghai"))
                })

                # 使用统一的 pay_service 进行退款
                with app.app_context():
                    execute_refund(task_user_id, float(refund_amount), task_id, fail_reason)
                    db.session.remove()  # 清理 session 避免缓存问题

                logger.info(f"Refunded {refund_amount} points to user {task_user_id} for task {task_id} (reason: {fail_reason[:50]})")
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
                "finished_at": datetime.now(ZoneInfo("Asia/Shanghai"))
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
