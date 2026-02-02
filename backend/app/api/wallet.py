"""
钱包/积分相关 API 路由
包含 CDK 兑换、流水查询等接口
"""
from flask import Blueprint, request, jsonify
from flask_jwt_extended import get_jwt_identity
from datetime import datetime
from app.utils.auth import jwt_and_redis_required
from app.services.pay_service import redeem_cdk
from zoneinfo import ZoneInfo

bp = Blueprint('wallet', __name__, url_prefix='/api/wallet')


@bp.route('/redeem', methods=['POST'])
@jwt_and_redis_required()
def redeem_cdk_route():
    """
    CDK 兑换 (含悲观锁防并发)
    POST /api/wallet/redeem
    Body: {"code": "XYZ-123-ABC"}
    """
    try:
        user_id = int(get_jwt_identity())
        data = request.get_json()
        code = data.get('code')

        if not code:
            return jsonify({"code": 400, "msg": "CDK code is required", "data": None}), 400
        # 预验证：确认 CDK 存在且状态允许兑换，避免在服务层抛出难以理解的异常
        from app.models.wallet import CDK

        cdk = CDK.query.filter_by(code=code).first()
        if not cdk:
            return jsonify({"code": 400, "msg": "Invalid CDK code", "data": None}), 400
        if cdk.status == 1:
            return jsonify({"code": 400, "msg": "CDK has already been used", "data": None}), 400
        if cdk.status == 2:
            return jsonify({"code": 400, "msg": "CDK has been invalidated", "data": None}), 400
        if cdk.expire_at and cdk.expire_at.isoformat() < datetime.now(ZoneInfo("Asia/Shanghai")).isoformat():
            return jsonify({"code": 400, "msg": "CDK has expired", "data": None}), 400

        # 调用 pay_service.redeem_cdk 执行兑换逻辑（服务层会再次使用悲观锁并提交）
        result = redeem_cdk(user_id, code)

        # 只返回可序列化的字段，防止传入非 JSON 可序列化对象导致 jsonify 失败
        added = None
        current = None
        try:
            if isinstance(result, dict):
                added = result.get('added_points')
                current = result.get('current_balance')
            else:
                # 保护性处理：尝试按属性读取
                added = getattr(result, 'added_points', None)
                current = getattr(result, 'current_balance', None)
        except Exception:
            added = None
            current = None

        return jsonify({
            "code": 200,
            "msg": "CDK redeemed successfully",
            "data": {
                "added_points": added,
                "current_balance": current
            }
        }), 200

    except ValueError as e:
        # 业务错误 (如 CDK 已使用、已过期)
        return jsonify({"code": 400, "msg": str(e), "data": None}), 400
    except Exception as e:
        # 返回异常信息以便前端调试（开发环境可保留）
        return jsonify({"code": 500, "msg": f"Internal error: {str(e)}", "data": None}), 500


@bp.route('/transactions', methods=['GET'])
@jwt_and_redis_required()
def get_transactions():
    """
    获取资金流水
    GET /api/wallet/transactions?page=1&size=20
    """
    try:
        user_id = int(get_jwt_identity())
        page = request.args.get('page', 1, type=int)
        size = request.args.get('size', 20, type=int)

        # 从数据库分页查询流水
        from app.models.wallet import Transaction

        pagination = Transaction.query.filter_by(user_id=user_id)\
            .order_by(Transaction.created_at.desc())\
            .paginate(page=page, per_page=size, error_out=False)

        return jsonify({
            "code": 200,
            "msg": "Success",
            "data": {
                "list": [t.to_dict() for t in pagination.items],
                "total": pagination.total,
                "page": page,
                "size": size
            }
        }), 200

    except Exception as e:
        return jsonify({"code": 500, "msg": "Internal error", "data": None}), 500


@bp.route('/balance', methods=['GET'])
@jwt_and_redis_required()
def get_balance():
    """
    获取当前余额（包含充值积分和活动积分）
    GET /api/wallet/balance
    """
    try:
        user_id = int(get_jwt_identity())

        from app.models.user import User

        user = User.query.get(user_id)
        if not user:
            return jsonify({"code": 404, "msg": "User not found", "data": None}), 404

        return jsonify({
            "code": 200,
            "msg": "Success",
            "data": {
                "total_balance": float(user.recharge_balance + user.activity_balance),
                "recharge_balance": float(user.recharge_balance),
                "recharge_balance_expire_at": user.recharge_balance_expire_at.isoformat() if user.recharge_balance_expire_at else None,
                "activity_balance": float(user.activity_balance)
            }
        }), 200

    except Exception as e:
        return jsonify({"code": 500, "msg": f"Internal error: {str(e)}", "data": None}), 500
