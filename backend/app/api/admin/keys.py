"""
密钥池管理 API 路由
提供密钥的增删改查、状态监控和统计功能
"""
from flask import Blueprint, request, jsonify
from flask_jwt_extended import get_jwt_identity
from app.utils.decorators import admin_required, login_required
from app.services.admin import (
    get_key_list,
    create_key,
    batch_create_keys,
    update_key,
    delete_key,
    trigger_cooldown,
    get_key_stats
)

bp = Blueprint('admin_keys', __name__)


@bp.route('/keys', methods=['GET'])
@login_required
@admin_required
def list_keys():
    """
    获取密钥列表
    GET /api/admin/keys?model=gpt-4

    Query Parameters:
        model (str): 模型筛选（可选）

    Returns:
        JSON: {
            "code": 0,
            "message": "Success",
            "data": [...]
        }
    """
    try:
        # 获取查询参数
        model_filter = request.args.get('model', None, type=str)

        # 调用服务层
        keys = get_key_list(model_filter=model_filter)

        return jsonify({
            "code": 0,
            "message": "Success",
            "data": keys
        }), 200

    except Exception as e:
        return jsonify({
            "code": 500,
            "message": f"Internal error: {str(e)}",
            "data": None
        }), 500


@bp.route('/keys', methods=['POST'])
@login_required
@admin_required
def create_key_endpoint():
    """
    添加密钥
    POST /api/admin/keys

    Request Body:
        {
            "model": "gpt-4",
            "api_base": "https://api.openai.com/v1",
            "key_secret": "sk-proj-abc123...",
            "max_concurrency": 3,
            "weight": 10
        }

    Returns:
        JSON: {
            "code": 0,
            "message": "Key added successfully",
            "data": {...}
        }
    """
    try:
        # 获取请求数据
        data = request.get_json()
        if not data:
            return jsonify({
                "code": 400,
                "message": "Request body is required",
                "data": None
            }), 400

        # 必填参数
        model = data.get('model')
        key_secret = data.get('key_secret')

        if not model or not key_secret:
            return jsonify({
                "code": 400,
                "message": "model and key_secret are required",
                "data": None
            }), 400

        # 可选参数
        api_base = data.get('api_base', '')
        max_concurrency = data.get('max_concurrency', 3)
        weight = data.get('weight', 10)

        # 调用服务层
        result = create_key(
            model=model,
            api_base=api_base,
            key_secret=key_secret,
            max_concurrency=max_concurrency,
            weight=weight
        )

        return jsonify({
            "code": 0,
            "message": "Key added successfully",
            "data": result
        }), 200

    except ValueError as e:
        return jsonify({
            "code": 400,
            "message": str(e),
            "data": None
        }), 400

    except Exception as e:
        return jsonify({
            "code": 500,
            "message": f"Internal error: {str(e)}",
            "data": None
        }), 500


@bp.route('/keys/batch', methods=['POST'])
@login_required
@admin_required
def batch_create_keys_endpoint():
    """
    批量添加密钥
    POST /api/admin/keys/batch

    Request Body:
        {
            "model": "gpt-4",
            "api_base": "https://api.openai.com/v1",
            "keys": ["sk-proj-abc123...", "sk-proj-def456..."],
            "max_concurrency": 3,
            "weight": 10
        }

    Returns:
        JSON: {
            "code": 0,
            "message": "Batch import completed",
            "data": {
                "success_count": 2,
                "failed_count": 0,
                "failed_keys": []
            }
        }
    """
    try:
        # 获取请求数据
        data = request.get_json()
        if not data:
            return jsonify({
                "code": 400,
                "message": "Request body is required",
                "data": None
            }), 400

        # 必填参数
        model = data.get('model')
        keys = data.get('keys')

        if not model or not keys:
            return jsonify({
                "code": 400,
                "message": "model and keys are required",
                "data": None
            }), 400

        if not isinstance(keys, list) or not keys:
            return jsonify({
                "code": 400,
                "message": "keys must be a non-empty array",
                "data": None
            }), 400

        # 可选参数
        api_base = data.get('api_base', '')
        max_concurrency = data.get('max_concurrency', 3)
        weight = data.get('weight', 10)

        # 调用服务层
        result = batch_create_keys(
            model=model,
            api_base=api_base,
            keys=keys,
            max_concurrency=max_concurrency,
            weight=weight
        )

        return jsonify({
            "code": 0,
            "message": "Batch import completed",
            "data": result
        }), 200

    except ValueError as e:
        return jsonify({
            "code": 400,
            "message": str(e),
            "data": None
        }), 400

    except Exception as e:
        return jsonify({
            "code": 500,
            "message": f"Internal error: {str(e)}",
            "data": None
        }), 500


