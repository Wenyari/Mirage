"""
活动服务层 (Activity Service)
包含活动领取、签到、过期处理等核心业务逻辑
"""
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
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
    now = datetime.now(ZoneInfo("Asia/Shanghai"))
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
        expire_at = datetime.now(ZoneInfo("Asia/Shanghai")) + timedelta(days=activity.expire_days)

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
    每日签到 - 修复版
    核心变更：计算好 consecutive_days 后直接存入数据库
    """
    user = User.query.with_for_update().get(user_id)
    if not user:
        raise ValueError("User not found")

    now = datetime.now(ZoneInfo("Asia/Shanghai"))
    today_date = now.strftime('%Y-%m-%d')
    yesterday = (now - timedelta(days=1)).strftime('%Y-%m-%d')
    print("1111111111111111111111111111111111111111111111", user.consecutive_days)
    # 1. 检查是否重复签到
    if user.last_checkin_at:
        last_date = user.last_checkin_at.strftime('%Y-%m-%d')
        if last_date == today_date:
            raise ValueError("Already checked in today")
        
        # 2. 判断是否连续
        if last_date == yesterday:
            # 连续：天数+1。如果超过7天，看你的需求是循环(1-7)还是累加
            # 这里保持你原有的循环逻辑：
            current_consecutive = (user.consecutive_days % 7) + 1
        else:
            # 断签：重置为1
            current_consecutive = 1
    else:
        # 首次签到
        current_consecutive = 1

    # 3. 获取奖励配置
    checkin_config = CheckinConfig.query.filter_by(
        day=current_consecutive, 
        is_active=1
    ).first()

    points = checkin_config.points if checkin_config else 0

    # 4. 更新数据库状态 (关键步骤)
    user.activity_balance += points
    user.last_checkin_at = now
    user.total_checkin_days += 1
    user.consecutive_days = current_consecutive  # <--- 直接保存计算好的连续天数

    # 创建流水
    transaction = Transaction(
        user_id=user_id,
        type='checkin',
        balance_type='activity',
        amount=points,
        balance_snapshot=user.activity_balance,
        remark=f"Daily checkin (day {current_consecutive})"
    )
    db.session.add(transaction)

    try:
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        raise ValueError(f"Failed to checkin: {str(e)}")
    print("consecutive_days", current_consecutive)
    return {
        "points": float(points),
        "consecutive_days": current_consecutive,
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
            ActivityClaim.expire_at <= datetime.now(ZoneInfo("Asia/Shanghai")),
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
            claim.expired_at = datetime.now(ZoneInfo("Asia/Shanghai"))

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
    获取签到状态 - 修复版
    核心变更：不再反推天数，而是根据 last_checkin_at 和存储的 consecutive_days 判断
    """
    user = User.query.get(user_id)
    if not user:
        raise ValueError("User not found")

    now = datetime.now(ZoneInfo("Asia/Shanghai"))
    today_date = now.strftime('%Y-%m-%d')
    
    has_checked_today = False
    display_consecutive_days = 0

    if user.last_checkin_at:
        last_date = user.last_checkin_at.strftime('%Y-%m-%d')
        yesterday = (now - timedelta(days=1)).strftime('%Y-%m-%d')

        if last_date == today_date:
            # 情况A：今天已签到
            has_checked_today = True
            # 直接读取数据库中存储的连续天数
            display_consecutive_days = user.consecutive_days
        elif last_date == yesterday:
            # 情况B：今天没签，但昨天签了（还在连续中）
            has_checked_today = False
            display_consecutive_days = user.consecutive_days
        else:
            # 情况C：断签了（昨天没签）
            has_checked_today = False
            display_consecutive_days = 0 
    else:
        # 新用户
        display_consecutive_days = 0

    # 计算下一个奖励
    # 逻辑：
    # 如果今天已签到(Day 3)，下个奖励是 Day 4 (3+1)
    # 如果今天没签到且没断签(Day 2)，今天要签的是 Day 3 (2+1)，所以"下个"奖励其实是当前的待领取奖励
    # 如果断签(0)，今天要签的是 Day 1 (0+1)
    
    # 注意：这里取决于前端对于"Next Reward"的定义。
    # 通常前端展示为：
    # 已签到 -> "明日可领 X 分"
    # 未签到 -> "今日签到可领 Y 分"
    
    if has_checked_today:
        next_day_cycle = (display_consecutive_days % 7) + 1
    else:
        next_day_cycle = (display_consecutive_days % 7) + 1
        
    next_config = CheckinConfig.query.filter_by(day=next_day_cycle, is_active=1).first()
    next_reward = float(next_config.points) if next_config else 0.00

    return {
        "has_checked_today": has_checked_today,
        "consecutive_days": display_consecutive_days,
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
    now = datetime.now(ZoneInfo("Asia/Shanghai"))

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
