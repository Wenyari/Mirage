"""
任务相关数据模型
包含任务表和模型定价表
"""
from app.extensions import db
from datetime import datetime
import uuid


class Task(db.Model):
    """AI 生成任务表"""
    __tablename__ = 'tasks'

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    model_name = db.Column(db.String(50), nullable=False)  # 如 'sora-v2'
    prompt = db.Column(db.Text, nullable=True)  # 用户提示词
    input_file_url = db.Column(db.Text, nullable=True)  # 参考图/视频
    params = db.Column(db.JSON, nullable=True)  # 动态参数 (时长、比例等)
    status = db.Column(db.Enum('pending', 'processing', 'success', 'failed'),
                       default='pending', nullable=False, index=True)
    result_url = db.Column(db.Text, nullable=True)  # 生成结果链接
    cost_points = db.Column(db.Numeric(10, 2), nullable=False)  # 消耗积分
    fail_reason = db.Column(db.String(255), nullable=True)  # 失败原因
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False, index=True)
    finished_at = db.Column(db.DateTime, nullable=True)

    # 组合索引：用于快速统计用户当前运行中的任务数（并发控制）
    __table_args__ = (
        db.Index('idx_user_status', 'user_id', 'status'),
    )

    def __repr__(self):
        return f'<Task {self.id} - {self.status}>'

    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'model_name': self.model_name,
            'prompt': self.prompt,
            'input_file_url': self.input_file_url,
            'params': self.params,
            'status': self.status,
            'result_url': self.result_url,
            'cost_points': float(self.cost_points),
            'fail_reason': self.fail_reason,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'finished_at': self.finished_at.isoformat() if self.finished_at else None,
        }


class ModelPricing(db.Model):
    """模型定价表"""
    __tablename__ = 'model_pricing'

    model_key = db.Column(db.String(50), primary_key=True)  # 模型标识
    base_cost = db.Column(db.Numeric(10, 2), nullable=False)  # 基础费用
    is_active = db.Column(db.SmallInteger, default=1, nullable=False)  # 是否上架
    config = db.Column(db.JSON, nullable=True)  # 扩展配置

    def __repr__(self):
        return f'<ModelPricing {self.model_key}>'

    def to_dict(self):
        """转换为字典"""
        return {
            'model_key': self.model_key,
            'base_cost': float(self.base_cost),
            'is_active': self.is_active,
            'config': self.config,
        }
