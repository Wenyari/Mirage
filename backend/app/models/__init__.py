"""
数据模型包初始化
统一导入所有模型
"""
from app.models.user import User, MembershipConfig
from app.models.task import Task
from app.models.wallet import CDK, Transaction
from app.models.model import Model, ModelConfig, ApiKey, ApiKeyModel
from app.models.activity import Activity, ActivityClaim, CheckinConfig

__all__ = [
    'User',
    'MembershipConfig',
    'Task',
    'CDK',
    'Transaction',
    'Model',
    'ModelConfig',
    'ApiKey',
    'ApiKeyModel',
    'Activity',
    'ActivityClaim',
    'CheckinConfig',
]
