"""
Cloudflare R2 存储服务测试
测试文件上传、删除、批量操作等功能
"""
import pytest
from unittest.mock import MagicMock, patch, Mock
from botocore.exceptions import ClientError
from app.services.storage_service import StorageService, storage_service


@pytest.mark.unit
class TestStorageService:
    """存储服务测试类"""

    @pytest.fixture
    def mock_boto3_client(self, mocker):
        """Mock boto3 S3 客户端"""
        mock_client = MagicMock()
        mocker.patch('boto3.client', return_value=mock_client)
        return mock_client

    @pytest.fixture
    def mock_env(self, monkeypatch):
        """Mock 环境变量"""
        monkeypatch.setenv('R2_ACCOUNT_ID', 'test-account-id')
        monkeypatch.setenv('R2_ACCESS_KEY_ID', 'test-access-key')
        monkeypatch.setenv('R2_SECRET_ACCESS_KEY', 'test-secret-key')
        monkeypatch.setenv('R2_BUCKET_NAME', 'test-bucket')
        monkeypatch.setenv('R2_PUBLIC_URL', 'https://cdn.test.com')

    @pytest.fixture
    def storage(self, mock_env, mock_boto3_client):
        """创建存储服务实例"""
        return StorageService()

    def test_storage_service_init_success(self, storage, mock_boto3_client):
        """测试存储服务初始化成功"""
        assert storage.account_id == 'test-account-id'
        assert storage.access_key_id == 'test-access-key'
        assert storage.secret_access_key == 'test-secret-key'
        assert storage.bucket_name == 'test-bucket'
        assert storage.public_url == 'https://cdn.test.com'
        assert storage.client is not None

    def test_storage_service_init_without_credentials(self, monkeypatch):
        """测试缺少凭证时的初始化"""
        # 清空环境变量
        for key in ['R2_ACCOUNT_ID', 'R2_ACCESS_KEY_ID', 'R2_SECRET_ACCESS_KEY', 'R2_BUCKET_NAME']:
            monkeypatch.delenv(key, raising=False)

        with patch('boto3.client'):
            service = StorageService()
            assert service.client is None

    def test_generate_object_key(self, storage):
        """测试对象键生成"""
        filename = 'test image.jpg'
        key = storage._generate_object_key(filename, prefix='uploads/')

        # 验证格式：uploads/YYYY/MM/DD/uuid-filename.jpg
        assert key.startswith('uploads/')
        assert key.endswith('-test_image.jpg')  # secure_filename 将空格转换为下划线
        assert len(key.split('/')) == 5  # uploads/year/month/day/filename

    def test_generate_object_key_without_prefix(self, storage):
        """测试无前缀的对象键生成"""
        filename = 'video.mp4'
        key = storage._generate_object_key(filename)

        # 验证格式：YYYY/MM/DD/uuid-filename.mp4
        assert key.endswith('-video.mp4')
        assert len(key.split('/')) == 4  # year/month/day/filename

    def test_upload_file_success(self, storage, mock_boto3_client):
        """测试文件上传成功"""
        file_data = b'test file content'
        filename = 'test.jpg'
        content_type = 'image/jpeg'

        # Mock put_object 成功
        mock_boto3_client.put_object.return_value = {}

        result = storage.upload_file(
            file_data=file_data,
            filename=filename,
            content_type=content_type,
            prefix='uploads/'
        )

        # 验证结果
        assert result['success'] is True
        assert 'url' in result
        assert 'key' in result
        assert result['url'].startswith('https://cdn.test.com/uploads/')
        assert result['key'].startswith('uploads/')

        # 验证 put_object 被正确调用
        mock_boto3_client.put_object.assert_called_once()
        call_args = mock_boto3_client.put_object.call_args[1]
        assert call_args['Bucket'] == 'test-bucket'
        assert call_args['Body'] == file_data
        assert call_args['ContentType'] == content_type

    def test_upload_file_without_content_type(self, storage, mock_boto3_client):
        """测试无 Content-Type 的文件上传"""
        file_data = b'test content'
        filename = 'test.txt'

        mock_boto3_client.put_object.return_value = {}

        result = storage.upload_file(file_data=file_data, filename=filename)

        assert result['success'] is True
        # Content-Type 不应该在参数中
        call_args = mock_boto3_client.put_object.call_args[1]
        assert 'ContentType' not in call_args

    def test_upload_file_client_error(self, storage, mock_boto3_client):
        """测试上传时 S3 客户端错误"""
        file_data = b'test content'
        filename = 'test.jpg'

        # Mock put_object 抛出异常
        mock_boto3_client.put_object.side_effect = ClientError(
            {'Error': {'Code': 'AccessDenied', 'Message': 'Access Denied'}},
            'PutObject'
        )

        result = storage.upload_file(file_data=file_data, filename=filename)

        assert result['success'] is False
        assert 'error' in result
        assert 'Access Denied' in result['error']

    def test_upload_file_generic_exception(self, storage, mock_boto3_client):
        """测试上传时一般异常"""
        file_data = b'test content'
        filename = 'test.jpg'

        # Mock put_object 抛出一般异常
        mock_boto3_client.put_object.side_effect = Exception('Network error')

        result = storage.upload_file(file_data=file_data, filename=filename)

        assert result['success'] is False
        assert 'error' in result
        assert 'Network error' in result['error']

    def test_upload_file_without_client(self, mock_env):
        """测试未初始化客户端时的上传"""
        with patch('boto3.client', return_value=None):
            service = StorageService()
            service.client = None

            result = service.upload_file(b'test', 'test.jpg')

            assert result['success'] is False
            assert 'not configured' in result['error']

    def test_upload_multiple_files_success(self, storage, mock_boto3_client):
        """测试批量上传成功"""
        files_data = [
            {'data': b'file1', 'filename': 'test1.jpg', 'content_type': 'image/jpeg'},
            {'data': b'file2', 'filename': 'test2.jpg', 'content_type': 'image/jpeg'},
            {'data': b'file3', 'filename': 'test3.jpg', 'content_type': 'image/jpeg'},
        ]

        mock_boto3_client.put_object.return_value = {}

        results = storage.upload_multiple_files(files_data, prefix='batch/')

        assert len(results) == 3
        for result in results:
            assert result['success'] is True
            assert 'url' in result
            assert 'key' in result

        # 验证 put_object 被调用 3 次
        assert mock_boto3_client.put_object.call_count == 3

    def test_upload_multiple_files_partial_failure(self, storage, mock_boto3_client):
        """测试批量上传部分失败"""
        files_data = [
            {'data': b'file1', 'filename': 'test1.jpg', 'content_type': 'image/jpeg'},
            {'data': b'file2', 'filename': 'test2.jpg', 'content_type': 'image/jpeg'},
        ]

        # 第一次成功，第二次失败
        mock_boto3_client.put_object.side_effect = [
            {},
            ClientError(
                {'Error': {'Code': 'NoSuchBucket', 'Message': 'Bucket not found'}},
                'PutObject'
            )
        ]

        results = storage.upload_multiple_files(files_data)

        assert len(results) == 2
        assert results[0]['success'] is True
        assert results[1]['success'] is False
        assert 'error' in results[1]

    def test_delete_file_success(self, storage, mock_boto3_client):
        """测试文件删除成功"""
        object_key = 'uploads/2024/01/08/abc123-test.jpg'

        mock_boto3_client.delete_object.return_value = {}

        result = storage.delete_file(object_key)

        assert result['success'] is True
        mock_boto3_client.delete_object.assert_called_once_with(
            Bucket='test-bucket',
            Key=object_key
        )

    def test_delete_file_client_error(self, storage, mock_boto3_client):
        """测试删除时客户端错误"""
        object_key = 'uploads/test.jpg'

        mock_boto3_client.delete_object.side_effect = ClientError(
            {'Error': {'Code': 'NoSuchKey', 'Message': 'Key not found'}},
            'DeleteObject'
        )

        result = storage.delete_file(object_key)

        assert result['success'] is False
        assert 'error' in result

    def test_delete_file_without_client(self, mock_env):
        """测试未初始化客户端时的删除"""
        with patch('boto3.client', return_value=None):
            service = StorageService()
            service.client = None

            result = service.delete_file('test.jpg')

            assert result['success'] is False
            assert 'not configured' in result['error']

    def test_delete_multiple_files_success(self, storage, mock_boto3_client):
        """测试批量删除成功"""
        object_keys = [
            'uploads/file1.jpg',
            'uploads/file2.jpg',
            'uploads/file3.jpg'
        ]

        mock_boto3_client.delete_object.return_value = {}

        result = storage.delete_multiple_files(object_keys)

        assert result['success'] is True
        assert result['deleted'] == 3
        assert result['failed'] == 0
        assert len(result['errors']) == 0
        assert mock_boto3_client.delete_object.call_count == 3

    def test_delete_multiple_files_partial_failure(self, storage, mock_boto3_client):
        """测试批量删除部分失败"""
        object_keys = ['file1.jpg', 'file2.jpg', 'file3.jpg']

        # 前两次成功，第三次失败
        mock_boto3_client.delete_object.side_effect = [
            {},
            {},
            ClientError(
                {'Error': {'Code': 'AccessDenied', 'Message': 'Access Denied'}},
                'DeleteObject'
            )
        ]

        result = storage.delete_multiple_files(object_keys)

        assert result['success'] is False
        assert result['deleted'] == 2
        assert result['failed'] == 1
        assert len(result['errors']) == 1
        assert result['errors'][0]['key'] == 'file3.jpg'

    def test_generate_presigned_url_success(self, storage, mock_boto3_client):
        """测试预签名 URL 生成成功"""
        object_key = 'uploads/test.jpg'
        expected_url = 'https://presigned-url.com/test.jpg?signature=abc123'

        mock_boto3_client.generate_presigned_url.return_value = expected_url

        result = storage.generate_presigned_url(object_key, expiration=3600)

        assert result['success'] is True
        assert result['url'] == expected_url

        mock_boto3_client.generate_presigned_url.assert_called_once_with(
            'get_object',
            Params={'Bucket': 'test-bucket', 'Key': object_key},
            ExpiresIn=3600
        )

    def test_generate_presigned_url_default_expiration(self, storage, mock_boto3_client):
        """测试默认过期时间的预签名 URL"""
        object_key = 'uploads/test.jpg'
        mock_boto3_client.generate_presigned_url.return_value = 'https://url.com'

        result = storage.generate_presigned_url(object_key)

        assert result['success'] is True
        call_args = mock_boto3_client.generate_presigned_url.call_args[1]
        assert call_args['ExpiresIn'] == 3600  # 默认 1 小时

    def test_generate_presigned_url_error(self, storage, mock_boto3_client):
        """测试预签名 URL 生成失败"""
        object_key = 'uploads/test.jpg'

        mock_boto3_client.generate_presigned_url.side_effect = ClientError(
            {'Error': {'Code': 'NoSuchKey', 'Message': 'Key not found'}},
            'GeneratePresignedUrl'
        )

        result = storage.generate_presigned_url(object_key)

        assert result['success'] is False
        assert 'error' in result

    def test_generate_presigned_url_without_client(self, mock_env):
        """测试未初始化客户端时生成预签名 URL"""
        with patch('boto3.client', return_value=None):
            service = StorageService()
            service.client = None

            result = service.generate_presigned_url('test.jpg')

            assert result['success'] is False
            assert 'not configured' in result['error']

    def test_file_exists_true(self, storage, mock_boto3_client):
        """测试文件存在检查 - 存在"""
        object_key = 'uploads/test.jpg'

        mock_boto3_client.head_object.return_value = {
            'ContentLength': 12345,
            'ContentType': 'image/jpeg'
        }

        exists = storage.file_exists(object_key)

        assert exists is True
        mock_boto3_client.head_object.assert_called_once_with(
            Bucket='test-bucket',
            Key=object_key
        )

    def test_file_exists_false(self, storage, mock_boto3_client):
        """测试文件存在检查 - 不存在"""
        object_key = 'uploads/nonexistent.jpg'

        mock_boto3_client.head_object.side_effect = ClientError(
            {'Error': {'Code': '404', 'Message': 'Not Found'}},
            'HeadObject'
        )

        exists = storage.file_exists(object_key)

        assert exists is False

    def test_file_exists_without_client(self, mock_env):
        """测试未初始化客户端时检查文件存在"""
        with patch('boto3.client', return_value=None):
            service = StorageService()
            service.client = None

            exists = service.file_exists('test.jpg')

            assert exists is False

    def test_url_construction_with_custom_domain(self, storage):
        """测试使用自定义域名构造 URL"""
        file_data = b'test'
        filename = 'test.jpg'

        with patch.object(storage.client, 'put_object', return_value={}):
            result = storage.upload_file(file_data, filename)

            assert result['success'] is True
            assert result['url'].startswith('https://cdn.test.com/')

    def test_url_construction_without_custom_domain(self, mock_env, mock_boto3_client, monkeypatch):
        """测试无自定义域名时构造 URL"""
        # 移除自定义域名
        monkeypatch.delenv('R2_PUBLIC_URL', raising=False)

        service = StorageService()
        service.client = mock_boto3_client

        mock_boto3_client.put_object.return_value = {}

        result = service.upload_file(b'test', 'test.jpg')

        assert result['success'] is True
        # 应该使用默认的 R2 URL 格式
        assert 'test-account-id.r2.cloudflarestorage.com' in result['url']

    def test_global_storage_service_instance(self):
        """测试全局存储服务实例"""
        assert storage_service is not None
        assert isinstance(storage_service, StorageService)
