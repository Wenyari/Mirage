"""
模型管理服务测试
测试模型的增删改查功能
"""
import pytest
from app.services.admin.model_service import (
    get_model_list,
    create_model,
    update_model,
    delete_model
)
from app.models import Model, ModelConfig, ApiKey, Task


@pytest.mark.unit
class TestModelService:
    """模型管理服务测试类"""

    def test_get_model_list_empty(self, app, db_session):
        """测试获取空模型列表"""
        with app.app_context():
            # 删除测试数据中的模型
            Model.query.delete()
            db_session.session.commit()

            models = get_model_list()
            assert isinstance(models, list)
            assert len(models) == 0

    def test_get_model_list_with_data(self, app, db_session):
        """测试获取有数据的模型列表"""
        with app.app_context():
            # 先清空已有模型
            Model.query.delete()
            db_session.session.commit()

            # 创建测试模型
            model1 = Model(key='test-model-1', name='Test Model 1', enabled=1)
            model2 = Model(key='test-model-2', name='Test Model 2', enabled=0)
            db_session.session.add(model1)
            db_session.session.add(model2)
            db_session.session.commit()

            models = get_model_list()
            assert len(models) == 2
            assert models[0]['key'] == 'test-model-1'
            assert models[0]['name'] == 'Test Model 1'
            assert models[0]['enabled'] == 1

    def test_create_model_success(self, app, db_session):
        """测试成功创建模型"""
        with app.app_context():
            result = create_model(
                key='gpt-4-turbo',
                name='GPT-4 Turbo',
                enabled=True,
                description='OpenAI GPT-4 Turbo model',
                color='bg-blue-500',
                icon_url='https://example.com/icon.png',
                max_concurrency_limit=30
            )

            assert result['key'] == 'gpt-4-turbo'
            assert result['name'] == 'GPT-4 Turbo'
            assert result['enabled'] == 1
            assert result['description'] == 'OpenAI GPT-4 Turbo model'
            assert result['max_concurrency_limit'] == 30

            # 验证数据库中存在
            model = Model.query.filter_by(key='gpt-4-turbo').first()
            assert model is not None
            assert model.name == 'GPT-4 Turbo'

    def test_create_model_invalid_key_format(self, app, db_session):
        """测试使用无效key格式创建模型"""
        with app.app_context():
            # 包含大写字母
            with pytest.raises(ValueError, match="must contain only lowercase letters"):
                create_model(
                    key='GPT-4',
                    name='GPT-4'
                )

            # 包含空格
            with pytest.raises(ValueError, match="must contain only lowercase letters"):
                create_model(
                    key='gpt 4',
                    name='GPT-4'
                )

            # 包含特殊字符
            with pytest.raises(ValueError, match="must contain only lowercase letters"):
                create_model(
                    key='gpt@4',
                    name='GPT-4'
                )

    def test_create_model_duplicate_key(self, app, db_session):
        """测试创建重复key的模型"""
        with app.app_context():
            # 创建第一个模型
            create_model(key='claude-3', name='Claude 3')

            # 尝试创建重复key的模型
            with pytest.raises(ValueError, match="already exists"):
                create_model(key='claude-3', name='Claude 3 Duplicate')

    def test_update_model_success(self, app, db_session):
        """测试成功更新模型"""
        with app.app_context():
            # 创建模型
            model = Model(key='gemini-pro', name='Gemini Pro', enabled=1)
            db_session.session.add(model)
            db_session.session.commit()

            # 更新模型
            result = update_model(
                key='gemini-pro',
                name='Gemini Pro Updated',
                enabled=False,
                description='Updated description',
                max_concurrency_limit=25
            )

            assert result['name'] == 'Gemini Pro Updated'
            assert result['enabled'] == 0
            assert result['description'] == 'Updated description'
            assert result['max_concurrency_limit'] == 25

    def test_update_model_not_found(self, app, db_session):
        """测试更新不存在的模型"""
        with app.app_context():
            with pytest.raises(ValueError, match="not found"):
                update_model(key='non-existent-model', name='New Name')

    def test_update_model_partial(self, app, db_session):
        """测试部分更新模型"""
        with app.app_context():
            # 创建模型
            model = Model(
                key='test-partial',
                name='Original Name',
                enabled=1,
                description='Original Description'
            )
            db_session.session.add(model)
            db_session.session.commit()

            # 只更新名称
            update_model(key='test-partial', name='New Name')

            updated = Model.query.filter_by(key='test-partial').first()
            assert updated.name == 'New Name'
            assert updated.enabled == 1  # 未修改
            assert updated.description == 'Original Description'  # 未修改

    def test_delete_model_success(self, app, db_session):
        """测试成功删除模型"""
        with app.app_context():
            # 创建模型
            model = Model(key='delete-test', name='Delete Test')
            db_session.session.add(model)
            db_session.session.commit()

            # 删除模型
            result = delete_model('delete-test')
            assert 'message' in result

            # 验证已删除
            deleted = Model.query.filter_by(key='delete-test').first()
            assert deleted is None

    def test_delete_model_not_found(self, app, db_session):
        """测试删除不存在的模型"""
        with app.app_context():
            with pytest.raises(ValueError, match="not found"):
                delete_model('non-existent')

    def test_delete_model_with_keys(self, app, db_session):
        """测试删除有关联密钥的模型"""
        with app.app_context():
            # 创建模型
            model = Model(key='with-keys', name='With Keys')
            db_session.session.add(model)
            db_session.session.commit()

            # 创建关联的密钥
            api_key = ApiKey(
                model='with-keys',
                api_base='https://api.example.com',
                key_secret='sk-test-123',
                max_concurrency=3
            )
            db_session.session.add(api_key)
            db_session.session.commit()

            # 尝试删除
            with pytest.raises(ValueError, match="Cannot delete model with existing keys or tasks"):
                delete_model('with-keys')

    def test_delete_model_with_tasks(self, app, db_session, test_user):
        """测试删除有关联任务的模型"""
        with app.app_context():
            # 创建模型
            model = Model(key='with-tasks', name='With Tasks')
            db_session.session.add(model)
            db_session.session.commit()

            # 创建关联的任务
            task = Task(
                user_id=test_user.id,
                model='with-tasks',
                prompt='Test prompt',
                status='pending',
                cost_points=10.0
            )
            db_session.session.add(task)
            db_session.session.commit()

            # 尝试删除
            with pytest.raises(ValueError, match="Cannot delete model with existing keys or tasks"):
                delete_model('with-tasks')

    def test_delete_model_with_config(self, app, db_session):
        """测试删除有配置的模型时也删除配置"""
        with app.app_context():
            # 创建模型
            model = Model(key='with-config', name='With Config')
            db_session.session.add(model)
            db_session.session.commit()

            # 创建配置
            config = ModelConfig(
                model='with-config',
                allowed_tiers=['T1', 'T2'],
                cost_per_call=10.0,
                token_cost_config={'enabled': False}
            )
            db_session.session.add(config)
            db_session.session.commit()

            # 删除模型
            delete_model('with-config')

            # 验证配置也被删除
            deleted_config = ModelConfig.query.filter_by(model='with-config').first()
            assert deleted_config is None
