"""
AI媒体资产管理 API 路由
提供媒体资产的增删改查接口
"""
from flask import Blueprint, request, jsonify
from app.utils.decorators import admin_required, login_required
from app.services.admin import (
    get_asset_list,
    get_asset_by_id,
    create_asset,
    update_asset,
    delete_asset,
    batch_delete_assets
)

bp = Blueprint('admin_ai_media_assets', __name__)


@bp.route('/ai-media-assets', methods=['GET'])
def list_assets():
    """
    获取媒体资产列表(公开访问)
    GET /api/admin/ai-media-assets?page=1&page_size=20&media_type=image&keyword=cat

    Query Parameters:
        page (int): 页码,默认1
        page_size (int): 每页数量,默认20
        media_type (str): 媒体类型筛选(image/video),可选
        keyword (str): 关键词搜索,可选

    Returns:
        JSON: {
            "code": 0,
            "message": "Success",
            "data": {
                "items": [...],
                "total": 100,
                "page": 1,
                "page_size": 20,
                "total_pages": 5
            }
        }
    """
    try:
        # 获取查询参数
        page = request.args.get('page', 1, type=int)
        page_size = request.args.get('page_size', 20, type=int)
        media_type = request.args.get('media_type', None, type=str)
        keyword = request.args.get('keyword', None, type=str)

        # 参数验证
        if page < 1:
            page = 1
        if page_size < 1 or page_size > 100:
            page_size = 20

        # 调用服务层
        result = get_asset_list(
            page=page,
            page_size=page_size,
            media_type=media_type,
            keyword=keyword
        )

        return jsonify({
            "code": 0,
            "message": "Success",
            "data": result
        }), 200

    except Exception as e:
        return jsonify({
            "code": 500,
            "message": f"Internal error: {str(e)}",
            "data": None
        }), 500


@bp.route('/ai-media-assets/<int:asset_id>', methods=['GET'])
@login_required
@admin_required
def get_asset_endpoint(asset_id):
    """
    获取单个媒体资产详情
    GET /api/admin/ai-media-assets/{id}

    Returns:
        JSON: {
            "code": 0,
            "message": "Success",
            "data": {...}
        }
    """
    try:
        # 调用服务层
        asset = get_asset_by_id(asset_id)

        return jsonify({
            "code": 0,
            "message": "Success",
            "data": asset
        }), 200

    except ValueError as e:
        return jsonify({
            "code": 404,
            "message": str(e),
            "data": None
        }), 404

    except Exception as e:
        return jsonify({
            "code": 500,
            "message": f"Internal error: {str(e)}",
            "data": None
        }), 500


@bp.route('/ai-media-assets', methods=['POST'])
@login_required
@admin_required
def create_asset_endpoint():
    """
    创建媒体资产
    POST /api/admin/ai-media-assets

    Request Body:
        {
            "title": "标题",
            "media_type": "image",
            "prompt_en": "English prompt",
            "prompt_zh": "中文提示词",
            "width": 1024,
            "height": 768,
            "r2_key": "images/202601/uuid.jpg",
            "r2_url": "https://...",
            "cover_r2_key": null,
            "cover_r2_url": null
        }

    Returns:
        JSON: {
            "code": 0,
            "message": "Asset created successfully",
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
        title = data.get('title')
        if not title:
            return jsonify({
                "code": 400,
                "message": "title is required",
                "data": None
            }), 400

        # 可选参数
        media_type = data.get('media_type', 'image')
        prompt_en = data.get('prompt_en')
        prompt_zh = data.get('prompt_zh')
        width = data.get('width', 0)
        height = data.get('height', 0)
        r2_key = data.get('r2_key')
        r2_url = data.get('r2_url')
        cover_r2_key = data.get('cover_r2_key')
        cover_r2_url = data.get('cover_r2_url')

        # 调用服务层
        result = create_asset(
            title=title,
            media_type=media_type,
            prompt_en=prompt_en,
            prompt_zh=prompt_zh,
            width=width,
            height=height,
            r2_key=r2_key,
            r2_url=r2_url,
            cover_r2_key=cover_r2_key,
            cover_r2_url=cover_r2_url
        )

        return jsonify({
            "code": 0,
            "message": "Asset created successfully",
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


@bp.route('/ai-media-assets/<int:asset_id>', methods=['PATCH'])
@login_required
@admin_required
def update_asset_endpoint(asset_id):
    """
    更新媒体资产
    PATCH /api/admin/ai-media-assets/{id}

    Request Body (所有字段可选):
        {
            "title": "新标题",
            "media_type": "video",
            "prompt_en": "Updated prompt",
            "width": 1920,
            "height": 1080
        }

    Returns:
        JSON: {
            "code": 0,
            "message": "Asset updated successfully",
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
        update_asset(asset_id, **data)

        return jsonify({
            "code": 0,
            "message": "Asset updated successfully",
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


@bp.route('/ai-media-assets/<int:asset_id>', methods=['DELETE'])
@login_required
@admin_required
def delete_asset_endpoint(asset_id):
    """
    删除媒体资产
    DELETE /api/admin/ai-media-assets/{id}

    Returns:
        JSON: {
            "code": 0,
            "message": "Asset deleted successfully",
            "data": null
        }
    """
    try:
        # 调用服务层
        delete_asset(asset_id)

        return jsonify({
            "code": 0,
            "message": "Asset deleted successfully",
            "data": None
        }), 200

    except ValueError as e:
        return jsonify({
            "code": 404,
            "message": str(e),
            "data": None
        }), 404

    except Exception as e:
        return jsonify({
            "code": 500,
            "message": f"Internal error: {str(e)}",
            "data": None
        }), 500


@bp.route('/ai-media-assets/batch-delete', methods=['POST'])
@login_required
@admin_required
def batch_delete_assets_endpoint():
    """
    批量删除媒体资产
    POST /api/admin/ai-media-assets/batch-delete

    Request Body:
        {
            "ids": [1, 2, 3, 4, 5]
        }

    Returns:
        JSON: {
            "code": 0,
            "message": "Batch delete completed",
            "data": {
                "success_count": 5,
                "failed_count": 0,
                "deleted_files": {
                    "total": 10,
                    "deleted": 10,
                    "failed": 0
                }
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
        ids = data.get('ids')
        if not ids:
            return jsonify({
                "code": 400,
                "message": "ids is required",
                "data": None
            }), 400

        # 调用服务层
        result = batch_delete_assets(ids)

        return jsonify({
            "code": 0,
            "message": "Batch delete completed",
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
