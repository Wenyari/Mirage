"""
数据模型包初始化
统一导入所有模型
"""
from app.models.user import User, MembershipConfig
from app.models.task import Task
from app.models.wallet import CDK, Transaction, ActivityPointGrant
from app.models.model import Model, ModelConfig, ApiKey, ApiKeyModel
from app.models.activity import Activity, ActivityClaim, CheckinConfig
from app.models.ai_media_asset import AiMediaAsset

__all__ = [
    'User',
    'MembershipConfig',
    'Task',
    'CDK',
    'Transaction',
    'ActivityPointGrant',
    'Model',
    'ModelConfig',
    'ApiKey',
    'ApiKeyModel',
    'Activity',
    'ActivityClaim',
    'CheckinConfig',
    'AiMediaAsset',
]
