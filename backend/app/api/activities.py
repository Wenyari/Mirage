"""
活动相关 API 路由 (用户端)
包含活动领取、签到、查询等接口
"""
from flask import Blueprint, request, jsonify
from flask_jwt_extended import get_jwt_identity
from app.utils.auth import jwt_and_redis_required
from app.services.activity_service import (
    claim_activity,
    daily_checkin,
    get_checkin_status,
    get_active_activities,
    get_user_activities
)

bp = Blueprint('activities', __name__, url_prefix='/api/activities')


@bp.route('/claim', methods=['POST'])
@jwt_and_redis_required()
def claim_activity_route():
    """
    领取活动积分
    POST /api/activities/claim
    Body: {"activity_code": "SPRING2024"}
    """
    try:
        user_id = int(get_jwt_identity())
        data = request.get_json()
        activity_code = data.get('activity_code')

        if not activity_code:
            return jsonify({"code": 400, "msg": "Activity code is required", "data": None}), 400

        result = claim_activity(user_id, activity_code)

        return jsonify({
            "code": 200,
            "msg": "Activity claimed successfully",
            "data": result
        }), 200

    except ValueError as e:
        # 业务错误（活动不存在、已达领取上限等）
        return jsonify({"code": 400, "msg": str(e), "data": None}), 400
    except Exception as e:
        return jsonify({"code": 500, "msg": f"Internal error: {str(e)}", "data": None}), 500


@bp.route('/checkin', methods=['POST'])
@jwt_and_redis_required()
def checkin_route():
    """
    每日签到
    POST /api/activities/checkin
    """
    try:
        user_id = int(get_jwt_identity())

        result = daily_checkin(user_id)

        return jsonify({
            "code": 200,
            "msg": "Checkin successful",
            "data": result
        }), 200

    except ValueError as e:
        # 业务错误（今日已签到等）
        return jsonify({"code": 400, "msg": str(e), "data": None}), 400
    except Exception as e:
        return jsonify({"code": 500, "msg": f"Internal error: {str(e)}", "data": None}), 500


@bp.route('/checkin/status', methods=['GET'])
@jwt_and_redis_required()
def checkin_status_route():
    """
    获取签到状态
    GET /api/activities/checkin/status
    """
    try:
        user_id = int(get_jwt_identity())

        result = get_checkin_status(user_id)

        return jsonify({
            "code": 200,
            "msg": "Success",
            "data": result
        }), 200

    except ValueError as e:
        return jsonify({"code": 400, "msg": str(e), "data": None}), 400
    except Exception as e:
        return jsonify({"code": 500, "msg": f"Internal error: {str(e)}", "data": None}), 500


@bp.route('/my-claims', methods=['GET'])
@jwt_and_redis_required()
def my_claims_route():
    """
    获取我的活动领取记录
    GET /api/activities/my-claims?page=1&size=20
    """
    try:
        user_id = int(get_jwt_identity())
        page = request.args.get('page', 1, type=int)
        size = request.args.get('size', 20, type=int)

        result = get_user_activities(user_id, page, size)

        return jsonify({
            "code": 200,
            "msg": "Success",
            "data": result
        }), 200

    except ValueError as e:
        return jsonify({"code": 400, "msg": str(e), "data": None}), 400
    except Exception as e:
        return jsonify({"code": 500, "msg": f"Internal error: {str(e)}", "data": None}), 500


@bp.route('/list', methods=['GET'])
def list_activities_route():
    """
    获取可用活动列表（公开接口）
    GET /api/activities/list
    """
    try:
        result = get_active_activities()

        return jsonify({
            "code": 200,
            "msg": "Success",
            "data": {"list": result}
        }), 200

    except Exception as e:
        return jsonify({"code": 500, "msg": f"Internal error: {str(e)}", "data": None}), 500
