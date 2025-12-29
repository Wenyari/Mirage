"""
用户 API 测试
"""
import pytest
import json


@pytest.mark.api
class TestUsersAPI:
    """用户 API 测试类"""

    def test_get_user_info_success(self, client, db_session, auth_headers, test_user):
        """测试获取个人信息"""
        response = client.get(
            '/api/users/me',
            headers=auth_headers
        )

        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['code'] == 200
        assert data['data']['id'] == test_user.id
        assert data['data']['email'] == test_user.email

    def test_get_user_info_no_auth(self, client, db_session):
        """测试未认证"""
        response = client.get('/api/users/me')

        assert response.status_code == 401

    def test_get_membership_plans_success(self, client, db_session):
        """测试获取会员等级列表"""
        response = client.get('/api/users/membership/plans')

        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['code'] == 200
        assert isinstance(data['data'], list)
        assert len(data['data']) == 5  # T1-T5

        # 验证数据结构
        plan = data['data'][0]
        assert 'level' in plan
        assert 'name' in plan
        assert 'concurrency_limit' in plan
