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
        user_id = int(get_jwt_identity())  # 修复：JWT返回字符串，转为整数
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
    查询任务状态（智能接口，自动附带排队或进度信息）
    GET /api/tasks/{task_id}

    返回数据根据任务状态不同：

    1. 状态 = pending (排队中)
    {
        "id": "task-uuid",
        "status": "pending",
        "progress": 0,
        "queue_info": {                    # 自动附带队列信息
            "user_queue": "vip",           # 用户所在队列
            "position": 10,                # 队列中的位置
            "vip_queue": 10,               # VIP 队列总数
            "normal_queue": 25             # 普通队列总数
        },
        ...
    }

    2. 状态 = processing (执行中)
    {
        "id": "task-uuid",
        "status": "processing",
        "progress": 45,                    # 实时进度 0-100
        ...
    }

    3. 状态 = success/failed/cancelled (已完成)
    {
        "id": "task-uuid",
        "status": "success",
        "progress": 100,
        "result_url": "https://...",       # 成功时有结果链接
        "fail_reason": "...",              # 失败时有错误原因
        ...
    }

    前端轮询策略：
    - pending: 2-3秒轮询，显示排队状态
    - processing: 3-5秒轮询，显示执行进度
    - success/failed/cancelled: 停止轮询
    """
    try:
        user_id = int(get_jwt_identity())  # 修复：JWT返回字符串，转为整数

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
        user_id = int(get_jwt_identity())  # 修复：JWT返回字符串，转为整数

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
        user_id = int(get_jwt_identity())  # 修复：JWT返回字符串，转为整数
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


@bp.route('/queue/status', methods=['GET'])
@jwt_and_redis_required()
def get_queue_status():
    """
    获取队列排队状态
    GET /api/tasks/queue/status

    返回示例:
    {
        "code": 200,
        "msg": "Success",
        "data": {
            "vip_queue": 10,         # VIP 队列排队任务数
            "normal_queue": 25,      # 普通队列排队任务数
            "user_queue": "vip",     # 当前用户所在队列 ("vip" 或 "normal")
            "user_position": 10      # 当前用户所在队列的排队人数
        }
    }
    """
    try:
        user_id = int(get_jwt_identity())  # 修复：JWT返回字符串，转为整数

        # 调用服务层获取队列状态
        queue_data = TaskService.get_queue_status(user_id)

        return jsonify({
            "code": 200,
            "msg": "Success",
            "data": queue_data
        }), 200

    except ValueError as e:
        return jsonify({"code": 404, "msg": str(e), "data": None}), 404
    except Exception as e:
        return jsonify({"code": 500, "msg": "Internal error", "data": None}), 500


@bp.route('/models', methods=['GET'])
@jwt_and_redis_required()
def get_available_models():
    """
    获取所有模型列表，并标注当前用户是否可用（用于激发付费欲望）
    GET /api/tasks/models

    返回示例（T1 用户）:
    {
        "code": 200,
        "msg": "Success",
        "data": [
            // 可用的模型（排在前面）
            {
                "key": "dall-e-3",
                "name": "DALL-E 3",
                "description": "图像生成模型",
                "cost_per_call": 50.00,
                "is_available": true,         // ✅ 当前用户可用
                "user_tier": "T1",            // 当前用户等级
                "min_tier": "T1",             // 最低要求等级
                "allowed_tiers": ["T1", "T2", "T3", "T4", "T5"],
                "color": "bg-green-500",
                "icon_url": "https://...",
                "enabled": 1,
                "max_concurrency_limit": 20,
                "created_at": "2026-01-04T10:00:00",
                "updated_at": "2026-01-04T10:00:00"
            },
            // 不可用的模型（排在后面，带锁图标提示）
            {
                "key": "sora-2",
                "name": "Sora-2",
                "description": "OpenAI Sora 视频生成模型",
                "cost_per_call": 100.00,
                "is_available": false,        // ❌ 当前用户不可用
                "user_tier": "T1",            // 当前用户等级
                "min_tier": "T3",             // 需要 T3 及以上
                "allowed_tiers": ["T3", "T4", "T5"],
                "color": "bg-blue-500",
                "icon_url": "https://...",
                "enabled": 1,
                "max_concurrency_limit": 10,
                "created_at": "2026-01-04T10:00:00",
                "updated_at": "2026-01-04T10:00:00"
            }
        ]
    }

    说明:
    - 返回所有启用的模型（enabled=1）和活跃配置（is_active=1）
    - is_available: 标注当前用户是否可用（true/false）
    - min_tier: 显示使用该模型的最低等级要求
    - user_tier: 显示用户当前等级
    - 排序规则: 可用的模型在前，不可用的在后；同等可用性按价格排序

    前端展示建议:
    - 可用模型: 正常显示，可点击使用
    - 不可用模型:
      * 添加锁图标 🔒
      * 灰色或半透明显示
      * 显示 "需要 T3 会员" 提示
      * 点击后弹出升级会员提示
    """
    try:
        user_id = int(get_jwt_identity())  # 修复：JWT返回字符串，转为整数

        # 调用服务层获取可用模型
        models = TaskService.get_available_models(user_id)

        return jsonify({
            "code": 200,
            "msg": "Success",
            "data": models
        }), 200

    except ValueError as e:
        return jsonify({"code": 404, "msg": str(e), "data": None}), 404
    except Exception as e:
        return jsonify({"code": 500, "msg": "Internal error", "data": None}), 500
