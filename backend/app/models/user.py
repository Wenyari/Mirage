"""
用户相关数据模型
包含用户表和会员配置表
"""
from app.extensions import db
from datetime import datetime


class User(db.Model):
    """用户表"""
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    email = db.Column(db.String(100), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    balance = db.Column(db.Numeric(10, 2), default=0.00, nullable=False)
    level = db.Column(db.SmallInteger, default=1, nullable=False)  # T1-T5
    role = db.Column(db.Enum('user', 'admin'), default='user', nullable=False)
    status = db.Column(db.SmallInteger, default=1, nullable=False)  # 1=正常, 0=封禁
    register_ip = db.Column(db.String(45), nullable=True)
    last_login_at = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    # 关系映射
    tasks = db.relationship('Task', backref='user', lazy='dynamic')
    transactions = db.relationship('Transaction', backref='user', lazy='dynamic')

    def __repr__(self):
        return f'<User {self.email}>'

    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'email': self.email,
            'balance': float(self.balance),
            'level': self.level,
            'vip_desc': f'T{self.level}',
            'role': self.role,
            'status': self.status,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }


class MembershipConfig(db.Model):
    """会员等级配置表 (T1-T5)"""
    __tablename__ = 'membership_configs'

    level = db.Column(db.SmallInteger, primary_key=True)  # 等级 1-5
    name = db.Column(db.String(20), nullable=False)  # T1, T2, T3, T4, T5
    concurrency_limit = db.Column(db.Integer, nullable=False)  # 并发任务数限制
    queue_priority = db.Column(db.Integer, default=0, nullable=False)  # 队列权重
    remark = db.Column(db.String(100), nullable=True)

    def __repr__(self):
        return f'<MembershipConfig {self.name}>'

    def to_dict(self):
        """转换为字典"""
        return {
            'level': self.level,
            'name': self.name,
            'concurrency_limit': self.concurrency_limit,
            'queue_priority': self.queue_priority,
            'remark': self.remark,
        }
