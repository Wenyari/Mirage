"""
文件上传 API 测试
测试文件上传、批量上传、删除等接口
"""
import pytest
import io
from flask import Flask
from werkzeug.datastructures import FileStorage
from app.api.upload import bp, allowed_file, get_content_type


@pytest.fixture
def client(app):
    """创建测试客户端"""
    app.register_blueprint(bp)
    return app.test_client()


@pytest.fixture
def auth_headers(app, test_user):
    """创建认证头"""
    from flask_jwt_extended import create_access_token

    with app.app_context():
        token = create_access_token(identity=str(test_user.id))
        return {'Authorization': f'Bearer {token}'}


@pytest.mark.unit
class TestUploadHelpers:
    """上传辅助函数测试"""

    def test_allowed_file_image(self):
        """测试图片文件类型验证"""
        assert allowed_file('test.jpg', 'image') is True
        assert allowed_file('test.png', 'image') is True
        assert allowed_file('test.gif', 'image') is True
        assert allowed_file('test.webp', 'image') is True
        assert allowed_file('test.bmp', 'image') is True

    def test_allowed_file_video(self):
        """测试视频文件类型验证"""
        assert allowed_file('test.mp4', 'video') is True
        assert allowed_file('test.avi', 'video') is True
        assert allowed_file('test.mov', 'video') is True
        assert allowed_file('test.mkv', 'video') is True
        assert allowed_file('test.webm', 'video') is True

    def test_allowed_file_audio(self):
        """测试音频文件类型验证"""
        assert allowed_file('test.mp3', 'audio') is True
        assert allowed_file('test.wav', 'audio') is True
        assert allowed_file('test.ogg', 'audio') is True

    def test_allowed_file_any_type(self):
        """测试不指定类型时的验证"""
        assert allowed_file('test.jpg') is True
        assert allowed_file('test.mp4') is True
        assert allowed_file('test.mp3') is True

    def test_allowed_file_invalid(self):
        """测试无效文件类型"""
        assert allowed_file('test.exe', 'image') is False
        assert allowed_file('test.pdf', 'video') is False
        assert allowed_file('test.doc', 'audio') is False
        assert allowed_file('test.txt') is False

    def test_allowed_file_no_extension(self):
        """测试无扩展名文件"""
        assert allowed_file('test', 'image') is False
        assert allowed_file('test') is False

    def test_allowed_file_case_insensitive(self):
        """测试大小写不敏感"""
        assert allowed_file('test.JPG', 'image') is True
        assert allowed_file('test.PNG', 'image') is True
        assert allowed_file('test.MP4', 'video') is True

    def test_get_content_type_image(self):
        """测试获取图片MIME类型"""
        assert get_content_type('test.jpg') == 'image/jpeg'
        assert get_content_type('test.png') == 'image/png'
        assert get_content_type('test.gif') == 'image/gif'

    def test_get_content_type_video(self):
        """测试获取视频MIME类型"""
        assert get_content_type('test.mp4') == 'video/mp4'
        assert get_content_type('test.avi') == 'video/x-msvideo'
        assert get_content_type('test.mov') == 'video/quicktime'

    def test_get_content_type_audio(self):
        """测试获取音频MIME类型"""
        assert get_content_type('test.mp3') == 'audio/mpeg'
        assert get_content_type('test.wav') == 'audio/wav'

    def test_get_content_type_unknown(self):
        """测试未知文件类型"""
        assert get_content_type('test.unknown') == 'application/octet-stream'
        assert get_content_type('test') == 'application/octet-stream'


