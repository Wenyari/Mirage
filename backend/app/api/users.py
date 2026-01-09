"""
用户相关 API 路由
包含个人信息、会员等级等接口
"""
from flask import Blueprint, request, jsonify
from flask_jwt_extended import get_jwt_identity
from app.utils.auth import jwt_and_redis_required

bp = Blueprint('users', __name__, url_prefix='/api/users')


@bp.route('/me', methods=['GET'])
@jwt_and_redis_required()
def get_user_info():
    """
    获取个人信息
    GET /api/users/me
    Header: Authorization: Bearer <token>
    """
    try:
        user_id = int(get_jwt_identity())

        # 从数据库查询用户信息
        from app.models.user import User

        user = User.query.get(user_id)
        if not user:
            return jsonify({"code": 404, "msg": "User not found", "data": None}), 404

        # 构建返回数据（使用 to_dict() 已包含新字段）
        user_data = user.to_dict()

        return jsonify({
            "code": 200,
            "msg": "Success",
            "data": user_data
        }), 200

    except Exception as e:
        return jsonify({"code": 500, "msg": f"Internal error: {str(e)}", "data": None}), 500


@bp.route('/membership/plans', methods=['GET'])
def get_membership_plans():
    """
    获取所有会员等级权益表
    GET /api/users/membership/plans
    """
    try:
        # TODO: 从数据库查询会员配置
        # from app.models import MembershipConfig
        # configs = MembershipConfig.query.all()
        # plans = [config.to_dict() for config in configs]

        plans = [
            {"level": 1, "name": "T1", "concurrency_limit": 1, "queue_priority": 0},
            {"level": 2, "name": "T2", "concurrency_limit": 2, "queue_priority": 5},
            {"level": 3, "name": "T3", "concurrency_limit": 3, "queue_priority": 10},
            {"level": 4, "name": "T4", "concurrency_limit": 4, "queue_priority": 15},
            {"level": 5, "name": "T5", "concurrency_limit": 5, "queue_priority": 20},
        ]

        return jsonify({
            "code": 200,
            "msg": "Success",
            "data": plans
        }), 200

    except Exception as e:
        return jsonify({"code": 500, "msg": "Internal error", "data": None}), 500
