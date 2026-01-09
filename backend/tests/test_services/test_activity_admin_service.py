"""
测试 activity_admin_service.py 业务逻辑
包含活动管理、统计、签到配置等功能测试
"""
import pytest
from datetime import datetime, timedelta
from app.services.admin.activity_admin_service import (
    create_activity,
    update_activity,
    delete_activity,
    get_activity_list,
    get_activity_stats,
    get_checkin_config,
    update_checkin_config
)
from app.models.activity import Activity, ActivityClaim, CheckinConfig


class TestCreateActivity:
    """测试创建活动"""

    def test_create_success(self, db_session):
        """测试：成功创建活动"""
        data = {
            'code': 'NEW-ACTIVITY',
            'name': '新活动',
            'description': '这是一个新活动',
            'points': 100,
            'expire_days': 30,
            'max_claims_per_user': 1,
            'required_level': 1,
            'start_at': '2024-01-01T00:00:00',
            'end_at': '2024-12-31T23:59:59'
        }

        result = create_activity(data)

        # 验证返回结果
        assert result['code'] == 'NEW-ACTIVITY'
        assert result['name'] == '新活动'
        assert result['points'] == 100.00
        assert result['status'] == 'active'

        # 验证数据库记录
        activity = Activity.query.filter_by(code='NEW-ACTIVITY').first()
        assert activity is not None
        assert activity.expire_days == 30

    def test_create_missing_required_field(self, db_session):
        """测试：缺少必填字段"""
        data = {
            'name': '新活动'
            # 缺少 code 和 points
        }

        with pytest.raises(ValueError) as exc_info:
            create_activity(data)

        assert "Missing required field" in str(exc_info.value)

    def test_create_duplicate_code(self, db_session, test_activity):
        """测试：活动代码重复"""
        data = {
            'code': test_activity.code,  # 重复的代码
            'name': '新活动',
            'points': 50
        }

        with pytest.raises(ValueError) as exc_info:
            create_activity(data)

        assert "already exists" in str(exc_info.value)

    def test_create_with_optional_fields(self, db_session):
        """测试：创建活动（仅必填字段）"""
        data = {
            'code': 'MINIMAL-ACTIVITY',
            'name': '最小活动',
            'points': 10
        }

        result = create_activity(data)

        # 验证可选字段有默认值
        assert result['max_claims_per_user'] == 1
        assert result['expire_days'] is None
        assert result['required_level'] is None

    def test_create_invalid_date_format(self, db_session):
        """测试：无效的日期格式"""
        data = {
            'code': 'INVALID-DATE',
            'name': '无效日期',
            'points': 10,
            'start_at': 'invalid-date'
        }

        with pytest.raises(ValueError) as exc_info:
            create_activity(data)

        assert "Invalid start_at format" in str(exc_info.value)


class TestUpdateActivity:
    """测试更新活动"""

    def test_update_success(self, db_session, test_activity):
        """测试：成功更新活动"""
        data = {
            'name': '更新后的活动',
            'description': '新描述',
            'points': 200,
            'status': 'paused'
        }

        result = update_activity(test_activity.id, data)

        # 验证返回结果
        assert result['name'] == '更新后的活动'
        assert result['points'] == 200.00
        assert result['status'] == 'paused'

        # 验证数据库记录
        db_session.session.refresh(test_activity)
        assert test_activity.name == '更新后的活动'
        assert test_activity.status == 'paused'

    def test_update_not_found(self, db_session):
        """测试：活动不存在"""
        with pytest.raises(ValueError) as exc_info:
            update_activity(99999, {'name': '新名称'})

        assert "Activity not found" in str(exc_info.value)

    def test_update_dates(self, db_session, test_activity):
        """测试：更新日期字段"""
        data = {
            'start_at': '2025-01-01T00:00:00',
            'end_at': '2025-12-31T23:59:59'
        }

        result = update_activity(test_activity.id, data)

        # 验证日期更新
        db_session.session.refresh(test_activity)
        assert test_activity.start_at.year == 2025
        assert test_activity.end_at.year == 2025

    def test_update_clear_dates(self, db_session, test_activity):
        """测试：清除日期字段（设为None）"""
        data = {
            'start_at': None,
            'end_at': None
        }

        result = update_activity(test_activity.id, data)

        db_session.session.refresh(test_activity)
        assert test_activity.start_at is None
        assert test_activity.end_at is None


