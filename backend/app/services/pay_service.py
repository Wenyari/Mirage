"""
支付服务层 (Pay Service)
包含 CDK 兑换、积分扣除、退款等核心业务逻辑
"""
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
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
    if cdk.expire_at:
        # 确保 cdk.expire_at 为 offset-aware
        expire_at = cdk.expire_at
        if expire_at.tzinfo is None:
            expire_at = expire_at.replace(tzinfo=ZoneInfo("Asia/Shanghai"))
            
        if expire_at < datetime.now(ZoneInfo("Asia/Shanghai")):
            raise ValueError("CDK has expired")

    # 4. 根据 CDK 类型处理
    # 一次性码: 标记已使用
    # 通用码: 不修改状态，可重复使用
    if cdk.type == 'once':
        cdk.status = 1
        cdk.used_by = user_id
        cdk.used_at = datetime.now(ZoneInfo("Asia/Shanghai"))

    # 5. 更新用户余额（充值到 recharge_balance）
    points = cdk.points
    user.recharge_balance += points

    # 更新过期时间 (取两者较大值)
    # 更新过期时间 (基于 cdk.valid_days)
    if cdk.valid_days:
        # 有效天数存在，计算新的过期时间
        new_expire_at = datetime.now(ZoneInfo("Asia/Shanghai")) + timedelta(days=cdk.valid_days)
        
        # 1. 如果用户当前余额为0（说明之前的过期时间已无效或已过期），直接设为新时间
        #    注意：用户余额在前面第5步已经加上了 points，所以我们要判断的是“加之前是否有余额”
        #    prev_balance = user.recharge_balance - points
        #    (或者直接检查 expire_at 是否为 None。如果余额>0但expire_at是None，说明是永久；如果余额=0，expire_at也为None)
        
        # 简单逻辑：
        # 如果 user.recharge_balance_expire_at 为 None，分两种情况：
        #   A. 之前是永久会员 (余额 > points) -> 保持 None (永久优先级最高)
        #   B. 之前没余额 (余额 == points) -> 设置为 new_expire_at
        
        # 如果 user.recharge_balance_expire_at 有值 -> 取 max(old, new)
        
        is_first_charge = (user.recharge_balance - points) <= 0
        
        if user.recharge_balance_expire_at is None:
            if is_first_charge:
                 user.recharge_balance_expire_at = new_expire_at
            # else: 之前有余额且expire为None，说明是永久，保持不变
        else:
             # 有旧的过期时间，取较大值
            current_expire_at = user.recharge_balance_expire_at
            if current_expire_at.tzinfo is None:
                current_expire_at = current_expire_at.replace(tzinfo=ZoneInfo("Asia/Shanghai"))
            
            if new_expire_at > current_expire_at:
                user.recharge_balance_expire_at = new_expire_at

    elif cdk.valid_days is None:
        # valid_days 为 None，视为“本次充值积分永久有效”
        # 规则：永久 > 任何期限
        # 所以直接设为 None
        user.recharge_balance_expire_at = None

    # 注意：cdk.expire_at 不再参与积分过期时间的计算，仅用于判断 CDK 本身是否过期。
    # 这样就实现了 cdk 兑换码有效期 vs 充值后的积分有效期的解耦。

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


