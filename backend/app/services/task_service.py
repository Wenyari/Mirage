"""
任务服务层 (Task Service)
包含任务提交、并发检查、入队等核心业务逻辑
"""
import json
from flask import current_app
from rq import Queue
from app.extensions import db, redis_client
from app.models import Task, User, MembershipConfig, ModelPricing
from app.services.pay_service import check_and_deduct_balance


def get_user_concurrency_limit(user_id: int) -> int:
    """
    获取用户的并发任务数限制

    Args:
        user_id: 用户 ID

    Returns:
        int: 并发任务数限制
    """
    user = User.query.get(user_id)
    if not user:
        raise ValueError("User not found")

    # 查询会员配置
    config = MembershipConfig.query.filter_by(level=user.level).first()
    if not config:
        return 1  # 默认值

    return config.concurrency_limit


def get_model_price(model_name: str) -> float:
    """
    获取模型定价

    Args:
        model_name: 模型名称

    Returns:
        float: 模型价格
    """
    # 先尝试从 Redis 缓存读取
    cache_key = f"config:pricing:{model_name}"
    cached_price = redis_client.get(cache_key)

    if cached_price:
        return float(cached_price)

    # 从数据库查询
    pricing = ModelPricing.query.filter_by(model_key=model_name, is_active=1).first()
    if not pricing:
        raise ValueError(f"Model '{model_name}' not found or not active")

    # 缓存到 Redis (1小时)
    redis_client.setex(cache_key, 3600, str(pricing.base_cost))

    return float(pricing.base_cost)


def submit_task(user_id: int, task_data: dict) -> str:
    """
    提交任务 (核心业务逻辑)

    1. 【并发检查】: 检查用户当前运行中的任务数是否超过配额
    2. 【计算费用】: 根据模型和参数计算需要扣除的积分
    3. 【预扣费】: 调用 pay_service 预扣除积分
    4. 【入库】: 创建 Task 记录，状态为 pending
    5. 【入队】: 根据用户等级将任务推入不同优先级的队列

    Args:
        user_id: 用户 ID
        task_data: 任务数据 {
            "model": "sora-v2",
            "prompt": "...",
            "params": {...},
            "input_file_url": "..."
        }

    Returns:
        str: 任务 ID (UUID)

    Raises:
        ValueError: 并发超限、余额不足等业务错误
    """
    # 1. 【并发检查】
    user = User.query.get(user_id)
    if not user:
        raise ValueError("User not found")

    concurrency_limit = get_user_concurrency_limit(user_id)

    # 统计用户当前运行中的任务数 (pending + processing)
    running_count = Task.query.filter(
        Task.user_id == user_id,
        Task.status.in_(['pending', 'processing'])
    ).count()

    if running_count >= concurrency_limit:
        raise ValueError(
            f"Task limit exceeded. You can run at most {concurrency_limit} tasks simultaneously. "
            f"Please upgrade your membership or wait for existing tasks to complete."
        )

    # 2. 【计算费用】
    model_name = task_data.get('model')
    if not model_name:
        raise ValueError("Model name is required")

    base_cost = get_model_price(model_name)

    # 根据参数调整价格 (例如根据时长)
    params = task_data.get('params', {})
    duration = params.get('duration', 1)  # 默认 1 倍
    cost = base_cost * duration

    # 3. 【预扣费】
    # 创建任务记录 (暂时不提交，获取 task_id 用于流水记录)
    new_task = Task(
        user_id=user_id,
        model_name=model_name,
        prompt=task_data.get('prompt'),
        input_file_url=task_data.get('input_file_url'),
        params=params,
        status='pending',
        cost_points=cost
    )
    db.session.add(new_task)
    db.session.flush()  # 获取 task_id

    try:
        check_and_deduct_balance(user_id, cost, new_task.id)
    except ValueError as e:
        db.session.rollback()
        raise e

    # 4. 【入库】
    db.session.commit()

    # 5. 【入队】
    # 根据用户等级决定队列优先级
    queue_name = 'high_priority' if user.level >= 4 else 'default'

    task_payload = {
        'task_id': new_task.id,
        'user_id': user_id,
        'model_name': model_name,
        'prompt': task_data.get('prompt'),
        'input_file_url': task_data.get('input_file_url'),
        'params': params
    }

    # 推入 RQ 队列
    try:
        q = Queue(queue_name, connection=redis_client)
        from app.tasks.sora_job import process_sora_task
        q.enqueue(process_sora_task, task_payload)
    except Exception as e:
        current_app.logger.error(f"Failed to enqueue task: {e}")
        # 如果入队失败，退款
        from app.services.pay_service import execute_refund
        execute_refund(user_id, cost, new_task.id, "Failed to enqueue task")
        new_task.status = 'failed'
        new_task.fail_reason = "System error: Failed to enqueue task"
        db.session.commit()
        raise ValueError("Failed to submit task, please try again later")

    return new_task.id


def get_task_by_id(task_id: str, user_id: int = None) -> Task:
    """
    根据 ID 查询任务

    Args:
        task_id: 任务 ID
        user_id: 用户 ID (可选，用于权限检查)

    Returns:
        Task: 任务对象

    Raises:
        ValueError: 任务不存在或无权访问
    """
    query = Task.query.filter_by(id=task_id)

    if user_id:
        query = query.filter_by(user_id=user_id)

    task = query.first()
    if not task:
        raise ValueError("Task not found or access denied")

    return task
