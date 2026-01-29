"""
AI媒体资产数据模型
对应 ai_media_assets 表,存储从爬虫采集的媒体资源
"""
from app.extensions import db
from datetime import datetime
from zoneinfo import ZoneInfo


class AiMediaAsset(db.Model):
    """AI媒体资产表"""
    __tablename__ = 'ai_media_assets'

    id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    source_id = db.Column(db.String(128), unique=True, nullable=False, index=True, comment='爬虫生成的唯一ID')
    title = db.Column(db.String(255), nullable=True, index=True, comment='标题')
    media_type = db.Column(db.String(50), default='image', nullable=False, comment='媒体类型: image/video')
    prompt_en = db.Column(db.Text, nullable=True, comment='英文提示词')
    prompt_zh = db.Column(db.Text, nullable=True, comment='中文提示词')
    width = db.Column(db.Integer, default=0, nullable=False, comment='宽度')
    height = db.Column(db.Integer, default=0, nullable=False, comment='高度')
    r2_key = db.Column(db.JSON, nullable=True, comment='R2存储路径(JSON数组)')
    r2_url = db.Column(db.JSON, nullable=True, comment='R2访问链接(JSON数组)')
    cover_r2_key = db.Column(db.String(255), nullable=True, comment='封面路径')
    cover_r2_url = db.Column(db.String(512), nullable=True, comment='封面链接')
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(ZoneInfo("Asia/Shanghai")), nullable=False)
    updated_at = db.Column(
        db.DateTime,
        default=lambda: datetime.now(ZoneInfo("Asia/Shanghai")),
        onupdate=lambda: datetime.now(ZoneInfo("Asia/Shanghai")),
        nullable=False
    )

    def __repr__(self):
        return f'<AiMediaAsset {self.title}>'

    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'source_id': self.source_id,
            'title': self.title,
            'media_type': self.media_type,
            'prompt_en': self.prompt_en,
            'prompt_zh': self.prompt_zh,
            'width': self.width,
            'height': self.height,
            'aspect_ratio': round(self.width / self.height, 2) if self.height > 0 else 0,
            'r2_key': self.r2_key,
            'r2_url': self.r2_url,
            'cover_r2_key': self.cover_r2_key,
            'cover_r2_url': self.cover_r2_url,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }
