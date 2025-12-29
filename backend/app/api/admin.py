"""
管理员 API 路由
包含 CDK 生成、用户管理、数据统计等接口
需要 @admin_required 装饰器保护
"""
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity

bp = Blueprint('admin', __name__, url_prefix='/api/admin')


@bp.route('/cdk/generate', methods=['POST'])
@jwt_required()
# @admin_required  # TODO: 添加管理员权限检查装饰器
def generate_cdk():
    """
    批量生成 CDK
    POST /api/admin/cdk/generate
    Body: {
        "points": 500,
        "count": 100,
        "batch_name": "开业活动",
        "expire_days": 30
    }
    """
    try:
        data = request.get_json()
        points = data.get('points')
        count = data.get('count')
        batch_name = data.get('batch_name', '')
        expire_days = data.get('expire_days')

        if not all([points, count]):
            return jsonify({"code": 400, "msg": "Missing required fields", "data": None}), 400

        # TODO: 调用 admin_service.generate_cdk_batch(...)
        # from app.services.admin_service import generate_cdk_batch
        # codes = generate_cdk_batch(points, count, batch_name, expire_days)

        return jsonify({
            "code": 200,
            "msg": f"Successfully generated {count} CDK codes",
            "data": {
                "batch_name": batch_name,
                "count": count,
                "codes": []  # TODO: 返回生成的 CDK 列表
            }
        }), 200

    except Exception as e:
        return jsonify({"code": 500, "msg": "Internal error", "data": None}), 500


@bp.route('/users/<int:user_id>/ban', methods=['PATCH'])
@jwt_required()
# @admin_required  # TODO: 添加管理员权限检查装饰器
def ban_user(user_id):
    """
    封禁/解封用户
    PATCH /api/admin/users/{user_id}/ban
    Body: {"status": 0}  # 0=封禁, 1=正常
    """
    try:
        data = request.get_json()
        status = data.get('status')

        if status not in [0, 1]:
            return jsonify({"code": 400, "msg": "Invalid status value", "data": None}), 400

        # TODO: 更新用户状态
        # from app.models import User
        # user = User.query.get(user_id)
        # if not user:
        #     return jsonify({"code": 404, "msg": "User not found", "data": None}), 404
        # user.status = status
        # db.session.commit()

        return jsonify({
            "code": 200,
            "msg": f"User {'banned' if status == 0 else 'unbanned'} successfully",
            "data": None
        }), 200

    except Exception as e:
        return jsonify({"code": 500, "msg": "Internal error", "data": None}), 500


@bp.route('/stats', methods=['GET'])
@jwt_required()
# @admin_required  # TODO: 添加管理员权限检查装饰器
def get_statistics():
    """
    获取仪表盘统计数据
    GET /api/admin/stats
    """
    try:
        # TODO: 统计各项数据
        # - 总用户数
        # - 总任务数
        # - 今日收入
        # - 各等级用户分布
        # - 任务成功率

        return jsonify({
            "code": 200,
            "msg": "Success",
            "data": {
                "total_users": 0,
                "total_tasks": 0,
                "total_revenue": 0.00,
                "today_revenue": 0.00,
                "user_level_distribution": {
                    "T1": 0, "T2": 0, "T3": 0, "T4": 0, "T5": 0
                },
                "task_success_rate": 0.0
            }
        }), 200

    except Exception as e:
        return jsonify({"code": 500, "msg": "Internal error", "data": None}), 500
