"""
Pytest 全局配置和 Fixtures - 业务逻辑测试专用
仅包含业务逻辑测试所需的配置，不包含接口测试相关内容
"""
import pytest
import bcrypt
from datetime import datetime
from app import create_app
from app.extensions import db, redis_client
from app.models import User, MembershipConfig, Task, CDK, Model
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
def db_session(app):
    """
    数据库会话 (函数级别)
    每个测试函数都会创建新的数据库会话，测试完成后回滚
    """
    with app.app_context():
        # 删除所有表（如果存在）
        db.drop_all()

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
        MembershipConfig(level=1, name='T1', concurrent_limit=1, queue_weight=1),
        MembershipConfig(level=2, name='T2', concurrent_limit=2, queue_weight=2),
        MembershipConfig(level=3, name='T3', concurrent_limit=3, queue_weight=3),
        MembershipConfig(level=4, name='T4', concurrent_limit=4, queue_weight=4),
        MembershipConfig(level=5, name='T5', concurrent_limit=5, queue_weight=5),
    ]
    for config in configs:
        db.session.add(config)

    # 创建模型
    models = [
        Model(key='openai', name='OpenAI', enabled=1),
        Model(key='sora', name='Sora', enabled=1),
    ]
    for model in models:
        db.session.add(model)

    db.session.commit()


@pytest.fixture
def test_user(db_session):
    """
    创建测试用户 - 用于业务逻辑测试
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
    创建管理员用户 - 用于业务逻辑测试
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
def test_cdk(db_session):
    """
    创建测试 CDK - 用于业务逻辑测试
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
    创建测试任务 - 用于业务逻辑测试
    """
    task = Task(
        user_id=test_user.id,
        model='openai',
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
    Mock Redis 客户端 - 用于不依赖 Redis 的单元测试
    """
    mock = mocker.MagicMock()
    mock.get.return_value = None
    mock.setex.return_value = True
    mock.delete.return_value = True
    return mock


@pytest.fixture
def mock_mail(mocker):
    """
    Mock 邮件发送 - 避免实际发送邮件
    """
    return mocker.patch('app.extensions.mail.send')
