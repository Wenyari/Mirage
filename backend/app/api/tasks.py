"""
任务相关 API 路由
包含任务提交、查询状态、取消、历史记录等接口
"""
from flask import Blueprint, request, jsonify
from flask_jwt_extended import get_jwt_identity
from app.utils.auth import jwt_and_redis_required
from app.services.task_service import TaskService

bp = Blueprint('tasks', __name__, url_prefix='/api/tasks')


@bp.route('', methods=['POST'])
@jwt_and_redis_required()
def create_task():
    """
    提交新任务 (含并发检查、预扣费、入队)
    POST /api/tasks
    Body: {
        "model": "sora",
        "prompt": "A beautiful sunset over the ocean",
        "params": {"duration": 5, "quality": "hd"},
        "input_file_url": "https://..."
    }
    """
    try:
        user_id = get_jwt_identity()
        data = request.get_json()

        model = data.get('model')
        prompt = data.get('prompt')

        if not model or not prompt:
            return jsonify({"code": 400, "msg": "Model and prompt are required", "data": None}), 400

        # 调用服务层提交任务
        result = TaskService.submit_task(user_id, data)

        return jsonify({
            "code": 200,
            "msg": result['msg'],
            "data": {
                "task_id": result['task_id'],
                "status": result['status']
            }
        }), 200

    except ValueError as e:
        # 业务错误 (如并发超限、余额不足)
        return jsonify({"code": 400, "msg": str(e), "data": None}), 400
    except Exception as e:
        return jsonify({"code": 500, "msg": "Internal error", "data": None}), 500


@bp.route('/<task_id>', methods=['GET'])
@jwt_and_redis_required()
def get_task_status(task_id):
    """
    查询任务状态 (轮询接口，支持实时进度)
    GET /api/tasks/{task_id}
    """
    try:
        user_id = get_jwt_identity()

        # 调用服务层查询任务
        task_data = TaskService.get_task_status(user_id, task_id)

        return jsonify({
            "code": 200,
            "msg": "Success",
            "data": task_data
        }), 200

    except ValueError as e:
        return jsonify({"code": 404, "msg": str(e), "data": None}), 404
    except Exception as e:
        return jsonify({"code": 500, "msg": "Internal error", "data": None}), 500


@bp.route('/<task_id>/cancel', methods=['POST'])
@jwt_and_redis_required()
def cancel_task(task_id):
    """
    取消任务 (仅限排队中的任务)
    POST /api/tasks/{task_id}/cancel
    """
    try:
        user_id = get_jwt_identity()

        # 调用服务层取消任务
        result = TaskService.cancel_task(user_id, task_id)

        return jsonify({
            "code": 200,
            "msg": result['msg'],
            "data": None
        }), 200

    except ValueError as e:
        return jsonify({"code": 400, "msg": str(e), "data": None}), 400
    except Exception as e:
        return jsonify({"code": 500, "msg": "Internal error", "data": None}), 500


@bp.route('', methods=['GET'])
@jwt_and_redis_required()
def get_task_history():
    """
    获取任务历史记录
    GET /api/tasks?page=1&size=20
    """
    try:
        user_id = get_jwt_identity()
        page = request.args.get('page', 1, type=int)
        size = request.args.get('size', 20, type=int)

        # 调用服务层查询历史
        result = TaskService.get_task_history(user_id, page, size)

        return jsonify({
            "code": 200,
            "msg": "Success",
            "data": result
        }), 200

    except Exception as e:
        return jsonify({"code": 500, "msg": "Internal error", "data": None}), 500
