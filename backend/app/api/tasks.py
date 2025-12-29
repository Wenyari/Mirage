"""
任务相关 API 路由
包含任务提交、查询状态、历史记录等接口
"""
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity

bp = Blueprint('tasks', __name__, url_prefix='/api/tasks')


@bp.route('', methods=['POST'])
@jwt_required()
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

        if not model:
            return jsonify({"code": 400, "msg": "Model is required", "data": None}), 400

        # TODO: 调用 task_service.submit_task(user_id, task_data)
        # from app.services.task_service import submit_task
        # task_id = submit_task(user_id, {
        #     'model': model,
        #     'prompt': prompt,
        #     'params': params,
        #     'input_file_url': input_file_url
        # })

        return jsonify({
            "code": 200,
            "msg": "Task submitted successfully",
            "data": {
                "task_id": "uuid-here",  # TODO: 返回实际 task_id
                "status": "pending"
            }
        }), 200

    except ValueError as e:
        # 业务错误 (如并发超限、余额不足)
        return jsonify({"code": 400, "msg": str(e), "data": None}), 400
    except Exception as e:
        return jsonify({"code": 500, "msg": "Internal error", "data": None}), 500


@bp.route('/<task_id>', methods=['GET'])
@jwt_required()
def get_task_status(task_id):
    """
    查询任务状态 (轮询接口)
    GET /api/tasks/{task_id}
    """
    try:
        user_id = get_jwt_identity()

        # TODO: 从数据库查询任务
        # from app.models import Task
        # task = Task.query.filter_by(id=task_id, user_id=user_id).first()
        # if not task:
        #     return jsonify({"code": 404, "msg": "Task not found", "data": None}), 404

        return jsonify({
            "code": 200,
            "msg": "Success",
            "data": {
                "id": task_id,
                "status": "processing",  # pending/processing/success/failed
                "progress": 50,  # 进度百分比 (可选)
                "result_url": None,  # 成功后返回结果链接
                "fail_reason": None,
                "created_at": "2024-01-01T00:00:00"
            }
        }), 200

    except Exception as e:
        return jsonify({"code": 500, "msg": "Internal error", "data": None}), 500


@bp.route('', methods=['GET'])
@jwt_required()
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
