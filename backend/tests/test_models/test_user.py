"""
用户模型测试
"""
import pytest
import bcrypt
from app.models import User, MembershipConfig


@pytest.mark.unit
class TestUserModel:
    """用户模型测试类"""

    def test_create_user(self, db_session):
        """测试创建用户"""
        password_hash = bcrypt.hashpw('password'.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

        user = User(
            email='newuser@example.com',
            password_hash=password_hash,
            balance=100.00,
            level=1,
            role='user',
            status=1
        )

        db_session.session.add(user)
        db_session.session.commit()

        assert user.id is not None
        assert user.email == 'newuser@example.com'
        assert user.balance == 100.00
        assert user.level == 1
        assert user.role == 'user'
        assert user.status == 1

    def test_user_email_unique(self, db_session, test_user):
        """测试邮箱唯一性约束"""
        password_hash = bcrypt.hashpw('password'.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

        duplicate_user = User(
            email=test_user.email,  # 重复邮箱
            password_hash=password_hash,
            balance=0.00,
            level=1
        )

        db_session.session.add(duplicate_user)

        with pytest.raises(Exception):  # 应该抛出唯一性约束异常
            db_session.session.commit()

    def test_user_to_dict(self, test_user):
        """测试用户转字典方法"""
        user_dict = test_user.to_dict()

        assert isinstance(user_dict, dict)
        assert user_dict['id'] == test_user.id
        assert user_dict['email'] == test_user.email
        assert user_dict['balance'] == float(test_user.balance)
        assert user_dict['level'] == test_user.level
        assert user_dict['vip_desc'] == f'T{test_user.level}'
        assert 'password_hash' not in user_dict  # 密码不应该在字典中

    def test_user_relationships(self, db_session, test_user):
        """测试用户关系映射"""
        from app.models import Task, Transaction

        # 创建任务
        task = Task(
            user_id=test_user.id,
            model_name='sora-v2',
            prompt='test',
            status='pending',
            cost_points=100.00
        )
        db_session.session.add(task)

        # 创建流水
        transaction = Transaction(
            user_id=test_user.id,
            type='recharge',
            amount=100.00,
            balance_snapshot=1100.00
        )
        db_session.session.add(transaction)
        db_session.session.commit()

        # 测试关系
        assert test_user.tasks.count() == 1
        assert test_user.transactions.count() == 1


@pytest.mark.unit
class TestMembershipConfigModel:
    """会员配置模型测试类"""

    def test_membership_config_exists(self, db_session):
        """测试会员配置初始化"""
        configs = MembershipConfig.query.all()

        assert len(configs) == 5  # T1-T5

        # 检查 T1
        t1 = MembershipConfig.query.filter_by(level=1).first()
        assert t1 is not None
        assert t1.name == 'T1'
        assert t1.concurrency_limit == 1

        # 检查 T5
        t5 = MembershipConfig.query.filter_by(level=5).first()
        assert t5 is not None
        assert t5.name == 'T5'
        assert t5.concurrency_limit == 5
        assert t5.queue_priority == 20

    def test_membership_config_to_dict(self, db_session):
        """测试会员配置转字典方法"""
        config = MembershipConfig.query.filter_by(level=3).first()
        config_dict = config.to_dict()

        assert isinstance(config_dict, dict)
        assert config_dict['level'] == 3
        assert config_dict['name'] == 'T3'
        assert config_dict['concurrency_limit'] == 3
        assert config_dict['queue_priority'] == 10
