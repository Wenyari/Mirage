"""
钱包/积分相关数据模型
包含 CDK 兑换码表和资金流水表
"""
from app.extensions import db
from datetime import datetime
from zoneinfo import ZoneInfo


class CDK(db.Model):
    """兑换码表 (充值卡密)"""
    __tablename__ = 'cdk'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    code = db.Column(db.String(32), unique=True, nullable=False, index=True)  # 兑换码
    points = db.Column(db.Integer, nullable=False)  # 面额（积分）
    type = db.Column(db.Enum('once', 'universal'), default='once', nullable=False)  # 类型
    batch_no = db.Column(db.String(50), nullable=True)  # 批次号
    status = db.Column(db.SmallInteger, default=0, nullable=False)  # 0=未使用, 1=已使用, 2=已作废
    used_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)  # 使用者
    used_at = db.Column(db.DateTime, nullable=True)  # 使用时间
    expire_at = db.Column(db.DateTime, nullable=True)  # 过期时间
    grant_level = db.Column(db.SmallInteger, nullable=True)  # 可授予的会员等级 (1-5)
    created_at = db.Column(db.DateTime, default=datetime.now(ZoneInfo("Asia/Shanghai")), nullable=False)

    def __repr__(self):
        return f'<CDK {self.code}>'

    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'code': self.code,
            'points': self.points,
            'type': self.type,
            'batch_no': self.batch_no,
            'status': self.status,
            'used_by': self.used_by,
            'used_at': self.used_at.isoformat() if self.used_at else None,
            'expire_at': self.expire_at.isoformat() if self.expire_at else None,
            'grant_level': self.grant_level,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }


class Transaction(db.Model):
    """资金流水表 (记录所有积分变动)"""
    __tablename__ = 'transactions'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    type = db.Column(db.Enum('recharge', 'task_cost', 'refund', 'system',
                              'checkin', 'activity_grant', 'activity_expire'),
                     nullable=False)  # 类型
    balance_type = db.Column(db.Enum('recharge', 'activity'), nullable=True, comment='积分类型')
    amount = db.Column(db.Numeric(10, 2), nullable=False)  # 变动金额 (+/-)
    balance_snapshot = db.Column(db.Numeric(10, 2), nullable=False)  # 变动后余额快照
    related_id = db.Column(db.String(50), nullable=True)  # 关联 ID (CDK ID or Task ID)
    activity_id = db.Column(db.Integer, nullable=True, comment='关联活动ID')
    remark = db.Column(db.String(255), nullable=True)  # 备注
    model = db.Column(db.String(50), nullable=True, comment='关联模型标识，例如 sora-2 或 gpt-4')
    created_at = db.Column(db.DateTime, default=datetime.now(ZoneInfo("Asia/Shanghai")), nullable=False, index=True)

    # 组合索引：用户查看账单
    __table_args__ = (
        db.Index('idx_user_created', 'user_id', 'created_at'),
        db.Index('idx_user_type_balance', 'user_id', 'type', 'balance_type'),
    )

    def __repr__(self):
        return f'<Transaction {self.id} - {self.type}>'

    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'type': self.type,
            'balance_type': self.balance_type,
            'model': self.model,
            'amount': float(self.amount),
            'balance_snapshot': float(self.balance_snapshot),
            'related_id': self.related_id,
            'activity_id': self.activity_id,
            'remark': self.remark,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }
