"""
用户管理服务测试
测试管理员对用户的各种管理操作
"""
import pytest
from decimal import Decimal
from app.services.admin.user_service import (
    get_user_list,
    get_user_detail,
    ban_user,
    unban_user,
    update_user_level,
    adjust_user_balance
)
from app.models import User, Transaction


@pytest.mark.unit
class TestUserManagementService:
    """用户管理服务测试类"""

    def test_get_user_list_empty(self, app, db_session):
        """测试空列表"""
        with app.app_context():
            result = get_user_list()

            assert result['total'] == 0
            assert result['pages'] == 0
            assert result['current_page'] == 1
            assert result['users'] == []

    def test_get_user_list_with_users(self, app, db_session):
        """测试获取用户列表"""
        with app.app_context():
            # 创建测试用户
            for i in range(5):
                user = User(
                    email=f'user{i}@example.com',
                    password_hash='hash',
                    balance=1000.00,
                    level=1,
                    status=1
                )
                db_session.session.add(user)

            db_session.session.commit()

            result = get_user_list()

            assert result['total'] == 5
            assert len(result['users']) == 5

    def test_get_user_list_pagination(self, app, db_session):
        """测试分页功能"""
        with app.app_context():
            # 创建25个用户
            for i in range(25):
                user = User(
                    email=f'user{i}@example.com',
                    password_hash='hash',
                    balance=1000.00,
                    level=1,
                    status=1
                )
                db_session.session.add(user)

            db_session.session.commit()

            # 获取第一页（每页10条）
            result = get_user_list(page=1, per_page=10)
            assert result['total'] == 25
            assert result['pages'] == 3
            assert result['current_page'] == 1
            assert len(result['users']) == 10

            # 获取第二页
            result = get_user_list(page=2, per_page=10)
            assert result['current_page'] == 2
            assert len(result['users']) == 10

            # 获取第三页
            result = get_user_list(page=3, per_page=10)
            assert result['current_page'] == 3
            assert len(result['users']) == 5

    def test_get_user_list_filter_by_keyword(self, app, db_session):
        """测试关键词搜索（邮箱）"""
        with app.app_context():
            # 创建不同邮箱的用户
            emails = ['test1@example.com', 'test2@example.com', 'other@example.com']
            for email in emails:
                user = User(
                    email=email,
                    password_hash='hash',
                    balance=1000.00,
                    level=1,
                    status=1
                )
                db_session.session.add(user)

            db_session.session.commit()

            # 搜索包含 "test" 的邮箱
            result = get_user_list(keyword='test')
            assert result['total'] == 2
            assert all('test' in user['email'] for user in result['users'])

    def test_get_user_list_filter_by_status(self, app, db_session):
        """测试状态筛选"""
        with app.app_context():
            # 创建不同状态的用户
            for i in range(3):
                user = User(
                    email=f'active{i}@example.com',
                    password_hash='hash',
                    balance=1000.00,
                    level=1,
                    status=1  # 正常
                )
                db_session.session.add(user)

            for i in range(2):
                user = User(
                    email=f'banned{i}@example.com',
                    password_hash='hash',
                    balance=1000.00,
                    level=1,
                    status=0  # 封禁
                )
                db_session.session.add(user)

            db_session.session.commit()

            # 筛选正常用户
            result = get_user_list(status=1)
            assert result['total'] == 3

            # 筛选封禁用户
            result = get_user_list(status=0)
            assert result['total'] == 2

    def test_get_user_list_filter_by_level(self, app, db_session):
        """测试等级筛选"""
        with app.app_context():
            # 创建不同等级的用户
            for level in [1, 2, 3, 4, 5]:
                for i in range(level):
                    user = User(
                        email=f'user_l{level}_{i}@example.com',
                        password_hash='hash',
                        balance=1000.00,
                        level=level,
                        status=1
                    )
                    db_session.session.add(user)

            db_session.session.commit()

            # 筛选T3用户
            result = get_user_list(level=3)
            assert result['total'] == 3
            assert all(user['level'] == 3 for user in result['users'])

    def test_ban_user_success(self, app, db_session, test_user):
        """测试成功封禁用户"""
        with app.app_context():
            admin_id = 999
            result = ban_user(test_user.id, admin_id)

            assert result['user_id'] == test_user.id
            assert result['status'] == 'banned'

            # 验证数据库状态
            user = User.query.get(test_user.id)
            assert user.status == 0

    def test_ban_user_not_found(self, app, db_session):
        """测试封禁不存在的用户"""
        with app.app_context():
            with pytest.raises(ValueError, match="User not found"):
                ban_user(9999, 1)

    def test_ban_user_already_banned(self, app, db_session):
        """测试重复封禁已封禁的用户"""
        with app.app_context():
            # 创建已封禁用户
            user = User(
                email='banned@example.com',
                password_hash='hash',
                balance=1000.00,
                level=1,
                status=0  # 已封禁
            )
            db_session.session.add(user)
            db_session.session.commit()

            with pytest.raises(ValueError, match="User is already banned"):
                ban_user(user.id, 1)

    def test_ban_user_cannot_ban_admin(self, app, db_session, admin_user):
        """测试不能封禁管理员"""
        with app.app_context():
            with pytest.raises(ValueError, match="Cannot ban admin user"):
                ban_user(admin_user.id, 1)

    def test_unban_user_success(self, app, db_session):
        """测试成功解封用户"""
        with app.app_context():
            # 创建已封禁用户
            user = User(
                email='banned@example.com',
                password_hash='hash',
                balance=1000.00,
                level=1,
                status=0  # 已封禁
            )
            db_session.session.add(user)
            db_session.session.commit()

            admin_id = 999
            result = unban_user(user.id, admin_id)

            assert result['user_id'] == user.id
            assert result['status'] == 'active'

            # 验证数据库状态
            user = User.query.get(user.id)
            assert user.status == 1

    def test_unban_user_not_found(self, app, db_session):
        """测试解封不存在的用户"""
        with app.app_context():
            with pytest.raises(ValueError, match="User not found"):
                unban_user(9999, 1)

    def test_unban_user_not_banned(self, app, db_session, test_user):
        """测试解封未被封禁的用户"""
        with app.app_context():
            with pytest.raises(ValueError, match="User is not banned"):
                unban_user(test_user.id, 1)

    def test_update_user_level_success(self, app, db_session, test_user):
        """测试成功修改用户等级"""
        with app.app_context():
            admin_id = 999
            result = update_user_level(test_user.id, 3, admin_id)

            assert result['user_id'] == test_user.id
            assert result['old_level'] == 1
            assert result['new_level'] == 3

            # 验证数据库状态
            user = User.query.get(test_user.id)
            assert user.level == 3

    def test_update_user_level_invalid_level(self, app, db_session, test_user):
        """测试无效的等级值"""
        with app.app_context():
            with pytest.raises(ValueError, match="Invalid level"):
                update_user_level(test_user.id, 6, 1)

            with pytest.raises(ValueError, match="Invalid level"):
                update_user_level(test_user.id, 0, 1)

    def test_update_user_level_user_not_found(self, app, db_session):
        """测试修改不存在用户的等级"""
        with app.app_context():
            with pytest.raises(ValueError, match="User not found"):
                update_user_level(9999, 3, 1)

    def test_adjust_user_balance_increase(self, app, db_session, test_user):
        """测试增加用户余额"""
        with app.app_context():
            admin_id = 999
            old_balance = float(test_user.balance)
            amount = 500.00

            result = adjust_user_balance(test_user.id, amount, "Test increase", admin_id)

            assert result['user_id'] == test_user.id
            assert result['old_balance'] == old_balance
            assert result['new_balance'] == old_balance + amount
            assert result['adjustment'] == amount

            # 验证数据库状态
            user = User.query.get(test_user.id)
            assert float(user.balance) == old_balance + amount

            # 验证交易记录
            transaction = Transaction.query.filter_by(
                user_id=test_user.id,
                type='system'
            ).first()
            assert transaction is not None
            assert float(transaction.amount) == amount
            assert float(transaction.balance_snapshot) == old_balance + amount
            assert transaction.remark == "Test increase"

    def test_adjust_user_balance_decrease(self, app, db_session, test_user):
        """测试扣除用户余额"""
        with app.app_context():
            admin_id = 999
            old_balance = float(test_user.balance)
            amount = -200.00

            result = adjust_user_balance(test_user.id, amount, "Test decrease", admin_id)

            assert result['user_id'] == test_user.id
            assert result['old_balance'] == old_balance
            assert result['new_balance'] == old_balance + amount
            assert result['adjustment'] == amount

            # 验证数据库状态
            user = User.query.get(test_user.id)
            assert float(user.balance) == old_balance + amount

    def test_adjust_user_balance_insufficient(self, app, db_session, test_user):
        """测试余额不足时扣除"""
        with app.app_context():
            admin_id = 999
            old_balance = float(test_user.balance)
            amount = -(old_balance + 100)  # 扣除超过余额的金额

            with pytest.raises(ValueError, match="Insufficient balance"):
                adjust_user_balance(test_user.id, amount, "Test", admin_id)

    def test_adjust_user_balance_user_not_found(self, app, db_session):
        """测试调整不存在用户的余额"""
        with app.app_context():
            with pytest.raises(ValueError, match="User not found"):
                adjust_user_balance(9999, 100, "Test", 1)

    def test_get_user_detail_success(self, app, db_session, test_user):
        """测试获取用户详情"""
        with app.app_context():
            # 创建一些任务和交易记录
            from app.models import Task

            # 创建任务
            for status in ['completed', 'processing', 'failed']:
                task = Task(
                    user_id=test_user.id,
                    platform='openai',
                    prompt='test',
                    status=status,
                    cost_points=100.00
                )
                db_session.session.add(task)

            # 创建交易记录
            tx1 = Transaction(
                user_id=test_user.id,
                type='recharge',
                amount=500.00,
                balance_snapshot=1500.00
            )
            db_session.session.add(tx1)

            tx2 = Transaction(
                user_id=test_user.id,
                type='task_cost',
                amount=-100.00,
                balance_snapshot=1400.00
            )
            db_session.session.add(tx2)

            db_session.session.commit()

            # 获取用户详情
            result = get_user_detail(test_user.id)

            assert result['id'] == test_user.id
            assert result['email'] == test_user.email
            assert 'statistics' in result
            assert result['statistics']['total_tasks'] == 3
            assert result['statistics']['completed_tasks'] == 1
            assert result['statistics']['processing_tasks'] == 1
            assert result['statistics']['total_recharge'] == 500.00
            assert result['statistics']['total_consumed'] == 100.00

    def test_get_user_detail_not_found(self, app, db_session):
        """测试获取不存在用户的详情"""
        with app.app_context():
            with pytest.raises(ValueError, match="User not found"):
                get_user_detail(9999)

    def test_get_user_detail_no_tasks_or_transactions(self, app, db_session, test_user):
        """测试无任务和交易记录的用户详情"""
        with app.app_context():
            result = get_user_detail(test_user.id)

            assert result['id'] == test_user.id
            assert result['statistics']['total_tasks'] == 0
            assert result['statistics']['completed_tasks'] == 0
            assert result['statistics']['processing_tasks'] == 0
            assert result['statistics']['total_recharge'] == 0.00
            assert result['statistics']['total_consumed'] == 0.00

    def test_get_user_list_combined_filters(self, app, db_session):
        """测试组合筛选条件"""
        with app.app_context():
            # 创建各种组合的用户
            users_data = [
                ('test1@example.com', 1, 3),  # 正常，T3
                ('test2@example.com', 1, 3),  # 正常，T3
                ('test3@example.com', 0, 3),  # 封禁，T3
                ('other@example.com', 1, 3),  # 正常，T3（邮箱不匹配）
                ('test4@example.com', 1, 2),  # 正常，T2（等级不匹配）
            ]

            for email, status, level in users_data:
                user = User(
                    email=email,
                    password_hash='hash',
                    balance=1000.00,
                    level=level,
                    status=status
                )
                db_session.session.add(user)

            db_session.session.commit()

            # 组合筛选：关键词=test，状态=正常，等级=3
            result = get_user_list(keyword='test', status=1, level=3)
            assert result['total'] == 2  # test1 和 test2

    def test_adjust_user_balance_default_remark(self, app, db_session, test_user):
        """测试余额调整默认备注"""
        with app.app_context():
            adjust_user_balance(test_user.id, 100, None, 1)

            # 验证交易记录使用默认备注
            transaction = Transaction.query.filter_by(
                user_id=test_user.id,
                type='system'
            ).first()
            assert transaction.remark == 'Admin adjustment'
