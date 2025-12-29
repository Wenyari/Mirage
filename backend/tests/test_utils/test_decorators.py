"""
装饰器工具测试
"""
import pytest
from flask import Flask
from flask_jwt_extended import create_access_token
from app.utils.decorators import login_required, admin_required, rate_limit


@pytest.mark.unit
class TestDecorators:
    """装饰器测试类"""

    def test_login_required_valid_token(self, app, client, db_session, redis_db, test_user):
        """测试登录检查装饰器 - 有效 Token"""
        with app.app_context():
            # 创建测试路由
            @app.route('/test_login')
            @login_required
            def test_route():
                from flask import jsonify
                return jsonify({"success": True})

            # 创建 Token
            token = create_access_token(identity=test_user.id)
            redis_db.setex(f"auth:token:{test_user.id}", 3600, token)

            # 发送请求
            response = client.get(
                '/test_login',
                headers={'Authorization': f'Bearer {token}'}
            )

            assert response.status_code == 200

    def test_login_required_no_token(self, app, client, db_session):
        """测试登录检查装饰器 - 无 Token"""
        with app.app_context():
            @app.route('/test_no_token')
            @login_required
            def test_route():
                from flask import jsonify
                return jsonify({"success": True})

            response = client.get('/test_no_token')

            assert response.status_code == 401

    def test_login_required_invalid_token(self, app, client, db_session, redis_db, test_user):
        """测试登录检查装饰器 - Token 不匹配（被顶号）"""
        with app.app_context():
            @app.route('/test_invalid_token')
            @login_required
            def test_route():
                from flask import jsonify
                return jsonify({"success": True})

            # 创建旧 Token
            old_token = create_access_token(identity=test_user.id)

            # 存入新 Token (模拟被顶号)
            new_token = create_access_token(identity=test_user.id)
            redis_db.setex(f"auth:token:{test_user.id}", 3600, new_token)

            # 使用旧 Token 请求
            response = client.get(
                '/test_invalid_token',
                headers={'Authorization': f'Bearer {old_token}'}
            )

            assert response.status_code == 401

    def test_admin_required_success(self, app, client, db_session, admin_user):
        """测试管理员权限装饰器 - 成功"""
        with app.app_context():
            from flask_jwt_extended import jwt_required

            @app.route('/test_admin')
            @jwt_required()
            @admin_required
            def test_route():
                from flask import jsonify
                return jsonify({"success": True})

            token = create_access_token(identity=admin_user.id)

            response = client.get(
                '/test_admin',
                headers={'Authorization': f'Bearer {token}'}
            )

            assert response.status_code == 200

    def test_admin_required_not_admin(self, app, client, db_session, test_user):
        """测试管理员权限装饰器 - 非管理员"""
        with app.app_context():
            from flask_jwt_extended import jwt_required

            @app.route('/test_not_admin')
            @jwt_required()
            @admin_required
            def test_route():
                from flask import jsonify
                return jsonify({"success": True})

            token = create_access_token(identity=test_user.id)

            response = client.get(
                '/test_not_admin',
                headers={'Authorization': f'Bearer {token}'}
            )

            assert response.status_code == 403

    def test_rate_limit_decorator(self, app, client, redis_db):
        """测试限流装饰器"""
        with app.app_context():
            @app.route('/test_rate_limit')
            @rate_limit(limit=3, period=60)
            def test_route():
                from flask import jsonify
                return jsonify({"success": True})

            # 前 3 次请求应该成功
            for i in range(3):
                response = client.get('/test_rate_limit')
                assert response.status_code == 200

            # 第 4 次请求应该被限流
            response = client.get('/test_rate_limit')
            assert response.status_code == 429
