"""
鉴权 API 测试
"""
import pytest
import json


@pytest.mark.api
class TestAuthAPI:
    """鉴权 API 测试类"""

    def test_send_verify_code_success(self, client, db_session, redis_db, mock_mail):
        """测试发送验证码成功"""
        response = client.post(
            '/api/auth/code',
            data=json.dumps({'email': 'test@example.com'}),
            content_type='application/json'
        )

        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['code'] == 200

        # 验证 Redis 中有验证码
        verify_key = "verify:email:test@example.com"
        code = redis_db.get(verify_key)
        assert code is not None

    def test_send_verify_code_missing_email(self, client, db_session):
        """测试缺少邮箱参数"""
        response = client.post(
            '/api/auth/code',
            data=json.dumps({}),
            content_type='application/json'
        )

        assert response.status_code == 400

    def test_register_success(self, client, db_session, redis_db):
        """测试用户注册成功"""
        email = 'newuser@example.com'
        code = '123456'

        # 先存入验证码
        verify_key = f"verify:email:{email}"
        redis_db.setex(verify_key, 300, code)

        response = client.post(
            '/api/auth/register',
            data=json.dumps({
                'email': email,
                'code': code,
                'password': 'password123'
            }),
            content_type='application/json'
        )

        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['code'] == 200
        assert 'user_id' in data['data']

    def test_register_invalid_code(self, client, db_session, redis_db):
        """测试验证码错误"""
        email = 'newuser@example.com'

        # 存入不同的验证码
        verify_key = f"verify:email:{email}"
        redis_db.setex(verify_key, 300, '999999')

        response = client.post(
            '/api/auth/register',
            data=json.dumps({
                'email': email,
                'code': '123456',
                'password': 'password123'
            }),
            content_type='application/json'
        )

        assert response.status_code == 400

    def test_login_success(self, client, db_session, redis_db, test_user):
        """测试登录成功"""
        response = client.post(
            '/api/auth/login',
            data=json.dumps({
                'email': test_user.email,
                'password': 'password123'
            }),
            content_type='application/json'
        )

        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['code'] == 200
        assert 'token' in data['data']
        assert 'user' in data['data']

    def test_login_wrong_password(self, client, db_session, test_user):
        """测试密码错误"""
        response = client.post(
            '/api/auth/login',
            data=json.dumps({
                'email': test_user.email,
                'password': 'wrongpassword'
            }),
            content_type='application/json'
        )

        assert response.status_code == 401

    def test_login_user_not_found(self, client, db_session):
        """测试用户不存在"""
        response = client.post(
            '/api/auth/login',
            data=json.dumps({
                'email': 'nonexistent@example.com',
                'password': 'password'
            }),
            content_type='application/json'
        )

        assert response.status_code == 401

    def test_get_current_user_success(self, client, db_session, auth_headers, test_user):
        """测试获取当前用户信息"""
        response = client.get(
            '/api/auth/me',
            headers=auth_headers
        )

        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['code'] == 200
        assert data['data']['id'] == test_user.id
        assert data['data']['email'] == test_user.email

    def test_get_current_user_no_token(self, client, db_session):
        """测试未提供 Token"""
        response = client.get('/api/auth/me')

        assert response.status_code == 401

    def test_get_current_user_invalid_token(self, client, db_session):
        """测试无效 Token"""
        response = client.get(
            '/api/auth/me',
            headers={'Authorization': 'Bearer invalid-token'}
        )

        assert response.status_code == 401
