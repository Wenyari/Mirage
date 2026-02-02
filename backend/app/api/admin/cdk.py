"""
CDK管理 API 路由
提供CDK的生成、查询、作废等功能
"""
from flask import Blueprint, request, jsonify
from flask_jwt_extended import get_jwt_identity
from app.utils.decorators import admin_required, login_required
from app.services.admin import (
    generate_cdk_batch,
    get_cdk_list,
    void_cdk_batch
)

bp = Blueprint('admin_cdk', __name__)


@bp.route('/cdk/generate', methods=['POST'])
@login_required
@admin_required
def generate_cdks():
    """
    批量生成CDK
    POST /api/admin/cdk/generate

    Request Body:
        {
            "amount": 500,              // 单个CDK面额（元）
            "count": 20,                // 生成数量
            "type": "once",             // 类型：once（单次使用）、multi（可重复使用）
            "batch_name": "春节活动"    // 批次名称（可选）
        }

    Returns:
        JSON: {
            "code": 0,
            "message": "CDK generated successfully",
            "data": {
                "batch_no": "BATCH20240320001",
                "cdks": [...]
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
        amount = data.get('amount')
        count = data.get('count')

        if amount is None or count is None:
            return jsonify({
                "code": 400,
                "message": "amount and count are required",
                "data": None
            }), 400

        # 可选参数
        cdk_type = data.get('type', 'once')
        batch_name = data.get('batch_name')
        grant_level = data.get('grant_level')
        expire_at = data.get('expire_at')

        # 参数验证
        try:
            amount = int(amount)
            count = int(count)
        except (ValueError, TypeError):
            return jsonify({
                "code": 400,
                "message": "amount and count must be integers",
                "data": None
            }), 400

        if amount <= 0:
            return jsonify({
                "code": 400,
                "message": "amount must be positive",
                "data": None
            }), 400

        if count <= 0 or count > 1000:
            return jsonify({
                "code": 400,
                "message": "count must be between 1 and 1000",
                "data": None
            }), 400

        if cdk_type not in ['once', 'multi']:
            return jsonify({
                "code": 400,
                "message": "type must be 'once' or 'multi'",
                "data": None
            }), 400

        # 调用服务层生成CDK，传递 grant_level 和 expire_at 如果存在
        result = generate_cdk_batch(
            amount=amount,
            count=count,
            type=cdk_type,
            batch_name=batch_name,
            grant_level=grant_level,
            expire_at=expire_at
        )

        return jsonify({
            "code": 0,
            "message": "CDK generated successfully",
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


@bp.route('/cdk', methods=['GET'])
@login_required
@admin_required
def list_cdks():
    """
    获取CDK列表（带分页和筛选）
    GET /api/admin/cdk?page=1&limit=10&batch_no=BATCH20240320001&status=unused&search=CDK-ABC

    Query Parameters:
        page (int): 页码，默认1
        limit (int): 每页数量，默认10
        batch_no (str): 批次号筛选
        status (str): 状态筛选（unused/used/void）
        search (str): 模糊搜索（批次号或CDK码）

    Returns:
        JSON: {
            "code": 0,
            "message": "Success",
            "data": {
                "items": [...],
                "total": 50,
                "page": 1,
                "limit": 10
            }
        }
    """
    try:
        # 获取查询参数
        page = request.args.get('page', 1, type=int)
        limit = request.args.get('limit', 10, type=int)
        batch_no = request.args.get('batch_no', None, type=str)
        status = request.args.get('status', None, type=str)
        search = request.args.get('search', None, type=str)

        # 参数验证
        if limit < 1 or limit > 100:
            return jsonify({
                "code": 400,
                "message": "limit must be between 1 and 100",
                "data": None
            }), 400

        if status and status not in ['unused', 'used', 'void']:
            return jsonify({
                "code": 400,
                "message": "status must be 'unused', 'used', or 'void'",
                "data": None
            }), 400

        # 调用服务层
        result = get_cdk_list(
            page=page,
            limit=limit,
            batch_no=batch_no,
            status=status,
            search=search
        )

        return jsonify({
            "code": 0,
            "message": "Success",
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


@bp.route('/cdk/void', methods=['POST'])
@login_required
@admin_required
def void_cdks():
    """
    批量作废CDK
    POST /api/admin/cdk/void

    Request Body (方式一：按批次作废):
        {
            "batch_no": "BATCH20240320001"
        }

    Request Body (方式二：按ID作废):
        {
            "ids": [1, 2, 3, 4, 5]
        }

    Returns:
        JSON: {
            "code": 0,
            "message": "CDKs voided successfully",
            "data": {
                "voided_count": 15
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

        batch_no = data.get('batch_no')
        ids = data.get('ids')

        # 必须提供batch_no或ids之一
        if not batch_no and not ids:
            return jsonify({
                "code": 400,
                "message": "Either batch_no or ids must be provided",
                "data": None
            }), 400

        # 不能同时提供batch_no和ids
        if batch_no and ids:
            return jsonify({
                "code": 400,
                "message": "Cannot specify both batch_no and ids",
                "data": None
            }), 400

        # 验证ids格式
        if ids is not None:
            if not isinstance(ids, list) or not ids:
                return jsonify({
                    "code": 400,
                    "message": "ids must be a non-empty array",
                    "data": None
                }), 400

            if not all(isinstance(id, int) for id in ids):
                return jsonify({
                    "code": 400,
                    "message": "All ids must be integers",
                    "data": None
                }), 400

        # 调用服务层
        result = void_cdk_batch(batch_no=batch_no, ids=ids)

        return jsonify({
            "code": 0,
            "message": "CDKs voided successfully",
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
