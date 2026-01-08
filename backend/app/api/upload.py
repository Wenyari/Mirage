"""
文件上传 API 路由
支持上传文件到 Cloudflare R2 对象存储
"""
from flask import Blueprint, request, jsonify
from flask_jwt_extended import get_jwt_identity
from app.utils.auth import jwt_and_redis_required
from app.services.storage_service import storage_service
import logging

bp = Blueprint('upload', __name__, url_prefix='/api/upload')
logger = logging.getLogger(__name__)

# 允许的文件类型
ALLOWED_EXTENSIONS = {
    'image': {'png', 'jpg', 'jpeg', 'gif', 'webp', 'bmp'},
    'video': {'mp4', 'avi', 'mov', 'mkv', 'webm', 'flv'},
    'audio': {'mp3', 'wav', 'ogg', 'aac', 'm4a'}
}

# MIME 类型映射
MIME_TYPES = {
    'png': 'image/png',
    'jpg': 'image/jpeg',
    'jpeg': 'image/jpeg',
    'gif': 'image/gif',
    'webp': 'image/webp',
    'bmp': 'image/bmp',
    'mp4': 'video/mp4',
    'avi': 'video/x-msvideo',
    'mov': 'video/quicktime',
    'mkv': 'video/x-matroska',
    'webm': 'video/webm',
    'mp3': 'audio/mpeg',
    'wav': 'audio/wav',
    'ogg': 'audio/ogg',
}


def allowed_file(filename: str, file_type: str = None) -> bool:
    """
    检查文件扩展名是否允许

    Args:
        filename: 文件名
        file_type: 文件类型（'image', 'video', 'audio'），如果为 None 则检查所有类型

    Returns:
        bool: 是否允许
    """
    if '.' not in filename:
        return False

    ext = filename.rsplit('.', 1)[1].lower()

    if file_type:
        return ext in ALLOWED_EXTENSIONS.get(file_type, set())
    else:
        # 检查所有类型
        for allowed_set in ALLOWED_EXTENSIONS.values():
            if ext in allowed_set:
                return True
        return False


def get_content_type(filename: str) -> str:
    """获取文件的 MIME 类型"""
    if '.' not in filename:
        return 'application/octet-stream'

    ext = filename.rsplit('.', 1)[1].lower()
    return MIME_TYPES.get(ext, 'application/octet-stream')


@bp.route('/file', methods=['POST'])
@jwt_and_redis_required()
def upload_file():
    """
    上传单个文件
    POST /api/upload/file

    Form Data:
        file: 文件
        type: 文件类型（可选，'image', 'video', 'audio'）

    Returns:
        {
            "code": 200,
            "msg": "Success",
            "data": {
                "url": "文件的公共 URL",
                "key": "对象键"
            }
        }
    """
    try:
        user_id = int(get_jwt_identity())

        # 检查是否有文件
        if 'file' not in request.files:
            return jsonify({"code": 400, "msg": "No file provided", "data": None}), 400

        file = request.files['file']

        if file.filename == '':
            return jsonify({"code": 400, "msg": "No file selected", "data": None}), 400

        # 获取文件类型参数
        file_type = request.form.get('type')

        # 验证文件类型
        if not allowed_file(file.filename, file_type):
            allowed = ALLOWED_EXTENSIONS.get(file_type) if file_type else 'all supported types'
            return jsonify({
                "code": 400,
                "msg": f"File type not allowed. Allowed types: {allowed}",
                "data": None
            }), 400

        # 读取文件数据
        file_data = file.read()

        # 获取 MIME 类型
        content_type = get_content_type(file.filename)

        # 上传到 R2
        result = storage_service.upload_file(
            file_data=file_data,
            filename=file.filename,
            content_type=content_type,
            prefix=f'uploads/user_{user_id}/'
        )

        if result['success']:
            logger.info(f"User {user_id} uploaded file: {result['key']}")
            return jsonify({
                "code": 200,
                "msg": "File uploaded successfully",
                "data": {
                    "url": result['url'],
                    "key": result['key']
                }
            }), 200
        else:
            return jsonify({
                "code": 500,
                "msg": f"Upload failed: {result.get('error')}",
                "data": None
            }), 500

    except Exception as e:
        logger.error(f"Upload error: {str(e)}", exc_info=True)
        return jsonify({"code": 500, "msg": "Internal error", "data": None}), 500


