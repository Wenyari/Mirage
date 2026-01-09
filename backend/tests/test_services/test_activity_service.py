"""
测试 activity_service.py 业务逻辑
包含活动领取、签到、过期处理等功能测试
"""
import pytest
from datetime import datetime, timedelta
from app.services.activity_service import (
    claim_activity,
    daily_checkin,
    expire_activity_points,
    get_checkin_status,
    get_active_activities,
    get_user_activities
)
from app.models.user import User
from app.models.wallet import Transaction
from app.models.activity import Activity, ActivityClaim, CheckinConfig


class TestClaimActivity:
    """测试活动领取"""

    def test_claim_success(self, db_session, test_user, test_activity):
        """测试：成功领取活动"""
        user = test_user
        activity = test_activity

        # 初始余额
        initial_activity_balance = user.activity_balance

        # 领取活动
        result = claim_activity(user.id, activity.code)

        # 验证返回结果
        assert result['points'] == 100.00
        assert result['expire_at'] is not None
        assert result['current_activity_balance'] == float(initial_activity_balance + 100)

        # 验证用户余额增加
        db_session.session.refresh(user)
        assert user.activity_balance == initial_activity_balance + 100

        # 验证领取记录
        claim = ActivityClaim.query.filter_by(
            user_id=user.id,
            activity_id=activity.id
        ).first()

        assert claim is not None
        assert claim.status == 'active'
        assert float(claim.points_granted) == 100.00

        # 验证流水记录
        transaction = Transaction.query.filter_by(
            user_id=user.id,
            type='activity_grant'
        ).first()

        assert transaction is not None
        assert transaction.balance_type == 'activity'
        assert float(transaction.amount) == 100.00

    def test_claim_activity_not_found(self, db_session, test_user):
        """测试：活动不存在"""
        with pytest.raises(ValueError) as exc_info:
            claim_activity(test_user.id, "NON-EXISTENT")

        assert "Activity not found" in str(exc_info.value)

    def test_claim_limit_reached(self, db_session, test_user, test_activity):
        """测试：达到领取上限"""
        user = test_user
        activity = test_activity

        # 第一次领取（应该成功）
        result1 = claim_activity(user.id, activity.code)
        assert result1['points'] == 100.00

        # 第二次领取（应该失败，max_claims_per_user=1）
        with pytest.raises(ValueError) as exc_info:
            claim_activity(user.id, activity.code)

        assert "Claim limit reached" in str(exc_info.value)

    def test_claim_level_requirement(self, db_session):
        """测试：等级要求"""
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

        # 创建需要T3等级的活动
        activity = Activity(
            code='HIGH-LEVEL-ACTIVITY',
            name='高等级活动',
            points=200.00,
            required_level=3,
            max_claims_per_user=1,
            status='active'
        )
        db_session.session.add(activity)
        db_session.session.commit()

        # 尝试领取（应该失败）
        with pytest.raises(ValueError) as exc_info:
            claim_activity(user.id, activity.code)

        assert "Requires level" in str(exc_info.value)

    def test_claim_activity_paused(self, db_session, test_user):
        """测试：活动已暂停"""
        activity = Activity(
            code='PAUSED-ACTIVITY',
            name='暂停的活动',
            points=50.00,
            status='paused'
        )
        db_session.session.add(activity)
        db_session.session.commit()

        with pytest.raises(ValueError) as exc_info:
            claim_activity(test_user.id, activity.code)

        assert "paused" in str(exc_info.value)

    def test_claim_activity_not_started(self, db_session, test_user):
        """测试：活动未开始"""
        activity = Activity(
            code='FUTURE-ACTIVITY',
            name='未来的活动',
            points=50.00,
            start_at=datetime.now() + timedelta(days=1),
            status='active'
        )
        db_session.session.add(activity)
        db_session.session.commit()

        with pytest.raises(ValueError) as exc_info:
            claim_activity(test_user.id, activity.code)

        assert "has not started" in str(exc_info.value)

    def test_claim_activity_ended(self, db_session, test_user):
        """测试：活动已结束"""
        activity = Activity(
            code='PAST-ACTIVITY',
            name='过去的活动',
            points=50.00,
            end_at=datetime.now() - timedelta(days=1),
            status='active'
        )
        db_session.session.add(activity)
        db_session.session.commit()

        with pytest.raises(ValueError) as exc_info:
            claim_activity(test_user.id, activity.code)

        assert "has ended" in str(exc_info.value)


