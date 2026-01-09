"""
API 蓝图注册
统一导入所有蓝图
"""
from app.api import auth, users, tasks, wallet, activities
from app.api.admin import admin_bp

# 导出所有蓝图
auth_bp = auth.bp
users_bp = users.bp
tasks_bp = tasks.bp
wallet_bp = wallet.bp
activities_bp = activities.bp

__all__ = [
    'auth_bp',
    'users_bp',
    'tasks_bp',
    'wallet_bp',
    'activities_bp',
    'admin_bp',
]
