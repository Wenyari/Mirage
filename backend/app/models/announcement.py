"""
公告相关数据模型
包含公告配置表
"""
from app.extensions import db
from datetime import datetime
from zoneinfo import ZoneInfo


class Announcement(db.Model):
    """公告配置表"""
    __tablename__ = 'announcements'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    title = db.Column(db.String(200), nullable=False, comment='公告标题')
    content = db.Column(db.Text, nullable=False, comment='公告内容')
    
    # 时间配置
    publish_time = db.Column(db.DateTime, nullable=False, comment='发布时间')
    
    # 状态
    is_active = db.Column(db.SmallInteger, default=1, nullable=False, comment='是否启用(0=禁用,1=启用)')
    
    created_at = db.Column(db.DateTime, default=datetime.now(ZoneInfo("Asia/Shanghai")), nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.now(ZoneInfo("Asia/Shanghai")), onupdate=datetime.now(ZoneInfo("Asia/Shanghai")))

    # 索引
    __table_args__ = (
        db.Index('idx_publish_time', 'publish_time'),
        db.Index('idx_is_active', 'is_active'),
    )

    def __repr__(self):
        return f'<Announcement {self.id}: {self.title}>'

    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'content': self.content,
            'publish_time': self.publish_time.isoformat() if self.publish_time else None,
            'is_active': bool(self.is_active),
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }
