"""
任务 API 测试
"""
import pytest
import json
import requests
from unittest.mock import patch, MagicMock


@pytest.mark.api
class TestTasksAPI:
    """任务 API 测试类"""

    def test_create_task_success(self, client, db_session, auth_headers, test_user, mocker):
        """测试提交任务成功"""
        # Mock RQ 队列
        mocker.patch('app.services.task_service.Queue')

        response = client.post(
            '/api/tasks',
            data=json.dumps({
                'model': 'sora-v2',
                'prompt': 'A beautiful sunset',
                'params': {'duration': 1}
            }),
            headers=auth_headers
        )

        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['code'] == 200
        assert 'task_id' in data['data']
        assert data['data']['status'] == 'pending'

    def test_create_task_no_auth(self, client, db_session):
        """测试未认证"""
        response = client.post(
            '/api/tasks',
            data=json.dumps({
                'model': 'sora-v2',
                'prompt': 'Test'
            }),
            content_type='application/json'
        )

        assert response.status_code == 401

    def test_create_task_missing_model(self, client, db_session, auth_headers):
        """测试缺少模型参数"""
        response = client.post(
            '/api/tasks',
            data=json.dumps({
                'prompt': 'Test'
            }),
            headers=auth_headers
        )

        assert response.status_code == 400

    def test_create_task_insufficient_balance(self, client, db_session, auth_headers, test_user):
        """测试余额不足"""
        # 设置余额为 0
        test_user.balance = 0
        db_session.session.commit()

        response = client.post(
            '/api/tasks',
            data=json.dumps({
                'model': 'sora-v2',
                'prompt': 'Test',
                'params': {'duration': 1}
            }),
            headers=auth_headers
        )

        assert response.status_code == 400

    def test_get_task_status_success(self, client, db_session, auth_headers, test_task):
        """测试查询任务状态"""
        response = client.get(
            f'/api/tasks/{test_task.id}',
            headers=auth_headers
        )

        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['code'] == 200
        assert data['data']['id'] == test_task.id
        assert data['data']['status'] == test_task.status

    def test_get_task_status_not_found(self, client, db_session, auth_headers):
        """测试任务不存在"""
        response = client.get(
            '/api/tasks/nonexistent-task-id',
            headers=auth_headers
        )

        assert response.status_code == 404

    def test_get_task_history_success(self, client, db_session, auth_headers, test_task):
        """测试获取任务历史"""
        response = client.get(
            '/api/tasks?page=1&size=20',
            headers=auth_headers
        )

        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['code'] == 200
        assert 'list' in data['data']
        assert 'total' in data['data']


