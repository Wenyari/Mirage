"""
AI媒体资产管理服务
提供媒体资产的增删改查功能
"""
import uuid
from datetime import datetime
from zoneinfo import ZoneInfo
from sqlalchemy import or_
from app.extensions import db
from app.models import AiMediaAsset
from app.services.storage_service import StorageService


# 创建AI媒体资产专用存储服务(使用assets bucket)
assets_storage = StorageService()
assets_storage.bucket_name = "assets"  # 覆盖默认bucket


def get_asset_list(page=1, page_size=20, media_type=None, keyword=None):
    """
    获取资产列表(分页)

    Args:
        page: 页码(从1开始)
        page_size: 每页数量
        media_type: 媒体类型筛选(可选)
        keyword: 关键词搜索(可选,搜索标题)

    Returns:
        dict: {
            'items': 资产列表,
            'total': 总数,
            'page': 当前页,
            'page_size': 每页数量,
            'total_pages': 总页数
        }
    """
    query = AiMediaAsset.query

    # 媒体类型筛选
    if media_type:
        query = query.filter(AiMediaAsset.media_type == media_type)

    # 关键词搜索(标题)
    if keyword:
        query = query.filter(AiMediaAsset.title.like(f'%{keyword}%'))

    # 按创建时间倒序
    query = query.order_by(AiMediaAsset.created_at.desc())

    # 分页
    pagination = query.paginate(
        page=page,
        per_page=page_size,
        error_out=False
    )

    return {
        'items': [asset.to_dict() for asset in pagination.items],
        'total': pagination.total,
        'page': page,
        'page_size': page_size,
        'total_pages': pagination.pages
    }


def get_asset_by_id(asset_id):
    """
    获取单个资产详情

    Args:
        asset_id: 资产ID

    Returns:
        dict: 资产数据

    Raises:
        ValueError: 资产不存在
    """
    asset = AiMediaAsset.query.get(asset_id)
    if not asset:
        raise ValueError(f"Asset {asset_id} not found")

    return asset.to_dict()


def create_asset(title, media_type='image', prompt_en=None, prompt_zh=None,
                 width=0, height=0, r2_key=None, r2_url=None,
                 cover_r2_key=None, cover_r2_url=None):
    """
    创建新资产

    Args:
        title: 标题
        media_type: 媒体类型(image/video)
        prompt_en: 英文提示词
        prompt_zh: 中文提示词
        width: 宽度
        height: 高度
        r2_key: R2存储路径
        r2_url: R2访问链接
        cover_r2_key: 封面路径
        cover_r2_url: 封面链接

    Returns:
        dict: 创建的资产数据

    Raises:
        ValueError: 参数无效
    """
    # 参数验证
    if media_type not in ['image', 'video']:
        raise ValueError("media_type must be 'image' or 'video'")

    # 自动生成source_id
    source_id = uuid.uuid4().hex

    # 创建资产
    asset = AiMediaAsset(
        source_id=source_id,
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

    db.session.add(asset)
    db.session.commit()

    return asset.to_dict()


def update_asset(asset_id, **kwargs):
    """
    更新资产

    Args:
        asset_id: 资产ID
        **kwargs: 需要更新的字段

    Returns:
        dict: 操作结果

    Raises:
        ValueError: 资产不存在或参数无效
    """
    asset = AiMediaAsset.query.get(asset_id)
    if not asset:
        raise ValueError(f"Asset {asset_id} not found")

    # 允许更新的字段
    allowed_fields = [
        'title', 'media_type', 'prompt_en', 'prompt_zh',
        'width', 'height', 'r2_key', 'r2_url',
        'cover_r2_key', 'cover_r2_url'
    ]

    # 更新字段
    for field, value in kwargs.items():
        if field in allowed_fields:
            setattr(asset, field, value)

    # 验证media_type
    if 'media_type' in kwargs and kwargs['media_type'] not in ['image', 'video']:
        raise ValueError("media_type must be 'image' or 'video'")

    asset.updated_at = datetime.now(ZoneInfo("Asia/Shanghai"))
    db.session.commit()

    return {'message': 'Asset updated successfully'}


def delete_asset(asset_id):
    """
    删除单个资产

    Args:
        asset_id: 资产ID

    Returns:
        dict: 操作结果

    Raises:
        ValueError: 资产不存在
    """
    asset = AiMediaAsset.query.get(asset_id)
    if not asset:
        raise ValueError(f"Asset {asset_id} not found")

    # 删除R2文件
    files_to_delete = []
    if asset.r2_key:
        files_to_delete.append(asset.r2_key)
    if asset.cover_r2_key:
        files_to_delete.append(asset.cover_r2_key)

    if files_to_delete:
        try:
            delete_result = assets_storage.delete_multiple_files(files_to_delete)
            # 记录日志但不阻止删除操作
            if not delete_result.get('success'):
                print(f"Warning: Failed to delete some files from R2: {delete_result.get('errors')}")
        except Exception as e:
            print(f"Warning: R2 deletion failed: {str(e)}")

    # 删除数据库记录
    db.session.delete(asset)
    db.session.commit()

    return {'message': 'Asset deleted successfully'}


def batch_delete_assets(asset_ids):
    """
    批量删除资产

    Args:
        asset_ids: 资产ID列表

    Returns:
        dict: {
            'success_count': 成功数量,
            'failed_count': 失败数量,
            'deleted_files': R2文件删除统计
        }

    Raises:
        ValueError: 参数无效
    """
    if not isinstance(asset_ids, list) or not asset_ids:
        raise ValueError("asset_ids must be a non-empty list")

    success_count = 0
    failed_count = 0
    all_r2_keys = []

    # 查询所有资产
    assets = AiMediaAsset.query.filter(AiMediaAsset.id.in_(asset_ids)).all()

    # 收集所有R2文件路径
    for asset in assets:
        if asset.r2_key:
            all_r2_keys.append(asset.r2_key)
        if asset.cover_r2_key:
            all_r2_keys.append(asset.cover_r2_key)

    # 批量删除R2文件
    r2_delete_result = {'success': True, 'deleted': 0, 'failed': 0}
    if all_r2_keys:
        try:
            r2_delete_result = assets_storage.delete_multiple_files(all_r2_keys)
        except Exception as e:
            print(f"Warning: R2 batch deletion failed: {str(e)}")

    # 删除数据库记录
    for asset in assets:
        try:
            db.session.delete(asset)
            success_count += 1
        except Exception as e:
            failed_count += 1
            print(f"Failed to delete asset {asset.id}: {str(e)}")

    db.session.commit()

    return {
        'success_count': success_count,
        'failed_count': failed_count,
        'deleted_files': {
            'total': len(all_r2_keys),
            'deleted': r2_delete_result.get('deleted', 0),
            'failed': r2_delete_result.get('failed', 0)
        }
    }
