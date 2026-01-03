"""
钱包/积分相关 API 路由
包含 CDK 兑换、流水查询等接口
"""
from flask import Blueprint, request, jsonify
from flask_jwt_extended import get_jwt_identity
from app.utils.auth import jwt_and_redis_required

bp = Blueprint('wallet', __name__, url_prefix='/api/wallet')


@bp.route('/redeem', methods=['POST'])
@jwt_and_redis_required()
def redeem_cdk():
    """
    CDK 兑换 (含悲观锁防并发)
    POST /api/wallet/redeem
    Body: {"code": "XYZ-123-ABC"}
    """
    try:
        user_id = get_jwt_identity()
        data = request.get_json()
        code = data.get('code')

        if not code:
            return jsonify({"code": 400, "msg": "CDK code is required", "data": None}), 400

        # TODO: 调用 pay_service.redeem_cdk(user_id, code)
        # from app.services.pay_service import redeem_cdk
        # result = redeem_cdk(user_id, code)

        return jsonify({
            "code": 200,
            "msg": "CDK redeemed successfully",
            "data": {
                "added_points": 100,  # TODO: 返回实际充值积分
                "current_balance": 500  # TODO: 返回当前余额
            }
        }), 200

    except ValueError as e:
        # 业务错误 (如 CDK 已使用、已过期)
        return jsonify({"code": 400, "msg": str(e), "data": None}), 400
    except Exception as e:
        return jsonify({"code": 500, "msg": "Internal error", "data": None}), 500


@bp.route('/transactions', methods=['GET'])
@jwt_and_redis_required()
def get_transactions():
    """
    获取资金流水
    GET /api/wallet/transactions?page=1&size=20
    """
    try:
        user_id = get_jwt_identity()
        page = request.args.get('page', 1, type=int)
        size = request.args.get('size', 20, type=int)

        # TODO: 从数据库分页查询流水
        # from app.models import Transaction
        # pagination = Transaction.query.filter_by(user_id=user_id)\
        #     .order_by(Transaction.created_at.desc())\
        #     .paginate(page=page, per_page=size, error_out=False)

        return jsonify({
            "code": 200,
            "msg": "Success",
            "data": {
                "list": [],  # TODO: 返回流水列表
                "total": 0,
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
    获取当前余额
    GET /api/wallet/balance
    """
    try:
        user_id = get_jwt_identity()

        # TODO: 从数据库查询用户余额
        # from app.models import User
        # user = User.query.get(user_id)
        # if not user:
        #     return jsonify({"code": 404, "msg": "User not found", "data": None}), 404

        return jsonify({
            "code": 200,
            "msg": "Success",
            "data": {
                "balance": 100.00  # TODO: 返回实际余额
            }
        }), 200

    except Exception as e:
        return jsonify({"code": 500, "msg": "Internal error", "data": None}), 500