class TestDailyCheckin:
    """测试每日签到"""

    def test_first_checkin(self, db_session, test_user):
        """测试：首次签到"""
        user = test_user

        # 首次签到
        result = daily_checkin(user.id)

        # 验证返回结果
        assert result['points'] == 10.00  # 第1天奖励
        assert result['consecutive_days'] == 1
        assert result['total_checkin_days'] == 1

        # 验证用户数据
        db_session.session.refresh(user)
        assert user.activity_balance == 10.00
        assert user.total_checkin_days == 1
        assert user.last_checkin_at is not None

    def test_consecutive_checkin(self, db_session, test_user):
        """测试：连续签到"""
        user = test_user

        # 第一天签到
        user.last_checkin_at = datetime.now() - timedelta(days=1)
        user.total_checkin_days = 1
        db_session.session.commit()

        # 第二天签到
        result = daily_checkin(user.id)

        # 验证返回结果
        assert result['points'] == 15.00  # 第2天奖励
        assert result['consecutive_days'] == 2
        assert result['total_checkin_days'] == 2

    def test_checkin_cycle(self, db_session, test_user):
        """测试：签到循环（1-7天）"""
        user = test_user

        # 模拟第6天签到
        user.last_checkin_at = datetime.now() - timedelta(days=1)
        user.total_checkin_days = 6
        db_session.session.commit()

        # 第7天签到
        result = daily_checkin(user.id)
        assert result['consecutive_days'] == 7
        assert result['points'] == 50.00  # 第7天奖励

        # 模拟第7天后再签到（应该重置为第1天）
        db_session.session.refresh(user)
        user.last_checkin_at = datetime.now() - timedelta(days=1)
        db_session.session.commit()

        result2 = daily_checkin(user.id)
        assert result2['consecutive_days'] == 1
        assert result2['points'] == 10.00  # 循环回第1天

    def test_broken_checkin_streak(self, db_session, test_user):
        """测试：断签"""
        user = test_user

        # 模拟3天前签到过
        user.last_checkin_at = datetime.now() - timedelta(days=3)
        user.total_checkin_days = 5
        db_session.session.commit()

        # 今天签到（应该重置为第1天）
        result = daily_checkin(user.id)

        assert result['consecutive_days'] == 1
        assert result['points'] == 10.00
        assert result['total_checkin_days'] == 6  # 累计天数仍然增加

    def test_duplicate_checkin(self, db_session, test_user):
        """测试：今天已签到"""
        user = test_user

        # 第一次签到
        daily_checkin(user.id)

        # 第二次签到（应该失败）
        with pytest.raises(ValueError) as exc_info:
            daily_checkin(user.id)

        assert "Already checked in today" in str(exc_info.value)

    def test_checkin_flow_record(self, db_session, test_user):
        """测试：签到流水记录"""
        user = test_user

        # 签到
        daily_checkin(user.id)

        # 验证流水记录
        transaction = Transaction.query.filter_by(
            user_id=user.id,
            type='checkin'
        ).first()

        assert transaction is not None
        assert transaction.balance_type == 'activity'
        assert float(transaction.amount) == 10.00


class TestGetCheckinStatus:
    """测试获取签到状态"""

    def test_never_checked_in(self, db_session, test_user):
        """测试：从未签到过"""
        result = get_checkin_status(test_user.id)

        assert result['has_checked_today'] is False
        assert result['consecutive_days'] == 0
        assert result['total_checkin_days'] == 0
        assert result['last_checkin_at'] is None
        assert result['next_reward'] == 10.00  # 第1天奖励

    def test_checked_in_today(self, db_session, test_user):
        """测试：今天已签到"""
        user = test_user

        # 签到
        daily_checkin(user.id)

        # 获取状态
        result = get_checkin_status(user.id)

        assert result['has_checked_today'] is True
        assert result['consecutive_days'] == 1
        assert result['total_checkin_days'] == 1

    def test_consecutive_status(self, db_session, test_user):
        """测试：连续签到状态"""
        user = test_user

        # 模拟昨天签到过
        user.last_checkin_at = datetime.now() - timedelta(days=1)
        user.total_checkin_days = 3
        db_session.session.commit()

        result = get_checkin_status(user.id)

        assert result['has_checked_today'] is False
        assert result['consecutive_days'] == 3
        assert result['next_reward'] == 25.00  # 第4天奖励