@bp.route('/files', methods=['POST'])
@jwt_and_redis_required()
def upload_files():
    """
    批量上传文件
    POST /api/upload/files

    Form Data:
        files[]: 多个文件
        type: 文件类型（可选，'image', 'video', 'audio'）

    Returns:
        {
            "code": 200,
            "msg": "Success",
            "data": {
                "uploaded": [
                    {"url": "...", "key": "..."},
                    ...
                ],
                "failed": [
                    {"filename": "...", "error": "..."},
                    ...
                ]
            }
        }
    """
    try:
        user_id = int(get_jwt_identity())

        # 检查是否有文件
        if 'files[]' not in request.files:
            return jsonify({"code": 400, "msg": "No files provided", "data": None}), 400

        files = request.files.getlist('files[]')

        if not files:
            return jsonify({"code": 400, "msg": "No files selected", "data": None}), 400

        # 获取文件类型参数
        file_type = request.form.get('type')

        uploaded = []
        failed = []

        for file in files:
            if file.filename == '':
                continue

            # 验证文件类型
            if not allowed_file(file.filename, file_type):
                failed.append({
                    'filename': file.filename,
                    'error': 'File type not allowed'
                })
                continue

            try:
                # 读取文件数据
                file_data = file.read()

                # 获取 MIME 类型
                content_type = get_content_type(file.filename)

                # 上传到 R2
                result = storage_service.upload_file(
                    file_data=file_data,
                    filename=file.filename,
                    content_type=content_type,
                    prefix=f'uploads/user_{user_id}/'
                )

                if result['success']:
                    uploaded.append({
                        'url': result['url'],
                        'key': result['key'],
                        'filename': file.filename
                    })
                    logger.info(f"User {user_id} uploaded file: {result['key']}")
                else:
                    failed.append({
                        'filename': file.filename,
                        'error': result.get('error')
                    })

            except Exception as e:
                logger.error(f"Error uploading {file.filename}: {str(e)}")
                failed.append({
                    'filename': file.filename,
                    'error': str(e)
                })

        return jsonify({
            "code": 200,
            "msg": "Upload completed",
            "data": {
                "uploaded": uploaded,
                "failed": failed
            }
        }), 200

    except Exception as e:
        logger.error(f"Batch upload error: {str(e)}", exc_info=True)
        return jsonify({"code": 500, "msg": "Internal error", "data": None}), 500


@bp.route('/delete/<path:object_key>', methods=['DELETE'])
@jwt_and_redis_required()
def delete_file(object_key: str):
    """
    删除文件
    DELETE /api/upload/delete/{object_key}

    Args:
        object_key: 对象键

    Returns:
        {
            "code": 200,
            "msg": "File deleted successfully",
            "data": None
        }
    """
    try:
        user_id = int(get_jwt_identity())

        # 安全检查：确保用户只能删除自己上传的文件
        if not object_key.startswith(f'uploads/user_{user_id}/'):
            return jsonify({
                "code": 403,
                "msg": "Permission denied",
                "data": None
            }), 403

        result = storage_service.delete_file(object_key)

        if result['success']:
            logger.info(f"User {user_id} deleted file: {object_key}")
            return jsonify({
                "code": 200,
                "msg": "File deleted successfully",
                "data": None
            }), 200
        else:
            return jsonify({
                "code": 500,
                "msg": f"Delete failed: {result.get('error')}",
                "data": None
            }), 500

    except Exception as e:
        logger.error(f"Delete error: {str(e)}", exc_info=True)
        return jsonify({"code": 500, "msg": "Internal error", "data": None}), 500
