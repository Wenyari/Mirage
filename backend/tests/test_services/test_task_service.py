"""
任务服务测试
"""
import pytest
from app.services.task_service import (
    get_user_concurrency_limit,
    get_model_price,
    submit_task
)
from app.models import Task


@pytest.mark.unit
class TestTaskService:
    """任务服务测试类"""

    def test_get_user_concurrency_limit(self, app, db_session, test_user):
        """测试获取用户并发限制"""
        with app.app_context():
            # T1 用户应该有 1 个并发限制
            limit = get_user_concurrency_limit(test_user.id)
            assert limit == 1

            # 修改为 T3
            test_user.level = 3
            db_session.session.commit()

            limit = get_user_concurrency_limit(test_user.id)
            assert limit == 3

    def test_get_user_concurrency_limit_user_not_found(self, app, db_session):
        """测试用户不存在"""
        with app.app_context():
            with pytest.raises(ValueError, match="User not found"):
                get_user_concurrency_limit(99999)

    def test_get_model_price(self, app, db_session, redis_db):
        """测试获取模型价格"""
        with app.app_context():
            price = get_model_price('sora-v2')
            assert price == 100.00

            price = get_model_price('sora-turbo')
            assert price == 50.00

            # 验证缓存
            cache_key = "config:pricing:sora-v2"
            cached_price = redis_db.get(cache_key)
            assert float(cached_price) == 100.00

    def test_get_model_price_not_found(self, app, db_session):
        """测试模型不存在"""
        with app.app_context():
            with pytest.raises(ValueError, match="Model .* not found"):
                get_model_price('nonexistent-model')

    def test_submit_task_success(self, app, db_session, redis_db, test_user, mocker):
        """测试提交任务成功"""
        with app.app_context():
            # Mock RQ 队列
            mock_queue = mocker.patch('app.services.task_service.Queue')

            task_data = {
                'model': 'sora-v2',
                'prompt': 'Test prompt',
                'params': {'duration': 1}
            }

            task_id = submit_task(test_user.id, task_data)

            assert task_id is not None

            # 验证任务创建
            task = Task.query.get(task_id)
            assert task is not None
            assert task.user_id == test_user.id
            assert task.model_name == 'sora-v2'
            assert task.status == 'pending'
            assert task.cost_points == 100.00  # 基础价格 100 * 时长 1

            # 验证余额扣除
            db_session.session.refresh(test_user)
            assert test_user.balance == 900.00  # 1000 - 100

    def test_submit_task_concurrency_limit(self, app, db_session, test_user):
        """测试并发限制"""
        with app.app_context():
            # T1 用户只能有 1 个并发任务
            # 先创建一个 pending 任务
            task1 = Task(
                user_id=test_user.id,
                model_name='sora-v2',
                status='pending',
                cost_points=100.00
            )
            db_session.session.add(task1)
            db_session.session.commit()

            # 尝试提交第二个任务
            task_data = {
                'model': 'sora-v2',
                'prompt': 'Test',
                'params': {'duration': 1}
            }

            with pytest.raises(ValueError, match="Task limit exceeded"):
                submit_task(test_user.id, task_data)

    def test_submit_task_insufficient_balance(self, app, db_session, test_user):
        """测试余额不足"""
        with app.app_context():
            # 设置余额为 50
            test_user.balance = 50.00
            db_session.session.commit()

            # 尝试提交需要 100 的任务
            task_data = {
                'model': 'sora-v2',
                'prompt': 'Test',
                'params': {'duration': 1}
            }

            with pytest.raises(ValueError, match="Insufficient balance"):
                submit_task(test_user.id, task_data)

    def test_submit_task_user_not_found(self, app, db_session):
        """测试用户不存在"""
        with app.app_context():
            task_data = {
                'model': 'sora-v2',
                'prompt': 'Test',
                'params': {'duration': 1}
            }

            with pytest.raises(ValueError, match="User not found"):
                submit_task(99999, task_data)

    def test_submit_task_model_not_found(self, app, db_session, test_user):
        """测试模型不存在"""
        with app.app_context():
            task_data = {
                'model': 'nonexistent-model',
                'prompt': 'Test',
                'params': {'duration': 1}
            }

            with pytest.raises(ValueError):
                submit_task(test_user.id, task_data)
