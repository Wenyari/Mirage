"""
活动管理 API 路由 (管理员端)
提供活动的创建、更新、删除、统计等功能
"""
from flask import Blueprint, request, jsonify
from flask_jwt_extended import get_jwt_identity
from app.utils.decorators import admin_required, login_required
from app.services.admin.activity_admin_service import (
    create_activity,
    update_activity,
    delete_activity,
    get_activity_list,
    get_activity_stats,
    get_checkin_config,
    update_checkin_config
)

bp = Blueprint('admin_activities', __name__)


@bp.route('/activities', methods=['POST'])
@login_required
@admin_required
def create_activity_route():
    """
    创建活动
    POST /api/admin/activities

    Request Body:
        {
            "code": "SPRING2024",
            "name": "春季福利",
            "description": "新春活动赠送积分",
            "points": 100,
            "expire_days": 30,
            "max_claims_per_user": 1,
            "required_level": 1,
            "start_at": "2024-03-01T00:00:00",
            "end_at": "2024-03-31T23:59:59"
        }

    Returns:
        JSON: {
            "code": 0,
            "message": "Activity created successfully",
            "data": {...}
        }
    """
    try:
        data = request.get_json()
        if not data:
            return jsonify({
                "code": 400,
                "message": "Request body is required",
                "data": None
            }), 400

        # 必填参数验证
        required_fields = ['code', 'name', 'points']
        for field in required_fields:
            if field not in data:
                return jsonify({
                    "code": 400,
                    "message": f"Missing required field: {field}",
                    "data": None
                }), 400

        result = create_activity(data)

        return jsonify({
            "code": 0,
            "message": "Activity created successfully",
            "data": result
        }), 200

    except ValueError as e:
        return jsonify({"code": 400, "message": str(e), "data": None}), 400
    except Exception as e:
        return jsonify({"code": 500, "message": f"Internal error: {str(e)}", "data": None}), 500


@bp.route('/activities/<int:activity_id>', methods=['PUT'])
@login_required
@admin_required
def update_activity_route(activity_id):
    """
    更新活动
    PUT /api/admin/activities/<activity_id>

    Request Body:
        {
            "name": "春季福利（更新）",
            "description": "...",
            "status": "paused"
            ...
        }

    Returns:
        JSON: {
            "code": 0,
            "message": "Activity updated successfully",
            "data": {...}
        }
    """
    try:
        data = request.get_json()
        if not data:
            return jsonify({
                "code": 400,
                "message": "Request body is required",
                "data": None
            }), 400

        result = update_activity(activity_id, data)

        return jsonify({
            "code": 0,
            "message": "Activity updated successfully",
            "data": result
        }), 200

    except ValueError as e:
        return jsonify({"code": 400, "message": str(e), "data": None}), 400
    except Exception as e:
        return jsonify({"code": 500, "message": f"Internal error: {str(e)}", "data": None}), 500


@bp.route('/activities/<int:activity_id>', methods=['DELETE'])
@login_required
@admin_required
def delete_activity_route(activity_id):
    """
    删除活动
    DELETE /api/admin/activities/<activity_id>

    Returns:
        JSON: {
            "code": 0,
            "message": "Activity deleted successfully",
            "data": null
        }
    """
    try:
        result = delete_activity(activity_id)

        return jsonify({
            "code": 0,
            "message": result.get('msg', 'Activity deleted successfully'),
            "data": None
        }), 200

    except ValueError as e:
        return jsonify({"code": 400, "message": str(e), "data": None}), 400
    except Exception as e:
        return jsonify({"code": 500, "message": f"Internal error: {str(e)}", "data": None}), 500


@bp.route('/activities', methods=['GET'])
@login_required
@admin_required
def list_activities_route():
    """
    获取活动列表（分页）
    GET /api/admin/activities?page=1&size=20&status=active

    Returns:
        JSON: {
            "code": 0,
            "message": "Success",
            "data": {
                "list": [...],
                "total": 50,
                "page": 1,
                "size": 20
            }
        }
    """
    try:
        page = request.args.get('page', 1, type=int)
        size = request.args.get('size', 20, type=int)
        status = request.args.get('status', None, type=str)

        result = get_activity_list(page, size, status)

        return jsonify({
            "code": 0,
            "message": "Success",
            "data": result
        }), 200

    except Exception as e:
        return jsonify({"code": 500, "message": f"Internal error: {str(e)}", "data": None}), 500


@bp.route('/activities/<int:activity_id>/stats', methods=['GET'])
@login_required
@admin_required
def activity_stats_route(activity_id):
    """
    获取活动统计信息
    GET /api/admin/activities/<activity_id>/stats

    Returns:
        JSON: {
            "code": 0,
            "message": "Success",
            "data": {
                "activity_id": 1,
                "total_claims": 150,
                "unique_users": 120,
                "total_points_granted": 15000.00,
                ...
            }
        }
    """
    try:
        result = get_activity_stats(activity_id)

        return jsonify({
            "code": 0,
            "message": "Success",
            "data": result
        }), 200

    except ValueError as e:
        return jsonify({"code": 400, "message": str(e), "data": None}), 400
    except Exception as e:
        return jsonify({"code": 500, "message": f"Internal error: {str(e)}", "data": None}), 500


@bp.route('/checkin/config', methods=['GET'])
@login_required
@admin_required
def get_checkin_config_route():
    """
    获取签到配置
    GET /api/admin/checkin/config

    Returns:
        JSON: {
            "code": 0,
            "message": "Success",
            "data": {
                "list": [
                    {"day": 1, "points": 10.00, "is_active": true},
                    ...
                ]
            }
        }
    """
    try:
        result = get_checkin_config()

        return jsonify({
            "code": 0,
            "message": "Success",
            "data": {"list": result}
        }), 200

    except Exception as e:
        return jsonify({"code": 500, "message": f"Internal error: {str(e)}", "data": None}), 500


@bp.route('/checkin/config', methods=['PUT'])
@login_required
@admin_required
def update_checkin_config_route():
    """
    更新签到配置
    PUT /api/admin/checkin/config

    Request Body:
        {
            "configs": [
                {"day": 1, "points": 10.00, "is_active": true},
                {"day": 2, "points": 15.00, "is_active": true},
                ...
            ]
        }

    Returns:
        JSON: {
            "code": 0,
            "message": "Checkin config updated successfully",
            "data": null
        }
    """
    try:
        data = request.get_json()
        if not data or 'configs' not in data:
            return jsonify({
                "code": 400,
                "message": "configs field is required",
                "data": None
            }), 400

        configs = data.get('configs')
        if not isinstance(configs, list):
            return jsonify({
                "code": 400,
                "message": "configs must be an array",
                "data": None
            }), 400

        result = update_checkin_config(configs)

        return jsonify({
            "code": 0,
            "message": result.get('msg', 'Checkin config updated successfully'),
            "data": None
        }), 200

    except ValueError as e:
        return jsonify({"code": 400, "message": str(e), "data": None}), 400
    except Exception as e:
        return jsonify({"code": 500, "message": f"Internal error: {str(e)}", "data": None}), 500
