"""
Sora 任务处理 (异步 Worker)
这是被 RQ Worker 执行的后台任务
"""
import time
from datetime import datetime
from app import create_app
from app.extensions import db
from app.models import Task
from app.services.model_gw import get_gateway
from app.services.pay_service import execute_refund

# 创建 Flask 应用上下文 (Worker 需要)
app = create_app()


def process_sora_task(task_payload: dict):
    """
    处理 Sora 生成任务

    执行流程:
    1. 从 Redis 队列取出任务数据
    2. 调用上游模型 API (通过 model_gw)
    3. 轮询上游 API 直到任务完成
    4. 【成功】: 更新 Task 状态为 success，保存 result_url
    5. 【失败】: 更新 Task 状态为 failed，执行自动退款

    Args:
        task_payload: {
            "task_id": "uuid",
            "user_id": 1,
            "model_name": "sora-v2",
            "prompt": "...",
            "input_file_url": "...",
            "params": {...}
        }
    """
    with app.app_context():
        task_id = task_payload['task_id']
        user_id = task_payload['user_id']
        model_name = task_payload['model_name']
        prompt = task_payload['prompt']
        params = task_payload.get('params', {})

        try:
            # 1. 获取数据库中的任务记录
            task = Task.query.get(task_id)
            if not task:
                app.logger.error(f"Task {task_id} not found in database")
                return

            # 2. 更新任务状态为 processing
            task.status = 'processing'
            db.session.commit()

            # 3. 调用模型网关
            gateway = get_gateway(model_name)

            # 提交任务到上游
            upstream_result = gateway.call_model(
                model_name=model_name,
                prompt=prompt,
                params=params
            )

            upstream_job_id = upstream_result.get('job_id')
            if not upstream_job_id:
                raise Exception("Failed to get upstream job ID")

            app.logger.info(f"Task {task_id} submitted to upstream, job_id: {upstream_job_id}")

            # 4. 轮询上游状态 (最多轮询 10 分钟)
            max_attempts = 120  # 10 分钟 (每 5 秒一次)
            attempt = 0

            while attempt < max_attempts:
                time.sleep(5)  # 等待 5 秒

                # 查询上游状态
                status_result = gateway.get_job_status(upstream_job_id)
                status = status_result.get('status')

                if status == 'success':
                    # 5. 【成功】: 保存结果
                    task.status = 'success'
                    task.result_url = status_result.get('result_url')
                    task.finished_at = datetime.now()
                    db.session.commit()

                    app.logger.info(f"Task {task_id} completed successfully")
                    return

                elif status == 'failed':
                    # 6. 【失败】: 退款
                    fail_reason = status_result.get('fail_reason', 'Unknown error')
                    task.status = 'failed'
                    task.fail_reason = fail_reason
                    task.finished_at = datetime.now()
                    db.session.commit()

                    # 执行退款
                    execute_refund(
                        user_id=user_id,
                        amount=float(task.cost_points),
                        task_id=task_id,
                        reason=f"Task failed: {fail_reason}"
                    )

                    app.logger.error(f"Task {task_id} failed: {fail_reason}")
                    return

                else:
                    # 仍在处理中，继续轮询
                    attempt += 1
                    app.logger.info(f"Task {task_id} still processing, attempt {attempt}/{max_attempts}")

            # 超时
            raise Exception(f"Task timeout after {max_attempts} attempts")

        except Exception as e:
            # 异常处理: 标记为失败并退款
            app.logger.error(f"Task {task_id} processing error: {e}")

            task = Task.query.get(task_id)
            if task:
                task.status = 'failed'
                task.fail_reason = str(e)
                task.finished_at = datetime.now()
                db.session.commit()

                # 执行退款
                execute_refund(
                    user_id=user_id,
                    amount=float(task.cost_points),
                    task_id=task_id,
                    reason=f"System error: {str(e)}"
                )
