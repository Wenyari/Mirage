"""
测试认证装饰器
"""
import pytest
from unittest.mock import Mock, patch
from flask import Flask
from flask_jwt_extended import JWTManager, create_access_token

from app.utils.auth import jwt_and_redis_required
from app.services import check_token_validity


class TestJWTAndRedisRequired:
    """测试 JWT + Redis 认证装饰器"""

    def setup_method(self):
        """测试前准备"""
        self.app = Flask(__name__)
        self.app.config['JWT_SECRET_KEY'] = 'test-secret-key'
        self.jwt = JWTManager(self.app)

        with self.app.app_context():
            # 创建测试token
            self.test_user_id = 123
            self.valid_token = create_access_token(identity=str(self.test_user_id))

    def test_valid_token_with_valid_redis(self):
        """测试有效的token和有效的Redis记录"""
        with self.app.app_context():
            # 创建装饰器函数
            @jwt_and_redis_required()
            def test_function():
                return {"success": True}

            with patch('app.utils.auth.check_token_validity', return_value=True), \
                 patch('flask_jwt_extended.get_jwt_identity', return_value=str(self.test_user_id)), \
                 patch('flask_jwt_extended.get_jwt', return_value={'sub': str(self.test_user_id)}), \
                 patch('flask.request') as mock_request:

                # 模拟请求头
                mock_request.headers.get.return_value = f"Bearer {self.valid_token}"

                # 调用函数
                result = test_function()
                assert result == {"success": True}

    def test_valid_token_with_invalid_redis(self):
        """测试有效的token但Redis记录无效（已登出）"""
        with self.app.app_context():
            @jwt_and_redis_required()
            def test_function():
                return {"success": True}

            with patch('app.utils.auth.check_token_validity', return_value=False), \
                 patch('flask_jwt_extended.get_jwt_identity', return_value=str(self.test_user_id)), \
                 patch('flask_jwt_extended.get_jwt', return_value={'sub': str(self.test_user_id)}), \
                 patch('flask.request') as mock_request, \
                 patch('flask.jsonify') as mock_jsonify:

                # 模拟请求头
                mock_request.headers.get.return_value = f"Bearer {self.valid_token}"

                # 模拟 jsonify 返回值
                mock_response = Mock()
                mock_jsonify.return_value = mock_response
                mock_response.status_code = 401

                # 调用函数
                result = test_function()

                # 验证返回了401错误
                mock_jsonify.assert_called_once()
                call_args = mock_jsonify.call_args[0][0]
                assert call_args['code'] == 401
                assert 'revoked' in call_args['msg']

    def test_invalid_jwt_token(self):
        """测试无效的JWT token"""
        with self.app.app_context():
            @jwt_and_redis_required()
            def test_function():
                return {"success": True}

            with patch('flask_jwt_extended.get_jwt_identity', side_effect=Exception("Invalid token")), \
                 patch('flask.jsonify') as mock_jsonify:

                mock_response = Mock()
                mock_jsonify.return_value = mock_response
                mock_response.status_code = 401

                # 调用函数
                result = test_function()

                # 验证返回了401错误
                mock_jsonify.assert_called_once()
                call_args = mock_jsonify.call_args[0][0]
                assert call_args['code'] == 401
                assert call_args['msg'] == "Invalid token"
