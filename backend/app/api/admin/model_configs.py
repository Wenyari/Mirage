"""
模型配置管理 API 路由
提供模型计费规则和权限配置的管理接口
"""
from flask import Blueprint, request, jsonify
from flask_jwt_extended import get_jwt_identity
from app.utils.decorators import admin_required, login_required
from app.services.admin import (
    get_model_config_list,
    get_available_models,
    create_model_config,
    update_model_config,
    delete_model_config
)

bp = Blueprint('admin_model_configs', __name__)


@bp.route('/model-configs', methods=['GET'])
@login_required
@admin_required
def list_model_configs():
    """
    获取模型配置列表
    GET /api/admin/model-configs

    Returns:
        JSON: {
            "code": 0,
            "message": "Success",
            "data": [...]
        }
    """
    try:
        configs = get_model_config_list()

        return jsonify({
            "code": 0,
            "message": "Success",
            "data": configs
        }), 200

    except Exception as e:
        return jsonify({
            "code": 500,
            "message": f"Internal error: {str(e)}",
            "data": None
        }), 500


@bp.route('/model-configs/available-models', methods=['GET'])
@login_required
@admin_required
def list_available_models():
    """
    获取可配置的模型列表
    GET /api/admin/model-configs/available-models

    Returns:
        JSON: {
            "code": 0,
            "message": "Success",
            "data": [...]
        }
    """
    try:
        models = get_available_models()

        return jsonify({
            "code": 0,
            "message": "Success",
            "data": models
        }), 200

    except Exception as e:
        return jsonify({
            "code": 500,
            "message": f"Internal error: {str(e)}",
            "data": None
        }), 500


@bp.route('/model-configs', methods=['POST'])
@login_required
@admin_required
def create_model_config_endpoint():
    """
    创建模型配置
    POST /api/admin/model-configs

    Request Body:
        {
            "model": "gemini-pro",
            "allowed_tiers": ["T1", "T2", "T3", "T4", "T5"],
            "cost_per_call": 20,
            "token_cost_config": {
                "enabled": true,
                "input_cost": 0.04,
                "output_cost": 0.08
            },
            "is_active": true,
            "description": "Google Gemini Pro 模型"
        }

    Returns:
        JSON: {
            "code": 0,
            "message": "Model config created successfully",
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
        allowed_tiers = data.get('allowed_tiers')
        cost_per_call = data.get('cost_per_call')
        token_cost_config = data.get('token_cost_config')

        if not model or not allowed_tiers or cost_per_call is None or not token_cost_config:
            return jsonify({
                "code": 400,
                "message": "model, allowed_tiers, cost_per_call, and token_cost_config are required",
                "data": None
            }), 400

        # 可选参数
        is_active = data.get('is_active', True)
        description = data.get('description')

        # 调用服务层
        result = create_model_config(
            model=model,
            allowed_tiers=allowed_tiers,
            cost_per_call=cost_per_call,
            token_cost_config=token_cost_config,
            is_active=is_active,
            description=description
        )

        return jsonify({
            "code": 0,
            "message": "Model config created successfully",
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


@bp.route('/model-configs/<int:config_id>', methods=['PATCH'])
@login_required
@admin_required
def update_model_config_endpoint(config_id):
    """
    更新模型配置
    PATCH /api/admin/model-configs/{id}

    Request Body (所有字段可选):
        {
            "allowed_tiers": ["T2", "T3", "T4", "T5"],
            "cost_per_call": 15,
            "token_cost_config": {
                "enabled": true,
                "input_cost": 0.035,
                "output_cost": 0.07
            },
            "is_active": true,
            "description": "更新后的描述"
        }

    Returns:
        JSON: {
            "code": 0,
            "message": "Model config updated successfully",
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
        update_model_config(
            config_id=config_id,
            allowed_tiers=data.get('allowed_tiers'),
            cost_per_call=data.get('cost_per_call'),
            token_cost_config=data.get('token_cost_config'),
            is_active=data.get('is_active'),
            description=data.get('description')
        )

        return jsonify({
            "code": 0,
            "message": "Model config updated successfully",
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


@bp.route('/model-configs/<int:config_id>', methods=['DELETE'])
@login_required
@admin_required
def delete_model_config_endpoint(config_id):
    """
    删除模型配置
    DELETE /api/admin/model-configs/{id}

    Returns:
        JSON: {
            "code": 0,
            "message": "Model config deleted successfully",
            "data": null
        }
    """
    try:
        # 调用服务层
        delete_model_config(config_id)

        return jsonify({
            "code": 0,
            "message": "Model config deleted successfully",
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
