"""
模型配置管理服务
提供模型计费规则和权限配置的管理功能
"""
from datetime import datetime
from app.extensions import db
from app.models import Model, ModelConfig, ApiKey


def get_model_config_list():
    """
    获取模型配置列表

    Returns:
        list: 模型配置列表（含模型名称）
    """
    configs = ModelConfig.query.all()

    result = []
    for config in configs:
        config_dict = config.to_dict()

        # 添加模型显示名称
        model = Model.query.filter_by(key=config.model).first()
        config_dict['model_name'] = model.name if model else config.model

        result.append(config_dict)

    return result


def get_available_models():
    """
    获取可配置的模型列表
    从 models 表中获取所有模型，并标记是否已有配置

    Returns:
        list: 模型列表（含配置状态和密钥数量）
    """
    models = Model.query.all()

    result = []
    for model in models:
        # 检查是否已有配置
        config = ModelConfig.query.filter_by(model=model.key).first()

        # 统计该模型的密钥数量（改为 JOIN 查询）
        key_count = db.session.query(ApiKey)\
            .join(ApiKey.models)\
            .filter(Model.key == model.key)\
            .count()

        result.append({
            'model': model.key,
            'model_name': model.name,
            'has_config': config is not None,
            'key_count': key_count
        })

    return result


def create_model_config(model, allowed_tiers, cost_per_call, token_cost_config, is_active=True, description=None):
    """
    创建模型配置

    Args:
        model: 模型标识
        allowed_tiers: 允许使用的等级数组
        cost_per_call: 每次调用扣除积分
        token_cost_config: Token 计费配置
        is_active: 是否启用
        description: 描述

    Returns:
        dict: 创建的配置数据

    Raises:
        ValueError: 参数无效或配置已存在
    """
    # 验证模型是否存在
    model_obj = Model.query.filter_by(key=model).first()
    if not model_obj:
        raise ValueError(f"Model '{model}' not found")

    # 检查是否已有配置
    existing = ModelConfig.query.filter_by(model=model).first()
    if existing:
        raise ValueError(f"Configuration for model '{model}' already exists")

    # 验证 allowed_tiers
    valid_tiers = ['T1', 'T2', 'T3', 'T4', 'T5']
    if not isinstance(allowed_tiers, list) or not allowed_tiers:
        raise ValueError("allowed_tiers must be a non-empty array")

    for tier in allowed_tiers:
        if tier not in valid_tiers:
            raise ValueError(f"Invalid tier '{tier}'. Must be one of {valid_tiers}")

    # 验证 token_cost_config
    if not isinstance(token_cost_config, dict):
        raise ValueError("token_cost_config must be an object")

    if 'enabled' not in token_cost_config:
        raise ValueError("token_cost_config.enabled is required")

    if token_cost_config['enabled']:
        if 'input_cost' not in token_cost_config or 'output_cost' not in token_cost_config:
            raise ValueError("input_cost and output_cost are required when token billing is enabled")

    # 创建配置
    config = ModelConfig(
        model=model,
        allowed_tiers=allowed_tiers,
        cost_per_call=cost_per_call,
        token_cost_config=token_cost_config,
        is_active=1 if is_active else 0,
        description=description
    )

    db.session.add(config)
    db.session.commit()

    # 返回带模型名称的数据
    result = config.to_dict()
    result['model_name'] = model_obj.name

    return result


def update_model_config(config_id, allowed_tiers=None, cost_per_call=None, token_cost_config=None, is_active=None, description=None, params=None):
    """
    更新模型配置

    Args:
        config_id: 配置ID
        allowed_tiers: 允许使用的等级数组
        cost_per_call: 每次调用扣除积分
        token_cost_config: Token 计费配置
        is_active: 是否启用
        description: 描述
        params: 可选参数

    Returns:
        dict: 操作结果

    Raises:
        ValueError: 配置不存在或参数无效
    """
    config = ModelConfig.query.get(config_id)
    if not config:
        raise ValueError(f"Model config {config_id} not found")

    # 更新字段
    if allowed_tiers is not None:
        valid_tiers = ['T1', 'T2', 'T3', 'T4', 'T5']
        if not isinstance(allowed_tiers, list) or not allowed_tiers:
            raise ValueError("allowed_tiers must be a non-empty array")

        for tier in allowed_tiers:
            if tier not in valid_tiers:
                raise ValueError(f"Invalid tier '{tier}'. Must be one of {valid_tiers}")

        config.allowed_tiers = allowed_tiers

    if cost_per_call is not None:
        if cost_per_call < 0:
            raise ValueError("cost_per_call must be non-negative")
        config.cost_per_call = cost_per_call

    if token_cost_config is not None:
        if not isinstance(token_cost_config, dict):
            raise ValueError("token_cost_config must be an object")

        if 'enabled' in token_cost_config and token_cost_config['enabled']:
            if 'input_cost' not in token_cost_config or 'output_cost' not in token_cost_config:
                raise ValueError("input_cost and output_cost are required when token billing is enabled")

        config.token_cost_config = token_cost_config

    if is_active is not None:
        config.is_active = 1 if is_active else 0

    if description is not None:
        config.description = description

    if params is not None:
        config.params = params

    config.updated_at = datetime.now()
    db.session.commit()

    return {'message': 'Model config updated successfully'}


def delete_model_config(config_id):
    """
    删除模型配置

    Args:
        config_id: 配置ID

    Returns:
        dict: 操作结果

    Raises:
        ValueError: 配置不存在
    """
    config = ModelConfig.query.get(config_id)
    if not config:
        raise ValueError(f"Model config {config_id} not found")

    db.session.delete(config)
    db.session.commit()

    return {'message': 'Model config deleted successfully'}
