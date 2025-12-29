"""
支付服务测试
"""
import pytest
from datetime import datetime, timedelta
from app.services.pay_service import (
    redeem_cdk,
    check_and_deduct_balance,
    execute_refund
)
from app.models import CDK, Transaction


@pytest.mark.unit
class TestPayService:
    """支付服务测试类"""

    def test_redeem_cdk_success(self, app, db_session, test_user, test_cdk):
        """测试 CDK 兑换成功"""
        with app.app_context():
            original_balance = test_user.balance

            result = redeem_cdk(test_user.id, test_cdk.code)

            assert result['added_points'] == test_cdk.points
            assert result['current_balance'] == float(original_balance + test_cdk.points)

            # 验证 CDK 状态更新
            db_session.session.refresh(test_cdk)
            assert test_cdk.status == 1
            assert test_cdk.used_by == test_user.id
            assert test_cdk.used_at is not None

            # 验证用户余额更新
            db_session.session.refresh(test_user)
            assert test_user.balance == original_balance + test_cdk.points

            # 验证流水记录
            transaction = Transaction.query.filter_by(
                user_id=test_user.id,
                type='recharge'
            ).first()
            assert transaction is not None
            assert transaction.amount == test_cdk.points

    def test_redeem_cdk_invalid_code(self, app, db_session, test_user):
        """测试无效的 CDK"""
        with app.app_context():
            with pytest.raises(ValueError, match="Invalid CDK code"):
                redeem_cdk(test_user.id, 'INVALID-CODE')

    def test_redeem_cdk_already_used(self, app, db_session, test_user, test_cdk):
        """测试 CDK 已使用"""
        with app.app_context():
            # 先使用一次
            test_cdk.status = 1
            test_cdk.used_by = test_user.id
            db_session.session.commit()

            # 再次尝试使用
            with pytest.raises(ValueError, match="CDK has already been used"):
                redeem_cdk(test_user.id, test_cdk.code)

    def test_redeem_cdk_expired(self, app, db_session, test_user, test_cdk):
        """测试 CDK 已过期"""
        with app.app_context():
            # 设置为已过期
            test_cdk.expire_at = datetime.utcnow() - timedelta(days=1)
            db_session.session.commit()

            with pytest.raises(ValueError, match="CDK has expired"):
                redeem_cdk(test_user.id, test_cdk.code)

    def test_redeem_cdk_universal_type(self, app, db_session, test_user):
        """测试通用类型 CDK（可重复使用）"""
        with app.app_context():
            # 创建通用 CDK
            universal_cdk = CDK(
                code='UNIVERSAL-CDK',
                points=100,
                type='universal',
                status=0
            )
            db_session.session.add(universal_cdk)
            db_session.session.commit()

            # 第一次使用
            redeem_cdk(test_user.id, universal_cdk.code)

            # 通用 CDK 状态不应该变为已使用
            db_session.session.refresh(universal_cdk)
            assert universal_cdk.status == 0

            # 可以再次使用
            redeem_cdk(test_user.id, universal_cdk.code)

    def test_check_and_deduct_balance_success(self, app, db_session, test_user):
        """测试扣除余额成功"""
        with app.app_context():
            original_balance = test_user.balance
            amount = 100.00
            task_id = 'TEST-TASK-123'

            check_and_deduct_balance(test_user.id, amount, task_id)

            # 验证余额扣除
            db_session.session.refresh(test_user)
            assert test_user.balance == original_balance - amount

            # 验证流水记录
            transaction = Transaction.query.filter_by(
                user_id=test_user.id,
                type='task_cost',
                related_id=task_id
            ).first()
            assert transaction is not None
            assert transaction.amount == -amount

    def test_check_and_deduct_balance_insufficient(self, app, db_session, test_user):
        """测试余额不足"""
        with app.app_context():
            # 设置余额为 50
            test_user.balance = 50.00
            db_session.session.commit()

            # 尝试扣除 100
            with pytest.raises(ValueError, match="Insufficient balance"):
                check_and_deduct_balance(test_user.id, 100.00, 'TEST-TASK')

    def test_execute_refund_success(self, app, db_session, test_user):
        """测试退款成功"""
        with app.app_context():
            original_balance = test_user.balance
            refund_amount = 50.00
            task_id = 'TEST-TASK-123'

            execute_refund(test_user.id, refund_amount, task_id, "Task failed")

            # 验证余额增加
            db_session.session.refresh(test_user)
            assert test_user.balance == original_balance + refund_amount

            # 验证流水记录
            transaction = Transaction.query.filter_by(
                user_id=test_user.id,
                type='refund',
                related_id=task_id
            ).first()
            assert transaction is not None
            assert transaction.amount == refund_amount
            assert 'Task failed' in transaction.remark

    def test_execute_refund_user_not_found(self, app, db_session):
        """测试退款时用户不存在（不应抛出异常）"""
        with app.app_context():
            # 不应该抛出异常
            execute_refund(99999, 100.00, 'TEST-TASK', 'Reason')
