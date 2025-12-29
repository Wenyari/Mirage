"""
鉴权服务测试
"""
import pytest
import bcrypt
from app.services.auth_service import (
    send_verify_code,
    register_user,
    login_user,
    check_token_validity
)
from app.models import User


@pytest.mark.unit
class TestAuthService:
    """鉴权服务测试类"""

    def test_send_verify_code_success(self, app, db_session, redis_db, mock_mail):
        """测试发送验证码成功"""
        with app.app_context():
            email = 'newuser@example.com'

            # 调用服务
            send_verify_code(email)

            # 验证 Redis 中存储了验证码
            verify_key = f"verify:email:{email}"
            code = redis_db.get(verify_key)

            assert code is not None
            assert len(code) == 6
            assert code.isdigit()

            # 验证邮件被发送
            mock_mail.assert_called_once()

    def test_send_verify_code_invalid_email(self, app, db_session):
        """测试无效邮箱"""
        with app.app_context():
            with pytest.raises(ValueError, match="Invalid email format"):
                send_verify_code('invalid-email')

    def test_register_user_success(self, app, db_session, redis_db):
        """测试用户注册成功"""
        with app.app_context():
            email = 'newuser@example.com'
            code = '123456'
            password = 'password123'

            # 先存入验证码
            verify_key = f"verify:email:{email}"
            redis_db.setex(verify_key, 300, code)

            # 注册用户
            user_id = register_user(email, code, password)

            # 验证
            assert user_id is not None

            user = User.query.get(user_id)
            assert user is not None
            assert user.email == email
            assert user.level == 1
            assert user.role == 'user'

            # 验证密码是否正确加密
            assert bcrypt.checkpw(password.encode('utf-8'), user.password_hash.encode('utf-8'))

            # 验证码应该被删除
            assert redis_db.get(verify_key) is None

    def test_register_user_invalid_code(self, app, db_session, redis_db):
        """测试验证码错误"""
        with app.app_context():
            email = 'newuser@example.com'
            code = '123456'

            # 存入不同的验证码
            verify_key = f"verify:email:{email}"
            redis_db.setex(verify_key, 300, '999999')

            # 应该抛出异常
            with pytest.raises(ValueError, match="Invalid verification code"):
                register_user(email, code, 'password123')

    def test_register_user_expired_code(self, app, db_session, redis_db):
        """测试验证码过期"""
        with app.app_context():
            email = 'newuser@example.com'
            code = '123456'

            # 不存入验证码（模拟过期）

            with pytest.raises(ValueError, match="Verification code expired"):
                register_user(email, code, 'password123')

    def test_register_user_duplicate_email(self, app, db_session, redis_db, test_user):
        """测试邮箱已存在"""
        with app.app_context():
            code = '123456'
            verify_key = f"verify:email:{test_user.email}"
            redis_db.setex(verify_key, 300, code)

            with pytest.raises(ValueError, match="Email already registered"):
                register_user(test_user.email, code, 'password123')

    def test_login_user_success(self, app, db_session, redis_db, test_user):
        """测试登录成功"""
        with app.app_context():
            result = login_user(test_user.email, 'password123')

            assert 'token' in result
            assert 'user' in result
            assert result['token'] is not None

            # 验证 Token 存入 Redis
            auth_token_key = f"auth:token:{test_user.id}"
            stored_token = redis_db.get(auth_token_key)
            assert stored_token == result['token']

    def test_login_user_invalid_email(self, app, db_session):
        """测试邮箱不存在"""
        with app.app_context():
            with pytest.raises(ValueError, match="Invalid email or password"):
                login_user('nonexistent@example.com', 'password')

    def test_login_user_wrong_password(self, app, db_session, test_user):
        """测试密码错误"""
        with app.app_context():
            with pytest.raises(ValueError, match="Invalid email or password"):
                login_user(test_user.email, 'wrongpassword')

    def test_login_user_banned(self, app, db_session, test_user):
        """测试账号被封禁"""
        with app.app_context():
            test_user.status = 0
            db_session.session.commit()

            with pytest.raises(ValueError, match="Account has been banned"):
                login_user(test_user.email, 'password123')

    def test_check_token_validity_valid(self, app, redis_db, test_user):
        """测试 Token 有效性检查 - 有效"""
        with app.app_context():
            token = 'test-token-123'
            auth_token_key = f"auth:token:{test_user.id}"
            redis_db.setex(auth_token_key, 3600, token)

            is_valid = check_token_validity(test_user.id, token)
            assert is_valid is True

    def test_check_token_validity_invalid(self, app, redis_db, test_user):
        """测试 Token 有效性检查 - 无效"""
        with app.app_context():
            auth_token_key = f"auth:token:{test_user.id}"
            redis_db.setex(auth_token_key, 3600, 'old-token')

            is_valid = check_token_validity(test_user.id, 'new-token')
            assert is_valid is False

    def test_check_token_validity_no_token(self, app, redis_db, test_user):
        """测试 Token 有效性检查 - 不存在"""
        with app.app_context():
            is_valid = check_token_validity(test_user.id, 'any-token')
            assert is_valid is False
