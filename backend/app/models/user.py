"""
用户相关数据模型
包含用户表和会员配置表
"""
from app.extensions import db
from datetime import datetime
from zoneinfo import ZoneInfo


class User(db.Model):
    """用户表"""
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    email = db.Column(db.String(100), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    recharge_balance = db.Column(db.Numeric(10, 2), default=0.00, nullable=False, comment='充值积分')
    activity_balance = db.Column(db.Numeric(10, 2), default=0.00, nullable=False, comment='活动积分')
    level = db.Column(db.SmallInteger, default=1, nullable=False)  # T1-T5
    role = db.Column(db.Enum('user', 'admin'), default='user', nullable=False)
    status = db.Column(db.SmallInteger, default=1, nullable=False)  # 1=正常, 0=封禁
    register_ip = db.Column(db.String(45), nullable=True)
    last_login_at = db.Column(db.DateTime, nullable=True)
    last_checkin_at = db.Column(db.DateTime, nullable=True, comment='最后签到时间')
    total_checkin_days = db.Column(db.Integer, default=0, nullable=False, comment='累计签到天数')
    created_at = db.Column(db.DateTime, default=datetime.now(ZoneInfo("Asia/Shanghai")), nullable=False)

    # 关系映射
    tasks = db.relationship('Task', backref='user', lazy='dynamic')
    transactions = db.relationship('Transaction', backref='user', lazy='dynamic')

    def __repr__(self):
        return f'<User {self.email}>'

    def to_dict(self):
        """
        转换为字典

        Note:
            status字段：1=正常，0=封禁（与数据库定义一致）
        """
        return {
            'id': self.id,
            'email': self.email,
            'role': self.role,  # 用户角色：'user' 或 'admin'
            'avatar': None,  # 头像URL（可选，暂未实现）
            'level': self.level,
            'recharge_balance': float(self.recharge_balance),
            'activity_balance': float(self.activity_balance),
            'total_balance': float(self.recharge_balance + self.activity_balance),
            'status': self.status,  # 1=正常，0=封禁
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'last_active': self.last_login_at.isoformat() if self.last_login_at else None,
            'last_checkin_at': self.last_checkin_at.isoformat() if self.last_checkin_at else None,
            'total_checkin_days': self.total_checkin_days,
        }


class MembershipConfig(db.Model):
    """会员等级配置表 (T1-T5)"""
    __tablename__ = 'membership_configs'

    level = db.Column(db.SmallInteger, primary_key=True)  # 等级 1-5
    name = db.Column(db.String(20), nullable=False)  # T1, T2, T3, T4, T5
    concurrent_limit = db.Column(db.Integer, nullable=False)  # 并发任务数限制
    queue_weight = db.Column(db.Integer, default=1, nullable=False)  # 队列权重
    price = db.Column(db.Numeric(10, 2), default=0.00, nullable=False)  # 月费价格
    description = db.Column(db.String(100), nullable=True)  # 等级描述

    def __repr__(self):
        return f'<MembershipConfig {self.name}>'

    def to_dict(self):
        """转换为字典"""
        return {
            'level': self.level,
            'name': self.name,
            'concurrent_limit': self.concurrent_limit,
            'queue_weight': self.queue_weight,
            'price': float(self.price),
            'description': self.description,
        }
