"""
认证相关的工具函数和装饰器
"""
from flask import request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt
from functools import wraps
from app.services import check_token_validity


def jwt_and_redis_required():
    """
    自定义装饰器：结合 JWT 验证和 Redis 单点登录检查
    确保用户已登录且 token 未被登出失效
    """
    def decorator(f):
        @wraps(f)
        @jwt_required()  # 先进行 JWT 验证
        def wrapper(*args, **kwargs):
            try:
                # 获取当前用户 ID 和 token
                user_id = get_jwt_identity()
                jwt_data = get_jwt()
                current_token = request.headers.get('Authorization', '').replace('Bearer ', '')

                # 检查 Redis 中的 token 是否有效（单点登录检查）
                if not check_token_validity(int(user_id), current_token):
                    return jsonify({
                        "code": 401,
                        "msg": "Token has been revoked (logged out from another session)",
                        "data": None
                    }), 401

                return f(*args, **kwargs)
            except Exception as e:
                current_app.logger.exception(f"Token validation error: {e}")
                return jsonify({
                    "code": 401,
                    "msg": "Invalid token",
                    "data": None
                }), 401
        return wrapper
    return decorator
