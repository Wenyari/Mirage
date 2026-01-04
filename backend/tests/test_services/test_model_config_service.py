"""
模型配置管理服务测试
测试模型计费规则和权限配置的管理功能
"""
import pytest
from app.services.admin.model_config_service import (
    get_model_config_list,
    get_available_models,
    create_model_config,
    update_model_config,
    delete_model_config
)
from app.models import Model, ModelConfig, ApiKey


@pytest.mark.unit
class TestModelConfigService:
    """模型配置管理服务测试类"""

    def test_get_model_config_list_empty(self, app, db_session):
        """测试获取空模型配置列表"""
        with app.app_context():
            ModelConfig.query.delete()
            db_session.session.commit()

            configs = get_model_config_list()
            assert isinstance(configs, list)
            assert len(configs) == 0

    def test_get_model_config_list_with_data(self, app, db_session):
        """测试获取有数据的模型配置列表"""
        with app.app_context():
            # 创建模型和配置
            model = Model(key='test-config', name='Test Config Model')
            db_session.session.add(model)

            config = ModelConfig(
                model='test-config',
                allowed_tiers=['T1', 'T2'],
                cost_per_call=10.0,
                token_cost_config={'enabled': False}
            )
            db_session.session.add(config)
            db_session.session.commit()

            configs = get_model_config_list()
            assert len(configs) >= 1

            # 查找测试配置
            test_config = next((c for c in configs if c['model'] == 'test-config'), None)
            assert test_config is not None
            assert test_config['model_name'] == 'Test Config Model'
            assert test_config['allowed_tiers'] == ['T1', 'T2']
            assert test_config['cost_per_call'] == 10.0

    def test_get_available_models(self, app, db_session):
        """测试获取可配置的模型列表"""
        with app.app_context():
            # 创建模型
            model1 = Model(key='available-1', name='Available 1')
            model2 = Model(key='available-2', name='Available 2')
            db_session.session.add_all([model1, model2])
            db_session.session.commit()

            # 为 model1 创建配置
            config = ModelConfig(
                model='available-1',
                allowed_tiers=['T1'],
                cost_per_call=10.0,
                token_cost_config={'enabled': False}
            )
            db_session.session.add(config)

            # 为 model1 创建密钥
            key = ApiKey(model='available-1', api_base='', key_secret='sk-test')
            db_session.session.add(key)
            db_session.session.commit()

            models = get_available_models()

            # 查找测试模型
            m1 = next((m for m in models if m['model'] == 'available-1'), None)
            m2 = next((m for m in models if m['model'] == 'available-2'), None)

            assert m1 is not None
            assert m1['has_config'] is True
            assert m1['key_count'] == 1

            assert m2 is not None
            assert m2['has_config'] is False
            assert m2['key_count'] == 0

    def test_create_model_config_success(self, app, db_session):
        """测试成功创建模型配置"""
        with app.app_context():
            # 创建模型
            model = Model(key='create-config', name='Create Config')
            db_session.session.add(model)
            db_session.session.commit()

            result = create_model_config(
                model='create-config',
                allowed_tiers=['T2', 'T3', 'T4', 'T5'],
                cost_per_call=20.0,
                token_cost_config={
                    'enabled': True,
                    'input_cost': 0.04,
                    'output_cost': 0.08
                },
                is_active=True,
                description='Test configuration'
            )

            assert result['model'] == 'create-config'
            assert result['model_name'] == 'Create Config'
            assert result['allowed_tiers'] == ['T2', 'T3', 'T4', 'T5']
            assert result['cost_per_call'] == 20.0
            assert result['token_cost_config']['enabled'] is True
            assert result['is_active'] == 1

            # 验证数据库
            config = ModelConfig.query.filter_by(model='create-config').first()
            assert config is not None

    def test_create_model_config_model_not_found(self, app, db_session):
        """测试创建配置时模型不存在"""
        with app.app_context():
            with pytest.raises(ValueError, match="not found"):
                create_model_config(
                    model='non-existent',
                    allowed_tiers=['T1'],
                    cost_per_call=10.0,
                    token_cost_config={'enabled': False}
                )

    def test_create_model_config_duplicate(self, app, db_session):
        """测试创建重复的模型配置"""
        with app.app_context():
            model = Model(key='duplicate-config', name='Duplicate')
            db_session.session.add(model)
            db_session.session.commit()

            # 创建第一个配置
            create_model_config(
                model='duplicate-config',
                allowed_tiers=['T1'],
                cost_per_call=10.0,
                token_cost_config={'enabled': False}
            )

            # 尝试创建重复配置
            with pytest.raises(ValueError, match="already exists"):
                create_model_config(
                    model='duplicate-config',
                    allowed_tiers=['T2'],
                    cost_per_call=20.0,
                    token_cost_config={'enabled': False}
                )

    def test_create_model_config_invalid_tiers(self, app, db_session):
        """测试使用无效等级创建配置"""
        with app.app_context():
            model = Model(key='invalid-tier', name='Invalid Tier')
            db_session.session.add(model)
            db_session.session.commit()

            # 空数组
            with pytest.raises(ValueError, match="must be a non-empty array"):
                create_model_config(
                    model='invalid-tier',
                    allowed_tiers=[],
                    cost_per_call=10.0,
                    token_cost_config={'enabled': False}
                )

            # 无效等级名称
            with pytest.raises(ValueError, match="Invalid tier"):
                create_model_config(
                    model='invalid-tier',
                    allowed_tiers=['T1', 'T6'],  # T6 不存在
                    cost_per_call=10.0,
                    token_cost_config={'enabled': False}
                )

    def test_create_model_config_invalid_token_config(self, app, db_session):
        """测试使用无效Token配置创建"""
        with app.app_context():
            model = Model(key='invalid-token', name='Invalid Token')
            db_session.session.add(model)
            db_session.session.commit()

            # 缺少 enabled 字段
            with pytest.raises(ValueError, match="enabled is required"):
                create_model_config(
                    model='invalid-token',
                    allowed_tiers=['T1'],
                    cost_per_call=10.0,
                    token_cost_config={}
                )

            # enabled=true 但缺少费率
            with pytest.raises(ValueError, match="input_cost and output_cost are required"):
                create_model_config(
                    model='invalid-token',
                    allowed_tiers=['T1'],
                    cost_per_call=10.0,
                    token_cost_config={'enabled': True}
                )

    def test_update_model_config_success(self, app, db_session):
        """测试成功更新模型配置"""
        with app.app_context():
            model = Model(key='update-config', name='Update Config')
            db_session.session.add(model)

            config = ModelConfig(
                model='update-config',
                allowed_tiers=['T1'],
                cost_per_call=10.0,
                token_cost_config={'enabled': False}
            )
            db_session.session.add(config)
            db_session.session.commit()

            update_model_config(
                config_id=config.id,
                allowed_tiers=['T1', 'T2', 'T3'],
                cost_per_call=15.0,
                token_cost_config={
                    'enabled': True,
                    'input_cost': 0.03,
                    'output_cost': 0.06
                },
                is_active=False,
                description='Updated'
            )

            updated = ModelConfig.query.get(config.id)
            assert updated.allowed_tiers == ['T1', 'T2', 'T3']
            assert float(updated.cost_per_call) == 15.0
            assert updated.token_cost_config['enabled'] is True
            assert updated.is_active == 0
            assert updated.description == 'Updated'

    def test_update_model_config_not_found(self, app, db_session):
        """测试更新不存在的配置"""
        with app.app_context():
            with pytest.raises(ValueError, match="not found"):
                update_model_config(config_id=99999, cost_per_call=10.0)

    def test_update_model_config_partial(self, app, db_session):
        """测试部分更新模型配置"""
        with app.app_context():
            model = Model(key='partial-update', name='Partial Update')
            db_session.session.add(model)

            config = ModelConfig(
                model='partial-update',
                allowed_tiers=['T1', 'T2'],
                cost_per_call=10.0,
                token_cost_config={'enabled': False},
                description='Original'
            )
            db_session.session.add(config)
            db_session.session.commit()

            # 只更新 cost_per_call
            update_model_config(config_id=config.id, cost_per_call=20.0)

            updated = ModelConfig.query.get(config.id)
            assert float(updated.cost_per_call) == 20.0
            assert updated.allowed_tiers == ['T1', 'T2']  # 未修改
            assert updated.description == 'Original'  # 未修改

    def test_update_model_config_negative_cost(self, app, db_session):
        """测试使用负数费用更新"""
        with app.app_context():
            model = Model(key='negative-cost', name='Negative Cost')
            db_session.session.add(model)

            config = ModelConfig(
                model='negative-cost',
                allowed_tiers=['T1'],
                cost_per_call=10.0,
                token_cost_config={'enabled': False}
            )
            db_session.session.add(config)
            db_session.session.commit()

            with pytest.raises(ValueError, match="must be non-negative"):
                update_model_config(config_id=config.id, cost_per_call=-10.0)

    def test_delete_model_config_success(self, app, db_session):
        """测试成功删除模型配置"""
        with app.app_context():
            model = Model(key='delete-config', name='Delete Config')
            db_session.session.add(model)

            config = ModelConfig(
                model='delete-config',
                allowed_tiers=['T1'],
                cost_per_call=10.0,
                token_cost_config={'enabled': False}
            )
            db_session.session.add(config)
            db_session.session.commit()

            config_id = config.id
            delete_model_config(config_id)

            deleted = ModelConfig.query.get(config_id)
            assert deleted is None

    def test_delete_model_config_not_found(self, app, db_session):
        """测试删除不存在的配置"""
        with app.app_context():
            with pytest.raises(ValueError, match="not found"):
                delete_model_config(99999)
