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

    # 5. 更新用户余额（充值到 recharge_balance）
    points = cdk.points
    user.recharge_balance += points

    # 6. 记录流水
    new_balance = user.recharge_balance
    transaction = Transaction(
        user_id=user_id,
        type='recharge',
        balance_type='recharge',  # 标记为充值积分
        amount=points,
        balance_snapshot=new_balance,
        related_id=str(cdk.id),
        remark=f"CDK recharge: {code}"
    )
    db.session.add(transaction)

    # 6.5 如果 CDK 指定了 grant_level，且用户当前等级低于该等级，则升级用户等级
    upgraded_to = None
    try:
        if getattr(cdk, 'grant_level', None):
            grant = int(cdk.grant_level)
            if user.level is None or user.level < grant:
                user.level = grant
                upgraded_to = grant
                # 可在 remark 中追加升级信息
                transaction.remark = f"{transaction.remark}; upgraded_to_T{grant}"
                db.session.add(transaction)
    except Exception:
        # 忽略升级失败，继续完成兑换（不会阻塞兑换）
        upgraded_to = None

    # 7. 提交事务
    try:
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        raise ValueError(f"Failed to redeem CDK: {str(e)}")

    result = {
        "added_points": points,
        "current_balance": float(new_balance)
    }
    if upgraded_to:
        result['upgraded_to'] = upgraded_to
    return result


def check_and_deduct_balance(user_id: int, amount: float, task_id: str):
    """
    检查余额并扣除（优先扣除活动积分）

    扣除策略：
    1. 优先扣除 activity_balance
    2. 不足时扣除 recharge_balance
    3. 两者合计不足时抛出异常

    流水记录：
    - 如果只扣除活动积分：1条流水（balance_type='activity'）
    - 如果同时扣除：2条流水（分别记录）

    Args:
        user_id: 用户 ID
        amount: 扣除金额
        task_id: 任务 ID

    Raises:
        ValueError: 余额不足
    """
    from decimal import Decimal

    user = User.query.with_for_update().get(user_id)  # 悲观锁
    if not user:
        raise ValueError("User not found")

    # 计算总余额
    total_balance = user.recharge_balance + user.activity_balance
    if total_balance < amount:
        raise ValueError(
            f"Insufficient balance. Required: {amount}, Available: {total_balance}"
        )

    # 计算扣除方案
    amount_decimal = Decimal(str(amount))
    deduct_from_activity = min(user.activity_balance, amount_decimal)
    deduct_from_recharge = amount_decimal - deduct_from_activity

    # 扣除积分
    user.activity_balance -= deduct_from_activity
    user.recharge_balance -= deduct_from_recharge

    # 记录流水（活动积分部分）
    if deduct_from_activity > 0:
        transaction1 = Transaction(
            user_id=user_id,
            type='task_cost',
            balance_type='activity',
            amount=-deduct_from_activity,
            balance_snapshot=user.activity_balance,
            related_id=task_id,
            remark=f"Task cost (activity): {task_id}"
        )
        db.session.add(transaction1)

    # 记录流水（充值积分部分）
    if deduct_from_recharge > 0:
        transaction2 = Transaction(
            user_id=user_id,
            type='task_cost',
            balance_type='recharge',
            amount=-deduct_from_recharge,
            balance_snapshot=user.recharge_balance,
            related_id=task_id,
            remark=f"Task cost (recharge): {task_id}"
        )
        db.session.add(transaction2)

    try:
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        raise ValueError(f"Failed to deduct balance: {str(e)}")


def execute_refund(user_id: int, amount: float, task_id: str, reason: str = "Task failed"):
    """
    执行退款 (任务失败时调用)

    简化处理：统一退到 recharge_balance

    Args:
        user_id: 用户 ID
        amount: 退款金额
        task_id: 任务 ID
        reason: 退款原因
    """
    from decimal import Decimal

    user = User.query.get(user_id)
    if not user:
        return  # 用户不存在，无法退款

    # 退款到充值余额（转换为 Decimal）
    amount_decimal = Decimal(str(amount))
    user.recharge_balance += amount_decimal

    # 记录流水
    transaction = Transaction(
        user_id=user_id,
        type='refund',
        balance_type='recharge',  # 标记为充值积分
        amount=amount_decimal,  # 正数表示收入
        balance_snapshot=user.recharge_balance,
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
