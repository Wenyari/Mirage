"""
任务相关 API 路由
包含任务提交、查询状态、历史记录等接口
"""
from flask import Blueprint, request, jsonify
from flask_jwt_extended import get_jwt_identity
from app.utils.auth import jwt_and_redis_required

bp = Blueprint('tasks', __name__, url_prefix='/api/tasks')


@bp.route('', methods=['POST'])
@jwt_and_redis_required()
def create_task():
    """
    提交新任务 (含并发检查、预扣费、入队)
    POST /api/tasks
    Body: {
        "model": "sora-v2",
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
        params = data.get('params', {})
        input_file_url = data.get('input_file_url')

        if not model or not prompt:
            return jsonify({"code": 400, "msg": "Model and prompt are required", "data": None}), 400

        # 生成模拟的task_id (临时实现)
        import uuid
        task_id = str(uuid.uuid4())

        return jsonify({
            "code": 200,
            "msg": "Task submitted successfully",
            "data": {
                "task_id": task_id,
                "status": "pending"
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
    查询任务状态 (轮询接口)
    GET /api/tasks/{task_id}
    """
    try:
        user_id = get_jwt_identity()

        # 临时模拟任务状态 (实际应该从数据库查询)
        import random
        import datetime

        # 模拟不同的状态 (用于测试)
        statuses = ["pending", "processing", "success", "failed"]
        status = random.choice(statuses)

        # 根据状态生成相应的数据
        if status == "success":
            result_url = "https://cdn.example.com/videos/generated-video.mp4"
            progress = 100
            fail_reason = None
        elif status == "failed":
            result_url = None
            progress = 0
            fail_reason = "Content violation: NSFW content detected"
        elif status == "processing":
            result_url = None
            progress = random.randint(10, 90)
            fail_reason = None
        else:  # pending
            result_url = None
            progress = 0
            fail_reason = None

        return jsonify({
            "code": 200,
            "msg": "Success",
            "data": {
                "id": task_id,
                "status": status,
                "progress": progress,
                "result_url": result_url,
                "fail_reason": fail_reason,
                "created_at": datetime.datetime.now().isoformat()
            }
        }), 200

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

        # TODO: 从数据库分页查询任务
        # from app.models import Task
        # pagination = Task.query.filter_by(user_id=user_id)\
        #     .order_by(Task.created_at.desc())\
        #     .paginate(page=page, per_page=size, error_out=False)

        return jsonify({
            "code": 200,
            "msg": "Success",
            "data": {
                "list": [],  # TODO: 返回任务列表
                "total": 0,
                "page": page,
                "size": size
            }
        }), 200

    except Exception as e:
        return jsonify({"code": 500, "msg": "Internal error", "data": None}), 500
