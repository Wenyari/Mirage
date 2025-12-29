"""
鉴权相关 API 路由
包含注册、登录、发送验证码等接口
"""
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity

bp = Blueprint('auth', __name__, url_prefix='/api/auth')


@bp.route('/code', methods=['POST'])
def send_verify_code():
    """
    发送邮箱验证码
    POST /api/auth/code
    Body: {"email": "user@example.com"}
    """
    try:
        data = request.get_json()
        email = data.get('email')

        if not email:
            return jsonify({"code": 400, "msg": "Email is required", "data": None}), 400

        # TODO: 调用 auth_service.send_verify_code(email)
        # from app.services.auth_service import send_verify_code
        # send_verify_code(email)

        return jsonify({
            "code": 200,
            "msg": "Verification code sent successfully",
            "data": None
        }), 200

    except ValueError as e:
        return jsonify({"code": 400, "msg": str(e), "data": None}), 400
    except Exception as e:
        return jsonify({"code": 500, "msg": "Internal error", "data": None}), 500


@bp.route('/register', methods=['POST'])
def register():
    """
    用户注册
    POST /api/auth/register
    Body: {"email": "...", "code": "123456", "password": "..."}
    """
    try:
        data = request.get_json()
        email = data.get('email')
        code = data.get('code')
        password = data.get('password')

        if not all([email, code, password]):
            return jsonify({"code": 400, "msg": "Missing required fields", "data": None}), 400

        # TODO: 调用 auth_service.register_user(email, code, password)
        # from app.services.auth_service import register_user
        # user_id = register_user(email, code, password)

        return jsonify({
            "code": 200,
            "msg": "Registration successful",
            "data": {"user_id": 1}  # TODO: 返回实际 user_id
        }), 200

    except ValueError as e:
        return jsonify({"code": 400, "msg": str(e), "data": None}), 400
    except Exception as e:
        return jsonify({"code": 500, "msg": "Internal error", "data": None}), 500


@bp.route('/login', methods=['POST'])
def login():
    """
    用户登录 (含单点登录互斥逻辑)
    POST /api/auth/login
    Body: {"email": "...", "password": "..."}
    """
    try:
        data = request.get_json()
        email = data.get('email')
        password = data.get('password')

        if not all([email, password]):
            return jsonify({"code": 400, "msg": "Email and password are required", "data": None}), 400

        # TODO: 调用 auth_service.login_user(email, password)
        # from app.services.auth_service import login_user
        # result = login_user(email, password, request.remote_addr)

        return jsonify({
            "code": 200,
            "msg": "Login successful",
            "data": {
                "token": "jwt_token_here",  # TODO: 返回实际 token
                "user": {
                    "id": 1,
                    "email": email,
                    "balance": 0,
                    "level": 1
                }
            }
        }), 200

    except ValueError as e:
        return jsonify({"code": 401, "msg": str(e), "data": None}), 401
    except Exception as e:
        return jsonify({"code": 500, "msg": "Internal error", "data": None}), 500


@bp.route('/me', methods=['GET'])
@jwt_required()
def get_current_user():
    """
    获取当前用户信息
    GET /api/auth/me
    Header: Authorization: Bearer <token>
    """
    try:
        user_id = get_jwt_identity()

        # TODO: 从数据库查询用户信息
        # from app.models import User
        # user = User.query.get(user_id)
        # if not user:
        #     return jsonify({"code": 404, "msg": "User not found", "data": None}), 404

        return jsonify({
            "code": 200,
            "msg": "Success",
            "data": {
                "id": user_id,
                "email": "user@example.com",
                "balance": 100.00,
                "level": 1,
                "vip_desc": "T1"
            }
        }), 200

    except Exception as e:
        return jsonify({"code": 500, "msg": "Internal error", "data": None}), 500
