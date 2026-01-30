"""
公告管理服务 (管理员端)
提供公告的增删改查功能
"""
from app.extensions import db
from app.models.announcement import Announcement
from datetime import datetime
from zoneinfo import ZoneInfo


def create_announcement(data):
    """
    创建公告
    
    Args:
        data: 包含公告信息的字典
            - title: 公告标题 (必填)
            - content: 公告内容 (必填)
            - publish_time: 发布时间 (必填, ISO格式字符串)
            - is_active: 是否启用 (可选, 默认为True)
    
    Returns:
        dict: 创建的公告信息
    
    Raises:
        ValueError: 参数验证失败
    """
    title = data.get('title')
    content = data.get('content')
    publish_time_str = data.get('publish_time')
    is_active = data.get('is_active', True)
    
    # 参数验证
    if not title or not title.strip():
        raise ValueError("Title is required")
    
    if not content or not content.strip():
        raise ValueError("Content is required")
    
    if not publish_time_str:
        raise ValueError("Publish time is required")
    
    # 解析发布时间
    try:
        publish_time = datetime.fromisoformat(publish_time_str.replace('Z', '+00:00'))
    except (ValueError, AttributeError):
        raise ValueError("Invalid publish_time format, expected ISO format")
    
    # 创建公告
    announcement = Announcement(
        title=title.strip(),
        content=content.strip(),
        publish_time=publish_time,
        is_active=1 if is_active else 0
    )
    
    db.session.add(announcement)
    db.session.commit()
    
    return announcement.to_dict()


def update_announcement(announcement_id, data):
    """
    更新公告
    
    Args:
        announcement_id: 公告ID
        data: 要更新的字段字典
            - title: 公告标题 (可选)
            - content: 公告内容 (可选)
            - publish_time: 发布时间 (可选, ISO格式字符串)
            - is_active: 是否启用 (可选)
    
    Returns:
        dict: 更新后的公告信息
    
    Raises:
        ValueError: 公告不存在或参数验证失败
    """
    announcement = Announcement.query.get(announcement_id)
    if not announcement:
        raise ValueError(f"Announcement with id {announcement_id} not found")
    
    # 更新标题
    if 'title' in data:
        title = data['title']
        if not title or not title.strip():
            raise ValueError("Title cannot be empty")
        announcement.title = title.strip()
    
    # 更新内容
    if 'content' in data:
        content = data['content']
        if not content or not content.strip():
            raise ValueError("Content cannot be empty")
        announcement.content = content.strip()
    
    # 更新发布时间
    if 'publish_time' in data:
        publish_time_str = data['publish_time']
        try:
            announcement.publish_time = datetime.fromisoformat(publish_time_str.replace('Z', '+00:00'))
        except (ValueError, AttributeError):
            raise ValueError("Invalid publish_time format, expected ISO format")
    
    # 更新启用状态
    if 'is_active' in data:
        announcement.is_active = 1 if data['is_active'] else 0
    
    db.session.commit()
    
    return announcement.to_dict()


def delete_announcement(announcement_id):
    """
    删除公告
    
    Args:
        announcement_id: 公告ID
    
    Returns:
        dict: 包含成功消息
    
    Raises:
        ValueError: 公告不存在
    """
    announcement = Announcement.query.get(announcement_id)
    if not announcement:
        raise ValueError(f"Announcement with id {announcement_id} not found")
    
    db.session.delete(announcement)
    db.session.commit()
    
    return {"msg": "Announcement deleted successfully"}


def get_announcement_list(page=1, size=20, is_active=None):
    """
    获取公告列表（分页，按发布时间倒序）
    
    Args:
        page: 页码，从1开始
        size: 每页数量
        is_active: 是否只获取启用的公告 (可选)
    
    Returns:
        dict: {
            "list": [...],
            "total": 总数,
            "page": 当前页,
            "size": 每页数量
        }
    """
    query = Announcement.query
    
    # 筛选启用状态
    if is_active is not None:
        query = query.filter_by(is_active=1 if is_active else 0)
    
    # 按发布时间倒序排列
    query = query.order_by(Announcement.publish_time.desc())
    
    # 分页
    total = query.count()
    announcements = query.offset((page - 1) * size).limit(size).all()
    
    return {
        'list': [a.to_dict() for a in announcements],
        'total': total,
        'page': page,
        'size': size
    }


def get_announcement_detail(announcement_id):
    """
    获取单个公告详情
    
    Args:
        announcement_id: 公告ID
    
    Returns:
        dict: 公告信息
    
    Raises:
        ValueError: 公告不存在
    """
    announcement = Announcement.query.get(announcement_id)
    if not announcement:
        raise ValueError(f"Announcement with id {announcement_id} not found")
    
    return announcement.to_dict()


def get_active_announcements(limit=10):
    """
    获取启用的公告列表（用于用户端显示）
    按发布时间倒序，只返回已发布的公告
    
    Args:
        limit: 返回的最大数量
    
    Returns:
        list: 公告列表
    """
    now = datetime.now(ZoneInfo("Asia/Shanghai"))
    
    announcements = Announcement.query.filter(
        Announcement.is_active == 1,
        Announcement.publish_time <= now
    ).order_by(
        Announcement.publish_time.desc()
    ).limit(limit).all()
    
    return [a.to_dict() for a in announcements]
