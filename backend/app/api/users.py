"""
用户相关 API 路由
包含个人信息、会员等级等接口
"""
from flask import Blueprint, request, jsonify
from flask_jwt_extended import get_jwt_identity
from app.utils.auth import jwt_and_redis_required
import bcrypt

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


@bp.route('/me', methods=['PATCH'])
@jwt_and_redis_required()
def update_user_info():
    """
    更新用户信息
    PATCH /api/users/me
    Body: {"name": "新用户名", "current_password": "当前密码", "new_password": "新密码"}
    Header: Authorization: Bearer <token>
    """
    try:
        user_id = int(get_jwt_identity())
        data = request.get_json()

        # 从数据库查询用户信息
        from app.models.user import User
        from app.extensions import db

        user = User.query.get(user_id)
        if not user:
            return jsonify({"code": 404, "msg": "User not found", "data": None}), 404

        # 更新用户名
        if 'name' in data:
            name = data['name'].strip()
            if len(name) > 50:
                return jsonify({"code": 400, "msg": "用户名长度不能超过50个字符", "data": None}), 400
            # 检查用户名是否已被使用（排除自己）
            existing_user = User.query.filter(User.name == name, User.id != user_id).first()
            if existing_user:
                return jsonify({"code": 400, "msg": "用户名已被使用", "data": None}), 400
            user.name = name or None

        # 更新密码
        if 'new_password' in data:
            current_password = data.get('current_password')
            new_password = data['new_password']

            # 验证当前密码
            if not current_password or not bcrypt.checkpw(current_password.encode('utf-8'), user.password_hash.encode('utf-8')):
                return jsonify({"code": 400, "msg": "当前密码错误", "data": None}), 400

            # 验证新密码长度
            if len(new_password) < 6:
                return jsonify({"code": 400, "msg": "新密码长度至少6个字符", "data": None}), 400

            # Hash新密码
            password_hash = bcrypt.hashpw(new_password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
            user.password_hash = password_hash

        # 保存更改
        db.session.commit()

        # 返回更新后的用户信息
        user_data = user.to_dict()
        return jsonify({
            "code": 200,
            "msg": "用户信息更新成功",
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
