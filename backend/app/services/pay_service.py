"""
支付服务层 (Pay Service)
包含 CDK 兑换、积分扣除、退款等核心业务逻辑
"""
from datetime import datetime
from sqlalchemy import select
from app.extensions import db
from app.models import User, CDK, Transaction


def redeem_cdk(user_id: int, code: str) -> dict:
    """
    CDK 兑换 (使用悲观锁防止并发)

    1. 开启 DB 事务
    2. SELECT * FROM cdk WHERE code=code FOR UPDATE (悲观锁)
    3. 校验状态 (未使用、未过期)
    4. UPDATE cdk SET status=1, used_by=user_id
    5. UPDATE users SET balance = balance + points
    6. INSERT INTO transactions (类型=充值)
    7. 提交事务

    Args:
        user_id: 用户 ID
        code: 兑换码

    Returns:
        dict: {"added_points": 100, "current_balance": 500}

    Raises:
        ValueError: CDK 无效、已使用、已过期等
    """
    # 1. 查询用户
    user = User.query.get(user_id)
    if not user:
        raise ValueError("User not found")

    # 2. 开启事务，使用悲观锁查询 CDK
    cdk = db.session.query(CDK).filter_by(code=code).with_for_update().first()

    if not cdk:
        raise ValueError("Invalid CDK code")

    # 3. 校验状态
    if cdk.status == 1:
        raise ValueError("CDK has already been used")

    if cdk.status == 2:
        raise ValueError("CDK has been invalidated")

    # 检查过期时间
    if cdk.expire_at and cdk.expire_at < datetime.utcnow():
        raise ValueError("CDK has expired")

    # 4. 根据 CDK 类型处理
    # 一次性码: 标记已使用
    # 通用码: 不修改状态，可重复使用
    if cdk.type == 'once':
        cdk.status = 1
        cdk.used_by = user_id
        cdk.used_at = datetime.utcnow()

    # 5. 更新用户余额
    points = cdk.points
    user.balance += points

    # 6. 记录流水
    new_balance = user.balance
    transaction = Transaction(
        user_id=user_id,
        type='recharge',
        amount=points,
        balance_snapshot=new_balance,
        related_id=str(cdk.id),
        remark=f"CDK recharge: {code}"
    )
    db.session.add(transaction)

    # 7. 提交事务
    try:
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        raise ValueError(f"Failed to redeem CDK: {str(e)}")

    return {
        "added_points": points,
        "current_balance": float(new_balance)
    }


def check_and_deduct_balance(user_id: int, amount: float, task_id: str):
    """
    检查余额并扣除 (任务提交时调用)

    1. 查询用户余额
    2. 如果 balance < amount，抛出 '余额不足'
    3. UPDATE users SET balance = balance - amount
    4. INSERT INTO transactions (类型=消费, related_id=task_id)

    Args:
        user_id: 用户 ID
        amount: 扣除金额
        task_id: 任务 ID

    Raises:
        ValueError: 余额不足
    """
    user = User.query.get(user_id)
    if not user:
        raise ValueError("User not found")

    # 检查余额
    if user.balance < amount:
        raise ValueError(
            f"Insufficient balance. Required: {amount}, Available: {user.balance}"
        )

    # 扣除余额
    user.balance -= amount

    # 记录流水
    transaction = Transaction(
        user_id=user_id,
        type='task_cost',
        amount=-amount,  # 负数表示支出
        balance_snapshot=user.balance,
        related_id=task_id,
        remark=f"Task cost: {task_id}"
    )
    db.session.add(transaction)

    try:
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        raise ValueError(f"Failed to deduct balance: {str(e)}")


def execute_refund(user_id: int, amount: float, task_id: str, reason: str = "Task failed"):
    """
    执行退款 (任务失败时调用)

    1. UPDATE users SET balance = balance + amount
    2. INSERT INTO transactions (类型=退款)

    Args:
        user_id: 用户 ID
        amount: 退款金额
        task_id: 任务 ID
        reason: 退款原因
    """
    user = User.query.get(user_id)
    if not user:
        return  # 用户不存在，无法退款

    # 退款
    user.balance += amount

    # 记录流水
    transaction = Transaction(
        user_id=user_id,
        type='refund',
        amount=amount,  # 正数表示收入
        balance_snapshot=user.balance,
        related_id=task_id,
        remark=f"Refund: {reason}"
    )
    db.session.add(transaction)

    try:
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        # 记录日志但不抛出异常
        from flask import current_app
        current_app.logger.error(f"Failed to execute refund: {e}")
