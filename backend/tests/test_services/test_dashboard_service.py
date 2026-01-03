"""
管理员仪表盘服务测试
测试仪表盘统计数据的业务逻辑
"""
import pytest
from datetime import datetime, timedelta
from app.services.admin.dashboard_service import (
    get_dashboard_overview,
    get_trend_chart_data
)
from app.models import User, Task, Transaction, CDK


@pytest.mark.unit
class TestDashboardService:
    """管理员仪表盘服务测试类"""

    def test_get_dashboard_overview_empty(self, app, db_session):
        """测试空数据情况下的仪表盘概览"""
        with app.app_context():
            data = get_dashboard_overview()

            assert data['today_new_users'] == 0
            assert data['today_points_consumed'] == 0.0
            assert data['today_cdk_recharge'] == 0.0
            assert data['active_tasks'] == 0

    def test_get_dashboard_overview_with_today_data(self, app, db_session):
        """测试今日数据统计"""
        with app.app_context():
            today = datetime.utcnow()

            # 创建今日新增用户
            for i in range(3):
                user = User(
                    email=f'user{i}@example.com',
                    password_hash='hash',
                    balance=1000.00,
                    level=1,
                    created_at=today
                )
                db_session.session.add(user)

            db_session.session.commit()

            # 创建今日任务（积分消耗）
            user = User.query.first()
            for i in range(2):
                task = Task(
                    user_id=user.id,
                    platform='openai',
                    prompt='test',
                    status='completed',
                    cost_points=100.00,
                    created_at=today
                )
                db_session.session.add(task)

            # 创建活跃任务
            active_task = Task(
                user_id=user.id,
                platform='openai',
                prompt='test',
                status='processing',
                cost_points=50.00,
                created_at=today
            )
            db_session.session.add(active_task)

            # 创建今日 CDK 充值记录
            transaction = Transaction(
                user_id=user.id,
                type='recharge',
                amount=500.00,
                balance_snapshot=1500.00,
                created_at=today
            )
            db_session.session.add(transaction)

            db_session.session.commit()

            # 获取统计数据
            data = get_dashboard_overview()

            assert data['today_new_users'] == 3
            assert data['today_points_consumed'] == 250.00  # 100 + 100 + 50
            assert data['today_cdk_recharge'] == 500.00
            assert data['active_tasks'] == 1

    def test_get_dashboard_overview_excludes_yesterday_data(self, app, db_session):
        """测试不包含昨日数据"""
        with app.app_context():
            yesterday = datetime.utcnow() - timedelta(days=1)
            today = datetime.utcnow()

            # 创建昨日用户
            old_user = User(
                email='old@example.com',
                password_hash='hash',
                balance=1000.00,
                level=1,
                created_at=yesterday
            )
            db_session.session.add(old_user)
            db_session.session.commit()

            # 创建昨日任务
            old_task = Task(
                user_id=old_user.id,
                platform='openai',
                prompt='test',
                status='completed',
                cost_points=200.00,
                created_at=yesterday
            )
            db_session.session.add(old_task)

            # 创建今日用户
            new_user = User(
                email='new@example.com',
                password_hash='hash',
                balance=1000.00,
                level=1,
                created_at=today
            )
            db_session.session.add(new_user)

            db_session.session.commit()

            # 获取统计数据
            data = get_dashboard_overview()

            # 应该只统计今日数据
            assert data['today_new_users'] == 1
            assert data['today_points_consumed'] == 0.0  # 昨日的任务不计入

    def test_get_dashboard_overview_only_counts_recharge_transactions(self, app, db_session, test_user):
        """测试只统计充值类型的交易"""
        with app.app_context():
            today = datetime.utcnow()

            # 创建充值记录
            recharge_tx = Transaction(
                user_id=test_user.id,
                type='recharge',
                amount=500.00,
                balance_snapshot=1500.00,
                created_at=today
            )
            db_session.session.add(recharge_tx)

            # 创建其他类型交易（不应计入）
            task_cost_tx = Transaction(
                user_id=test_user.id,
                type='task_cost',
                amount=-100.00,
                balance_snapshot=1400.00,
                created_at=today
            )
            db_session.session.add(task_cost_tx)

            refund_tx = Transaction(
                user_id=test_user.id,
                type='refund',
                amount=50.00,
                balance_snapshot=1450.00,
                created_at=today
            )
            db_session.session.add(refund_tx)

            db_session.session.commit()

            # 获取统计数据
            data = get_dashboard_overview()

            # 应该只计入 recharge 类型
            assert data['today_cdk_recharge'] == 500.00

    def test_get_trend_chart_data_7_days(self, app, db_session):
        """测试获取7天趋势数据"""
        with app.app_context():
            today = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)

            # 创建不同日期的数据
            for i in range(7):
                day = today - timedelta(days=i)

                # 创建用户
                user = User(
                    email=f'user_day{i}@example.com',
                    password_hash='hash',
                    balance=1000.00,
                    level=1,
                    created_at=day
                )
                db_session.session.add(user)
                db_session.session.commit()

                # 创建任务
                task = Task(
                    user_id=user.id,
                    platform='openai',
                    prompt='test',
                    status='completed',
                    cost_points=100.00 * (i + 1),
                    created_at=day
                )
                db_session.session.add(task)

                # 创建充值记录
                transaction = Transaction(
                    user_id=user.id,
                    type='recharge',
                    amount=200.00 * (i + 1),
                    balance_snapshot=1000.00,
                    created_at=day
                )
                db_session.session.add(transaction)

            db_session.session.commit()

            # 获取趋势数据
            data = get_trend_chart_data(days=7)

            # 验证返回7条记录
            assert len(data) == 7

            # 验证数据结构
            for item in data:
                assert 'date' in item
                assert 'new_users' in item
                assert 'points_consumed' in item
                assert 'cdk_recharge' in item

            # 验证日期顺序（从旧到新）
            assert data[0]['date'] < data[-1]['date']

    def test_get_trend_chart_data_30_days(self, app, db_session):
        """测试获取30天趋势数据"""
        with app.app_context():
            data = get_trend_chart_data(days=30)

            # 验证返回30条记录
            assert len(data) == 30

            # 验证每条记录都有完整字段
            for item in data:
                assert 'date' in item
                assert 'new_users' in item
                assert 'points_consumed' in item
                assert 'cdk_recharge' in item

    def test_get_trend_chart_data_fills_missing_days(self, app, db_session):
        """测试填充缺失日期（确保每天都有数据，即使为0）"""
        with app.app_context():
            today = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)

            # 只在第3天创建数据
            day3 = today - timedelta(days=3)
            user = User(
                email='user@example.com',
                password_hash='hash',
                balance=1000.00,
                level=1,
                created_at=day3
            )
            db_session.session.add(user)
            db_session.session.commit()

            # 获取7天数据
            data = get_trend_chart_data(days=7)

            # 验证返回7条记录
            assert len(data) == 7

            # 验证大部分天数为0
            zero_days = [item for item in data if item['new_users'] == 0]
            assert len(zero_days) == 6

            # 验证第3天有数据
            non_zero_days = [item for item in data if item['new_users'] > 0]
            assert len(non_zero_days) == 1

    def test_get_trend_chart_data_invalid_days_defaults_to_7(self, app, db_session):
        """测试无效的天数参数默认返回7天"""
        with app.app_context():
            # 传入无效值
            data = get_trend_chart_data(days=15)

            # 应该返回7天数据
            assert len(data) == 7

            data = get_trend_chart_data(days=0)
            assert len(data) == 7

            data = get_trend_chart_data(days=100)
            assert len(data) == 7

    def test_get_trend_chart_data_date_format(self, app, db_session):
        """测试日期格式正确"""
        with app.app_context():
            data = get_trend_chart_data(days=7)

            for item in data:
                # 验证日期格式为 YYYY-MM-DD
                date_str = item['date']
                assert len(date_str) == 10
                assert date_str[4] == '-'
                assert date_str[7] == '-'

                # 验证可以解析为日期
                datetime.strptime(date_str, '%Y-%m-%d')

    def test_get_trend_chart_data_correct_date_range(self, app, db_session):
        """测试日期范围正确"""
        with app.app_context():
            today = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
            data = get_trend_chart_data(days=7)

            # 第一天应该是6天前
            first_date = datetime.strptime(data[0]['date'], '%Y-%m-%d')
            expected_first = today - timedelta(days=6)
            assert first_date.date() == expected_first.date()

            # 最后一天应该是今天
            last_date = datetime.strptime(data[-1]['date'], '%Y-%m-%d')
            assert last_date.date() == today.date()

    def test_get_trend_chart_data_multiple_users_same_day(self, app, db_session):
        """测试同一天多个用户的统计"""
        with app.app_context():
            today = datetime.utcnow()

            # 创建5个同一天的用户
            for i in range(5):
                user = User(
                    email=f'user{i}@example.com',
                    password_hash='hash',
                    balance=1000.00,
                    level=1,
                    created_at=today
                )
                db_session.session.add(user)

            db_session.session.commit()

            data = get_trend_chart_data(days=7)

            # 找到今天的数据
            today_str = today.strftime('%Y-%m-%d')
            today_data = [item for item in data if item['date'] == today_str][0]

            # 验证统计正确
            assert today_data['new_users'] == 5

    def test_get_dashboard_overview_active_tasks_only_processing(self, app, db_session, test_user):
        """测试活跃任务只统计 processing 状态"""
        with app.app_context():
            # 创建不同状态的任务
            statuses = ['pending', 'processing', 'completed', 'failed']
            for status in statuses:
                task = Task(
                    user_id=test_user.id,
                    platform='openai',
                    prompt='test',
                    status=status,
                    cost_points=100.00
                )
                db_session.session.add(task)

            db_session.session.commit()

            data = get_dashboard_overview()

            # 应该只统计 processing 状态
            assert data['active_tasks'] == 1