@pytest.mark.api
class TestSoraThirdPartyAPI:
    """第三方 Sora API 集成测试"""

    def test_sora_api_call_model_success(self):
        """测试第三方 Sora API 任务提交"""
        from app.services.model_gw import SoraGateway

        # Mock HTTP请求
        with patch('app.services.model_gw.requests.post') as mock_post:
            # 模拟成功的API响应
            mock_response = MagicMock()
            mock_response.raise_for_status.return_value = None
            mock_response.json.return_value = {
                'task_id': 'video_test_123456789'
            }
            mock_post.return_value = mock_response

            # 创建网关实例
            gateway = SoraGateway()

            # 调用API
            result = gateway.call_model(
                model_name='sora-2',
                prompt='A beautiful sunset over the ocean',
                params={
                    'aspect_ratio': '16:9',
                    'hd': False,
                    'duration': 10
                }
            )

            # 验证结果
            assert result['job_id'] == 'video_test_123456789'
            assert result['status'] == 'pending'

            # 验证请求参数
            mock_post.assert_called_once()
            args, kwargs = mock_post.call_args
            url = args[0]
            assert url == 'https://ai.t8star.cn/v2/videos/generations'

            # 验证请求头
            headers = kwargs['headers']
            assert 'Authorization' in headers
            assert headers['Authorization'].startswith('Bearer ')

            # 验证请求体
            payload = kwargs['json']
            assert payload['model'] == 'sora-2'
            assert payload['prompt'] == 'A beautiful sunset over the ocean'
            assert payload['aspect_ratio'] == '16:9'
            assert payload['hd'] is False
            assert payload['duration'] == '10'
            assert payload['watermark'] is False
            assert payload['private'] is False

    def test_sora_api_get_job_status_success(self):
        """测试第三方 Sora API 任务状态查询 - 成功"""
        from app.services.model_gw import SoraGateway

        # Mock HTTP请求
        with patch('app.services.model_gw.requests.get') as mock_get:
            # 模拟成功的任务状态响应
            mock_response = MagicMock()
            mock_response.raise_for_status.return_value = None
            mock_response.json.return_value = {
                'status': 'SUCCESS',
                'data': {
                    'output': 'https://example.com/video.mp4'
                }
            }
            mock_get.return_value = mock_response

            # 创建网关实例
            gateway = SoraGateway()

            # 查询任务状态
            result = gateway.get_job_status('video_test_123456789')

            # 验证结果
            assert result['status'] == 'success'
            assert result['result_url'] == 'https://example.com/video.mp4'

            # 验证请求
            mock_get.assert_called_once_with(
                'https://ai.t8star.cn/v2/videos/generations/video_test_123456789',
                headers={'Authorization': 'Bearer ***REMOVED***'},
                timeout=30
            )

    def test_sora_api_get_job_status_processing(self):
        """测试第三方 Sora API 任务状态查询 - 处理中"""
        from app.services.model_gw import SoraGateway

        with patch('app.services.model_gw.requests.get') as mock_get:
            # 模拟处理中的任务状态响应
            mock_response = MagicMock()
            mock_response.raise_for_status.return_value = None
            mock_response.json.return_value = {
                'status': 'IN_PROGRESS',
                'progress': '50%'
            }
            mock_get.return_value = mock_response

            gateway = SoraGateway()
            result = gateway.get_job_status('video_test_123456789')

            assert result['status'] == 'processing'
            assert result['result_url'] is None

    def test_sora_api_get_job_status_failed(self):
        """测试第三方 Sora API 任务状态查询 - 失败"""
        from app.services.model_gw import SoraGateway

        with patch('app.services.model_gw.requests.get') as mock_get:
            # 模拟失败的任务状态响应
            mock_response = MagicMock()
            mock_response.raise_for_status.return_value = None
            mock_response.json.return_value = {
                'status': 'FAILURE',
                'fail_reason': 'Content violation: NSFW content detected'
            }
            mock_get.return_value = mock_response

            gateway = SoraGateway()
            result = gateway.get_job_status('video_test_123456789')

            assert result['status'] == 'failed'
            assert result['fail_reason'] == 'Content violation: NSFW content detected'

    def test_sora_api_call_model_http_error(self):
        """测试第三方 Sora API 调用失败"""
        from app.services.model_gw import SoraGateway
        from requests.exceptions import RequestException
        from app import create_app

        # 创建Flask应用上下文
        app = create_app()
        with app.app_context():
            with patch('app.services.model_gw.requests.post') as mock_post:
                # 模拟HTTP错误
                mock_post.side_effect = RequestException('Connection timeout')

                gateway = SoraGateway()

                with pytest.raises(Exception) as exc_info:
                    gateway.call_model('sora-2', 'Test prompt')

                assert 'Failed to call Sora API' in str(exc_info.value)

    @pytest.mark.integration
    def test_sora_api_real_call(self):
        """集成测试：实际调用第三方 Sora API（需要网络连接）"""
        pytest.skip("跳过真实API调用测试，避免消耗API额度")

        # 如果要运行真实测试，请取消上面的skip并运行：
        # from app.services.model_gw import SoraGateway
        # gateway = SoraGateway()
        # result = gateway.call_model('sora-2', 'A simple test prompt')
        # assert 'job_id' in result
        # assert result['status'] == 'pending'
