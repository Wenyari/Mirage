"""
测试 pay_service.py 业务逻辑
包含优先扣除、CDK兑换、退款等功能测试
"""
import pytest
from decimal import Decimal
from datetime import datetime, timedelta
from app.services.pay_service import (
    check_and_deduct_balance,
    redeem_cdk,
    execute_refund
)
from app.models.user import User
from app.models.wallet import CDK, Transaction


class TestCheckAndDeductBalance:
    """测试积分扣除（优先扣除逻辑）"""

    def test_deduct_from_activity_only(self, db_session, test_user_with_activity_balance):
        """测试：只扣除活动积分（余额充足）"""
        user = test_user_with_activity_balance

        # 初始余额：recharge=100, activity=50
        assert user.recharge_balance == 100.00
        assert user.activity_balance == 50.00

        # 扣除 30 积分
        check_and_deduct_balance(user.id, 30.00, "test-task-1")

        # 刷新用户数据
        db_session.session.refresh(user)

        # 验证：只扣除活动积分
        assert user.recharge_balance == 100.00
        assert user.activity_balance == 20.00

        # 验证流水记录
        transactions = Transaction.query.filter_by(user_id=user.id).all()
        assert len(transactions) == 1
        assert transactions[0].type == 'task_cost'
        assert transactions[0].balance_type == 'activity'
        assert float(transactions[0].amount) == -30.00

    def test_deduct_from_both_balances(self, db_session, test_user_with_activity_balance):
        """测试：同时扣除两种积分（活动积分不足）"""
        user = test_user_with_activity_balance

        # 初始余额：recharge=100, activity=50
        assert user.recharge_balance == 100.00
        assert user.activity_balance == 50.00

        # 扣除 80 积分（活动积分只有50）
        check_and_deduct_balance(user.id, 80.00, "test-task-2")

        # 刷新用户数据
        db_session.session.refresh(user)

        # 验证：activity扣完，recharge扣30
        assert user.recharge_balance == 70.00
        assert user.activity_balance == 0.00

        # 验证流水记录（应该有2条）
        transactions = Transaction.query.filter_by(
            user_id=user.id,
            related_id="test-task-2"
        ).order_by(Transaction.id).all()

        assert len(transactions) == 2

        # 第一条：activity扣除50
        assert transactions[0].balance_type == 'activity'
        assert float(transactions[0].amount) == -50.00
        assert float(transactions[0].balance_snapshot) == 0.00

        # 第二条：recharge扣除30
        assert transactions[1].balance_type == 'recharge'
        assert float(transactions[1].amount) == -30.00
        assert float(transactions[1].balance_snapshot) == 70.00

    def test_deduct_from_recharge_only(self, db_session, test_user):
        """测试：只扣除充值积分（无活动积分）"""
        user = test_user

        # 初始余额：recharge=10000, activity=0
        assert user.recharge_balance == 10000.00
        assert user.activity_balance == 0.00

        # 扣除 100 积分
        check_and_deduct_balance(user.id, 100.00, "test-task-3")

        # 刷新用户数据
        db_session.session.refresh(user)

        # 验证：只扣除充值积分
        assert user.recharge_balance == 9900.00
        assert user.activity_balance == 0.00

        # 验证流水记录
        transactions = Transaction.query.filter_by(
            user_id=user.id,
            related_id="test-task-3"
        ).all()

        assert len(transactions) == 1
        assert transactions[0].balance_type == 'recharge'
        assert float(transactions[0].amount) == -100.00

    def test_insufficient_balance(self, db_session, test_user_with_activity_balance):
        """测试：余额不足抛出异常"""
        user = test_user_with_activity_balance

        # 初始总余额：150 (recharge=100, activity=50)
        with pytest.raises(ValueError) as exc_info:
            check_and_deduct_balance(user.id, 200.00, "test-task-4")

        assert "Insufficient balance" in str(exc_info.value)

        # 验证余额未变
        db_session.session.refresh(user)
        assert user.recharge_balance == 100.00
        assert user.activity_balance == 50.00

    def test_user_not_found(self, db_session):
        """测试：用户不存在"""
        with pytest.raises(ValueError) as exc_info:
            check_and_deduct_balance(99999, 10.00, "test-task-5")

        assert "User not found" in str(exc_info.value)


