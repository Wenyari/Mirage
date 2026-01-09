"""
Pytest 全局配置和 Fixtures - 业务逻辑测试专用
仅包含业务逻辑测试所需的配置，不包含接口测试相关内容
"""
import pytest
import bcrypt
from datetime import datetime
from app import create_app
from app.extensions import db, redis_client
from app.models import User, MembershipConfig, Task, CDK, Model, ModelConfig
from app.models.activity import Activity, ActivityClaim, CheckinConfig
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
        # 先移除现有会话
        db.session.remove()

        # 删除所有表（如果存在）
        db.drop_all()

        # 重新创建所有表
        db.create_all()

        # 初始化基础数据
        _init_test_data()

        yield db

        # 测试完成后，回滚事务并删除所有表
        db.session.rollback()
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
        Model(key='sora-2', name='Sora-2', enabled=1),
    ]
    for model in models:
        db.session.add(model)

    # 创建模型配置
    model_configs = [
        ModelConfig(
            model='openai',
            allowed_tiers=['T1', 'T2', 'T3', 'T4', 'T5'],
            cost_per_call=10.00,
            is_active=1
        ),
        ModelConfig(
            model='sora',
            allowed_tiers=['T3', 'T4', 'T5'],
            cost_per_call=100.00,
            is_active=1
        ),
        ModelConfig(
            model='sora-2',
            allowed_tiers=['T3', 'T4', 'T5'],
            cost_per_call=100.00,
            is_active=1
        ),
    ]
    for config in model_configs:
        db.session.add(config)

    # 创建签到配置（1-7天）
    checkin_configs = [
        CheckinConfig(day=1, points=10.00, is_active=1),
        CheckinConfig(day=2, points=15.00, is_active=1),
        CheckinConfig(day=3, points=20.00, is_active=1),
        CheckinConfig(day=4, points=25.00, is_active=1),
        CheckinConfig(day=5, points=30.00, is_active=1),
        CheckinConfig(day=6, points=40.00, is_active=1),
        CheckinConfig(day=7, points=50.00, is_active=1),
    ]
    for config in checkin_configs:
        db.session.add(config)

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
        recharge_balance=10000.00,  # 充值积分
        activity_balance=0.00,  # 活动积分
        level=3,  # 提升到 T3，可以使用 sora-2
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
        recharge_balance=10000.00,  # 充值积分
        activity_balance=0.00,  # 活动积分
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


@pytest.fixture
def test_activity(db_session):
    """
    创建测试活动 - 用于业务逻辑测试
    """
    activity = Activity(
        code='TEST-ACTIVITY',
        name='测试活动',
        description='这是一个测试活动',
        points=100.00,
        expire_days=30,
        max_claims_per_user=1,
        required_level=1,
        start_at=datetime(2024, 1, 1),
        end_at=datetime(2030, 12, 31),
        status='active'
    )
    db_session.session.add(activity)
    db_session.session.commit()

    return activity


@pytest.fixture
def test_user_with_activity_balance(db_session):
    """
    创建有活动积分的测试用户
    """
    password_hash = bcrypt.hashpw('password123'.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

    user = User(
        email='activity_user@example.com',
        password_hash=password_hash,
        recharge_balance=100.00,
        activity_balance=50.00,  # 有活动积分
        level=3,
        role='user',
        status=1
    )
    db_session.session.add(user)
    db_session.session.commit()

    return user
