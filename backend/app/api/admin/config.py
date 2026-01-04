"""
系统配置管理 API 路由
提供会员等级配置等系统级配置的管理接口
"""
from flask import Blueprint, request, jsonify
from flask_jwt_extended import get_jwt_identity
from app.utils.decorators import admin_required, login_required
from app.services.admin import (
    get_membership_config,
    update_membership_config
)

bp = Blueprint('admin_config', __name__)


@bp.route('/config/membership', methods=['GET'])
@login_required
@admin_required
def get_membership_config_endpoint():
    """
    获取会员等级配置
    GET /api/admin/config/membership

    Returns:
        JSON: {
            "code": 0,
            "message": "Success",
            "data": {
                "T1": {...},
                "T2": {...},
                ...
            }
        }
    """
    try:
        config = get_membership_config()

        return jsonify({
            "code": 0,
            "message": "Success",
            "data": config
        }), 200

    except Exception as e:
        return jsonify({
            "code": 500,
            "message": f"Internal error: {str(e)}",
            "data": None
        }), 500


@bp.route('/config/membership', methods=['PUT'])
@login_required
@admin_required
def update_membership_config_endpoint():
    """
    更新会员等级配置
    PUT /api/admin/config/membership

    Request Body:
        {
            "T1": {
                "concurrent_limit": 1,
                "queue_weight": 1,
                "price": 0
            },
            "T2": {
                "concurrent_limit": 3,
                "queue_weight": 2,
                "price": 29
            },
            ...
        }

    Returns:
        JSON: {
            "code": 0,
            "message": "Membership config updated successfully",
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

        # 调用服务层
        update_membership_config(data)

        return jsonify({
            "code": 0,
            "message": "Membership config updated successfully",
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
