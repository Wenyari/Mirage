"""
装饰器工具
包含权限检查、单点登录互斥检查等装饰器
"""
from functools import wraps
from flask import jsonify, request
from flask_jwt_extended import get_jwt_identity, verify_jwt_in_request
from app.models import User
from app.services.auth_service import check_token_validity


def login_required(f):
    """
    登录检查装饰器 (替代 @jwt_required)
    增加了单点登录互斥检查
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # 1. JWT 校验
        try:
            verify_jwt_in_request()
        except Exception as e:
            return jsonify({"code": 401, "msg": "Invalid or expired token", "data": None}), 401

        # 2. 单点登录互斥检查
        user_id = get_jwt_identity()
        auth_header = request.headers.get('Authorization', '')

        if not auth_header.startswith('Bearer '):
            return jsonify({"code": 401, "msg": "Invalid authorization header", "data": None}), 401

        current_token = auth_header.split(' ')[1]

        # 检查 Redis 中存储的 Token 是否与当前 Token 一致
        if not check_token_validity(user_id, current_token):
            return jsonify({
                "code": 401,
                "msg": "Your account has been logged in on another device",
                "data": None
            }), 401

        # 3. 检查账号状态
        user = User.query.get(user_id)
        if not user or user.status == 0:
            return jsonify({"code": 403, "msg": "Account has been banned", "data": None}), 403

        return f(*args, **kwargs)

    return decorated_function


def admin_required(f):
    """
    管理员权限检查装饰器
    必须在 @jwt_required 或 @login_required 之后使用
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        user_id = get_jwt_identity()
        user = User.query.get(user_id)

        if not user or user.role != 'admin':
            return jsonify({
                "code": 403,
                "msg": "Admin permission required",
                "data": None
            }), 403

        return f(*args, **kwargs)

    return decorated_function


def rate_limit(limit: int = 100, period: int = 3600):
    """
    限流装饰器 (基于 IP)

    Args:
        limit: 限制次数
        period: 时间周期 (秒)

    Usage:
        @rate_limit(limit=10, period=60)  # 1分钟最多10次
        def my_endpoint():
            pass
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            from app.extensions import redis_client

            # 获取客户端 IP
            ip = request.remote_addr
            key = f"rate:limit:{ip}:{f.__name__}"

            # 获取当前计数
            current = redis_client.get(key)

            if current is None:
                # 第一次请求，设置计数器
                redis_client.setex(key, period, 1)
            else:
                current = int(current)
                if current >= limit:
                    return jsonify({
                        "code": 429,
                        "msg": "Too many requests, please try again later",
                        "data": None
                    }), 429
                # 增加计数
                redis_client.incr(key)

            return f(*args, **kwargs)

        return decorated_function
    return decorator
