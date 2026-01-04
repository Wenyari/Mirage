"""
会员等级配置管理服务
提供会员等级的查询和更新功能
"""
from app.extensions import db
from app.models import MembershipConfig


def get_membership_config():
    """
    获取会员等级配置
    返回以等级名称为key的字典格式

    Returns:
        dict: {
            'T1': {...},
            'T2': {...},
            ...
        }
    """
    configs = MembershipConfig.query.order_by(MembershipConfig.level).all()

    result = {}
    for config in configs:
        result[config.name] = {
            'level': config.level,
            'name': config.name,
            'concurrent_limit': config.concurrent_limit,
            'queue_weight': config.queue_weight,
            'price': float(config.price) if config.price else 0,
            'description': config.description
        }

    return result


def update_membership_config(config_data):
    """
    更新会员等级配置
    批量更新所有等级的配置

    Args:
        config_data: 配置数据字典 {
            'T1': {'concurrent_limit': 1, 'queue_weight': 1, 'price': 0},
            'T2': {...},
            ...
        }

    Returns:
        dict: 操作结果

    Raises:
        ValueError: 参数无效
    """
    valid_tiers = ['T1', 'T2', 'T3', 'T4', 'T5']

    # 验证输入数据
    if not isinstance(config_data, dict):
        raise ValueError("Config data must be an object")

    # 更新每个等级的配置
    for tier_name, tier_config in config_data.items():
        if tier_name not in valid_tiers:
            raise ValueError(f"Invalid tier '{tier_name}'. Must be one of {valid_tiers}")

        # 查找对应的配置记录
        config = MembershipConfig.query.filter_by(name=tier_name).first()
        if not config:
            raise ValueError(f"Membership config for '{tier_name}' not found")

        # 更新字段
        if 'concurrent_limit' in tier_config:
            concurrent_limit = tier_config['concurrent_limit']
            if not isinstance(concurrent_limit, int) or concurrent_limit < 1:
                raise ValueError(f"concurrent_limit for {tier_name} must be a positive integer")
            config.concurrent_limit = concurrent_limit

        if 'queue_weight' in tier_config:
            queue_weight = tier_config['queue_weight']
            if not isinstance(queue_weight, int) or queue_weight < 1:
                raise ValueError(f"queue_weight for {tier_name} must be a positive integer")
            config.queue_weight = queue_weight

        if 'price' in tier_config:
            price = tier_config['price']
            if not isinstance(price, (int, float)) or price < 0:
                raise ValueError(f"price for {tier_name} must be a non-negative number")
            config.price = price

    db.session.commit()

    return {'message': 'Membership config updated successfully'}
