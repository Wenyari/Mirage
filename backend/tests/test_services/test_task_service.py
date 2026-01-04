"""
任务服务测试
"""
import pytest
from decimal import Decimal
from app.services.task_service import TaskService
from app.models import Task, User


@pytest.mark.unit
class TestTaskService:
    """任务服务测试类"""

    def test_submit_task_success(self, app, db_session, redis_db, test_user, mocker):
        """测试提交任务成功"""
        with app.app_context():
            # 记录初始余额
            initial_balance = test_user.balance
            user_id = test_user.id

            # Mock KeyManager.allocate_key
            mock_allocate = mocker.patch('app.services.task_service.KeyManager.allocate_key')
            mock_allocate.return_value = None  # 模拟无可用密钥，进入等待队列

            task_data = {
                'model': 'sora-2',
                'prompt': 'Test prompt',
                'params': {'duration': 1}
            }

            result = TaskService.submit_task(user_id, task_data)

            assert result['task_id'] is not None
            assert result['status'] == 'pending'

            # 验证任务创建
            task = Task.query.get(result['task_id'])
            assert task is not None
            assert task.user_id == user_id
            assert task.model == 'sora-2'
            assert task.status == 'pending'

            # 重新查询用户验证余额扣除
            user = User.query.get(user_id)
            assert user.balance < initial_balance  # 余额应该减少

    def test_submit_task_concurrency_limit(self, app, db_session, test_user):
        """测试并发限制"""
        with app.app_context():
            # T3 用户有 3 个并发限制，先创建 3 个 processing 任务
            for i in range(3):
                task = Task(
                    user_id=test_user.id,
                    model='sora-2',
                    status='processing',
                    cost_points=100.00,
                    prompt=f'test {i}'
                )
                db_session.session.add(task)
            db_session.session.commit()

            # 尝试提交第 4 个任务
            task_data = {
                'model': 'sora-2',
                'prompt': 'Test',
                'params': {'duration': 1}
            }

            with pytest.raises(ValueError, match="Concurrent limit exceeded"):
                TaskService.submit_task(test_user.id, task_data)

    def test_submit_task_insufficient_balance(self, app, db_session, test_user):
        """测试余额不足"""
        with app.app_context():
            # 设置余额为 50
            test_user.balance = 50.00
            db_session.session.commit()

            # 尝试提交需要 100 的任务
            task_data = {
                'model': 'sora-2',
                'prompt': 'Test',
                'params': {'duration': 1}
            }

            with pytest.raises(ValueError, match="Insufficient balance"):
                TaskService.submit_task(test_user.id, task_data)

    def test_submit_task_user_not_found(self, app, db_session):
        """测试用户不存在"""
        with app.app_context():
            task_data = {
                'model': 'sora-2',
                'prompt': 'Test',
                'params': {'duration': 1}
            }

            with pytest.raises(ValueError, match="User not found"):
                TaskService.submit_task(99999, task_data)

    def test_submit_task_model_not_available(self, app, db_session, test_user):
        """测试模型不可用"""
        with app.app_context():
            task_data = {
                'model': 'nonexistent-model',
                'prompt': 'Test',
                'params': {'duration': 1}
            }

            with pytest.raises(ValueError, match="is not available"):
                TaskService.submit_task(test_user.id, task_data)

    def test_cancel_task_success(self, app, db_session, test_user):
        """测试取消任务成功"""
        with app.app_context():
            user_id = test_user.id
            initial_balance = test_user.balance

            # 创建一个 pending 任务
            task = Task(
                user_id=user_id,
                model='sora-2',
                status='pending',
                cost_points=100.00,
                prompt='test'
            )
            db_session.session.add(task)
            db_session.session.commit()
            task_id = task.id

            # 取消任务
            result = TaskService.cancel_task(user_id, task_id)

            assert result['msg'] == "Task cancelled successfully"

            # 重新查询验证任务状态
            task = Task.query.get(task_id)
            assert task.status == 'cancelled'

            # 重新查询验证退款
            user = User.query.get(user_id)
            assert user.balance == initial_balance + Decimal('100.00')

    def test_cancel_task_not_pending(self, app, db_session, test_user):
        """测试取消非 pending 状态的任务"""
        with app.app_context():
            # 创建一个 processing 任务
            task = Task(
                user_id=test_user.id,
                model='sora-2',
                status='processing',
                cost_points=100.00,
                prompt='test'
            )
            db_session.session.add(task)
            db_session.session.commit()

            # 尝试取消
            with pytest.raises(ValueError, match="Only pending tasks can be cancelled"):
                TaskService.cancel_task(test_user.id, task.id)

    def test_get_task_status(self, app, db_session, test_user):
        """测试获取任务状态"""
        with app.app_context():
            # 创建一个任务
            task = Task(
                user_id=test_user.id,
                model='sora-2',
                status='processing',
                progress=50,
                cost_points=100.00,
                prompt='test'
            )
            db_session.session.add(task)
            db_session.session.commit()

            # 获取状态
            status = TaskService.get_task_status(test_user.id, task.id)

            assert status['id'] == task.id
            assert status['status'] == 'processing'
            assert status['progress'] == 50

    def test_get_task_history(self, app, db_session, test_user):
        """测试获取任务历史"""
        with app.app_context():
            # 创建多个任务
            for i in range(5):
                task = Task(
                    user_id=test_user.id,
                    model='sora-2',
                    status='success',
                    cost_points=100.00,
                    prompt=f'test {i}'
                )
                db_session.session.add(task)
            db_session.session.commit()

            # 获取历史
            result = TaskService.get_task_history(test_user.id, page=1, size=3)

            assert result['total'] == 5
            assert len(result['list']) == 3
            assert result['page'] == 1
            assert result['size'] == 3
