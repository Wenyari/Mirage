"""
模型管理服务
提供模型的增删改查功能
"""
from datetime import datetime
from sqlalchemy import or_
from app.extensions import db
from app.models import Model, ModelConfig, ApiKey, Task


def get_model_list():
    """
    获取所有模型列表

    Returns:
        list: 模型列表
    """
    models = Model.query.all()
    return [model.to_dict() for model in models]


def create_model(key, name, enabled=True, description=None, color=None, icon_url=None, max_concurrency_limit=20):
    """
    创建新模型

    Args:
        key: 模型唯一标识
        name: 模型显示名称
        enabled: 是否启用
        description: 模型描述
        color: UI颜色标识
        icon_url: 模型图标URL
        max_concurrency_limit: 建议的最大并发限制

    Returns:
        dict: 创建的模型数据

    Raises:
        ValueError: 参数无效或模型已存在
    """
    # 验证key格式（只允许小写字母、数字、下划线、中划线）
    import re
    if not re.match(r'^[a-z0-9_-]+$', key):
        raise ValueError("Model key must contain only lowercase letters, numbers, underscores, and hyphens")

    # 检查是否已存在
    existing = Model.query.filter_by(key=key).first()
    if existing:
        raise ValueError(f"Model with key '{key}' already exists")

    # 创建模型
    model = Model(
        key=key,
        name=name,
        enabled=1 if enabled else 0,
        description=description,
        color=color,
        icon_url=icon_url,
        max_concurrency_limit=max_concurrency_limit
    )

    db.session.add(model)
    db.session.commit()

    return model.to_dict()


def update_model(key, name=None, enabled=None, description=None, color=None, icon_url=None, max_concurrency_limit=None):
    """
    更新模型配置

    Args:
        key: 模型标识
        name: 模型显示名称
        enabled: 是否启用
        description: 模型描述
        color: UI颜色标识
        icon_url: 模型图标URL
        max_concurrency_limit: 建议的最大并发限制

    Returns:
        dict: 更新后的模型数据

    Raises:
        ValueError: 模型不存在
    """
    model = Model.query.filter_by(key=key).first()
    if not model:
        raise ValueError(f"Model '{key}' not found")

    # 更新字段
    if name is not None:
        model.name = name
    if enabled is not None:
        model.enabled = 1 if enabled else 0
    if description is not None:
        model.description = description
    if color is not None:
        model.color = color
    if icon_url is not None:
        model.icon_url = icon_url
    if max_concurrency_limit is not None:
        model.max_concurrency_limit = max_concurrency_limit

    model.updated_at = datetime.utcnow()
    db.session.commit()

    return model.to_dict()


def delete_model(key):
    """
    删除模型

    Args:
        key: 模型标识

    Returns:
        dict: 删除结果

    Raises:
        ValueError: 模型不存在或有关联数据
    """
    model = Model.query.filter_by(key=key).first()
    if not model:
        raise ValueError(f"Model '{key}' not found")

    # 检查是否有关联的密钥（改为 JOIN 查询）
    key_count = db.session.query(ApiKey)\
        .join(ApiKey.models)\
        .filter(Model.key == key)\
        .count()

    # 检查是否有关联的任务
    task_count = Task.query.filter_by(model=key).count()

    if key_count > 0 or task_count > 0:
        raise ValueError(f"Cannot delete model with existing keys or tasks", {
            'key_count': key_count,
            'task_count': task_count
        })

    # 删除模型配置（如果存在）
    ModelConfig.query.filter_by(model=key).delete()

    # 删除模型
    db.session.delete(model)
    db.session.commit()

    return {
        'message': f"Model '{key}' deleted successfully"
    }
