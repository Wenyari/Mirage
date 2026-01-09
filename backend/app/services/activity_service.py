"""
活动服务层 (Activity Service)
包含活动领取、签到、过期处理等核心业务逻辑
"""
from datetime import datetime, timedelta
from decimal import Decimal
from sqlalchemy import and_
from app.extensions import db
from app.models.user import User
from app.models.wallet import Transaction
from app.models.activity import Activity, ActivityClaim, CheckinConfig


def claim_activity(user_id: int, activity_code: str) -> dict:
    """
    领取活动积分

    业务流程：
    1. 验证活动（存在、有效期、状态）
    2. 验证用户权限（等级要求）
    3. 检查领取次数限制
    4. 使用悲观锁更新 activity_balance
    5. 创建 activity_claims 记录
    6. 创建 transactions 流水

    Args:
        user_id: 用户 ID
        activity_code: 活动代码

    Returns:
        dict: {
            "points": 100,
            "expire_at": "2024-04-01T00:00:00",
            "current_activity_balance": 500,
            "total_balance": 1500
        }

    Raises:
        ValueError: 活动无效、已达领取上限等
    """
    # 查询活动（使用悲观锁）
    activity = Activity.query.filter_by(code=activity_code).with_for_update().first()
    if not activity:
        raise ValueError("Activity not found")

    # 验证活动状态
    if activity.status != 'active':
        raise ValueError(f"Activity is {activity.status}")

    # 验证时间范围
    now = datetime.utcnow()
    if activity.start_at and activity.start_at > now:
        raise ValueError("Activity has not started")
    if activity.end_at and activity.end_at < now:
        raise ValueError("Activity has ended")

    # 查询用户（使用悲观锁）
    user = User.query.with_for_update().get(user_id)
    if not user:
        raise ValueError("User not found")

    # 验证用户等级
    if activity.required_level and user.level < activity.required_level:
        raise ValueError(f"Requires level T{activity.required_level} or higher")

    # 检查领取次数
    claim_count = ActivityClaim.query.filter_by(
        user_id=user_id,
        activity_id=activity.id
    ).count()

    if claim_count >= activity.max_claims_per_user:
        raise ValueError("Claim limit reached")

    # 增加活动积分
    user.activity_balance += activity.points

    # 计算过期时间
    expire_at = None
    if activity.expire_days:
        expire_at = datetime.utcnow() + timedelta(days=activity.expire_days)

    # 创建领取记录
    claim = ActivityClaim(
        user_id=user_id,
        activity_id=activity.id,
        points_granted=activity.points,
        expire_at=expire_at,
        status='active'
    )
    db.session.add(claim)

    # 创建流水
    transaction = Transaction(
        user_id=user_id,
        type='activity_grant',
        balance_type='activity',
        amount=activity.points,
        balance_snapshot=user.activity_balance,
        activity_id=activity.id,
        remark=f"Activity: {activity.name}"
    )
    db.session.add(transaction)

    try:
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        raise ValueError(f"Failed to claim activity: {str(e)}")

    return {
        "points": float(activity.points),
        "expire_at": expire_at.isoformat() if expire_at else None,
        "current_activity_balance": float(user.activity_balance),
        "total_balance": float(user.recharge_balance + user.activity_balance)
    }


def daily_checkin(user_id: int) -> dict:
    """
    每日签到

    业务流程：
    1. 检查今天是否已签到
    2. 判断连续签到天数
    3. 获取奖励积分
    4. 更新 activity_balance
    5. 更新签到信息
    6. 创建流水

    Args:
        user_id: 用户 ID

    Returns:
        dict: {
            "points": 20,
            "consecutive_days": 3,
            "total_checkin_days": 15,
            "current_activity_balance": 520,
            "total_balance": 1520
        }

    Raises:
        ValueError: 今日已签到、配置错误等
    """
    user = User.query.with_for_update().get(user_id)
    if not user:
        raise ValueError("User not found")

    now = datetime.utcnow()
    today_date = now.strftime('%Y-%m-%d')

    # 检查今天是否已签到
    if user.last_checkin_at:
        last_date = user.last_checkin_at.strftime('%Y-%m-%d')
        if last_date == today_date:
            raise ValueError("Already checked in today")

        # 判断是否连续签到
        yesterday = (now - timedelta(days=1)).strftime('%Y-%m-%d')
        if last_date == yesterday:
            # 连续签到，天数+1（循环1-7）
            consecutive_days = (user.total_checkin_days % 7) + 1
        else:
            # 断签，重置为第1天
            consecutive_days = 1
    else:
        consecutive_days = 1

    # 从配置获取奖励积分
    checkin_config = CheckinConfig.query.filter_by(
        day=consecutive_days,
        is_active=1
    ).first()

    if not checkin_config:
        raise ValueError("Checkin config not found")

    points = checkin_config.points

    # 更新用户数据
    user.activity_balance += points
    user.last_checkin_at = now
    user.total_checkin_days += 1

    # 创建流水
    transaction = Transaction(
        user_id=user_id,
        type='checkin',
        balance_type='activity',
        amount=points,
        balance_snapshot=user.activity_balance,
        remark=f"Daily checkin (day {consecutive_days})"
    )
    db.session.add(transaction)

    try:
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        raise ValueError(f"Failed to checkin: {str(e)}")

    return {
        "points": float(points),
        "consecutive_days": consecutive_days,
        "total_checkin_days": user.total_checkin_days,
        "current_activity_balance": float(user.activity_balance),
        "total_balance": float(user.recharge_balance + user.activity_balance)
    }