def check_and_deduct_balance(user_id: int, amount: float, task_id: str, model: str = None):
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
            model=model,
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
            model=model,
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
    执行退款 (任务失败或取消时调用)
    
    修复逻辑：
    查询该任务的扣费流水，将积分原路退回（活动积分退回活动余额，充值积分退回充值余额）
    如果只有充值积分扣除，则全退充值
    如果找不到流水（极少见），兜底退回充值余额

    Args:
        user_id: 用户 ID
        amount: 退款金额
        task_id: 任务 ID
        reason: 退款原因
    """
    from decimal import Decimal
    
    # 使用悲观锁获取用户，防止并发问题
    user = User.query.with_for_update().get(user_id)
    if not user:
        return  # 用户不存在，无法退款

    amount_decimal = Decimal(str(amount))
    
    # 1. 查询该任务的原始扣费记录
    cost_transactions = Transaction.query.filter_by(
        related_id=task_id, 
        type='task_cost'
    ).all()
    
    # 统计从各处扣除的金额（取绝对值，因为 cost 记录是负数）
    deducted_activity = Decimal('0')
    deducted_recharge = Decimal('0')
    
    # 标记是否找到了对应的扣费记录
    found_transactions = False
    
    for tx in cost_transactions:
        found_transactions = True
        abs_amount = abs(tx.amount)
        if tx.balance_type == 'activity':
            deducted_activity += abs_amount
        else:
            # recharge or other types default to recharge refund
            deducted_recharge += abs_amount
            
    # 2. 计算退款分配
    # 正常情况下，退款金额应该等于（或小于）总扣除金额
    # 如果系统有部分退款逻辑，这里按比例或者优先退充值可能更合理？
    # 但目前 execute_refund 通常是全额退款
    
    refund_activity = Decimal('0')
    refund_recharge = Decimal('0')
    
    if found_transactions:
        # 如果找到了流水，按实际扣除情况退款
        # 防止退款金额超过实际扣除金额（以防调用端传错 amount）
        total_deducted = deducted_activity + deducted_recharge
        
        if amount_decimal >= total_deducted:
            # 全额退款（或超额退款，正常不应发生），按原路返回
            refund_activity = deducted_activity
            refund_recharge = amount_decimal - deducted_activity # 剩余的都退充值（如果 amount > total，多出来的也退充值）
        else:
            # 部分退款（极少见）：策略 -> 优先退充值，再退活动？还是优先退活动？
            # 既然扣费是优先扣活动，退款理应优先退充值（对用户有利）？
            # 或者原路退回？为了逻辑一致性，这里简化为：
            # 如果是全额退款场景，直接按扣除比例退。
            # 如果是部分退款，这里简单处理：优先退还充值部分（也就是真正值钱的部分）
            
            if amount_decimal <= deducted_recharge:
                refund_recharge = amount_decimal
            else:
                refund_recharge = deducted_recharge
                refund_activity = amount_decimal - deducted_recharge
    else:
        # 兜底：没找到流水（可能是旧数据或异常），全部退到充值余额
        # 或者 amount 为 0
        refund_recharge = amount_decimal

    # 3. 执行退款更新
    if refund_activity > 0:
        user.activity_balance += refund_activity
        
        # 记录活动积分退款流水
        t1 = Transaction(
            user_id=user_id,
            type='refund',
            balance_type='activity',
            amount=refund_activity,
            balance_snapshot=user.activity_balance,
            related_id=task_id,
            remark=f"Refund (activity): {reason}"
        )
        db.session.add(t1)
        
    if refund_recharge > 0:
        user.recharge_balance += refund_recharge
        
        # 记录充值积分退款流水
        t2 = Transaction(
            user_id=user_id,
            type='refund',
            balance_type='recharge',
            amount=refund_recharge,
            balance_snapshot=user.recharge_balance,
            related_id=task_id,
            remark=f"Refund (recharge): {reason}"
        )
        db.session.add(t2)

    try:
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        # 记录日志但不抛出异常
        from flask import current_app
        current_app.logger.error(f"Failed to execute refund: {e}")


def expire_recharge_points() -> dict:
    """
    清理过期的充值积分 (定时任务调用)

    逻辑：
    1. 查询所有 recharge_balance_expire_at < now 且 recharge_balance > 0 的用户
    2. 将 recharge_balance 重置为 0
    3. 插入 Transaction 记录

    Returns:
        dict: {"expired_count": 10, "total_points_expired": 5000}
    """
    now = datetime.now(ZoneInfo("Asia/Shanghai"))
    
    # 查询过期用户 (recharge_balance > 0 且 expire_at < now)
    # 注意：这里我们不对管理员特殊处理，只要有 expired_at 且过期了就清空。
    # 如果管理员账号不应该过期，则不应该设置 expire_at。
    expired_users = User.query.filter(
        User.recharge_balance > 0,
        User.recharge_balance_expire_at.isnot(None),
        User.recharge_balance_expire_at < now
    ).all()

    expired_count = 0
    total_points = 0.0

    for user in expired_users:
        try:
            points_to_expire = user.recharge_balance
            if points_to_expire <= 0:
                continue

            user.recharge_balance = 0
            user.recharge_balance_expire_at = None # 清空过期时间

            # 记录流水
            tx = Transaction(
                user_id=user.id,
                type='system',
                balance_type='recharge',
                amount=-points_to_expire,
                balance_snapshot=0,
                remark=f"Points expired at {now.strftime('%Y-%m-%d %H:%M:%S')}"
            )
            db.session.add(tx)
            
            expired_count += 1
            total_points += float(points_to_expire)
            
        except Exception as e:
            # 单个用户失败不影响整体
            print(f"Failed to expire points for user {user.id}: {e}")
            continue

    try:
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        raise ValueError(f"Failed to commit expiration: {str(e)}")

    return {
        "expired_count": expired_count,
        "total_points_expired": total_points
    }
