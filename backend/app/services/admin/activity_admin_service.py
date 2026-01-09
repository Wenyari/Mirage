"""
活动管理服务层 (Activity Admin Service)
供管理员使用的活动管理功能
"""
from datetime import datetime
from sqlalchemy import func
from app.extensions import db
from app.models.activity import Activity, ActivityClaim, CheckinConfig


def create_activity(data: dict) -> dict:
    """
    创建活动

    Args:
        data: {
            "code": "SPRING2024",
            "name": "春季福利",
            "description": "...",
            "points": 100,
            "expire_days": 30,
            "max_claims_per_user": 1,
            "required_level": 1,
            "start_at": "2024-03-01T00:00:00",
            "end_at": "2024-03-31T23:59:59"
        }

    Returns:
        dict: 创建的活动信息

    Raises:
        ValueError: 参数错误、活动代码重复等
    """
    # 验证必填字段
    required_fields = ['code', 'name', 'points']
    for field in required_fields:
        if field not in data:
            raise ValueError(f"Missing required field: {field}")

    # 检查活动代码是否已存在
    existing = Activity.query.filter_by(code=data['code']).first()
    if existing:
        raise ValueError(f"Activity code '{data['code']}' already exists")

    # 解析日期时间
    start_at = None
    end_at = None
    if data.get('start_at'):
        try:
            start_at = datetime.fromisoformat(data['start_at'].replace('Z', '+00:00'))
        except ValueError:
            raise ValueError("Invalid start_at format")

    if data.get('end_at'):
        try:
            end_at = datetime.fromisoformat(data['end_at'].replace('Z', '+00:00'))
        except ValueError:
            raise ValueError("Invalid end_at format")

    # 创建活动
    activity = Activity(
        code=data['code'],
        name=data['name'],
        description=data.get('description'),
        points=data['points'],
        expire_days=data.get('expire_days'),
        max_claims_per_user=data.get('max_claims_per_user', 1),
        required_level=data.get('required_level'),
        start_at=start_at,
        end_at=end_at,
        status='active'
    )

    db.session.add(activity)

    try:
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        raise ValueError(f"Failed to create activity: {str(e)}")

    return activity.to_dict()


def update_activity(activity_id: int, data: dict) -> dict:
    """
    更新活动

    Args:
        activity_id: 活动 ID
        data: 要更新的字段

    Returns:
        dict: 更新后的活动信息

    Raises:
        ValueError: 活动不存在、参数错误等
    """
    activity = Activity.query.get(activity_id)
    if not activity:
        raise ValueError("Activity not found")

    # 更新允许的字段
    updatable_fields = [
        'name', 'description', 'points', 'expire_days',
        'max_claims_per_user', 'required_level', 'status'
    ]

    for field in updatable_fields:
        if field in data:
            setattr(activity, field, data[field])

    # 更新日期时间字段
    if 'start_at' in data:
        if data['start_at']:
            try:
                activity.start_at = datetime.fromisoformat(data['start_at'].replace('Z', '+00:00'))
            except ValueError:
                raise ValueError("Invalid start_at format")
        else:
            activity.start_at = None

    if 'end_at' in data:
        if data['end_at']:
            try:
                activity.end_at = datetime.fromisoformat(data['end_at'].replace('Z', '+00:00'))
            except ValueError:
                raise ValueError("Invalid end_at format")
        else:
            activity.end_at = None

    activity.updated_at = datetime.utcnow()

    try:
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        raise ValueError(f"Failed to update activity: {str(e)}")

    return activity.to_dict()


def delete_activity(activity_id: int) -> dict:
    """
    删除活动

    Args:
        activity_id: 活动 ID

    Returns:
        dict: {"msg": "Activity deleted successfully"}

    Raises:
        ValueError: 活动不存在
    """
    activity = Activity.query.get(activity_id)
    if not activity:
        raise ValueError("Activity not found")

    # 检查是否有领取记录
    claims_count = ActivityClaim.query.filter_by(activity_id=activity_id).count()

    if claims_count > 0:
        # 如果有领取记录，建议设置为 ended 而不是删除
        raise ValueError(
            f"Cannot delete activity with {claims_count} claims. "
            "Consider setting status to 'ended' instead."
        )

    db.session.delete(activity)

    try:
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        raise ValueError(f"Failed to delete activity: {str(e)}")

    return {"msg": "Activity deleted successfully"}