def expire_activity_points() -> dict:
    """
    处理过期的活动积分（定时任务调用）

    业务流程：
    1. 查询过期的 activity_claims（expire_at <= now, status='active'）
    2. 批量处理（每次100条）
    3. 扣除用户 activity_balance
    4. 更新 claim status = 'expired'
    5. 创建流水

    Returns:
        dict: {
            "expired_count": 15,
            "total_points_expired": 1500.00
        }
    """
    expired_count = 0
    total_points_expired = Decimal('0.00')

    # 批量处理（避免长事务）
    BATCH_SIZE = 100

    while True:
        expired_claims = ActivityClaim.query.filter(
            ActivityClaim.expire_at <= datetime.utcnow(),
            ActivityClaim.status == 'active'
        ).limit(BATCH_SIZE).with_for_update().all()

        if not expired_claims:
            break

        for claim in expired_claims:
            user = User.query.with_for_update().get(claim.user_id)
            if not user:
                continue

            # 计算实际扣除金额（不能超过当前余额）
            deduct_amount = min(claim.points_granted, user.activity_balance)

            if deduct_amount > 0:
                user.activity_balance -= deduct_amount

                # 创建流水
                transaction = Transaction(
                    user_id=claim.user_id,
                    type='activity_expire',
                    balance_type='activity',
                    amount=-deduct_amount,
                    balance_snapshot=user.activity_balance,
                    activity_id=claim.activity_id,
                    remark=f"Activity points expired"
                )
                db.session.add(transaction)

            # 更新状态
            claim.status = 'expired'
            claim.expired_at = datetime.utcnow()

            expired_count += 1
            total_points_expired += deduct_amount

        try:
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            from flask import current_app
            current_app.logger.error(f"Failed to expire activity points: {e}")
            break

    return {
        "expired_count": expired_count,
        "total_points_expired": float(total_points_expired)
    }


def get_checkin_status(user_id: int) -> dict:
    """
    获取签到状态

    Args:
        user_id: 用户 ID

    Returns:
        dict: {
            "has_checked_today": false,
            "consecutive_days": 2,
            "total_checkin_days": 15,
            "last_checkin_at": "2024-03-01T08:00:00",
            "next_reward": 20.00
        }
    """
    user = User.query.get(user_id)
    if not user:
        raise ValueError("User not found")

    now = datetime.utcnow()
    today_date = now.strftime('%Y-%m-%d')

    # 检查今天是否已签到
    has_checked_today = False
    consecutive_days = 0

    if user.last_checkin_at:
        last_date = user.last_checkin_at.strftime('%Y-%m-%d')
        if last_date == today_date:
            has_checked_today = True
            consecutive_days = (user.total_checkin_days % 7)
            if consecutive_days == 0:
                consecutive_days = 7
        else:
            # 判断是否连续签到
            yesterday = (now - timedelta(days=1)).strftime('%Y-%m-%d')
            if last_date == yesterday:
                consecutive_days = (user.total_checkin_days % 7)
            else:
                consecutive_days = 0

    # 获取下次签到奖励
    next_day = consecutive_days + 1 if consecutive_days < 7 else 1
    next_config = CheckinConfig.query.filter_by(day=next_day, is_active=1).first()
    next_reward = float(next_config.points) if next_config else 0.00

    return {
        "has_checked_today": has_checked_today,
        "consecutive_days": consecutive_days,
        "total_checkin_days": user.total_checkin_days,
        "last_checkin_at": user.last_checkin_at.isoformat() if user.last_checkin_at else None,
        "next_reward": next_reward
    }


def get_active_activities() -> list:
    """
    获取当前可用活动列表

    Returns:
        list: [
            {
                "id": 1,
                "code": "SPRING2024",
                "name": "春季福利",
                "description": "...",
                "points": 100,
                "expire_days": 30,
                "required_level": 1,
                "start_at": "...",
                "end_at": "..."
            }
        ]
    """
    now = datetime.utcnow()

    activities = Activity.query.filter(
        Activity.status == 'active',
        (Activity.start_at.is_(None)) | (Activity.start_at <= now),
        (Activity.end_at.is_(None)) | (Activity.end_at >= now)
    ).all()

    return [activity.to_dict() for activity in activities]


def get_user_activities(user_id: int, page: int = 1, size: int = 20) -> dict:
    """
    获取用户领取记录（分页）

    Args:
        user_id: 用户 ID
        page: 页码
        size: 每页大小

    Returns:
        dict: {
            "list": [...],
            "total": 50,
            "page": 1,
            "size": 20
        }
    """
    pagination = ActivityClaim.query.filter_by(user_id=user_id)\
        .order_by(ActivityClaim.claimed_at.desc())\
        .paginate(page=page, per_page=size, error_out=False)

    # 获取活动详情
    claims_list = []
    for claim in pagination.items:
        claim_dict = claim.to_dict()

        # 附加活动信息
        activity = Activity.query.get(claim.activity_id)
        if activity:
            claim_dict['activity_name'] = activity.name
            claim_dict['activity_code'] = activity.code

        claims_list.append(claim_dict)

    return {
        "list": claims_list,
        "total": pagination.total,
        "page": page,
        "size": size
    }
