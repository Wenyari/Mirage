"""
管理员服务层
集中导出所有管理员相关的服务
"""
from .dashboard_service import get_dashboard_overview, get_trend_chart_data
from .user_service import (
    get_user_list,
    get_user_detail,
    update_user_profile,
    adjust_user_balance,
    # 保留旧版接口以兼容性（但标记为deprecated）
    ban_user,
    unban_user,
    update_user_level,
)
from .cdk_service import (
    generate_cdk_batch,
    get_cdk_list,
    void_cdk_batch,
)
from .model_service import (
    get_model_list,
    create_model,
    update_model,
    delete_model,
)
from .key_service import (
    get_key_list,
    create_key,
    batch_create_keys,
    update_key,
    delete_key,
    trigger_cooldown,
    get_key_stats,
)
from .model_config_service import (
    get_model_config_list,
    get_available_models,
    create_model_config,
    update_model_config,
    delete_model_config,
)
from .membership_config_service import (
    get_membership_config,
    update_membership_config,
)

__all__ = [
    # Dashboard服务
    'get_dashboard_overview',
    'get_trend_chart_data',
    # 用户管理服务
    'get_user_list',
    'get_user_detail',
    'update_user_profile',
    'adjust_user_balance',
    # 旧版接口（兼容性）
    'ban_user',
    'unban_user',
    'update_user_level',
    # CDK管理服务
    'generate_cdk_batch',
    'get_cdk_list',
    'void_cdk_batch',
    # 模型管理服务
    'get_model_list',
    'create_model',
    'update_model',
    'delete_model',
    # 密钥管理服务
    'get_key_list',
    'create_key',
    'batch_create_keys',
    'update_key',
    'delete_key',
    'trigger_cooldown',
    'get_key_stats',
    # 模型配置管理服务
    'get_model_config_list',
    'get_available_models',
    'create_model_config',
    'update_model_config',
    'delete_model_config',
    # 会员配置管理服务
    'get_membership_config',
    'update_membership_config',
]
