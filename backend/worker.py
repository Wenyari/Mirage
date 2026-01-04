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
from app import create_app
from app.extensions import db
from app.models.task import Task
from app.services.key_manager import KeyManager

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

    logger.info(f"Processing task {task_id} with key {key_id}")

    # 1. 更新 DB 为 Processing
    task = Task.query.get(task_id)
    if not task:
        logger.error(f"Task {task_id} not found in database")
        return

    task.status = 'processing'
    task.api_key_id = key_id
    db.session.commit()

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

        # 解析响应
        response_data = resp.json()
        task_uuid = response_data.get('id')

        if not task_uuid:
            raise Exception("No task ID returned from API")

        logger.info(f"Task {task_id} submitted successfully, upstream ID: {task_uuid}")

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

            data = check.json()
            state = data.get('status')  # SUCCEEDED / FAILED / RUNNING
            progress = data.get('progress', 0)

            logger.debug(f"Task {task_id} status: {state}, progress: {progress}%")

            # 写入 Redis 实时进度
            if state in ['RUNNING', 'PROCESSING']:
                get_redis().setex(f"task:progress:{task_id}", 86400, progress)

            elif state in ['SUCCEEDED', 'SUCCESS', 'COMPLETED']:
                # 任务成功
                task.status = 'success'
                task.progress = 100
                task.result_url = data.get('output', {}).get('url') or data.get('result_url')
                task.finished_at = datetime.now()

                # 清理 Redis 进度
                get_redis().delete(f"task:progress:{task_id}")

                db.session.commit()
                logger.info(f"Task {task_id} completed successfully")
                break

            elif state in ['FAILED', 'ERROR']:
                # 任务失败
                fail_reason = data.get('failure_reason') or data.get('error') or 'Unknown error'
                raise Exception(fail_reason)

    except Exception as e:
        # 任务失败处理
        logger.error(f"Task {task_id} failed: {str(e)}")

        task.status = 'failed'
        task.progress = 0
        task.fail_reason = str(e)[:255]  # 限制长度
        task.finished_at = datetime.now()

        # 清理 Redis 进度
        get_redis().delete(f"task:progress:{task_id}")

        db.session.commit()

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
