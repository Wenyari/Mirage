"""
钱包模型测试
"""
import pytest
from datetime import datetime
from app.models import CDK, Transaction


@pytest.mark.unit
class TestCDKModel:
    """CDK 模型测试类"""

    def test_create_cdk(self, db_session):
        """测试创建 CDK"""
        cdk = CDK(
            code='NEW-CDK-12345',
            points=1000,
            type='once',
            batch_no='BATCH-001',
            status=0,
            expire_at=datetime(2025, 12, 31)
        )

        db_session.session.add(cdk)
        db_session.session.commit()

        assert cdk.id is not None
        assert cdk.code == 'NEW-CDK-12345'
        assert cdk.points == 1000
        assert cdk.type == 'once'
        assert cdk.status == 0

    def test_cdk_code_unique(self, db_session, test_cdk):
        """测试 CDK 码唯一性约束"""
        duplicate_cdk = CDK(
            code=test_cdk.code,  # 重复的 CDK 码
            points=500,
            type='once',
            status=0
        )

        db_session.session.add(duplicate_cdk)

        with pytest.raises(Exception):  # 应该抛出唯一性约束异常
            db_session.session.commit()

    def test_cdk_status_change(self, db_session, test_user, test_cdk):
        """测试 CDK 状态变更"""
        assert test_cdk.status == 0
        assert test_cdk.used_by is None

        # 标记为已使用
        test_cdk.status = 1
        test_cdk.used_by = test_user.id
        test_cdk.used_at = datetime.now(ZoneInfo("Asia/Shanghai"))
        db_session.session.commit()

        assert test_cdk.status == 1
        assert test_cdk.used_by == test_user.id
        assert test_cdk.used_at is not None

    def test_cdk_to_dict(self, test_cdk):
        """测试 CDK 转字典方法"""
        cdk_dict = test_cdk.to_dict()

        assert isinstance(cdk_dict, dict)
        assert cdk_dict['code'] == test_cdk.code
        assert cdk_dict['points'] == test_cdk.points
        assert cdk_dict['type'] == test_cdk.type
        assert cdk_dict['status'] == test_cdk.status


@pytest.mark.unit
class TestTransactionModel:
    """交易流水模型测试类"""

    def test_create_transaction(self, db_session, test_user):
        """测试创建流水"""
        transaction = Transaction(
            user_id=test_user.id,
            type='recharge',
            amount=500.00,
            balance_snapshot=1500.00,
            related_id='CDK-123',
            remark='CDK recharge'
        )

        db_session.session.add(transaction)
        db_session.session.commit()

        assert transaction.id is not None
        assert transaction.user_id == test_user.id
        assert transaction.type == 'recharge'
        assert transaction.amount == 500.00
        assert transaction.balance_snapshot == 1500.00

    def test_transaction_types(self, db_session, test_user):
        """测试不同类型的流水"""
        types = ['recharge', 'task_cost', 'refund', 'system']

        for trans_type in types:
            transaction = Transaction(
                user_id=test_user.id,
                type=trans_type,
                amount=100.00,
                balance_snapshot=1000.00
            )
            db_session.session.add(transaction)
            db_session.session.commit()

            assert transaction.type == trans_type

    def test_transaction_to_dict(self, db_session, test_user):
        """测试流水转字典方法"""
        transaction = Transaction(
            user_id=test_user.id,
            type='task_cost',
            amount=-100.00,
            balance_snapshot=900.00,
            related_id='TASK-123',
            remark='Task generation cost'
        )
        db_session.session.add(transaction)
        db_session.session.commit()

        trans_dict = transaction.to_dict()

        assert isinstance(trans_dict, dict)
        assert trans_dict['user_id'] == test_user.id
        assert trans_dict['type'] == 'task_cost'
        assert trans_dict['amount'] == -100.00
        assert trans_dict['balance_snapshot'] == 900.00
        assert trans_dict['related_id'] == 'TASK-123'
