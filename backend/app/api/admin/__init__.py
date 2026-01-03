"""
管理员 API 模块
统一管理所有管理员相关的子蓝图
"""
from flask import Blueprint
from .dashboard import bp as dashboard_bp

# 创建管理员主蓝图，URL前缀为 /api/admin
admin_bp = Blueprint('admin', __name__, url_prefix='/api/admin')

# 注册各个子模块的蓝图
admin_bp.register_blueprint(dashboard_bp)

# 导出主蓝图供 app 使用
__all__ = ['admin_bp']
