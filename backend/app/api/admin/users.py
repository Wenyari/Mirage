"""
用户管理 API 路由
提供管理员对用户的管理功能
"""
from flask import Blueprint, request, jsonify
from flask_jwt_extended import get_jwt_identity
from app.utils.decorators import admin_required, login_required
from app.services.admin import (
    get_user_list,
    get_user_detail,
    update_user_profile,
    adjust_user_balance
)

bp = Blueprint('admin_users', __name__)


@bp.route('/users', methods=['GET'])
@login_required
@admin_required
def list_users():
    """
    获取用户列表（带分页和筛选）
    GET /api/admin/users?page=1&limit=10&email=test&status=1&level=3

    Query Parameters:
        page (int): 页码，默认1
        limit (int): 每页数量，默认10
        email (str): 邮箱搜索（模糊匹配）
        status (int): 状态筛选 (1=正常, 0=封禁)
        level (int): 等级筛选 (1-5)

    Returns:
        JSON: {
            "code": 0,
            "message": "Success",
            "data": {
                "items": [...],
                "total": 100,
                "page": 1,
                "limit": 10
            }
        }
    """
    try:
        # 获取查询参数
        page = request.args.get('page', 1, type=int)
        limit = request.args.get('limit', 10, type=int)
        email = request.args.get('email', None, type=str)
        status = request.args.get('status', None, type=int)
        level = request.args.get('level', None, type=int)

        # 参数验证
        if limit < 1 or limit > 100:
            return jsonify({
                "code": 400,
                "message": "limit must be between 1 and 100",
                "data": None
            }), 400

        if status is not None and status not in [0, 1]:
            return jsonify({
                "code": 400,
                "message": "status must be 0 or 1",
                "data": None
            }), 400

        if level is not None and level not in [1, 2, 3, 4, 5]:
            return jsonify({
                "code": 400,
                "message": "level must be between 1 and 5",
                "data": None
            }), 400

        # 调用服务层
        data = get_user_list(
            page=page,
            limit=limit,
            email=email,
            status=status,
            level=level
        )

        return jsonify({
            "code": 0,
            "message": "Success",
            "data": data
        }), 200

    except Exception as e:
        return jsonify({
            "code": 500,
            "message": f"Internal error: {str(e)}",
            "data": None
        }), 500


@bp.route('/users/<int:user_id>/details', methods=['GET'])
@login_required
@admin_required
def get_user_details(user_id):
    """
    获取用户详细信息
    GET /api/admin/users/{user_id}/details

    Returns:
        JSON: {
            "code": 0,
            "message": "Success",
            "data": {
                "user": {...},
                "recent_transactions": [...],
                "recent_tasks": [...]
            }
        }
    """
    try:
        data = get_user_detail(user_id)

        return jsonify({
            "code": 0,
            "message": "Success",
            "data": data
        }), 200

    except ValueError as e:
        return jsonify({
            "code": 404,
            "message": str(e),
            "data": None
        }), 404

    except Exception as e:
        return jsonify({
            "code": 500,
            "message": f"Internal error: {str(e)}",
            "data": None
        }), 500


@bp.route('/users/<int:user_id>/profile', methods=['PATCH'])
@login_required
@admin_required
def update_profile(user_id):
    """
    修改用户资料（等级和状态）
    PATCH /api/admin/users/{user_id}/profile

    Request Body:
        {
            "level": 3,     // 用户等级：1-5（可选）
            "status": 0     // 用户状态：1=正常, 0=封禁（可选）
        }

    Returns:
        JSON: {
            "code": 0,
            "message": "User profile updated successfully",
            "data": null
        }
    """
    try:
        # 获取请求数据
        data = request.get_json()
        if not data:
            return jsonify({
                "code": 400,
                "message": "Request body is required",
                "data": None
            }), 400

        level = data.get('level')
        status = data.get('status')

        # 至少需要一个参数
        if level is None and status is None:
            return jsonify({
                "code": 400,
                "message": "At least one of 'level' or 'status' is required",
                "data": None
            }), 400

        # 验证等级
        if level is not None and (not isinstance(level, int) or level not in [1, 2, 3, 4, 5]):
            return jsonify({
                "code": 400,
                "message": "level must be an integer between 1 and 5",
                "data": None
            }), 400

        # 验证状态
        if status is not None and status not in [0, 1]:
            return jsonify({
                "code": 400,
                "message": "status must be 0 or 1",
                "data": None
            }), 400

        admin_id = get_jwt_identity()
        update_user_profile(user_id, level=level, status=status, admin_id=admin_id)

        return jsonify({
            "code": 0,
            "message": "User profile updated successfully",
            "data": None
        }), 200

    except ValueError as e:
        return jsonify({
            "code": 400,
            "message": str(e),
            "data": None
        }), 400

    except Exception as e:
        return jsonify({
            "code": 500,
            "message": f"Internal error: {str(e)}",
            "data": None
        }), 500


@bp.route('/users/<int:user_id>/balance', methods=['PATCH'])
@login_required
@admin_required
def adjust_balance(user_id):
    """
    人工充值/扣费
    PATCH /api/admin/users/{user_id}/balance

    Request Body:
        {
            "amount": 100,              // 变动金额（正数=充值，负数=扣费）
            "reason": "活动奖励",         // 原因说明
            "balance_type": "recharge"  // 积分类型：'recharge' 或 'activity'（可选，默认 'recharge'）
        }

    Returns:
        JSON: {
            "code": 0,
            "message": "Balance updated successfully",
            "data": {
                "balance_type": "recharge",
                "new_balance": 1100
            }
        }
    """
    try:
        # 获取请求数据
        data = request.get_json()
        if not data or 'amount' not in data:
            return jsonify({
                "code": 400,
                "message": "amount is required",
                "data": None
            }), 400

        amount = data['amount']
        reason = data.get('reason', 'Admin adjustment')
        balance_type = data.get('balance_type', 'recharge')

        # 验证金额
        try:
            amount = float(amount)
        except (ValueError, TypeError):
            return jsonify({
                "code": 400,
                "message": "amount must be a valid number",
                "data": None
            }), 400

        if amount == 0:
            return jsonify({
                "code": 400,
                "message": "amount cannot be zero",
                "data": None
            }), 400

        # 验证积分类型
        if balance_type not in ['recharge', 'activity']:
            return jsonify({
                "code": 400,
                "message": "balance_type must be 'recharge' or 'activity'",
                "data": None
            }), 400

        admin_id = get_jwt_identity()
        result = adjust_user_balance(user_id, amount, reason, admin_id, balance_type)

        return jsonify({
            "code": 0,
            "message": "Balance updated successfully",
            "data": {
                "balance_type": result['balance_type'],
                "new_balance": result['new_balance']
            }
        }), 200

    except ValueError as e:
        return jsonify({
            "code": 400,
            "message": str(e),
            "data": None
        }), 400

    except Exception as e:
        return jsonify({
            "code": 500,
            "message": f"Internal error: {str(e)}",
            "data": None
        }), 500
