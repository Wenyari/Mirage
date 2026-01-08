"""
Cloudflare R2 对象存储服务
提供文件上传、下载、删除等功能
兼容 S3 API
"""
import os
import logging
import boto3
from botocore.client import Config
from botocore.exceptions import ClientError
from datetime import datetime, timedelta
from werkzeug.utils import secure_filename
import uuid

logger = logging.getLogger(__name__)


class StorageService:
    """Cloudflare R2 存储服务"""

    def __init__(self):
        """初始化 R2 客户端"""
        self.account_id = os.getenv('R2_ACCOUNT_ID')
        self.access_key_id = os.getenv('R2_ACCESS_KEY_ID')
        self.secret_access_key = os.getenv('R2_SECRET_ACCESS_KEY')
        self.bucket_name = os.getenv('R2_BUCKET_NAME')
        self.public_url = os.getenv('R2_PUBLIC_URL')  # R2 自定义域名或公共 URL

        if not all([self.account_id, self.access_key_id, self.secret_access_key, self.bucket_name]):
            logger.warning("R2 storage credentials not fully configured")
            self.client = None
            return

        # 创建 S3 兼容客户端
        self.client = boto3.client(
            's3',
            endpoint_url=f'https://{self.account_id}.r2.cloudflarestorage.com',
            aws_access_key_id=self.access_key_id,
            aws_secret_access_key=self.secret_access_key,
            config=Config(signature_version='s3v4'),
            region_name='auto'
        )

    def _generate_object_key(self, filename: str, prefix: str = '') -> str:
        """
        生成唯一的对象键

        Args:
            filename: 原始文件名
            prefix: 路径前缀（如 'images/', 'videos/'）

        Returns:
            str: 对象键，格式如 'images/2024/01/uuid-filename.jpg'
        """
        # 安全化文件名
        safe_filename = secure_filename(filename)

        # 生成唯一ID
        unique_id = str(uuid.uuid4())[:8]

        # 按日期分目录
        date_path = datetime.utcnow().strftime('%Y/%m/%d')

        # 拼接文件名
        name, ext = os.path.splitext(safe_filename)
        object_key = f"{prefix}{date_path}/{unique_id}-{name}{ext}"

        return object_key

    def upload_file(self, file_data, filename: str, content_type: str = None, prefix: str = 'uploads/') -> dict:
        """
        上传文件到 R2

        Args:
            file_data: 文件数据（bytes 或 file-like object）
            filename: 文件名
            content_type: MIME 类型（如 'image/png'）
            prefix: 存储路径前缀

        Returns:
            dict: {
                'success': True/False,
                'url': '文件的公共 URL',
                'key': '对象键',
                'error': '错误信息（如果失败）'
            }
        """
        if not self.client:
            return {'success': False, 'error': 'R2 storage not configured'}

        try:
            # 生成对象键
            object_key = self._generate_object_key(filename, prefix)

            # 准备上传参数
            upload_args = {
                'Bucket': self.bucket_name,
                'Key': object_key,
                'Body': file_data
            }

            # 添加 Content-Type
            if content_type:
                upload_args['ContentType'] = content_type

            # 上传文件
            self.client.put_object(**upload_args)

            # 构造公共 URL
            if self.public_url:
                file_url = f"{self.public_url.rstrip('/')}/{object_key}"
            else:
                file_url = f"https://{self.bucket_name}.{self.account_id}.r2.cloudflarestorage.com/{object_key}"

            logger.info(f"File uploaded successfully: {object_key}")

            return {
                'success': True,
                'url': file_url,
                'key': object_key
            }

        except ClientError as e:
            error_msg = f"Failed to upload file: {str(e)}"
            logger.error(error_msg)
            return {'success': False, 'error': error_msg}
        except Exception as e:
            error_msg = f"Unexpected error during upload: {str(e)}"
            logger.error(error_msg)
            return {'success': False, 'error': error_msg}

    def upload_multiple_files(self, files_data: list, prefix: str = 'uploads/') -> list:
        """
        批量上传文件

        Args:
            files_data: 文件数据列表，每项为 {'data': bytes, 'filename': str, 'content_type': str}
            prefix: 存储路径前缀

        Returns:
            list: 上传结果列表
        """
        results = []

        for file_info in files_data:
            result = self.upload_file(
                file_data=file_info.get('data'),
                filename=file_info.get('filename'),
                content_type=file_info.get('content_type'),
                prefix=prefix
            )
            results.append(result)

        return results

    def delete_file(self, object_key: str) -> dict:
        """
        删除文件

        Args:
            object_key: 对象键

        Returns:
            dict: {'success': True/False, 'error': '错误信息'}
        """
        if not self.client:
            return {'success': False, 'error': 'R2 storage not configured'}

        try:
            self.client.delete_object(
                Bucket=self.bucket_name,
                Key=object_key
            )

            logger.info(f"File deleted successfully: {object_key}")
            return {'success': True}

        except ClientError as e:
            error_msg = f"Failed to delete file: {str(e)}"
            logger.error(error_msg)
            return {'success': False, 'error': error_msg}
        except Exception as e:
            error_msg = f"Unexpected error during deletion: {str(e)}"
            logger.error(error_msg)
            return {'success': False, 'error': error_msg}

    def delete_multiple_files(self, object_keys: list) -> dict:
        """
        批量删除文件

        Args:
            object_keys: 对象键列表

        Returns:
            dict: {
                'success': True/False,
                'deleted': 成功删除的数量,
                'failed': 失败的数量,
                'errors': 错误列表
            }
        """
        if not self.client:
            return {'success': False, 'error': 'R2 storage not configured'}

        deleted = 0
        failed = 0
        errors = []

        for key in object_keys:
            result = self.delete_file(key)
            if result['success']:
                deleted += 1
            else:
                failed += 1
                errors.append({'key': key, 'error': result.get('error')})

        return {
            'success': failed == 0,
            'deleted': deleted,
            'failed': failed,
            'errors': errors
        }

    def generate_presigned_url(self, object_key: str, expiration: int = 3600) -> dict:
        """
        生成预签名 URL（用于临时下载）

        Args:
            object_key: 对象键
            expiration: 过期时间（秒），默认1小时

        Returns:
            dict: {'success': True/False, 'url': '预签名 URL', 'error': '错误信息'}
        """
        if not self.client:
            return {'success': False, 'error': 'R2 storage not configured'}

        try:
            url = self.client.generate_presigned_url(
                'get_object',
                Params={
                    'Bucket': self.bucket_name,
                    'Key': object_key
                },
                ExpiresIn=expiration
            )

            return {'success': True, 'url': url}

        except ClientError as e:
            error_msg = f"Failed to generate presigned URL: {str(e)}"
            logger.error(error_msg)
            return {'success': False, 'error': error_msg}

    def file_exists(self, object_key: str) -> bool:
        """
        检查文件是否存在

        Args:
            object_key: 对象键

        Returns:
            bool: 文件是否存在
        """
        if not self.client:
            return False

        try:
            self.client.head_object(Bucket=self.bucket_name, Key=object_key)
            return True
        except ClientError:
            return False


# 创建全局实例
storage_service = StorageService()
