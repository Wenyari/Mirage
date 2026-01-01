"""
Pytest 全局配置和 Fixtures
提供测试所需的各种工具和环境
"""
import pytest
import bcrypt
from datetime import datetime
from app import create_app
from app.extensions import db, redis_client
from app.models import User, MembershipConfig, ModelPricing, Task, CDK, Transaction
from app.config import Config


class TestConfig(Config):
    """测试环境配置"""
    TESTING = True
    DEBUG = False

    # 使用内存数据库 (SQLite)
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    # SQLite in-memory 不支持某些 create_engine 参数，测试时使用空的 engine options
    SQLALCHEMY_ENGINE_OPTIONS = {}

    # 使用独立的 Redis 数据库
    REDIS_URL = 'redis://localhost:6379/15'

    # JWT 配置
    JWT_SECRET_KEY = 'test-secret-key'

    # 禁用 CSRF
    WTF_CSRF_ENABLED = False

    # 邮件配置 (测试模式不实际发送)
    MAIL_SUPPRESS_SEND = True
    MAIL_DEFAULT_SENDER = 'test@example.com'


@pytest.fixture(scope='session')
def app():
    """
    创建 Flask 应用 (会话级别)
    整个测试会话中只创建一次
    """
    app = create_app(TestConfig)

    # 创建应用上下文
    with app.app_context():
        yield app


@pytest.fixture(scope='function')
def client(app):
    """
    Flask 测试客户端 (函数级别)
    每个测试函数都会创建新的客户端
    """
    return app.test_client()


@pytest.fixture(scope='function')
def db_session(app):
    """
    数据库会话 (函数级别)
    每个测试函数都会创建新的数据库会话，测试完成后回滚
    """
    with app.app_context():
        # 创建所有表
        db.create_all()

        # 初始化基础数据
        _init_test_data()

        yield db

        # 测试完成后，删除所有表
        db.session.remove()
        db.drop_all()


@pytest.fixture(scope='function')
def redis_db(app):
    """
    Redis 数据库 (函数级别)
    每个测试函数完成后清空 Redis
    """
    with app.app_context():
        yield redis_client

        # 清空测试数据库（如果 Redis 未配置则跳过）
        try:
            if redis_client is not None:
        redis_client.flushdb()
        except Exception:
            # 忽略清理错误（测试环境可能没有 Redis）
            pass


def _init_test_data():
    """初始化测试数据"""
    # 创建会员等级配置
    configs = [
        MembershipConfig(level=1, name='T1', concurrency_limit=1, queue_priority=0),
        MembershipConfig(level=2, name='T2', concurrency_limit=2, queue_priority=5),
        MembershipConfig(level=3, name='T3', concurrency_limit=3, queue_priority=10),
        MembershipConfig(level=4, name='T4', concurrency_limit=4, queue_priority=15),
        MembershipConfig(level=5, name='T5', concurrency_limit=5, queue_priority=20),
    ]
    for config in configs:
        db.session.add(config)

    # 创建模型定价
    pricings = [
        ModelPricing(model_key='sora-v2', base_cost=100.00, is_active=1),
        ModelPricing(model_key='sora-turbo', base_cost=50.00, is_active=1),
    ]
    for pricing in pricings:
        db.session.add(pricing)

    db.session.commit()


@pytest.fixture
def test_user(db_session):
    """
    创建测试用户
    """
    password_hash = bcrypt.hashpw('password123'.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

    user = User(
        email='test@example.com',
        password_hash=password_hash,
        balance=1000.00,
        level=1,
        role='user',
        status=1
    )
    db_session.session.add(user)
    db_session.session.commit()

    return user


@pytest.fixture
def admin_user(db_session):
    """
    创建管理员用户
    """
    password_hash = bcrypt.hashpw('admin123'.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

    user = User(
        email='admin@example.com',
        password_hash=password_hash,
        balance=10000.00,
        level=5,
        role='admin',
        status=1
    )
    db_session.session.add(user)
    db_session.session.commit()

    return user


@pytest.fixture
def auth_headers(client, test_user):
    """
    获取认证 Header
    """
    from flask_jwt_extended import create_access_token

    token = create_access_token(identity=test_user.id)

    # 将 Token 存入 Redis (模拟单点登录)
    from app.extensions import redis_client
    auth_token_key = f"auth:token:{test_user.id}"
    redis_client.setex(auth_token_key, 604800, token)

    return {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json'
    }


@pytest.fixture
def admin_headers(client, admin_user):
    """
    获取管理员认证 Header
    """
    from flask_jwt_extended import create_access_token

    token = create_access_token(identity=admin_user.id)

    from app.extensions import redis_client
    auth_token_key = f"auth:token:{admin_user.id}"
    redis_client.setex(auth_token_key, 604800, token)

    return {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json'
    }


@pytest.fixture
def test_cdk(db_session):
    """
    创建测试 CDK
    """
    cdk = CDK(
        code='TEST-CDK-12345',
        points=500,
        type='once',
        batch_no='TEST-BATCH',
        status=0,
        expire_at=datetime(2030, 12, 31)
    )
    db_session.session.add(cdk)
    db_session.session.commit()

    return cdk


@pytest.fixture
def test_task(db_session, test_user):
    """
    创建测试任务
    """
    task = Task(
        user_id=test_user.id,
        model_name='sora-v2',
        prompt='Test prompt',
        params={'duration': 5},
        status='pending',
        cost_points=100.00
    )
    db_session.session.add(task)
    db_session.session.commit()

    return task


@pytest.fixture
def mock_redis(mocker):
    """
    Mock Redis 客户端
    """
    mock = mocker.MagicMock()
    mock.get.return_value = None
    mock.setex.return_value = True
    mock.delete.return_value = True
    return mock


@pytest.fixture
def mock_mail(mocker):
    """
    Mock 邮件发送
    """
    return mocker.patch('app.extensions.mail.send')
