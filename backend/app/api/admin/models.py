"""
模型管理 API 路由
提供模型的增删改查功能
"""
from flask import Blueprint, request, jsonify
from flask_jwt_extended import get_jwt_identity
from app.utils.decorators import admin_required, login_required
from app.services.admin import (
    get_model_list,
    create_model,
    update_model,
    delete_model
)

bp = Blueprint('admin_models', __name__)


@bp.route('/models', methods=['GET'])
@login_required
@admin_required
def list_models():
    """
    获取模型列表
    GET /api/admin/models?tags=video,generation

    Query Parameters:
        tags (str): 标签筛选（逗号分隔，可选）

    Returns:
        JSON: {
            "code": 0,
            "message": "success",
            "data": [...]
        }
    """
    try:
        # 获取查询参数
        tags_filter = request.args.get('tags', None, type=str)

        # 调用服务层
        models = get_model_list(tags_filter=tags_filter)

        return jsonify({
            "code": 0,
            "message": "success",
            "data": models
        }), 200

    except Exception as e:
        return jsonify({
            "code": 500,
            "message": f"Internal error: {str(e)}",
            "data": None
        }), 500


@bp.route('/models', methods=['POST'])
@login_required
@admin_required
def create_model_endpoint():
    """
    创建模型
    POST /api/admin/models

    Request Body:
        {
            "key": "claude-3-sonnet",
            "name": "Claude 3 Sonnet",
            "enabled": true,
            "description": "Anthropic Claude 3 Sonnet 模型",
            "color": "bg-orange-400",
            "icon_url": "https://example.com/icon.png",
            "max_concurrency_limit": 20,
            "tags": ["text", "chat", "multimodal"]
        }

    Returns:
        JSON: {
            "code": 0,
            "message": "Model created successfully",
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
        key = data.get('key')
        name = data.get('name')

        if not key or not name:
            return jsonify({
                "code": 400,
                "message": "key and name are required",
                "data": None
            }), 400

        # 可选参数
        enabled = data.get('enabled', True)
        description = data.get('description')
        color = data.get('color')
        icon_url = data.get('icon_url')
        max_concurrency_limit = data.get('max_concurrency_limit', 20)
        tags = data.get('tags')

        # 调用服务层
        result = create_model(
            key=key,
            name=name,
            enabled=enabled,
            description=description,
            color=color,
            icon_url=icon_url,
            max_concurrency_limit=max_concurrency_limit,
            tags=tags
        )

        return jsonify({
            "code": 0,
            "message": "Model created successfully",
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


@bp.route('/models/<string:key>', methods=['PATCH'])
@login_required
@admin_required
def update_model_endpoint(key):
    """
    更新模型
    PATCH /api/admin/models/:key

    Request Body:
        {
            "name": "Claude 3.5 Sonnet",
            "enabled": false,
            "description": "Updated description",
            "color": "bg-indigo-500",
            "icon_url": "https://new-icon.png",
            "max_concurrency_limit": 30,
            "tags": ["text", "chat"]
        }

    Returns:
        JSON: {
            "code": 0,
            "message": "Model updated successfully",
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

        # 调用服务层
        result = update_model(
            key=key,
            name=data.get('name'),
            enabled=data.get('enabled'),
            description=data.get('description'),
            color=data.get('color'),
            icon_url=data.get('icon_url'),
            max_concurrency_limit=data.get('max_concurrency_limit'),
            tags=data.get('tags')
        )

        return jsonify({
            "code": 0,
            "message": "Model updated successfully",
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


@bp.route('/models/<string:key>', methods=['DELETE'])
@login_required
@admin_required
def delete_model_endpoint(key):
    """
    删除模型
    DELETE /api/admin/models/:key

    Returns:
        JSON: {
            "code": 0,
            "message": "Model deleted successfully",
            "data": null
        }
    """
    try:
        # 调用服务层
        delete_model(key)

        return jsonify({
            "code": 0,
            "message": "Model deleted successfully",
            "data": None
        }), 200

    except ValueError as e:
        # 检查是否是有关联数据的错误
        error_msg = str(e)
        if "Cannot delete model with existing keys or tasks" in error_msg:
            # 从错误中提取详细信息
            try:
                import json
                # 尝试从异常参数中获取统计信息
                return jsonify({
                    "code": 400,
                    "message": error_msg,
                    "data": e.args[1] if len(e.args) > 1 else None
                }), 400
            except:
                pass

        return jsonify({
            "code": 400,
            "message": error_msg,
            "data": None
        }), 400

    except Exception as e:
        return jsonify({
            "code": 500,
            "message": f"Internal error: {str(e)}",
            "data": None
        }), 500