@bp.route('/keys/<int:key_id>', methods=['PATCH'])
@login_required
@admin_required
def update_key_endpoint(key_id):
    """
    更新密钥配置
    PATCH /api/admin/keys/{id}

    Request Body:
        {
            "max_concurrency": 5,
            "weight": 20,
            "status": 1
        }

    Returns:
        JSON: {
            "code": 0,
            "message": "Key updated successfully",
            "data": null
        }
    """
    try:
        # 获取请求数据
        data = request.get_json()
        if not data:
            return jsonify({
                "code": 400,
                "message": "Request body is required",
                "data": None
            }), 400

        # 调用服务层
        update_key(
            key_id=key_id,
            max_concurrency=data.get('max_concurrency'),
            weight=data.get('weight'),
            status=data.get('status')
        )

        return jsonify({
            "code": 0,
            "message": "Key updated successfully",
            "data": None
        }), 200

    except ValueError as e:
        return jsonify({
            "code": 400,
            "message": str(e),
            "data": None
        }), 400

    except Exception as e:
        return jsonify({
            "code": 500,
            "message": f"Internal error: {str(e)}",
            "data": None
        }), 500


@bp.route('/keys/<int:key_id>', methods=['DELETE'])
@login_required
@admin_required
def delete_key_endpoint(key_id):
    """
    删除密钥
    DELETE /api/admin/keys/{id}

    Returns:
        JSON: {
            "code": 0,
            "message": "Key deleted successfully",
            "data": null
        }
    """
    try:
        # 调用服务层
        delete_key(key_id)

        return jsonify({
            "code": 0,
            "message": "Key deleted successfully",
            "data": None
        }), 200

    except ValueError as e:
        return jsonify({
            "code": 400,
            "message": str(e),
            "data": None
        }), 400

    except Exception as e:
        return jsonify({
            "code": 500,
            "message": f"Internal error: {str(e)}",
            "data": None
        }), 500


@bp.route('/keys/<int:key_id>/cooldown', methods=['POST'])
@login_required
@admin_required
def cooldown_endpoint(key_id):
    """
    手动触发熔断/解除熔断
    POST /api/admin/keys/{id}/cooldown

    Request Body:
        {
            "action": "trigger",
            "duration": 300
        }

    Returns:
        JSON: {
            "code": 0,
            "message": "Cooldown triggered successfully",
            "data": {
                "cooling_until": "2024-03-20T16:15:00Z"
            }
        }
    """
    try:
        # 获取请求数据
        data = request.get_json()
        if not data:
            return jsonify({
                "code": 400,
                "message": "Request body is required",
                "data": None
            }), 400

        # 必填参数
        action = data.get('action')
        if not action:
            return jsonify({
                "code": 400,
                "message": "action is required",
                "data": None
            }), 400

        # 可选参数
        duration = data.get('duration', 300)

        # 调用服务层
        result = trigger_cooldown(
            key_id=key_id,
            action=action,
            duration=duration
        )

        return jsonify({
            "code": 0,
            "message": result['message'],
            "data": {
                "cooling_until": result.get('cooling_until')
            }
        }), 200

    except ValueError as e:
        return jsonify({
            "code": 400,
            "message": str(e),
            "data": None
        }), 400

    except Exception as e:
        return jsonify({
            "code": 500,
            "message": f"Internal error: {str(e)}",
            "data": None
        }), 500


@bp.route('/keys/stats', methods=['GET'])
@login_required
@admin_required
def stats_endpoint():
    """
    获取密钥统计信息
    GET /api/admin/keys/stats

    Returns:
        JSON: {
            "code": 0,
            "message": "Success",
            "data": {
                "by_model": [...],
                "total_calls_today": 3420,
                "total_errors_today": 45,
                "error_rate": 1.32
            }
        }
    """
    try:
        # 调用服务层
        stats = get_key_stats()

        return jsonify({
            "code": 0,
            "message": "Success",
            "data": stats
        }), 200

    except Exception as e:
        return jsonify({
            "code": 500,
            "message": f"Internal error: {str(e)}",
            "data": None
        }), 500
