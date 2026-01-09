"""
任务服务测试
"""
import pytest
from decimal import Decimal
from datetime import datetime, timedelta
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


@pytest.mark.unit
class TestTaskServiceCleanup:
    """任务清理功能测试类"""

    def test_cleanup_old_tasks_success(self, app, db_session, test_user, mocker):
        """测试清理超过3天的任务成功"""
        with app.app_context():
            # Mock storage_service
            mock_storage = mocker.patch('app.services.task_service.storage_service')
            mock_storage.delete_multiple_files.return_value = {
                'deleted': 2,
                'failed': 0,
                'errors': []
            }

            # 创建一个超过3天的已完成任务
            old_task = Task(
                user_id=test_user.id,
                model='sora-2',
                status='success',
                cost_points=100.00,
                prompt='old task',
                input_file_url=['https://cdn.test.com/uploads/input1.jpg'],
                result_url='https://cdn.test.com/uploads/result.mp4',
                finished_at=datetime.now(ZoneInfo("Asia/Shanghai")) - timedelta(days=4)
            )
            db_session.session.add(old_task)
            db_session.session.commit()
            old_task_id = old_task.id

            # 执行清理
            result = TaskService.cleanup_old_tasks(days=3)

            # 验证结果
            assert result['deleted'] == 1
            assert result['deleted_files'] == 2
            assert len(result['errors']) == 0

            # 验证任务已被删除
            task = Task.query.get(old_task_id)
            assert task is None

            # 验证删除文件被调用
            mock_storage.delete_multiple_files.assert_called_once()

    def test_cleanup_old_tasks_with_multiple_input_files(self, app, db_session, test_user, mocker):
        """测试清理包含多个输入文件的任务"""
        with app.app_context():
            mock_storage = mocker.patch('app.services.task_service.storage_service')
            mock_storage.delete_multiple_files.return_value = {
                'deleted': 4,
                'failed': 0,
                'errors': []
            }

            # 创建任务，包含多个输入文件
            old_task = Task(
                user_id=test_user.id,
                model='sora-2',
                status='success',
                cost_points=100.00,
                prompt='task with multiple files',
                input_file_url=[
                    'https://cdn.test.com/uploads/input1.jpg',
                    'https://cdn.test.com/uploads/input2.jpg',
                    'https://cdn.test.com/uploads/input3.jpg'
                ],
                result_url='https://cdn.test.com/uploads/result.mp4',
                finished_at=datetime.now(ZoneInfo("Asia/Shanghai")) - timedelta(days=5)
            )
            db_session.session.add(old_task)
            db_session.session.commit()

            result = TaskService.cleanup_old_tasks(days=3)

            assert result['deleted'] == 1
            assert result['deleted_files'] == 4

            # 验证删除了4个文件（3个输入 + 1个结果）
            call_args = mock_storage.delete_multiple_files.call_args[0][0]
            assert len(call_args) == 4

    def test_cleanup_old_tasks_not_delete_recent(self, app, db_session, test_user, mocker):
        """测试不清理未超过3天的任务"""
        with app.app_context():
            mock_storage = mocker.patch('app.services.task_service.storage_service')

            # 创建一个2天前的任务（不应该被清理）
            recent_task = Task(
                user_id=test_user.id,
                model='sora-2',
                status='success',
                cost_points=100.00,
                prompt='recent task',
                finished_at=datetime.now(ZoneInfo("Asia/Shanghai")) - timedelta(days=2)
            )
            db_session.session.add(recent_task)
            db_session.session.commit()
            recent_task_id = recent_task.id

            result = TaskService.cleanup_old_tasks(days=3)

            # 验证没有删除
            assert result['deleted'] == 0
            assert result['deleted_files'] == 0

            # 验证任务仍然存在
            task = Task.query.get(recent_task_id)
            assert task is not None

            # 验证没有调用删除文件
            mock_storage.delete_multiple_files.assert_not_called()

    def test_cleanup_old_tasks_not_delete_pending(self, app, db_session, test_user, mocker):
        """测试不清理未完成的任务"""
        with app.app_context():
            mock_storage = mocker.patch('app.services.task_service.storage_service')

            # 创建一个超过3天但状态为pending的任务（不应该被清理）
            pending_task = Task(
                user_id=test_user.id,
                model='sora-2',
                status='pending',
                cost_points=100.00,
                prompt='pending task',
                finished_at=datetime.now(ZoneInfo("Asia/Shanghai")) - timedelta(days=5)
            )
            db_session.session.add(pending_task)
            db_session.session.commit()
            pending_task_id = pending_task.id

            result = TaskService.cleanup_old_tasks(days=3)

            # 验证没有删除
            assert result['deleted'] == 0

            # 验证任务仍然存在
            task = Task.query.get(pending_task_id)
            assert task is not None

            mock_storage.delete_multiple_files.assert_not_called()

    def test_cleanup_old_tasks_not_delete_without_finished_at(self, app, db_session, test_user, mocker):
        """测试不清理没有finished_at的任务"""
        with app.app_context():
            mock_storage = mocker.patch('app.services.task_service.storage_service')

            # 创建一个没有finished_at的任务
            task = Task(
                user_id=test_user.id,
                model='sora-2',
                status='processing',
                cost_points=100.00,
                prompt='task without finished_at',
                finished_at=None
            )
            db_session.session.add(task)
            db_session.session.commit()
            task_id = task.id

            result = TaskService.cleanup_old_tasks(days=3)

            # 验证没有删除
            assert result['deleted'] == 0

            # 验证任务仍然存在
            task = Task.query.get(task_id)
            assert task is not None

    def test_cleanup_old_tasks_multiple_statuses(self, app, db_session, test_user, mocker):
        """测试清理多种状态的任务（success, failed, cancelled）"""
        with app.app_context():
            mock_storage = mocker.patch('app.services.task_service.storage_service')
            mock_storage.delete_multiple_files.return_value = {
                'deleted': 0,
                'failed': 0,
                'errors': []
            }

            # 创建不同状态的旧任务
            statuses = ['success', 'failed', 'cancelled']
            task_ids = []

            for status in statuses:
                task = Task(
                    user_id=test_user.id,
                    model='sora-2',
                    status=status,
                    cost_points=100.00,
                    prompt=f'{status} task',
                    finished_at=datetime.now(ZoneInfo("Asia/Shanghai")) - timedelta(days=4)
                )
                db_session.session.add(task)
                db_session.session.commit()
                task_ids.append(task.id)

            result = TaskService.cleanup_old_tasks(days=3)

            # 验证所有3个任务都被删除
            assert result['deleted'] == 3

            # 验证所有任务都不存在
            for task_id in task_ids:
                task = Task.query.get(task_id)
                assert task is None

    def test_cleanup_old_tasks_with_file_deletion_error(self, app, db_session, test_user, mocker):
        """测试文件删除失败时的处理"""
        with app.app_context():
            mock_storage = mocker.patch('app.services.task_service.storage_service')
            mock_storage.delete_multiple_files.return_value = {
                'deleted': 1,
                'failed': 1,
                'errors': [{'key': 'uploads/failed.jpg', 'error': 'Access Denied'}]
            }

            old_task = Task(
                user_id=test_user.id,
                model='sora-2',
                status='success',
                cost_points=100.00,
                prompt='task with file error',
                input_file_url=['https://cdn.test.com/uploads/input.jpg'],
                result_url='https://cdn.test.com/uploads/result.mp4',
                finished_at=datetime.now(ZoneInfo("Asia/Shanghai")) - timedelta(days=4)
            )
            db_session.session.add(old_task)
            db_session.session.commit()
            old_task_id = old_task.id

            result = TaskService.cleanup_old_tasks(days=3)

            # 任务应该仍然被删除，即使文件删除部分失败
            assert result['deleted'] == 1
            assert result['deleted_files'] == 1
            assert len(result['errors']) > 0

            # 验证任务已被删除
            task = Task.query.get(old_task_id)
            assert task is None

    def test_cleanup_old_tasks_custom_days(self, app, db_session, test_user, mocker):
        """测试自定义保留天数"""
        with app.app_context():
            mock_storage = mocker.patch('app.services.task_service.storage_service')
            mock_storage.delete_multiple_files.return_value = {
                'deleted': 0,
                'failed': 0,
                'errors': []
            }

            # 创建一个4天前的任务
            task = Task(
                user_id=test_user.id,
                model='sora-2',
                status='success',
                cost_points=100.00,
                prompt='task',
                finished_at=datetime.now(ZoneInfo("Asia/Shanghai")) - timedelta(days=4)
            )
            db_session.session.add(task)
            db_session.session.commit()
            task_id = task.id

            # 使用5天作为保留期（4天前的任务不应该被删除）
            result = TaskService.cleanup_old_tasks(days=5)

            assert result['deleted'] == 0

            # 验证任务仍然存在
            task = Task.query.get(task_id)
            assert task is not None

            # 使用3天作为保留期（4天前的任务应该被删除）
            result = TaskService.cleanup_old_tasks(days=3)

            assert result['deleted'] == 1

            # 验证任务已被删除
            task = Task.query.get(task_id)
            assert task is None

    def test_cleanup_old_tasks_without_files(self, app, db_session, test_user, mocker):
        """测试清理没有关联文件的任务"""
        with app.app_context():
            mock_storage = mocker.patch('app.services.task_service.storage_service')

            # 创建没有文件的任务
            old_task = Task(
                user_id=test_user.id,
                model='sora-2',
                status='success',
                cost_points=100.00,
                prompt='task without files',
                input_file_url=None,
                result_url=None,
                finished_at=datetime.now(ZoneInfo("Asia/Shanghai")) - timedelta(days=4)
            )
            db_session.session.add(old_task)
            db_session.session.commit()
            old_task_id = old_task.id

            result = TaskService.cleanup_old_tasks(days=3)

            # 任务应该被删除
            assert result['deleted'] == 1
            assert result['deleted_files'] == 0

            # 验证任务已被删除
            task = Task.query.get(old_task_id)
            assert task is None

            # 不应该调用文件删除
            mock_storage.delete_multiple_files.assert_not_called()

    def test_cleanup_old_tasks_with_empty_input_file_list(self, app, db_session, test_user, mocker):
        """测试input_file_url为空列表的情况"""
        with app.app_context():
            mock_storage = mocker.patch('app.services.task_service.storage_service')
            mock_storage.delete_multiple_files.return_value = {
                'deleted': 1,
                'failed': 0,
                'errors': []
            }

            old_task = Task(
                user_id=test_user.id,
                model='sora-2',
                status='success',
                cost_points=100.00,
                prompt='task',
                input_file_url=[],  # 空列表
                result_url='https://cdn.test.com/uploads/result.mp4',
                finished_at=datetime.now(ZoneInfo("Asia/Shanghai")) - timedelta(days=4)
            )
            db_session.session.add(old_task)
            db_session.session.commit()

            result = TaskService.cleanup_old_tasks(days=3)

            assert result['deleted'] == 1
            assert result['deleted_files'] == 1

            # 应该只删除result文件
            call_args = mock_storage.delete_multiple_files.call_args[0][0]
            assert len(call_args) == 1

    def test_cleanup_old_tasks_batch_cleanup(self, app, db_session, test_user, mocker):
        """测试批量清理多个任务"""
        with app.app_context():
            mock_storage = mocker.patch('app.services.task_service.storage_service')
            mock_storage.delete_multiple_files.return_value = {
                'deleted': 2,
                'failed': 0,
                'errors': []
            }

            # 创建10个旧任务
            for i in range(10):
                task = Task(
                    user_id=test_user.id,
                    model='sora-2',
                    status='success',
                    cost_points=100.00,
                    prompt=f'task {i}',
                    input_file_url=[f'https://cdn.test.com/uploads/input{i}.jpg'],
                    result_url=f'https://cdn.test.com/uploads/result{i}.mp4',
                    finished_at=datetime.now(ZoneInfo("Asia/Shanghai")) - timedelta(days=4)
                )
                db_session.session.add(task)
            db_session.session.commit()

            result = TaskService.cleanup_old_tasks(days=3)

            # 验证所有10个任务都被删除
            assert result['deleted'] == 10
            # 每个任务有2个文件（1个输入 + 1个结果），共20个文件
            assert result['deleted_files'] == 20

            # 验证删除文件被调用10次（每个任务一次）
            assert mock_storage.delete_multiple_files.call_count == 10
