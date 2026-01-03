"""
管理员服务层
集中导出所有管理员相关的服务
"""
from .dashboard_service import get_dashboard_overview, get_trend_chart_data
from .user_service import (
    get_user_list,
    get_user_detail,
    ban_user,
    unban_user,
    update_user_level,
    adjust_user_balance
)

__all__ = [
    'get_dashboard_overview',
    'get_trend_chart_data',
    'get_user_list',
    'get_user_detail',
    'ban_user',
    'unban_user',
    'update_user_level',
    'adjust_user_balance',
]
