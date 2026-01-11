"""
鉴权相关 API 路由
包含注册、登录、发送验证码等接口
"""
from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.utils.auth import jwt_and_redis_required
from app.utils.turnstile import verify_turnstile
# avoid name collision with route function 'send_verify_code'
from app.services import send_verify_code as send_verify_code_service, register_user, login_user

bp = Blueprint('auth', __name__, url_prefix='/api/auth')


@bp.route('/code', methods=['POST'])
def send_verify_code():
    """
    发送邮箱验证码
    POST /api/auth/code
    Body: {"email": "user@example.com", "cf_token": "TURNSTILE_TOKEN_STRING"}
    """
    try:
        data = request.get_json(silent=True) or {}
        # 支持 JSON body 或 query string 两种方式传参
        email = data.get('email') or request.args.get('email')
        cf_token = data.get('cf_token') or request.args.get('cf_token')

        if not email:
            return jsonify({"code": 400, "msg": "Email is required", "data": None}), 400

        if not cf_token:
            return jsonify({"code": 400, "msg": "Captcha token is required", "data": None}), 400

        # 验证 Cloudflare Turnstile Token
        user_ip = request.remote_addr
        if not verify_turnstile(cf_token, user_ip):
            current_app.logger.warning(f"Turnstile verification failed for {email} from IP {user_ip}")
            return jsonify({"code": 400, "msg": "Captcha verification failed", "data": None}), 400

        try:
            # 调用服务层发送验证码
            send_verify_code_service(email)
        except ValueError as e:
            # 业务错误（格式/限流/SMTP失败等）返回 400
            current_app.logger.warning(f"send_verify_code failed for {email}: {e}")
            return jsonify({"code": 400, "msg": str(e), "data": None}), 400
        except Exception as e:
            # 未知错误返回 500，记录日志以便排查
            current_app.logger.exception(f"Unexpected error in send_verify_code: {e}")
            return jsonify({"code": 500, "msg": "Internal error", "data": None}), 500

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
        # 支持 JSON body 或 query string 两种方式传参（与 login 保持一致）
        if request.is_json:
            try:
                data = request.get_json()
            except Exception:
                # 如果 Content-Type 是 JSON 但 body 为空或无效，回退到 query string
                data = request.args.to_dict()
        else:
            data = request.args.to_dict()

        email = (data or {}).get('email')
        code = (data or {}).get('code')
        password = (data or {}).get('password')

        if not all([email, code, password]):
            return jsonify({"code": 400, "msg": "Missing required fields", "data": None}), 400

        user_id = register_user(email, code, password)

        return jsonify({
            "code": 200,
            "msg": "Registration successful",
            "data": {"user_id": user_id}
        }), 200

    except ValueError as e:
        return jsonify({"code": 400, "msg": str(e), "data": None}), 400
    except Exception as e:
        current_app.logger.exception(f"Unexpected error in register: {e}")
        return jsonify({"code": 500, "msg": "Internal error", "data": None}), 500


@bp.route('/login', methods=['POST'])
def login():
    """
    用户登录
    POST /api/auth/login
    Body: {"email": "...", "password": "...", "cf_token": "TURNSTILE_TOKEN_STRING"}
    """
    try:
        # 支持JSON body和URL参数两种方式
        if request.is_json:
            data = request.get_json()
        else:
            data = request.args.to_dict()

        email = data.get('email')
        password = data.get('password')
        cf_token = data.get('cf_token')

        if not all([email, password]):
            return jsonify({"code": 400, "msg": "Email and password are required", "data": None}), 400

        if not cf_token:
            return jsonify({"code": 400, "msg": "Captcha token is required", "data": None}), 400

        # 验证 Cloudflare Turnstile Token
        user_ip = request.remote_addr
        if not verify_turnstile(cf_token, user_ip):
            current_app.logger.warning(f"Turnstile verification failed for login attempt from IP {user_ip}")
            return jsonify({"code": 400, "msg": "Captcha verification failed", "data": None}), 400

        # 使用服务层登录逻辑（验证数据库并生成 token）
        result = login_user(email, password, request.remote_addr)

        return jsonify({
            "code": 200,
            "msg": "Login successful！",
            "data": result
        }), 200

    except Exception as e:
        return jsonify({"code": 500, "msg": f"Internal error: {str(e)}", "data": None}), 500


@bp.route('/logout', methods=['POST'])
@jwt_required()
def logout():
    """
    用户登出，清除 Redis 中保存的单点登录 Token
    POST /api/auth/logout
    Header: Authorization: Bearer <token>
    """
    try:
        user_id = get_jwt_identity()

        # 尝试从 Redis 删除该用户的 token（如果 Redis 未配置则记录警告）
        try:
            from app.extensions import redis_client
        except Exception:
            redis_client = None

        if redis_client is None:
            current_app.logger.warning("Redis not configured; cannot revoke token on logout")
        else:
            auth_key = f"auth:token:{user_id}"
            try:
                redis_client.delete(auth_key)
            except Exception as e:
                current_app.logger.exception(f"Failed to delete auth token for user {user_id}: {e}")

        return jsonify({"code": 200, "msg": "Logout successful", "data": None}), 200

    except Exception as e:
        current_app.logger.exception(f"Unexpected error in logout: {e}")
        return jsonify({"code": 500, "msg": "Internal error", "data": None}), 500


@bp.route('/me', methods=['GET'])
@jwt_and_redis_required()
def get_current_user():
    """
    获取当前用户信息
    GET /api/auth/me
    Header: Authorization: Bearer <token>
    """
    try:
        user_id = get_jwt_identity()

        # 从数据库查询用户信息并返回真实数据
        from app.models.user import User
        from app.models.user import MembershipConfig

        try:
            uid = int(user_id)
        except Exception:
            uid = user_id

        user = User.query.get(uid)
        if not user:
            return jsonify({"code": 404, "msg": "User not found", "data": None}), 404

        # 获取会员描述（如 T1/T2..）
        try:
            membership = MembershipConfig.query.filter_by(level=user.level).first()
            vip_desc = membership.name if membership else f"T{user.level}"
        except Exception:
            vip_desc = f"T{user.level}"

        # 计算总余额
        total_balance = float(user.recharge_balance + user.activity_balance)

        return jsonify({
            "code": 200,
            "msg": "Success",
            "data": {
                "id": user.id,
                "email": user.email,
                "name": user.name,  # 用户名
                "balance": total_balance,  # 兼容旧版前端
                "balance_detail": {
                    "recharge_balance": float(user.recharge_balance),
                    "activity_balance": float(user.activity_balance),
                    "total_balance": total_balance
                },
                "checkin_info": {
                    "last_checkin_at": user.last_checkin_at.isoformat() if user.last_checkin_at else None,
                    "total_checkin_days": user.total_checkin_days
                },
                "level": user.level,
                "vip_desc": vip_desc,
                "role": user.role,
                "status": user.status,
                "created_at": user.created_at.isoformat() if user.created_at else None,
                "last_active": getattr(user, 'last_active', None)
            }
        }), 200

    except Exception as e:
        return jsonify({"code": 500, "msg": "Internal error", "data": None}), 500
