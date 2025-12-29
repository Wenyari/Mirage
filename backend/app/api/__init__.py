"""
API 蓝图注册
统一导入所有蓝图
"""
from app.api import auth, users, tasks, wallet, admin

# 导出所有蓝图
auth_bp = auth.bp
users_bp = users.bp
tasks_bp = tasks.bp
wallet_bp = wallet.bp
admin_bp = admin.bp

__all__ = [
    'auth_bp',
    'users_bp',
    'tasks_bp',
    'wallet_bp',
    'admin_bp',
]