class TestDeleteActivity:
    """测试删除活动"""

    def test_delete_success(self, db_session, test_activity):
        """测试：成功删除活动（无领取记录）"""
        activity_id = test_activity.id

        result = delete_activity(activity_id)

        assert "successfully" in result['msg']

        # 验证数据库记录已删除
        activity = Activity.query.get(activity_id)
        assert activity is None

    def test_delete_with_claims(self, db_session, test_user, test_activity):
        """测试：有领取记录时无法删除"""
        from app.services.activity_service import claim_activity

        # 创建领取记录
        claim_activity(test_user.id, test_activity.code)

        # 尝试删除（应该失败）
        with pytest.raises(ValueError) as exc_info:
            delete_activity(test_activity.id)

        assert "Cannot delete activity" in str(exc_info.value)
        assert "claims" in str(exc_info.value)

    def test_delete_not_found(self, db_session):
        """测试：活动不存在"""
        with pytest.raises(ValueError) as exc_info:
            delete_activity(99999)

        assert "Activity not found" in str(exc_info.value)


class TestGetActivityList:
    """测试获取活动列表"""

    def test_get_all_activities(self, db_session):
        """测试：获取所有活动"""
        # 创建多个活动
        activities = [
            Activity(code='ACT1', name='活动1', points=10, status='active'),
            Activity(code='ACT2', name='活动2', points=20, status='paused'),
            Activity(code='ACT3', name='活动3', points=30, status='ended'),
        ]
        for activity in activities:
            db_session.session.add(activity)
        db_session.session.commit()

        result = get_activity_list(page=1, size=20)

        # 验证结果
        assert result['total'] == 3
        assert len(result['list']) == 3

    def test_filter_by_status(self, db_session):
        """测试：按状态筛选"""
        # 创建多个活动
        activities = [
            Activity(code='ACT-A1', name='活动A1', points=10, status='active'),
            Activity(code='ACT-A2', name='活动A2', points=20, status='active'),
            Activity(code='ACT-P1', name='活动P1', points=30, status='paused'),
        ]
        for activity in activities:
            db_session.session.add(activity)
        db_session.session.commit()

        # 只获取 active 状态
        result = get_activity_list(page=1, size=20, status='active')

        assert result['total'] == 2
        for item in result['list']:
            assert item['status'] == 'active'

    def test_pagination(self, db_session):
        """测试：分页功能"""
        # 创建5个活动
        for i in range(5):
            activity = Activity(
                code=f'PAGE-ACT-{i}',
                name=f'分页活动{i}',
                points=10,
                status='active'
            )
            db_session.session.add(activity)
        db_session.session.commit()

        # 获取第1页（size=2）
        result = get_activity_list(page=1, size=2)

        assert result['total'] == 5
        assert len(result['list']) == 2
        assert result['page'] == 1
        assert result['size'] == 2

        # 获取第2页
        result2 = get_activity_list(page=2, size=2)
        assert len(result2['list']) == 2


class TestGetActivityStats:
    """测试获取活动统计"""

    def test_stats_no_claims(self, db_session, test_activity):
        """测试：无领取记录的统计"""
        result = get_activity_stats(test_activity.id)

        # 验证统计数据
        assert result['activity_id'] == test_activity.id
        assert result['total_claims'] == 0
        assert result['unique_users'] == 0
        assert result['total_points_granted'] == 0.00

    def test_stats_with_claims(self, db_session, test_user, test_activity):
        """测试：有领取记录的统计"""
        from app.services.activity_service import claim_activity

        # 用户领取活动
        claim_activity(test_user.id, test_activity.code)

        result = get_activity_stats(test_activity.id)

        # 验证统计数据
        assert result['total_claims'] == 1
        assert result['unique_users'] == 1
        assert result['total_points_granted'] == 100.00
        assert result['active_claims'] == 1
        assert result['expired_claims'] == 0

    def test_stats_multiple_users(self, db_session, test_activity):
        """测试：多用户领取统计"""
        from app.services.activity_service import claim_activity
        from app.models.user import User

        # 创建3个用户
        users = []
        for i in range(3):
            user = User(
                email=f'user{i}@example.com',
                password_hash='hash',
                recharge_balance=0.00,
                activity_balance=0.00,
                level=1,
                role='user',
                status=1
            )
            db_session.session.add(user)
            users.append(user)
        db_session.session.commit()

        # 更新活动允许多次领取
        test_activity.max_claims_per_user = 3
        db_session.session.commit()

        # 所有用户领取
        for user in users:
            claim_activity(user.id, test_activity.code)

        result = get_activity_stats(test_activity.id)

        # 验证统计
        assert result['total_claims'] == 3
        assert result['unique_users'] == 3
        assert result['total_points_granted'] == 300.00

    def test_stats_not_found(self, db_session):
        """测试：活动不存在"""
        with pytest.raises(ValueError) as exc_info:
            get_activity_stats(99999)

        assert "Activity not found" in str(exc_info.value)


