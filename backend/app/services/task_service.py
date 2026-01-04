"""
任务管理服务
负责任务的创建、提交、取消等业务逻辑
集成密钥池调度系统
"""
import json
import logging
import uuid
from datetime import datetime
from decimal import Decimal
from app.extensions import db
from app.models.task import Task
from app.models.user import User, MembershipConfig
from app.models.model import ModelConfig
from app.services.key_manager import KeyManager

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

        # 检查余额
        if user.balance < cost:
            raise ValueError(f"Insufficient balance. Required: {cost}, Available: {user.balance}")

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

        # 5. 扣除积分（预扣费）
        user.balance -= Decimal(str(cost))

        # 6. 创建任务记录
        task_id = str(uuid.uuid4())
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
        )

        db.session.add(task)
        db.session.commit()

        logger.info(f"Task {task_id} created for user {user_id}, cost: {cost}")

        # 7. 构造任务 Payload
        payload = {
            "task_id": task_id,
            "user_id": user_id,
            "model": model_key,
            "params": params,
            "prompt": prompt,
            "input_file_url": input_file_url,
        }

        # 8. 尝试直接获取密钥（快车道）
        key = KeyManager.allocate_key(model_key)

        if key:
            # 有资源 -> 注入密钥 -> 进执行队列
            payload['key_id'] = key.id
            payload['api_base'] = key.api_base
            payload['api_key'] = key.key_secret

            get_redis().rpush(KeyManager.QUEUE_RUNNABLE, json.dumps(payload))
            msg = "Task is being processed"
            logger.info(f"Task {task_id} directly dispatched to runnable queue with key {key.id}")
        else:
            # 无资源 -> 进等待队列（慢车道）
            # 根据用户等级分流
            target_queue = KeyManager.QUEUE_VIP if user.level >= 4 else KeyManager.QUEUE_NORMAL

            get_redis().rpush(target_queue, json.dumps(payload))
            msg = "Task is in priority queue" if user.level >= 4 else "Task is in queue"
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

        # 修改状态为 cancelled（惰性删除）
        task.status = 'cancelled'
        task.progress = 0

        # 退款
        user = User.query.get(user_id)
        user.balance += task.cost_points

        db.session.commit()

        logger.info(f"Task {task_id} cancelled by user {user_id}, refunded {task.cost_points}")

        return {"msg": "Task cancelled successfully"}

    @classmethod
    def get_task_status(cls, user_id: int, task_id: str):
        """
        获取任务状态（支持实时进度）

        Args:
            user_id: 用户 ID
            task_id: 任务 ID

        Returns:
            dict: 任务详情

        Raises:
            ValueError: 业务错误
        """
        task = Task.query.get(task_id)

        if not task:
            raise ValueError("Task not found")

        if task.user_id != user_id:
            raise ValueError("Permission denied")

        # 如果任务正在执行，从 Redis 读取实时进度
        if task.status == 'processing':
            redis_progress = get_redis().get(f"task:progress:{task_id}")
            if redis_progress:
                task.progress = int(redis_progress)

        return task.to_dict()

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
