"""
管理员仪表盘 API 路由
提供仪表盘数据接口
"""
from flask import Blueprint, request, jsonify
from app.utils.decorators import admin_required, login_required
from app.services.admin import get_dashboard_overview, get_trend_chart_data

bp = Blueprint('admin_dashboard', __name__)


@bp.route('/stats/overview', methods=['GET'])
@login_required
@admin_required
def get_overview():
    """
    获取核心指标
    GET /api/admin/stats/overview

    Returns:
        JSON: {
            "code": 0,
            "message": "Success",
            "data": {
                "today_new_users": 42,
                "today_points_consumed": 12500.50,
                "today_cdk_recharge": 50000.00,
                "active_tasks": 18
            }
        }
    """
    try:
        data = get_dashboard_overview()
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


@bp.route('/stats/chart', methods=['GET'])
@login_required
@admin_required
def get_chart_data():
    """
    获取趋势图数据
    GET /api/admin/stats/chart?days=7

    Query Parameters:
        days (str): 查询天数，可选值："7" 或 "30"，默认为 "7"

    Returns:
        JSON: {
            "code": 0,
            "message": "Success",
            "data": [
                {
                    "date": "2024-12-24",
                    "new_users": 35,
                    "points_consumed": 9800.50,
                    "cdk_recharge": 28000.00
                },
                ...
            ]
        }
    """
    try:
        # 获取查询参数
        days_str = request.args.get('days', '7')

        # 验证参数
        if days_str not in ['7', '30']:
            return jsonify({
                "code": 400,
                "message": "Invalid days parameter. Must be '7' or '30'",
                "data": None
            }), 400

        days = int(days_str)
        data = get_trend_chart_data(days=days)

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
