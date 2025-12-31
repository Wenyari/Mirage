"""
任务相关数据模型
包含任务表
"""
from app.extensions import db
from datetime import datetime
import uuid


class Task(db.Model):
    """AI 生成任务表"""
    __tablename__ = 'tasks'

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    platform = db.Column(db.String(50), db.ForeignKey('platforms.key'), nullable=False)  # 平台标识 (外键关联 platforms.key)
    prompt = db.Column(db.Text, nullable=True)  # 用户提示词
    input_file_url = db.Column(db.Text, nullable=True)  # 参考图/视频
    params = db.Column(db.JSON, nullable=True)  # 动态参数 (时长、比例等)
    status = db.Column(db.Enum('pending', 'processing', 'success', 'failed'),
                       default='pending', nullable=False, index=True)
    result_url = db.Column(db.Text, nullable=True)  # 生成结果链接
    cost_points = db.Column(db.Numeric(10, 2), nullable=False)  # 消耗积分
    token_usage = db.Column(db.JSON, nullable=True)  # Token 使用情况 {"input": 1000, "output": 500}
    api_key_id = db.Column(db.Integer, db.ForeignKey('api_keys.id'), nullable=True)  # 使用的密钥 ID
    fail_reason = db.Column(db.String(255), nullable=True)  # 失败原因
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False, index=True)
    finished_at = db.Column(db.DateTime, nullable=True)

    # 组合索引：用于快速统计用户当前运行中的任务数（并发控制）
    __table_args__ = (
        db.Index('idx_user_status', 'user_id', 'status'),
        db.Index('idx_platform', 'platform'),
    )

    def __repr__(self):
        return f'<Task {self.id} - {self.status}>'

    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'platform': self.platform,
            'prompt': self.prompt,
            'input_file_url': self.input_file_url,
            'params': self.params,
            'status': self.status,
            'result_url': self.result_url,
            'cost_points': float(self.cost_points),
            'token_usage': self.token_usage,
            'api_key_id': self.api_key_id,
            'fail_reason': self.fail_reason,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'finished_at': self.finished_at.isoformat() if self.finished_at else None,
        }
