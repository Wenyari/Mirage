"""
任务模型测试
"""
import pytest
from datetime import datetime
from app.models import Task, ModelPricing


@pytest.mark.unit
class TestTaskModel:
    """任务模型测试类"""

    def test_create_task(self, db_session, test_user):
        """测试创建任务"""
        task = Task(
            user_id=test_user.id,
            model_name='sora-v2',
            prompt='A beautiful sunset',
            input_file_url='https://example.com/input.jpg',
            params={'duration': 5, 'quality': 'hd'},
            status='pending',
            cost_points=100.00
        )

        db_session.session.add(task)
        db_session.session.commit()

        assert task.id is not None
        assert task.user_id == test_user.id
        assert task.model_name == 'sora-v2'
        assert task.status == 'pending'
        assert task.cost_points == 100.00
        assert task.params['duration'] == 5

    def test_task_status_enum(self, db_session, test_user):
        """测试任务状态枚举"""
        statuses = ['pending', 'processing', 'success', 'failed']

        for status in statuses:
            task = Task(
                user_id=test_user.id,
                model_name='sora-v2',
                status=status,
                cost_points=50.00
            )
            db_session.session.add(task)
            db_session.session.commit()

            assert task.status == status

    def test_task_to_dict(self, test_task):
        """测试任务转字典方法"""
        task_dict = test_task.to_dict()

        assert isinstance(task_dict, dict)
        assert task_dict['id'] == test_task.id
        assert task_dict['user_id'] == test_task.user_id
        assert task_dict['model_name'] == test_task.model_name
        assert task_dict['status'] == test_task.status
        assert task_dict['cost_points'] == float(test_task.cost_points)

    def test_task_update_status(self, db_session, test_task):
        """测试更新任务状态"""
        test_task.status = 'processing'
        db_session.session.commit()

        assert test_task.status == 'processing'

        test_task.status = 'success'
        test_task.result_url = 'https://example.com/result.mp4'
        test_task.finished_at = datetime.now(ZoneInfo("Asia/Shanghai"))
        db_session.session.commit()

        assert test_task.status == 'success'
        assert test_task.result_url is not None
        assert test_task.finished_at is not None


@pytest.mark.unit
class TestModelPricingModel:
    """模型定价测试类"""

    def test_model_pricing_exists(self, db_session):
        """测试模型定价初始化"""
        pricings = ModelPricing.query.all()

        assert len(pricings) >= 2

        sora = ModelPricing.query.filter_by(model_key='sora-v2').first()
        assert sora is not None
        assert sora.base_cost == 100.00
        assert sora.is_active == 1

    def test_model_pricing_to_dict(self, db_session):
        """测试模型定价转字典方法"""
        pricing = ModelPricing.query.filter_by(model_key='sora-v2').first()
        pricing_dict = pricing.to_dict()

        assert isinstance(pricing_dict, dict)
        assert pricing_dict['model_key'] == 'sora-v2'
        assert pricing_dict['base_cost'] == 100.00
        assert pricing_dict['is_active'] == 1
