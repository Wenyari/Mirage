"""
模型管理服务
提供模型的增删改查功能
"""
from datetime import datetime
from zoneinfo import ZoneInfo
from sqlalchemy import or_
from app.extensions import db
from app.models import Model, ModelConfig, ApiKey, Task


def get_model_list(tags_filter=None):
    """
    获取所有模型列表

    Args:
        tags_filter: 标签筛选（逗号分隔的标签，如 "video,generation"）
                    满足任一标签即返回（OR逻辑）

    Returns:
        list: 模型列表
    """
    query = Model.query

    # 标签筛选（如果提供）
    if tags_filter:
        tags = [t.strip() for t in tags_filter.split(',')]
        # 使用Python过滤（简单实现）
        all_models = query.all()
        filtered_models = []
        for model in all_models:
            if model.tags and any(tag in model.tags for tag in tags):
                filtered_models.append(model.to_dict())
        return filtered_models

    models = query.all()
    return [model.to_dict() for model in models]


def create_model(key, name, enabled=True, description=None, color=None, icon_url=None, max_concurrency_limit=20, tags=None):
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
        tags: 模型分类标签（字符串数组）

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

    # 验证tags格式（如果提供）
    if tags is not None:
        if not isinstance(tags, list):
            raise ValueError("tags must be a list")
        if not all(isinstance(tag, str) for tag in tags):
            raise ValueError("All tags must be strings")

    # 创建模型
    model = Model(
        key=key,
        name=name,
        enabled=1 if enabled else 0,
        description=description,
        color=color,
        icon_url=icon_url,
        max_concurrency_limit=max_concurrency_limit,
        tags=tags
    )

    db.session.add(model)
    db.session.commit()

    return model.to_dict()


def update_model(key, name=None, enabled=None, description=None, color=None, icon_url=None, max_concurrency_limit=None, tags=None):
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
        tags: 模型分类标签（字符串数组）

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
    if tags is not None:
        # 验证tags格式
        if not isinstance(tags, list):
            raise ValueError("tags must be a list")
        if not all(isinstance(tag, str) for tag in tags):
            raise ValueError("All tags must be strings")
        model.tags = tags

    model.updated_at = datetime.now(ZoneInfo("Asia/Shanghai"))
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
