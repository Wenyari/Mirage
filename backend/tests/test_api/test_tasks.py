"""
任务 API 测试
"""
import pytest
import json


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
