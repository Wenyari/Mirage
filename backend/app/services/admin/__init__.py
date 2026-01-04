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
]
