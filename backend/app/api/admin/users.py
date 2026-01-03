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
    ban_user,
    unban_user,
    update_user_level,
    adjust_user_balance
)

bp = Blueprint('admin_users', __name__)


@bp.route('/users', methods=['GET'])
@login_required
@admin_required
def list_users():
    """
    获取用户列表（带分页和筛选）
    GET /api/admin/users?page=1&per_page=20&keyword=test&status=1&level=3

    Query Parameters:
        page (int): 页码，默认1
        per_page (int): 每页数量，默认20
        keyword (str): 搜索关键词（邮箱）
        status (int): 状态筛选 (0=封禁, 1=正常)
        level (int): 等级筛选 (1-5)

    Returns:
        JSON: {
            "code": 0,
            "message": "Success",
            "data": {
                "total": 100,
                "pages": 5,
                "current_page": 1,
                "per_page": 20,
                "users": [...]
            }
        }
    """
    try:
        # 获取查询参数
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        keyword = request.args.get('keyword', None, type=str)
        status = request.args.get('status', None, type=int)
        level = request.args.get('level', None, type=int)

        # 参数验证
        if per_page < 1 or per_page > 100:
            return jsonify({
                "code": 400,
                "message": "per_page must be between 1 and 100",
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
            per_page=per_page,
            keyword=keyword,
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


@bp.route('/users/<int:user_id>', methods=['GET'])
@login_required
@admin_required
def get_user(user_id):
    """
    获取用户详细信息
    GET /api/admin/users/{user_id}

    Returns:
        JSON: {
            "code": 0,
            "message": "Success",
            "data": {用户详细信息}
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


@bp.route('/users/<int:user_id>/ban', methods=['POST'])
@login_required
@admin_required
def ban_user_endpoint(user_id):
    """
    封禁用户
    POST /api/admin/users/{user_id}/ban

    Returns:
        JSON: {
            "code": 0,
            "message": "Success",
            "data": {操作结果}
        }
    """
    try:
        admin_id = get_jwt_identity()
        data = ban_user(user_id, admin_id)

        return jsonify({
            "code": 0,
            "message": "Success",
            "data": data
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


@bp.route('/users/<int:user_id>/unban', methods=['POST'])
@login_required
@admin_required
def unban_user_endpoint(user_id):
    """
    解封用户
    POST /api/admin/users/{user_id}/unban

    Returns:
        JSON: {
            "code": 0,
            "message": "Success",
            "data": {操作结果}
        }
    """
    try:
        admin_id = get_jwt_identity()
        data = unban_user(user_id, admin_id)

        return jsonify({
            "code": 0,
            "message": "Success",
            "data": data
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


@bp.route('/users/<int:user_id>/level', methods=['PUT'])
@login_required
@admin_required
def update_level(user_id):
    """
    修改用户等级
    PUT /api/admin/users/{user_id}/level

    Request Body:
        {
            "level": 3
        }

    Returns:
        JSON: {
            "code": 0,
            "message": "Success",
            "data": {操作结果}
        }
    """
    try:
        # 获取请求数据
        data = request.get_json()
        if not data or 'level' not in data:
            return jsonify({
                "code": 400,
                "message": "level is required",
                "data": None
            }), 400

        new_level = data['level']

        # 验证等级
        if not isinstance(new_level, int) or new_level not in [1, 2, 3, 4, 5]:
            return jsonify({
                "code": 400,
                "message": "level must be an integer between 1 and 5",
                "data": None
            }), 400

        admin_id = get_jwt_identity()
        result = update_user_level(user_id, new_level, admin_id)

        return jsonify({
            "code": 0,
            "message": "Success",
            "data": result
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


@bp.route('/users/<int:user_id>/balance', methods=['POST'])
@login_required
@admin_required
def adjust_balance(user_id):
    """
    调整用户余额
    POST /api/admin/users/{user_id}/balance

    Request Body:
        {
            "amount": 100.50,  // 正数=增加，负数=扣除
            "remark": "Manual adjustment by admin"
        }

    Returns:
        JSON: {
            "code": 0,
            "message": "Success",
            "data": {操作结果}
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
        remark = data.get('remark', 'Admin adjustment')

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

        admin_id = get_jwt_identity()
        result = adjust_user_balance(user_id, amount, remark, admin_id)

        return jsonify({
            "code": 0,
            "message": "Success",
            "data": result
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