class TestExpireActivityPoints:
    """测试活动积分过期"""

    def test_expire_single_claim(self, db_session, test_user, test_activity):
        """测试：单个积分过期"""
        user = test_user
        activity = test_activity

        # 先领取活动
        claim_activity(user.id, activity.code)

        # 验证余额增加
        db_session.session.refresh(user)
        assert user.activity_balance == 100.00

        # 手动设置过期时间（过去时间）
        claim = ActivityClaim.query.filter_by(user_id=user.id).first()
        claim.expire_at = datetime.now() - timedelta(days=1)
        db_session.session.commit()

        # 执行过期处理
        result = expire_activity_points()

        # 验证结果
        assert result['expired_count'] == 1
        assert result['total_points_expired'] == 100.00

        # 验证余额扣除
        db_session.session.refresh(user)
        assert user.activity_balance == 0.00

        # 验证领取记录状态
        db_session.session.refresh(claim)
        assert claim.status == 'expired'
        assert claim.expired_at is not None

        # 验证流水记录
        transaction = Transaction.query.filter_by(
            user_id=user.id,
            type='activity_expire'
        ).first()

        assert transaction is not None
        assert float(transaction.amount) == -100.00

    def test_expire_partial_balance(self, db_session, test_user, test_activity):
        """测试：积分过期但余额不足（部分扣除）"""
        user = test_user
        activity = test_activity

        # 领取活动（获得100积分）
        claim_activity(user.id, activity.code)

        # 手动减少余额（模拟已经使用了一部分）
        user.activity_balance = 30.00
        db_session.session.commit()

        # 设置过期时间
        claim = ActivityClaim.query.filter_by(user_id=user.id).first()
        claim.expire_at = datetime.now() - timedelta(days=1)
        db_session.session.commit()

        # 执行过期处理
        result = expire_activity_points()

        # 验证只扣除了30（当前余额）
        assert result['total_points_expired'] == 30.00

        db_session.session.refresh(user)
        assert user.activity_balance == 0.00

    def test_no_expired_claims(self, db_session):
        """测试：没有过期积分"""
        result = expire_activity_points()

        assert result['expired_count'] == 0
        assert result['total_points_expired'] == 0.00

    def test_permanent_points_not_expired(self, db_session, test_user):
        """测试：永久积分不过期"""
        # 创建无过期时间的活动
        activity = Activity(
            code='PERMANENT',
            name='永久活动',
            points=50.00,
            expire_days=None,  # 永久
            max_claims_per_user=1,
            status='active'
        )
        db_session.session.add(activity)
        db_session.session.commit()

        # 领取活动
        claim_activity(test_user.id, activity.code)

        # 执行过期处理
        result = expire_activity_points()

        # 验证没有过期
        assert result['expired_count'] == 0

        # 验证余额未变
        db_session.session.refresh(test_user)
        assert test_user.activity_balance == 50.00


class TestGetActiveActivities:
    """测试获取可用活动列表"""

    def test_get_active_only(self, db_session):
        """测试：只返回active状态的活动"""
        # 创建多个活动
        activities = [
            Activity(code='ACTIVE1', name='活动1', points=10, status='active'),
            Activity(code='PAUSED1', name='活动2', points=20, status='paused'),
            Activity(code='ENDED1', name='活动3', points=30, status='ended'),
        ]
        for activity in activities:
            db_session.session.add(activity)
        db_session.session.commit()

        result = get_active_activities()

        # 只返回 active 状态
        assert len(result) == 1
        assert result[0]['code'] == 'ACTIVE1'

    def test_time_filter(self, db_session):
        """测试：时间范围过滤"""
        now = datetime.now()

        activities = [
            Activity(
                code='CURRENT',
                name='当前活动',
                points=10,
                start_at=now - timedelta(days=1),
                end_at=now + timedelta(days=1),
                status='active'
            ),
            Activity(
                code='FUTURE',
                name='未来活动',
                points=20,
                start_at=now + timedelta(days=1),
                status='active'
            ),
            Activity(
                code='PAST',
                name='过去活动',
                points=30,
                end_at=now - timedelta(days=1),
                status='active'
            ),
        ]
        for activity in activities:
            db_session.session.add(activity)
        db_session.session.commit()

        result = get_active_activities()

        # 只返回当前有效的活动
        assert len(result) == 1
        assert result[0]['code'] == 'CURRENT'


class TestGetUserActivities:
    """测试获取用户领取记录"""

    def test_get_user_claims(self, db_session, test_user, test_activity):
        """测试：获取用户领取记录"""
        # 领取活动
        claim_activity(test_user.id, test_activity.code)

        # 获取记录
        result = get_user_activities(test_user.id, page=1, size=20)

        # 验证结果
        assert result['total'] == 1
        assert len(result['list']) == 1

        claim = result['list'][0]
        assert claim['user_id'] == test_user.id
        assert claim['activity_name'] == test_activity.name
        assert claim['activity_code'] == test_activity.code

    def test_pagination(self, db_session, test_user):
        """测试：分页功能"""
        # 创建多个活动并领取
        for i in range(5):
            activity = Activity(
                code=f'ACTIVITY-{i}',
                name=f'活动{i}',
                points=10.00,
                max_claims_per_user=1,
                status='active'
            )
            db_session.session.add(activity)
        db_session.session.commit()

        for i in range(5):
            claim_activity(test_user.id, f'ACTIVITY-{i}')

        # 获取第1页（size=3）
        result = get_user_activities(test_user.id, page=1, size=3)

        assert result['total'] == 5
        assert len(result['list']) == 3
        assert result['page'] == 1
        assert result['size'] == 3