def get_activity_list(page: int = 1, size: int = 20, status: str = None) -> dict:
    """
    获取活动列表（分页）

    Args:
        page: 页码
        size: 每页大小
        status: 状态筛选（可选）

    Returns:
        dict: {
            "list": [...],
            "total": 50,
            "page": 1,
            "size": 20
        }
    """
    query = Activity.query

    # 状态筛选
    if status:
        query = query.filter_by(status=status)

    pagination = query.order_by(Activity.created_at.desc())\
        .paginate(page=page, per_page=size, error_out=False)

    return {
        "list": [activity.to_dict() for activity in pagination.items],
        "total": pagination.total,
        "page": page,
        "size": size
    }


def get_activity_stats(activity_id: int) -> dict:
    """
    获取活动统计信息

    Args:
        activity_id: 活动 ID

    Returns:
        dict: {
            "activity_id": 1,
            "total_claims": 150,
            "unique_users": 120,
            "total_points_granted": 15000.00,
            "active_claims": 100,
            "expired_claims": 30,
            "used_claims": 20
        }

    Raises:
        ValueError: 活动不存在
    """
    activity = Activity.query.get(activity_id)
    if not activity:
        raise ValueError("Activity not found")

    # 统计领取记录
    total_claims = ActivityClaim.query.filter_by(activity_id=activity_id).count()
    unique_users = db.session.query(func.count(func.distinct(ActivityClaim.user_id)))\
        .filter(ActivityClaim.activity_id == activity_id)\
        .scalar()

    # 统计赠送积分总额
    total_points = db.session.query(func.sum(ActivityClaim.points_granted))\
        .filter(ActivityClaim.activity_id == activity_id)\
        .scalar()

    # 按状态统计
    active_claims = ActivityClaim.query.filter_by(
        activity_id=activity_id,
        status='active'
    ).count()

    expired_claims = ActivityClaim.query.filter_by(
        activity_id=activity_id,
        status='expired'
    ).count()

    used_claims = ActivityClaim.query.filter_by(
        activity_id=activity_id,
        status='used'
    ).count()

    return {
        "activity_id": activity_id,
        "total_claims": total_claims,
        "unique_users": unique_users or 0,
        "total_points_granted": float(total_points) if total_points else 0.00,
        "active_claims": active_claims,
        "expired_claims": expired_claims,
        "used_claims": used_claims
    }


def get_checkin_config() -> list:
    """
    获取签到配置

    Returns:
        list: [
            {
                "id": 1,
                "day": 1,
                "points": 10.00,
                "is_active": true
            },
            ...
        ]
    """
    configs = CheckinConfig.query.order_by(CheckinConfig.day).all()
    return [config.to_dict() for config in configs]


def update_checkin_config(configs: list) -> dict:
    """
    更新签到配置

    Args:
        configs: [
            {"day": 1, "points": 10.00, "is_active": true},
            {"day": 2, "points": 15.00, "is_active": true},
            ...
        ]

    Returns:
        dict: {"msg": "Checkin config updated successfully"}

    Raises:
        ValueError: 参数错误
    """
    if not configs or not isinstance(configs, list):
        raise ValueError("Invalid configs format")

    # 验证每个配置
    for config_data in configs:
        if 'day' not in config_data or 'points' not in config_data:
            raise ValueError("Missing required fields: day, points")

        day = config_data['day']
        if day < 1 or day > 7:
            raise ValueError(f"Invalid day: {day}, must be between 1 and 7")

        # 查询或创建配置
        config = CheckinConfig.query.filter_by(day=day).first()

        if config:
            # 更新现有配置
            config.points = config_data['points']
            config.is_active = config_data.get('is_active', 1)
            config.updated_at = datetime.utcnow()
        else:
            # 创建新配置
            config = CheckinConfig(
                day=day,
                points=config_data['points'],
                is_active=config_data.get('is_active', 1)
            )
            db.session.add(config)

    try:
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        raise ValueError(f"Failed to update checkin config: {str(e)}")

    return {"msg": "Checkin config updated successfully"}