@pytest.mark.unit
class TestUploadAPI:
    """文件上传 API 测试"""

    def test_upload_file_success(self, app, client, db_session, auth_headers, mocker):
        """测试单文件上传成功"""
        with app.app_context():
            # Mock storage service
            mock_storage = mocker.patch('app.api.upload.storage_service')
            mock_storage.upload_file.return_value = {
                'success': True,
                'url': 'https://cdn.test.com/uploads/user_1/2024/01/08/abc123-test.jpg',
                'key': 'uploads/user_1/2024/01/08/abc123-test.jpg'
            }

            # 创建测试文件
            data = {
                'file': (io.BytesIO(b'test image content'), 'test.jpg'),
                'type': 'image'
            }

            response = client.post(
                '/api/upload/file',
                data=data,
                headers=auth_headers,
                content_type='multipart/form-data'
            )

            assert response.status_code == 200
            json_data = response.get_json()
            assert json_data['code'] == 200
            assert json_data['msg'] == 'File uploaded successfully'
            assert 'url' in json_data['data']
            assert 'key' in json_data['data']

            # 验证 storage_service 被调用
            mock_storage.upload_file.assert_called_once()

    def test_upload_file_without_auth(self, client):
        """测试未认证的上传请求"""
        data = {
            'file': (io.BytesIO(b'test'), 'test.jpg')
        }

        response = client.post(
            '/api/upload/file',
            data=data,
            content_type='multipart/form-data'
        )

        assert response.status_code == 401

    def test_upload_file_no_file_provided(self, app, client, db_session, auth_headers):
        """测试未提供文件"""
        with app.app_context():
            response = client.post(
                '/api/upload/file',
                data={},
                headers=auth_headers,
                content_type='multipart/form-data'
            )

            assert response.status_code == 400
            json_data = response.get_json()
            assert json_data['code'] == 400
            assert 'No file provided' in json_data['msg']

    def test_upload_file_empty_filename(self, app, client, db_session, auth_headers):
        """测试空文件名"""
        with app.app_context():
            data = {
                'file': (io.BytesIO(b'test'), '')
            }

            response = client.post(
                '/api/upload/file',
                data=data,
                headers=auth_headers,
                content_type='multipart/form-data'
            )

            assert response.status_code == 400
            json_data = response.get_json()
            assert json_data['code'] == 400
            assert 'No file selected' in json_data['msg']

    def test_upload_file_invalid_type(self, app, client, db_session, auth_headers):
        """测试无效文件类型"""
        with app.app_context():
            data = {
                'file': (io.BytesIO(b'test'), 'test.exe'),
                'type': 'image'
            }

            response = client.post(
                '/api/upload/file',
                data=data,
                headers=auth_headers,
                content_type='multipart/form-data'
            )

            assert response.status_code == 400
            json_data = response.get_json()
            assert json_data['code'] == 400
            assert 'not allowed' in json_data['msg']

    def test_upload_file_storage_error(self, app, client, db_session, auth_headers, mocker):
        """测试存储服务错误"""
        with app.app_context():
            mock_storage = mocker.patch('app.api.upload.storage_service')
            mock_storage.upload_file.return_value = {
                'success': False,
                'error': 'Storage service error'
            }

            data = {
                'file': (io.BytesIO(b'test'), 'test.jpg')
            }

            response = client.post(
                '/api/upload/file',
                data=data,
                headers=auth_headers,
                content_type='multipart/form-data'
            )

            assert response.status_code == 500
            json_data = response.get_json()
            assert json_data['code'] == 500
            assert 'Upload failed' in json_data['msg']

    def test_upload_file_without_type_parameter(self, app, client, db_session, auth_headers, mocker):
        """测试不指定文件类型参数"""
        with app.app_context():
            mock_storage = mocker.patch('app.api.upload.storage_service')
            mock_storage.upload_file.return_value = {
                'success': True,
                'url': 'https://cdn.test.com/test.jpg',
                'key': 'test.jpg'
            }

            data = {
                'file': (io.BytesIO(b'test'), 'test.jpg')
            }

            response = client.post(
                '/api/upload/file',
                data=data,
                headers=auth_headers,
                content_type='multipart/form-data'
            )

            assert response.status_code == 200

    def test_upload_files_success(self, app, client, db_session, auth_headers, mocker):
        """测试批量上传成功"""
        with app.app_context():
            mock_storage = mocker.patch('app.api.upload.storage_service')
            mock_storage.upload_file.side_effect = [
                {
                    'success': True,
                    'url': 'https://cdn.test.com/test1.jpg',
                    'key': 'test1.jpg'
                },
                {
                    'success': True,
                    'url': 'https://cdn.test.com/test2.jpg',
                    'key': 'test2.jpg'
                }
            ]

            data = {
                'files[]': [
                    (io.BytesIO(b'test1'), 'test1.jpg'),
                    (io.BytesIO(b'test2'), 'test2.jpg')
                ]
            }

            response = client.post(
                '/api/upload/files',
                data=data,
                headers=auth_headers,
                content_type='multipart/form-data'
            )

            assert response.status_code == 200
            json_data = response.get_json()
            assert json_data['code'] == 200
            assert len(json_data['data']['uploaded']) == 2
            assert len(json_data['data']['failed']) == 0

    def test_upload_files_partial_failure(self, app, client, db_session, auth_headers, mocker):
        """测试批量上传部分失败"""
        with app.app_context():
            mock_storage = mocker.patch('app.api.upload.storage_service')
            mock_storage.upload_file.side_effect = [
                {
                    'success': True,
                    'url': 'https://cdn.test.com/test1.jpg',
                    'key': 'test1.jpg'
                },
                {
                    'success': False,
                    'error': 'Upload failed'
                }
            ]

            data = {
                'files[]': [
                    (io.BytesIO(b'test1'), 'test1.jpg'),
                    (io.BytesIO(b'test2'), 'test2.jpg')
                ]
            }

            response = client.post(
                '/api/upload/files',
                data=data,
                headers=auth_headers,
                content_type='multipart/form-data'
            )

            assert response.status_code == 200
            json_data = response.get_json()
            assert len(json_data['data']['uploaded']) == 1
            assert len(json_data['data']['failed']) == 1

    def test_upload_files_invalid_type(self, app, client, db_session, auth_headers):
        """测试批量上传包含无效类型"""
        with app.app_context():
            data = {
                'files[]': [
                    (io.BytesIO(b'test1'), 'test1.jpg'),
                    (io.BytesIO(b'test2'), 'test2.exe')
                ],
                'type': 'image'
            }

            response = client.post(
                '/api/upload/files',
                data=data,
                headers=auth_headers,
                content_type='multipart/form-data'
            )

            assert response.status_code == 200
            json_data = response.get_json()
            # test1.jpg 应该成功，test2.exe 应该失败
            assert len(json_data['data']['failed']) >= 1

    def test_upload_files_no_files(self, app, client, db_session, auth_headers):
        """测试批量上传未提供文件"""
        with app.app_context():
            response = client.post(
                '/api/upload/files',
                data={},
                headers=auth_headers,
                content_type='multipart/form-data'
            )

            assert response.status_code == 400
            json_data = response.get_json()
            assert 'No files provided' in json_data['msg']

    def test_delete_file_success(self, app, client, db_session, auth_headers, mocker):
        """测试删除文件成功"""
        with app.app_context():
            mock_storage = mocker.patch('app.api.upload.storage_service')
            mock_storage.delete_file.return_value = {'success': True}

            # 用户只能删除自己的文件
            object_key = 'uploads/user_1/2024/01/08/test.jpg'

            response = client.delete(
                f'/api/upload/delete/{object_key}',
                headers=auth_headers
            )

            assert response.status_code == 200
            json_data = response.get_json()
            assert json_data['code'] == 200
            assert 'deleted successfully' in json_data['msg']

            mock_storage.delete_file.assert_called_once_with(object_key)

    def test_delete_file_permission_denied(self, app, client, db_session, auth_headers):
        """测试删除其他用户的文件"""
        with app.app_context():
            # 尝试删除其他用户的文件
            object_key = 'uploads/user_999/2024/01/08/test.jpg'

            response = client.delete(
                f'/api/upload/delete/{object_key}',
                headers=auth_headers
            )

            assert response.status_code == 403
            json_data = response.get_json()
            assert json_data['code'] == 403
            assert 'Permission denied' in json_data['msg']

    def test_delete_file_storage_error(self, app, client, db_session, auth_headers, mocker):
        """测试删除文件存储错误"""
        with app.app_context():
            mock_storage = mocker.patch('app.api.upload.storage_service')
            mock_storage.delete_file.return_value = {
                'success': False,
                'error': 'File not found'
            }

            object_key = 'uploads/user_1/2024/01/08/test.jpg'

            response = client.delete(
                f'/api/upload/delete/{object_key}',
                headers=auth_headers
            )

            assert response.status_code == 500
            json_data = response.get_json()
            assert json_data['code'] == 500
            assert 'Delete failed' in json_data['msg']

    def test_delete_file_without_auth(self, client):
        """测试未认证的删除请求"""
        response = client.delete('/api/upload/delete/test.jpg')
        assert response.status_code == 401

    def test_upload_video_file(self, app, client, db_session, auth_headers, mocker):
        """测试上传视频文件"""
        with app.app_context():
            mock_storage = mocker.patch('app.api.upload.storage_service')
            mock_storage.upload_file.return_value = {
                'success': True,
                'url': 'https://cdn.test.com/test.mp4',
                'key': 'test.mp4'
            }

            data = {
                'file': (io.BytesIO(b'video content'), 'test.mp4'),
                'type': 'video'
            }

            response = client.post(
                '/api/upload/file',
                data=data,
                headers=auth_headers,
                content_type='multipart/form-data'
            )

            assert response.status_code == 200
            json_data = response.get_json()
            assert json_data['code'] == 200

    def test_upload_audio_file(self, app, client, db_session, auth_headers, mocker):
        """测试上传音频文件"""
        with app.app_context():
            mock_storage = mocker.patch('app.api.upload.storage_service')
            mock_storage.upload_file.return_value = {
                'success': True,
                'url': 'https://cdn.test.com/test.mp3',
                'key': 'test.mp3'
            }

            data = {
                'file': (io.BytesIO(b'audio content'), 'test.mp3'),
                'type': 'audio'
            }

            response = client.post(
                '/api/upload/file',
                data=data,
                headers=auth_headers,
                content_type='multipart/form-data'
            )

            assert response.status_code == 200
            json_data = response.get_json()
            assert json_data['code'] == 200