class TestRedeemCDK:
    """测试 CDK 兑换"""

    def test_redeem_success(self, db_session, test_user, test_cdk):
        """测试：成功兑换 CDK"""
        user = test_user
        cdk = test_cdk

        # 初始余额
        initial_balance = user.recharge_balance

        # 兑换
        result = redeem_cdk(user.id, cdk.code)

        # 验证返回结果
        assert result['added_points'] == 500
        assert result['current_balance'] == float(initial_balance + 500)

        # 验证用户余额增加（充值到 recharge_balance）
        db_session.session.refresh(user)
        assert user.recharge_balance == initial_balance + 500
        assert user.activity_balance == 0.00

        # 验证 CDK 状态
        db_session.session.refresh(cdk)
        assert cdk.status == 1
        assert cdk.used_by == user.id
        assert cdk.used_at is not None

        # 验证流水记录
        transaction = Transaction.query.filter_by(
            user_id=user.id,
            type='recharge'
        ).first()

        assert transaction is not None
        assert transaction.balance_type == 'recharge'
        assert float(transaction.amount) == 500.00

    def test_redeem_invalid_code(self, db_session, test_user):
        """测试：无效的 CDK 代码"""
        with pytest.raises(ValueError) as exc_info:
            redeem_cdk(test_user.id, "INVALID-CODE")

        assert "Invalid CDK code" in str(exc_info.value)

    def test_redeem_already_used(self, db_session, test_user, test_cdk):
        """测试：CDK 已被使用"""
        cdk = test_cdk

        # 第一次兑换
        redeem_cdk(test_user.id, cdk.code)

        # 第二次兑换（应该失败）
        with pytest.raises(ValueError) as exc_info:
            redeem_cdk(test_user.id, cdk.code)

        assert "already been used" in str(exc_info.value)

    def test_redeem_expired(self, db_session, test_user):
        """测试：CDK 已过期"""
        # 创建过期的 CDK
        expired_cdk = CDK(
            code='EXPIRED-CDK',
            points=100,
            type='once',
            status=0,
            expire_at=datetime.now() - timedelta(days=1)
        )
        db_session.session.add(expired_cdk)
        db_session.session.commit()

        with pytest.raises(ValueError) as exc_info:
            redeem_cdk(test_user.id, expired_cdk.code)

        assert "expired" in str(exc_info.value)

    def test_redeem_universal_cdk(self, db_session, test_user):
        """测试：通用 CDK（可重复使用）"""
        # 创建通用 CDK
        universal_cdk = CDK(
            code='UNIVERSAL-CDK',
            points=50,
            type='universal',
            status=0
        )
        db_session.session.add(universal_cdk)
        db_session.session.commit()

        # 第一次兑换
        result1 = redeem_cdk(test_user.id, universal_cdk.code)
        assert result1['added_points'] == 50

        # 验证 CDK 状态未改变（通用码不标记为已使用）
        db_session.session.refresh(universal_cdk)
        assert universal_cdk.status == 0

        # 第二次兑换（应该成功）
        result2 = redeem_cdk(test_user.id, universal_cdk.code)
        assert result2['added_points'] == 50

    def test_redeem_with_level_grant(self, db_session):
        """测试：CDK 授予会员等级"""
        # 创建低等级用户
        user = User(
            email='lowlevel@example.com',
            password_hash='hash',
            recharge_balance=0.00,
            activity_balance=0.00,
            level=1,
            role='user',
            status=1
        )
        db_session.session.add(user)

        # 创建带等级授予的 CDK
        cdk = CDK(
            code='LEVEL-CDK',
            points=100,
            type='once',
            status=0,
            grant_level=3
        )
        db_session.session.add(cdk)
        db_session.session.commit()

        # 兑换
        result = redeem_cdk(user.id, cdk.code)

        # 验证等级升级
        db_session.session.refresh(user)
        assert user.level == 3
        assert result.get('upgraded_to') == 3


class TestExecuteRefund:
    """测试退款功能"""

    def test_refund_success(self, db_session, test_user):
        """测试：成功退款"""
        user = test_user
        initial_balance = user.recharge_balance

        # 执行退款
        execute_refund(user.id, 100.00, "test-task-6", "Task failed")

        # 验证余额增加（退到 recharge_balance）
        db_session.session.refresh(user)
        assert user.recharge_balance == initial_balance + 100

        # 验证流水记录
        transaction = Transaction.query.filter_by(
            user_id=user.id,
            type='refund'
        ).first()

        assert transaction is not None
        assert transaction.balance_type == 'recharge'
        assert float(transaction.amount) == 100.00
        assert transaction.related_id == "test-task-6"
        assert "Task failed" in transaction.remark

    def test_refund_user_not_found(self, db_session):
        """测试：用户不存在时不抛出异常"""
        # 退款不应该抛出异常（在日志中记录错误）
        execute_refund(99999, 100.00, "test-task-7", "Test")

        # 验证没有流水记录
        transaction = Transaction.query.filter_by(
            related_id="test-task-7"
        ).first()
        assert transaction is None


class TestConcurrency:
    """测试并发安全（悲观锁）"""

    def test_concurrent_deduct(self, db_session, test_user_with_activity_balance):
        """
        测试并发扣除（简单模拟）
        实际并发测试需要多线程，这里只验证悲观锁不会报错
        """
        user = test_user_with_activity_balance

        # 模拟两次扣除
        check_and_deduct_balance(user.id, 20.00, "task-1")
        check_and_deduct_balance(user.id, 20.00, "task-2")

        # 验证余额正确
        db_session.session.refresh(user)
        assert user.activity_balance == 10.00

        # 验证流水记录数量
        transactions = Transaction.query.filter_by(user_id=user.id).all()
        assert len(transactions) == 2
