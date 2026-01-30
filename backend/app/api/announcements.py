"""
公告 API 路由 (用户端)
提供公告的查询功能（无需权限）
"""
from flask import Blueprint, request, jsonify
from app.services.admin import get_active_announcements

bp = Blueprint('announcements', __name__, url_prefix='/api')


@bp.route('/announcements', methods=['GET'])
def list_announcements_route():
    """
    获取启用的公告列表（用户端）
    GET /api/announcements?limit=10

    Query Parameters:
        limit (int): 返回的最大数量，默认10

    Returns:
        JSON: {
            "code": 0,
            "message": "Success",
            "data": [...]
        }
    """
    try:
        limit = request.args.get('limit', 10, type=int)
        
        # 限制最大数量
        if limit > 50:
            limit = 50

        result = get_active_announcements(limit)

        return jsonify({
            "code": 0,
            "message": "Success",
            "data": result
        }), 200

    except Exception as e:
        return jsonify({"code": 500, "message": f"Internal error: {str(e)}", "data": None}), 500
