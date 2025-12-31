"""
平台相关数据模型
包含平台基本信息、平台配置和密钥池管理
"""
from app.extensions import db
from datetime import datetime


class Platform(db.Model):
    """平台基本信息表"""
    __tablename__ = 'platforms'

    key = db.Column(db.String(50), primary_key=True)  # 平台唯一标识
    name = db.Column(db.String(100), nullable=False)  # 平台显示名称
    enabled = db.Column(db.SmallInteger, default=1, nullable=False)  # 是否启用
    description = db.Column(db.Text, nullable=True)  # 平台描述
    color = db.Column(db.String(50), nullable=True)  # UI 颜色标识
    icon_url = db.Column(db.String(255), nullable=True)  # 平台图标 URL
    max_concurrency_limit = db.Column(db.Integer, default=20, nullable=False)  # 最大并发限制
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # 关系映射
    config = db.relationship('PlatformConfig', backref='platform_info', uselist=False, lazy=True)
    api_keys = db.relationship('ApiKey', backref='platform_info', lazy='dynamic')
    tasks = db.relationship('Task', backref='platform_info', lazy='dynamic')

    # 索引
    __table_args__ = (
        db.Index('idx_enabled', 'enabled'),
    )

    def __repr__(self):
        return f'<Platform {self.key}>'

    def to_dict(self):
        """转换为字典"""
        return {
            'key': self.key,
            'name': self.name,
            'enabled': self.enabled,
            'description': self.description,
            'color': self.color,
            'icon_url': self.icon_url,
            'max_concurrency_limit': self.max_concurrency_limit,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }


class PlatformConfig(db.Model):
    """平台配置表（替代原 model_pricing 表）"""
    __tablename__ = 'platform_configs'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    platform = db.Column(db.String(50), db.ForeignKey('platforms.key'), unique=True, nullable=False)
    allowed_tiers = db.Column(db.JSON, nullable=False)  # 允许使用的等级数组 ["T1","T2",...]
    cost_per_call = db.Column(db.Numeric(10, 2), default=0.00, nullable=False)  # 固定计费
    token_cost_config = db.Column(db.JSON, nullable=True)  # Token 计费配置
    is_active = db.Column(db.SmallInteger, default=1, nullable=False)  # 是否启用
    description = db.Column(db.Text, nullable=True)  # 配置说明
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # 索引
    __table_args__ = (
        db.Index('idx_platform', 'platform'),
        db.Index('idx_active', 'is_active'),
    )

    def __repr__(self):
        return f'<PlatformConfig {self.platform}>'

    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'platform': self.platform,
            'allowed_tiers': self.allowed_tiers,
            'cost_per_call': float(self.cost_per_call),
            'token_cost_config': self.token_cost_config,
            'is_active': self.is_active,
            'description': self.description,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }


class ApiKey(db.Model):
    """密钥池管理表"""
    __tablename__ = 'api_keys'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    platform = db.Column(db.String(50), db.ForeignKey('platforms.key'), nullable=False)
    key_secret = db.Column(db.String(512), nullable=False)  # 密钥本体（建议加密存储）
    max_concurrency = db.Column(db.Integer, default=3, nullable=False)  # 最大并发限制
    weight = db.Column(db.SmallInteger, default=10, nullable=False)  # 权重 (1-100)
    status = db.Column(db.SmallInteger, default=1, nullable=False)  # 状态：1=启用, 0=停用
    total_calls = db.Column(db.Integer, default=0, nullable=False)  # 累计调用次数
    total_errors = db.Column(db.Integer, default=0, nullable=False)  # 累计失败次数
    last_used_at = db.Column(db.DateTime, nullable=True)  # 最后使用时间
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # 关系映射
    tasks = db.relationship('Task', backref='api_key_info', lazy='dynamic')

    # 索引
    __table_args__ = (
        db.Index('idx_platform_status', 'platform', 'status'),
        db.Index('idx_weight', 'weight'),
    )

    def __repr__(self):
        return f'<ApiKey {self.id} - {self.platform}>'

    def to_dict(self, include_secret=False):
        """转换为字典"""
        result = {
            'id': self.id,
            'platform': self.platform,
            'max_concurrency': self.max_concurrency,
            'weight': self.weight,
            'status': self.status,
            'total_calls': self.total_calls,
            'total_errors': self.total_errors,
            'last_used_at': self.last_used_at.isoformat() if self.last_used_at else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }

        # 只在需要时返回密钥
        if include_secret:
            result['key_secret'] = self.key_secret
        else:
            # 只显示前后几位
            result['key_secret_preview'] = f"{self.key_secret[:10]}...{self.key_secret[-4:]}" if len(self.key_secret) > 14 else "***"

        return result
