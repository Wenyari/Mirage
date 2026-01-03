"""
管理员服务层
集中导出所有管理员相关的服务
"""
from .dashboard_service import get_dashboard_overview, get_trend_chart_data

__all__ = [
    'get_dashboard_overview',
    'get_trend_chart_data',
]
