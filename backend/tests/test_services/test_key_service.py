"""
密钥管理服务测试
测试密钥的增删改查、状态监控和统计功能
"""
import pytest
from app.services.admin.key_service import (
    get_key_list,
    create_key,
    batch_create_keys,
    update_key,
    delete_key,
    trigger_cooldown,
    get_key_stats
)
from app.models import Model, ApiKey
from app.extensions import redis_client


@pytest.mark.unit
class TestKeyService:
    """密钥管理服务测试类"""

    def setup_method(self):
        """每个测试方法执行前的设置"""
        # 清理 Redis 测试数据
        try:
            if redis_client:
                # 只清理测试相关的 key
                for key in redis_client.scan_iter("pool:*"):
                    redis_client.delete(key)
        except Exception:
            pass

    def test_get_key_list_empty(self, app, db_session):
        """测试获取空密钥列表"""
        with app.app_context():
            ApiKey.query.delete()
            db_session.session.commit()

            keys = get_key_list()
            assert isinstance(keys, list)
            assert len(keys) == 0

    def test_get_key_list_with_data(self, app, db_session):
        """测试获取有数据的密钥列表"""
        with app.app_context():
            # 创建测试模型
            model = Model(key='test-model', name='Test Model')
            db_session.session.add(model)
            db_session.session.commit()

            # 创建测试密钥
            key1 = ApiKey(
                model='test-model',
                api_base='https://api.test.com',
                key_secret='sk-test-123',
                max_concurrency=3,
                weight=10
            )
            key2 = ApiKey(
                model='test-model',
                api_base='https://api.test.com',
                key_secret='sk-test-456',
                max_concurrency=5,
                weight=20
            )
            db_session.session.add(key1)
            db_session.session.add(key2)
            db_session.session.commit()

            keys = get_key_list()
            assert len(keys) == 2
            assert 'current_usage' in keys[0]
            assert 'is_cooling' in keys[0]
            assert keys[0]['current_usage'] == 0  # 默认值

    def test_get_key_list_with_filter(self, app, db_session):
        """测试带模型筛选的密钥列表"""
        with app.app_context():
            # 创建两个模型
            model1 = Model(key='model-1', name='Model 1')
            model2 = Model(key='model-2', name='Model 2')
            db_session.session.add_all([model1, model2])
            db_session.session.commit()

            # 创建不同模型的密钥
            key1 = ApiKey(model='model-1', api_base='https://api.test.com', key_secret='sk-1')
            key2 = ApiKey(model='model-2', api_base='https://api.test.com', key_secret='sk-2')
            db_session.session.add_all([key1, key2])
            db_session.session.commit()

            # 筛选 model-1 的密钥
            keys = get_key_list(model_filter='model-1')
            assert len(keys) == 1
            assert keys[0]['model'] == 'model-1'

    def test_create_key_success(self, app, db_session):
        """测试成功创建密钥"""
        with app.app_context():
            # 使用已存在的模型 (由 conftest.py 初始化)
            result = create_key(
                model='openai',
                api_base='https://api.openai.com/v1',
                key_secret='sk-proj-abc123',
                max_concurrency=5,
                weight=15
            )

            assert result['model'] == 'openai'
            assert result['api_base'] == 'https://api.openai.com/v1'
            assert 'key_secret_preview' in result
            assert result['max_concurrency'] == 5
            assert result['weight'] == 15

            # 验证数据库
            key = ApiKey.query.filter_by(key_secret='sk-proj-abc123').first()
            assert key is not None

    def test_create_key_model_not_found(self, app, db_session):
        """测试创建密钥时模型不存在"""
        with app.app_context():
            with pytest.raises(ValueError, match="not found"):
                create_key(
                    model='non-existent',
                    api_base='https://api.test.com',
                    key_secret='sk-test'
                )

    def test_create_key_invalid_concurrency(self, app, db_session):
        """测试使用无效并发数创建密钥"""
        with app.app_context():
            model = Model(key='test', name='Test')
            db_session.session.add(model)
            db_session.session.commit()

            # 并发数太小
            with pytest.raises(ValueError, match="must be between 1 and 100"):
                create_key(model='test', api_base='', key_secret='sk-test', max_concurrency=0)

            # 并发数太大
            with pytest.raises(ValueError, match="must be between 1 and 100"):
                create_key(model='test', api_base='', key_secret='sk-test', max_concurrency=101)

    def test_create_key_invalid_weight(self, app, db_session):
        """测试使用无效权重创建密钥"""
        with app.app_context():
            model = Model(key='test', name='Test')
            db_session.session.add(model)
            db_session.session.commit()

            # 权重太小
            with pytest.raises(ValueError, match="must be between 1 and 100"):
                create_key(model='test', api_base='', key_secret='sk-test', weight=0)

            # 权重太大
            with pytest.raises(ValueError, match="must be between 1 and 100"):
                create_key(model='test', api_base='', key_secret='sk-test', weight=101)

    def test_batch_create_keys_success(self, app, db_session):
        """测试批量创建密钥成功"""
        with app.app_context():
            model = Model(key='batch-test', name='Batch Test')
            db_session.session.add(model)
            db_session.session.commit()

            keys = ['sk-key-1', 'sk-key-2', 'sk-key-3']
            result = batch_create_keys(
                model='batch-test',
                api_base='https://api.test.com',
                keys=keys,
                max_concurrency=3,
                weight=10
            )

            assert result['success_count'] == 3
            assert result['failed_count'] == 0
            assert len(result['failed_keys']) == 0

            # 验证数据库
            created = ApiKey.query.filter_by(model='batch-test').count()
            assert created == 3

    def test_batch_create_keys_exceed_limit(self, app, db_session):
        """测试批量创建超过限制"""
        with app.app_context():
            model = Model(key='test', name='Test')
            db_session.session.add(model)
            db_session.session.commit()

            keys = [f'sk-key-{i}' for i in range(101)]  # 101个密钥
            with pytest.raises(ValueError, match="Cannot add more than 100 keys"):
                batch_create_keys(model='test', api_base='', keys=keys)

    def test_batch_create_keys_model_not_found(self, app, db_session):
        """测试批量创建时模型不存在"""
        with app.app_context():
            with pytest.raises(ValueError, match="not found"):
                batch_create_keys(
                    model='non-existent',
                    api_base='',
                    keys=['sk-1', 'sk-2']
                )

    def test_update_key_success(self, app, db_session):
        """测试成功更新密钥"""
        with app.app_context():
            model = Model(key='update-test', name='Update Test')
            db_session.session.add(model)
            key = ApiKey(
                model='update-test',
                api_base='https://api.test.com',
                key_secret='sk-update',
                max_concurrency=3,
                weight=10
            )
            db_session.session.add(key)
            db_session.session.commit()

            update_key(
                key_id=key.id,
                max_concurrency=10,
                weight=20,
                status=0
            )

            updated = ApiKey.query.get(key.id)
            assert updated.max_concurrency == 10
            assert updated.weight == 20
            assert updated.status == 0

    def test_update_key_not_found(self, app, db_session):
        """测试更新不存在的密钥"""
        with app.app_context():
            with pytest.raises(ValueError, match="not found"):
                update_key(key_id=99999, max_concurrency=5)

    def test_delete_key_success(self, app, db_session):
        """测试成功删除密钥"""
        with app.app_context():
            model = Model(key='delete-test', name='Delete Test')
            db_session.session.add(model)
            key = ApiKey(
                model='delete-test',
                api_base='https://api.test.com',
                key_secret='sk-delete'
            )
            db_session.session.add(key)
            db_session.session.commit()

            key_id = key.id
            delete_key(key_id)

            deleted = ApiKey.query.get(key_id)
            assert deleted is None

    def test_delete_key_not_found(self, app, db_session):
        """测试删除不存在的密钥"""
        with app.app_context():
            with pytest.raises(ValueError, match="not found"):
                delete_key(99999)

    def test_trigger_cooldown_success(self, app, db_session, redis_db):
        """测试触发熔断"""
        # 如果Redis不可用，跳过测试
        if not redis_db:
            pytest.skip("Redis is not available")

        with app.app_context():
            model = Model(key='cooldown-test', name='Cooldown Test')
            db_session.session.add(model)
            key = ApiKey(
                model='cooldown-test',
                api_base='https://api.test.com',
                key_secret='sk-cooldown'
            )
            db_session.session.add(key)
            db_session.session.commit()

            # 触发熔断
            result = trigger_cooldown(key.id, 'trigger', duration=300)
            assert 'cooling_until' in result
            assert result['cooling_until'] is not None

    def test_release_cooldown_success(self, app, db_session, redis_db):
        """测试解除熔断"""
        # 如果Redis不可用，跳过测试
        if not redis_db:
            pytest.skip("Redis is not available")

        with app.app_context():
            model = Model(key='release-test', name='Release Test')
            db_session.session.add(model)
            key = ApiKey(
                model='release-test',
                api_base='https://api.test.com',
                key_secret='sk-release'
            )
            db_session.session.add(key)
            db_session.session.commit()

            # 先触发熔断
            trigger_cooldown(key.id, 'trigger')

            # 解除熔断
            result = trigger_cooldown(key.id, 'release')
            assert result['cooling_until'] is None

    def test_trigger_cooldown_invalid_action(self, app, db_session):
        """测试无效的熔断操作"""
        with app.app_context():
            model = Model(key='test', name='Test')
            db_session.session.add(model)
            key = ApiKey(model='test', api_base='', key_secret='sk-test')
            db_session.session.add(key)
            db_session.session.commit()

            with pytest.raises(ValueError, match="must be 'trigger' or 'release'"):
                trigger_cooldown(key.id, 'invalid')

    def test_trigger_cooldown_redis_unavailable(self, app, db_session, mocker):
        """测试Redis不可用时的错误处理"""
        # Mock redis_client 为 None
        mocker.patch('app.services.admin.key_service.redis_client', None)

        with app.app_context():
            model = Model(key='test-redis', name='Test Redis')
            db_session.session.add(model)
            key = ApiKey(model='test-redis', api_base='', key_secret='sk-test-redis')
            db_session.session.add(key)
            db_session.session.commit()

            with pytest.raises(ValueError, match="Redis is not available"):
                trigger_cooldown(key.id, 'trigger')

    def test_get_key_stats(self, app, db_session):
        """测试获取密钥统计"""
        with app.app_context():
            # 创建测试数据
            model1 = Model(key='stats-1', name='Stats 1')
            model2 = Model(key='stats-2', name='Stats 2')
            db_session.session.add_all([model1, model2])

            key1 = ApiKey(model='stats-1', api_base='', key_secret='sk-1', max_concurrency=5, status=1)
            key2 = ApiKey(model='stats-1', api_base='', key_secret='sk-2', max_concurrency=3, status=1)
            key3 = ApiKey(model='stats-2', api_base='', key_secret='sk-3', max_concurrency=10, status=1)
            db_session.session.add_all([key1, key2, key3])
            db_session.session.commit()

            stats = get_key_stats()

            assert 'by_model' in stats
            assert len(stats['by_model']) == 2

            # 验证统计数据
            stats_1 = next((s for s in stats['by_model'] if s['model'] == 'stats-1'), None)
            assert stats_1 is not None
            assert stats_1['total_keys'] == 2
            assert stats_1['active_keys'] == 2
            assert stats_1['total_concurrency'] == 8  # 5 + 3