class TestGetCheckinConfig:
    """测试获取签到配置"""

    def test_get_default_config(self, db_session):
        """测试：获取默认签到配置"""
        result = get_checkin_config()

        # 验证返回7天配置
        assert len(result) == 7

        # 验证第1天配置
        day1 = next(c for c in result if c['day'] == 1)
        assert day1['points'] == 10.00
        assert day1['is_active'] is True

        # 验证第7天配置
        day7 = next(c for c in result if c['day'] == 7)
        assert day7['points'] == 50.00


class TestUpdateCheckinConfig:
    """测试更新签到配置"""

    def test_update_success(self, db_session):
        """测试：成功更新签到配置"""
        configs = [
            {'day': 1, 'points': 20.00, 'is_active': True},
            {'day': 2, 'points': 30.00, 'is_active': True},
        ]

        result = update_checkin_config(configs)

        assert "successfully" in result['msg']

        # 验证数据库更新
        config1 = CheckinConfig.query.filter_by(day=1).first()
        assert float(config1.points) == 20.00

        config2 = CheckinConfig.query.filter_by(day=2).first()
        assert float(config2.points) == 30.00

    def test_update_invalid_day(self, db_session):
        """测试：无效的天数"""
        configs = [
            {'day': 0, 'points': 10.00},  # 无效：day应该是1-7
        ]

        with pytest.raises(ValueError) as exc_info:
            update_checkin_config(configs)

        assert "Invalid day" in str(exc_info.value)

    def test_update_missing_fields(self, db_session):
        """测试：缺少必填字段"""
        configs = [
            {'day': 1}  # 缺少 points
        ]

        with pytest.raises(ValueError) as exc_info:
            update_checkin_config(configs)

        assert "Missing required fields" in str(exc_info.value)

    def test_update_create_new_config(self, db_session):
        """测试：创建新的签到配置"""
        # 先删除第8天配置（如果存在）
        CheckinConfig.query.filter_by(day=8).delete()
        db_session.session.commit()

        # 创建第8天配置（虽然不推荐，但测试系统支持）
        configs = [
            {'day': 8, 'points': 60.00, 'is_active': True}
        ]

        # 注意：这会因为 day 验证失败
        with pytest.raises(ValueError):
            update_checkin_config(configs)

    def test_update_disable_config(self, db_session):
        """测试：禁用签到配置"""
        configs = [
            {'day': 1, 'points': 10.00, 'is_active': False}
        ]

        update_checkin_config(configs)

        # 验证配置被禁用
        config = CheckinConfig.query.filter_by(day=1).first()
        assert config.is_active == 0

    def test_update_empty_list(self, db_session):
        """测试：空配置列表"""
        with pytest.raises(ValueError) as exc_info:
            update_checkin_config([])

        assert "Invalid configs format" in str(exc_info.value)

    def test_update_not_list(self, db_session):
        """测试：非列表类型"""
        with pytest.raises(ValueError) as exc_info:
            update_checkin_config({'day': 1, 'points': 10})

        assert "Invalid configs format" in str(exc_info.value)


class TestIntegration:
    """集成测试：测试完整业务流程"""

    def test_full_activity_lifecycle(self, db_session, test_user):
        """测试：活动完整生命周期"""
        # 1. 管理员创建活动
        activity_data = {
            'code': 'LIFECYCLE-TEST',
            'name': '生命周期测试',
            'points': 100,
            'expire_days': 30,
            'max_claims_per_user': 1
        }
        created = create_activity(activity_data)
        activity_id = created['id']

        # 2. 获取活动列表（应该包含新活动）
        activities = get_activity_list()
        assert any(a['code'] == 'LIFECYCLE-TEST' for a in activities['list'])

        # 3. 用户领取活动
        from app.services.activity_service import claim_activity
        claim_activity(test_user.id, 'LIFECYCLE-TEST')

        # 4. 查看统计（应该有1次领取）
        stats = get_activity_stats(activity_id)
        assert stats['total_claims'] == 1

        # 5. 管理员暂停活动
        update_activity(activity_id, {'status': 'paused'})

        # 6. 用户尝试再次领取（应该失败）
        with pytest.raises(ValueError):
            claim_activity(test_user.id, 'LIFECYCLE-TEST')

        # 7. 管理员恢复活动
        update_activity(activity_id, {'status': 'active'})

        # 8. 管理员删除活动（应该失败，因为有领取记录）
        with pytest.raises(ValueError):
            delete_activity(activity_id)
