"""
管理员 API 测试
"""
import pytest
import json


@pytest.mark.api
class TestAdminAPI:
    """管理员 API 测试类"""

    def test_generate_cdk_success(self, client, db_session, admin_headers):
        """测试生成 CDK 成功"""
        response = client.post(
            '/api/admin/cdk/generate',
            data=json.dumps({
                'points': 500,
                'count': 10,
                'batch_name': 'Test Batch',
                'expire_days': 30
            }),
            headers=admin_headers
        )

        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['code'] == 200

    def test_generate_cdk_missing_params(self, client, db_session, admin_headers):
        """测试缺少参数"""
        response = client.post(
            '/api/admin/cdk/generate',
            data=json.dumps({
                'points': 500
                # 缺少 count
            }),
            headers=admin_headers
        )

        assert response.status_code == 400

    def test_generate_cdk_no_auth(self, client, db_session):
        """测试未认证"""
        response = client.post(
            '/api/admin/cdk/generate',
            data=json.dumps({
                'points': 500,
                'count': 10
            }),
            content_type='application/json'
        )

        assert response.status_code == 401

    def test_ban_user_success(self, client, db_session, admin_headers, test_user):
        """测试封禁用户"""
        response = client.patch(
            f'/api/admin/users/{test_user.id}/ban',
            data=json.dumps({
                'status': 0
            }),
            headers=admin_headers
        )

        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['code'] == 200

    def test_ban_user_invalid_status(self, client, db_session, admin_headers, test_user):
        """测试无效状态值"""
        response = client.patch(
            f'/api/admin/users/{test_user.id}/ban',
            data=json.dumps({
                'status': 99
            }),
            headers=admin_headers
        )

        assert response.status_code == 400

    def test_get_statistics_success(self, client, db_session, admin_headers):
        """测试获取统计数据"""
        response = client.get(
            '/api/admin/stats',
            headers=admin_headers
        )

        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['code'] == 200
        assert 'total_users' in data['data']
        assert 'total_tasks' in data['data']
