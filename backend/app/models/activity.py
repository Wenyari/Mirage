"""
活动相关数据模型
包含活动配置表、活动领取记录表、签到配置表
"""
from app.extensions import db
from datetime import datetime


class Activity(db.Model):
    """活动配置表"""
    __tablename__ = 'activities'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    code = db.Column(db.String(50), unique=True, nullable=False, index=True, comment='活动代码')
    name = db.Column(db.String(100), nullable=False, comment='活动名称')
    description = db.Column(db.Text, nullable=True, comment='活动描述')

    # 积分配置
    points = db.Column(db.Numeric(10, 2), nullable=False, comment='赠送积分数量')
    expire_days = db.Column(db.Integer, nullable=True, comment='积分有效期(天)，null表示永久')

    # 领取限制
    max_claims_per_user = db.Column(db.Integer, default=1, nullable=False, comment='每用户最多领取次数')
    required_level = db.Column(db.SmallInteger, nullable=True, comment='要求的最低会员等级')

    # 活动时间
    start_at = db.Column(db.DateTime, nullable=True, comment='活动开始时间')
    end_at = db.Column(db.DateTime, nullable=True, comment='活动结束时间')

    # 状态
    status = db.Column(
        db.Enum('active', 'paused', 'ended'),
        default='active',
        nullable=False,
        comment='活动状态'
    )

    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # 关系
    claims = db.relationship('ActivityClaim', backref='activity', lazy='dynamic')

    # 索引
    __table_args__ = (
        db.Index('idx_status_time', 'status', 'start_at', 'end_at'),
    )

    def __repr__(self):
        return f'<Activity {self.code}>'

    def to_dict(self):
        return {
            'id': self.id,
            'code': self.code,
            'name': self.name,
            'description': self.description,
            'points': float(self.points),
            'expire_days': self.expire_days,
            'max_claims_per_user': self.max_claims_per_user,
            'required_level': self.required_level,
            'start_at': self.start_at.isoformat() if self.start_at else None,
            'end_at': self.end_at.isoformat() if self.end_at else None,
            'status': self.status,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }


class ActivityClaim(db.Model):
    """活动领取记录表"""
    __tablename__ = 'activity_claims'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    activity_id = db.Column(db.Integer, db.ForeignKey('activities.id'), nullable=False)

    # 积分信息
    points_granted = db.Column(db.Numeric(10, 2), nullable=False, comment='实际赠送积分')
    expire_at = db.Column(db.DateTime, nullable=True, comment='积分过期时间')

    # 状态
    status = db.Column(
        db.Enum('active', 'expired', 'used'),
        default='active',
        nullable=False,
        comment='领取状态'
    )

    claimed_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    expired_at = db.Column(db.DateTime, nullable=True, comment='实际过期时间（系统扣除时填写）')

    # 关系
    user = db.relationship('User', backref='activity_claims')

    # 索引
    __table_args__ = (
        db.Index('idx_user_activity', 'user_id', 'activity_id'),
        db.Index('idx_expire_status', 'expire_at', 'status'),
    )

    def __repr__(self):
        return f'<ActivityClaim {self.id}>'

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'activity_id': self.activity_id,
            'points_granted': float(self.points_granted),
            'expire_at': self.expire_at.isoformat() if self.expire_at else None,
            'status': self.status,
            'claimed_at': self.claimed_at.isoformat() if self.claimed_at else None,
            'expired_at': self.expired_at.isoformat() if self.expired_at else None,
        }


class CheckinConfig(db.Model):
    """签到配置表"""
    __tablename__ = 'checkin_configs'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    day = db.Column(db.Integer, unique=True, nullable=False, comment='连续签到天数(1-7)')
    points = db.Column(db.Numeric(10, 2), nullable=False, comment='奖励积分')
    is_active = db.Column(db.SmallInteger, default=1, nullable=False, comment='是否启用')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f'<CheckinConfig Day{self.day}>'

    def to_dict(self):
        return {
            'id': self.id,
            'day': self.day,
            'points': float(self.points),
            'is_active': bool(self.is_active),
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }
