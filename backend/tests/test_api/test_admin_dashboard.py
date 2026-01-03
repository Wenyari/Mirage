"""
测试管理员仪表盘接口
"""
import pytest
from datetime import datetime, timedelta
from app.extensions import db
from app.models import User, Task, Transaction


class TestDashboardOverview:
    """测试仪表盘核心指标接口"""

    def test_get_overview_success(self, client, admin_headers, db_session):
        """测试成功获取核心指标"""
        # 创建测试数据
        today = datetime.utcnow()

        # 创建今日新增用户
        user1 = User(email='user1@test.com', password_hash='hash1', created_at=today)
        user2 = User(email='user2@test.com', password_hash='hash2', created_at=today)
        db.session.add_all([user1, user2])
        db.session.commit()

        # 创建任务（一个活跃，一个已完成）
        task1 = Task(
            user_id=user1.id,
            platform='openai',
            status='processing',
            cost_points=100.50,
            created_at=today
        )
        task2 = Task(
            user_id=user2.id,
            platform='openai',
            status='success',
            cost_points=200.00,
            created_at=today
        )
        db.session.add_all([task1, task2])
        db.session.commit()

        # 创建充值记录
        trans = Transaction(
            user_id=user1.id,
            type='recharge',
            amount=1000.00,
            balance_snapshot=1000.00,
            created_at=today
        )
        db.session.add(trans)
        db.session.commit()

        # 发送请求
        response = client.get('/api/admin/stats/overview', headers=admin_headers)

        # 验证响应
        assert response.status_code == 200
        data = response.get_json()
        assert data['code'] == 0
        assert data['message'] == 'Success'
        assert 'data' in data

        # 验证数据字段
        result = data['data']
        assert 'today_new_users' in result
        assert 'today_points_consumed' in result
        assert 'today_cdk_recharge' in result
        assert 'active_tasks' in result

        # 验证数据值（今日新增2个用户，但conftest可能已创建admin_user）
        assert result['today_new_users'] >= 2
        assert result['today_points_consumed'] == 300.50  # 100.50 + 200.00
        assert result['today_cdk_recharge'] == 1000.00
        assert result['active_tasks'] == 1  # 只有task1是processing

    def test_get_overview_empty_data(self, client, admin_headers, db_session):
        """测试没有数据时的响应"""
        response = client.get('/api/admin/stats/overview', headers=admin_headers)

        assert response.status_code == 200
        data = response.get_json()
        assert data['code'] == 0

        result = data['data']
        # 没有今日数据时应该返回0
        assert result['today_points_consumed'] == 0.0
        assert result['today_cdk_recharge'] == 0.0

    def test_get_overview_unauthorized(self, client):
        """测试未授权访问"""
        response = client.get('/api/admin/stats/overview')
        assert response.status_code == 401

    def test_get_overview_non_admin(self, client, auth_headers):
        """测试非管理员用户访问"""
        response = client.get('/api/admin/stats/overview', headers=auth_headers)
        assert response.status_code == 403
        data = response.get_json()
        assert data['code'] == 403


class TestDashboardChart:
    """测试仪表盘趋势图接口"""

    def test_get_chart_7_days_success(self, client, admin_headers, db_session):
        """测试获取7天趋势数据"""
        # 创建不同日期的测试数据
        today = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)

        for i in range(7):
            date = today - timedelta(days=i)

            # 创建用户
            user = User(
                email=f'user_day{i}@test.com',
                password_hash='hash',
                created_at=date
            )
            db.session.add(user)
            db.session.commit()

            # 创建任务
            task = Task(
                user_id=user.id,
                platform='openai',
                status='success',
                cost_points=100.00 * (i + 1),
                created_at=date
            )
            db.session.add(task)

            # 创建充值记录
            trans = Transaction(
                user_id=user.id,
                type='recharge',
                amount=500.00 * (i + 1),
                balance_snapshot=500.00 * (i + 1),
                created_at=date
            )
            db.session.add(trans)

        db.session.commit()

        # 发送请求
        response = client.get('/api/admin/stats/chart?days=7', headers=admin_headers)

        # 验证响应
        assert response.status_code == 200
        data = response.get_json()
        assert data['code'] == 0
        assert data['message'] == 'Success'
        assert 'data' in data

        # 验证数据结构
        chart_data = data['data']
        assert len(chart_data) == 7

        # 验证第一个数据点的字段
        first_point = chart_data[0]
        assert 'date' in first_point
        assert 'new_users' in first_point
        assert 'points_consumed' in first_point
        assert 'cdk_recharge' in first_point

        # 验证数据类型
        assert isinstance(first_point['date'], str)
        assert isinstance(first_point['new_users'], int)
        assert isinstance(first_point['points_consumed'], (int, float))
        assert isinstance(first_point['cdk_recharge'], (int, float))

    def test_get_chart_30_days_success(self, client, admin_headers, db_session):
        """测试获取30天趋势数据"""
        response = client.get('/api/admin/stats/chart?days=30', headers=admin_headers)

        assert response.status_code == 200
        data = response.get_json()
        assert data['code'] == 0
        assert len(data['data']) == 30

    def test_get_chart_default_days(self, client, admin_headers, db_session):
        """测试不传days参数时默认返回7天数据"""
        response = client.get('/api/admin/stats/chart', headers=admin_headers)

        assert response.status_code == 200
        data = response.get_json()
        assert data['code'] == 0
        assert len(data['data']) == 7

    def test_get_chart_invalid_days(self, client, admin_headers):
        """测试无效的days参数"""
        # 测试不支持的天数
        response = client.get('/api/admin/stats/chart?days=15', headers=admin_headers)
        assert response.status_code == 400
        data = response.get_json()
        assert data['code'] == 400
        assert 'Invalid days parameter' in data['message']

        # 测试非数字参数
        response = client.get('/api/admin/stats/chart?days=abc', headers=admin_headers)
        assert response.status_code == 400

    def test_get_chart_unauthorized(self, client):
        """测试未授权访问"""
        response = client.get('/api/admin/stats/chart?days=7')
        assert response.status_code == 401

    def test_get_chart_non_admin(self, client, auth_headers):
        """测试非管理员用户访问"""
        response = client.get('/api/admin/stats/chart?days=7', headers=auth_headers)
        assert response.status_code == 403


class TestDashboardDataAccuracy:
    """测试数据准确性"""

    def test_points_consumed_calculation(self, client, admin_headers, db_session):
        """测试积分消耗计算准确性"""
        today = datetime.utcnow()
        yesterday = today - timedelta(days=1)

        user = User(email='calc_test@test.com', password_hash='hash')
        db.session.add(user)
        db.session.commit()

        # 今日任务
        today_task1 = Task(
            user_id=user.id,
            platform='openai',
            status='success',
            cost_points=123.45,
            created_at=today
        )
        today_task2 = Task(
            user_id=user.id,
            platform='openai',
            status='failed',
            cost_points=67.89,
            created_at=today
        )

        # 昨日任务（不应计入今日）
        yesterday_task = Task(
            user_id=user.id,
            platform='openai',
            status='success',
            cost_points=999.99,
            created_at=yesterday
        )

        db.session.add_all([today_task1, today_task2, yesterday_task])
        db.session.commit()

        response = client.get('/api/admin/stats/overview', headers=admin_headers)
        data = response.get_json()

        # 今日消耗应该是 123.45 + 67.89 = 191.34
        expected = 123.45 + 67.89
        assert abs(data['data']['today_points_consumed'] - expected) < 0.01

    def test_cdk_recharge_filter(self, client, admin_headers, db_session):
        """测试CDK充值只统计recharge类型"""
        today = datetime.utcnow()

        user = User(email='recharge_test@test.com', password_hash='hash')
        db.session.add(user)
        db.session.commit()

        # recharge类型（应该计入）
        trans1 = Transaction(
            user_id=user.id,
            type='recharge',
            amount=1000.00,
            balance_snapshot=1000.00,
            created_at=today
        )

        # task_cost类型（不应计入）
        trans2 = Transaction(
            user_id=user.id,
            type='task_cost',
            amount=-100.00,
            balance_snapshot=900.00,
            created_at=today
        )

        # refund类型（不应计入）
        trans3 = Transaction(
            user_id=user.id,
            type='refund',
            amount=50.00,
            balance_snapshot=950.00,
            created_at=today
        )

        db.session.add_all([trans1, trans2, trans3])
        db.session.commit()

        response = client.get('/api/admin/stats/overview', headers=admin_headers)
        data = response.get_json()

        # 只有trans1应该被计入
        assert data['data']['today_cdk_recharge'] == 1000.00

    def test_active_tasks_count(self, client, admin_headers, db_session):
        """测试活跃任务统计准确性"""
        user = User(email='active_test@test.com', password_hash='hash')
        db.session.add(user)
        db.session.commit()

        # 创建不同状态的任务
        tasks = [
            Task(user_id=user.id, platform='openai', status='processing', cost_points=10),
            Task(user_id=user.id, platform='openai', status='processing', cost_points=10),
            Task(user_id=user.id, platform='openai', status='pending', cost_points=10),
            Task(user_id=user.id, platform='openai', status='success', cost_points=10),
            Task(user_id=user.id, platform='openai', status='failed', cost_points=10),
        ]
        db.session.add_all(tasks)
        db.session.commit()

        response = client.get('/api/admin/stats/overview', headers=admin_headers)
        data = response.get_json()

        # 只有2个processing状态的任务
        assert data['data']['active_tasks'] == 2
