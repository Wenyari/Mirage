"""
公告管理 API 路由 (管理员端)
提供公告的创建、更新、删除、列表查询等功能
"""
from flask import Blueprint, request, jsonify
from flask_jwt_extended import get_jwt_identity
from app.utils.decorators import admin_required, login_required
from app.services.admin import (
    create_announcement,
    update_announcement,
    delete_announcement,
    get_announcement_list,
    get_announcement_detail
)

bp = Blueprint('admin_announcements', __name__)


@bp.route('/announcements', methods=['POST'])
@login_required
@admin_required
def create_announcement_route():
    """
    创建公告
    POST /api/admin/announcements

    Request Body:
        {
            "title": "系统维护通知",
            "content": "本周六凌晨2:00-4:00进行系统维护...",
            "publish_time": "2024-03-20T10:00:00",
            "is_active": true
        }

    Returns:
        JSON: {
            "code": 0,
            "message": "Announcement created successfully",
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
        required_fields = ['title', 'content', 'publish_time']
        for field in required_fields:
            if field not in data:
                return jsonify({
                    "code": 400,
                    "message": f"Missing required field: {field}",
                    "data": None
                }), 400

        result = create_announcement(data)

        return jsonify({
            "code": 0,
            "message": "Announcement created successfully",
            "data": result
        }), 200

    except ValueError as e:
        return jsonify({"code": 400, "message": str(e), "data": None}), 400
    except Exception as e:
        return jsonify({"code": 500, "message": f"Internal error: {str(e)}", "data": None}), 500


@bp.route('/announcements/<int:announcement_id>', methods=['PUT'])
@login_required
@admin_required
def update_announcement_route(announcement_id):
    """
    更新公告
    PUT /api/admin/announcements/<announcement_id>

    Request Body:
        {
            "title": "系统维护通知（更新）",
            "content": "...",
            "publish_time": "2024-03-20T12:00:00",
            "is_active": false
        }

    Returns:
        JSON: {
            "code": 0,
            "message": "Announcement updated successfully",
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

        result = update_announcement(announcement_id, data)

        return jsonify({
            "code": 0,
            "message": "Announcement updated successfully",
            "data": result
        }), 200

    except ValueError as e:
        return jsonify({"code": 400, "message": str(e), "data": None}), 400
    except Exception as e:
        return jsonify({"code": 500, "message": f"Internal error: {str(e)}", "data": None}), 500


@bp.route('/announcements/<int:announcement_id>', methods=['DELETE'])
@login_required
@admin_required
def delete_announcement_route(announcement_id):
    """
    删除公告
    DELETE /api/admin/announcements/<announcement_id>

    Returns:
        JSON: {
            "code": 0,
            "message": "Announcement deleted successfully",
            "data": null
        }
    """
    try:
        result = delete_announcement(announcement_id)

        return jsonify({
            "code": 0,
            "message": result.get('msg', 'Announcement deleted successfully'),
            "data": None
        }), 200

    except ValueError as e:
        return jsonify({"code": 400, "message": str(e), "data": None}), 400
    except Exception as e:
        return jsonify({"code": 500, "message": f"Internal error: {str(e)}", "data": None}), 500


@bp.route('/announcements', methods=['GET'])
@login_required
@admin_required
def list_announcements_route():
    """
    获取公告列表（分页）
    GET /api/admin/announcements?page=1&size=20&is_active=true

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
        is_active_str = request.args.get('is_active', None, type=str)
        
        # 转换is_active参数
        is_active = None
        if is_active_str is not None:
            is_active = is_active_str.lower() in ['true', '1', 'yes']

        result = get_announcement_list(page, size, is_active)

        return jsonify({
            "code": 0,
            "message": "Success",
            "data": result
        }), 200

    except Exception as e:
        return jsonify({"code": 500, "message": f"Internal error: {str(e)}", "data": None}), 500


@bp.route('/announcements/<int:announcement_id>', methods=['GET'])
@login_required
@admin_required
def get_announcement_route(announcement_id):
    """
    获取单个公告详情
    GET /api/admin/announcements/<announcement_id>

    Returns:
        JSON: {
            "code": 0,
            "message": "Success",
            "data": {...}
        }
    """
    try:
        result = get_announcement_detail(announcement_id)

        return jsonify({
            "code": 0,
            "message": "Success",
            "data": result
        }), 200

    except ValueError as e:
        return jsonify({"code": 400, "message": str(e), "data": None}), 400
    except Exception as e:
        return jsonify({"code": 500, "message": f"Internal error: {str(e)}", "data": None}), 500
