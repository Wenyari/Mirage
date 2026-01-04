"""
会员配置管理服务测试
测试会员等级的查询和更新功能
"""
import pytest
from app.services.admin.membership_config_service import (
    get_membership_config,
    update_membership_config
)
from app.models import MembershipConfig


@pytest.mark.unit
class TestMembershipConfigService:
    """会员配置管理服务测试类"""

    def test_get_membership_config(self, app, db_session):
        """测试获取会员配置"""
        with app.app_context():
            config = get_membership_config()

            # 验证返回格式
            assert isinstance(config, dict)
            assert 'T1' in config
            assert 'T2' in config
            assert 'T3' in config
            assert 'T4' in config
            assert 'T5' in config

            # 验证 T1 配置
            t1 = config['T1']
            assert t1['level'] == 1
            assert t1['name'] == 'T1'
            assert 'concurrent_limit' in t1
            assert 'queue_weight' in t1
            assert 'price' in t1
            assert 'description' in t1

    def test_get_membership_config_values(self, app, db_session):
        """测试会员配置的具体值"""
        with app.app_context():
            config = get_membership_config()

            # 验证价格为数字类型
            for tier in ['T1', 'T2', 'T3', 'T4', 'T5']:
                assert isinstance(config[tier]['price'], (int, float))
                assert isinstance(config[tier]['concurrent_limit'], int)
                assert isinstance(config[tier]['queue_weight'], int)

            # T1 应该是免费的
            assert config['T1']['price'] == 0

    def test_update_membership_config_success(self, app, db_session):
        """测试成功更新会员配置"""
        with app.app_context():
            # 更新配置
            update_data = {
                'T1': {
                    'concurrent_limit': 2,
                    'queue_weight': 1,
                    'price': 0
                },
                'T2': {
                    'concurrent_limit': 4,
                    'queue_weight': 2,
                    'price': 39
                }
            }

            result = update_membership_config(update_data)
            assert 'message' in result

            # 验证更新结果
            t1_config = MembershipConfig.query.filter_by(name='T1').first()
            assert t1_config.concurrent_limit == 2

            t2_config = MembershipConfig.query.filter_by(name='T2').first()
            assert t2_config.concurrent_limit == 4
            assert float(t2_config.price) == 39

    def test_update_membership_config_all_tiers(self, app, db_session):
        """测试更新所有等级配置"""
        with app.app_context():
            update_data = {
                'T1': {'concurrent_limit': 1, 'queue_weight': 1, 'price': 0},
                'T2': {'concurrent_limit': 3, 'queue_weight': 2, 'price': 29},
                'T3': {'concurrent_limit': 5, 'queue_weight': 3, 'price': 99},
                'T4': {'concurrent_limit': 10, 'queue_weight': 4, 'price': 299},
                'T5': {'concurrent_limit': 20, 'queue_weight': 5, 'price': 999}
            }

            update_membership_config(update_data)

            # 验证所有配置都已更新
            configs = MembershipConfig.query.all()
            for config in configs:
                tier_name = config.name
                expected = update_data[tier_name]
                assert config.concurrent_limit == expected['concurrent_limit']
                assert config.queue_weight == expected['queue_weight']
                assert float(config.price) == expected['price']

    def test_update_membership_config_partial(self, app, db_session):
        """测试部分更新会员配置"""
        with app.app_context():
            # 获取原始配置
            original = MembershipConfig.query.filter_by(name='T1').first()
            original_price = float(original.price)

            # 只更新并发限制
            update_data = {
                'T1': {
                    'concurrent_limit': 5
                }
            }

            update_membership_config(update_data)

            # 验证只更新了指定字段
            updated = MembershipConfig.query.filter_by(name='T1').first()
            assert updated.concurrent_limit == 5
            assert float(updated.price) == original_price  # 价格未变

    def test_update_membership_config_invalid_tier(self, app, db_session):
        """测试更新无效的等级"""
        with app.app_context():
            update_data = {
                'T6': {  # 不存在的等级
                    'concurrent_limit': 10,
                    'queue_weight': 6,
                    'price': 1999
                }
            }

            with pytest.raises(ValueError, match="Invalid tier"):
                update_membership_config(update_data)

    def test_update_membership_config_invalid_concurrent_limit(self, app, db_session):
        """测试使用无效并发限制更新"""
        with app.app_context():
            # 并发限制为0
            with pytest.raises(ValueError, match="must be a positive integer"):
                update_membership_config({
                    'T1': {'concurrent_limit': 0}
                })

            # 并发限制为负数
            with pytest.raises(ValueError, match="must be a positive integer"):
                update_membership_config({
                    'T1': {'concurrent_limit': -1}
                })

            # 并发限制为非整数
            with pytest.raises(ValueError, match="must be a positive integer"):
                update_membership_config({
                    'T1': {'concurrent_limit': 1.5}
                })

    def test_update_membership_config_invalid_queue_weight(self, app, db_session):
        """测试使用无效队列权重更新"""
        with app.app_context():
            # 权重为0
            with pytest.raises(ValueError, match="must be a positive integer"):
                update_membership_config({
                    'T1': {'queue_weight': 0}
                })

            # 权重为负数
            with pytest.raises(ValueError, match="must be a positive integer"):
                update_membership_config({
                    'T1': {'queue_weight': -1}
                })

    def test_update_membership_config_invalid_price(self, app, db_session):
        """测试使用无效价格更新"""
        with app.app_context():
            # 价格为负数
            with pytest.raises(ValueError, match="must be a non-negative number"):
                update_membership_config({
                    'T1': {'price': -10}
                })

    def test_update_membership_config_not_dict(self, app, db_session):
        """测试使用非字典类型更新"""
        with app.app_context():
            with pytest.raises(ValueError, match="must be an object"):
                update_membership_config("invalid")

            with pytest.raises(ValueError, match="must be an object"):
                update_membership_config([])

    def test_update_membership_config_tier_not_found(self, app, db_session):
        """测试更新不存在的等级配置"""
        with app.app_context():
            # 临时删除一个配置
            MembershipConfig.query.filter_by(name='T5').delete()
            db_session.session.commit()

            with pytest.raises(ValueError, match="not found"):
                update_membership_config({
                    'T5': {'concurrent_limit': 20}
                })

    def test_update_membership_config_preserve_unspecified(self, app, db_session):
        """测试更新时保留未指定的字段"""
        with app.app_context():
            # 获取原始值
            original = MembershipConfig.query.filter_by(name='T3').first()
            original_limit = original.concurrent_limit
            original_weight = original.queue_weight

            # 只更新价格
            update_membership_config({
                'T3': {'price': 199}
            })

            # 验证其他字段未变
            updated = MembershipConfig.query.filter_by(name='T3').first()
            assert updated.concurrent_limit == original_limit
            assert updated.queue_weight == original_weight
            assert float(updated.price) == 199

    def test_update_membership_config_multiple_tiers(self, app, db_session):
        """测试同时更新多个等级"""
        with app.app_context():
            update_data = {
                'T1': {'concurrent_limit': 2},
                'T2': {'concurrent_limit': 5},
                'T3': {'price': 88}
            }

            update_membership_config(update_data)

            # 验证所有更新
            t1 = MembershipConfig.query.filter_by(name='T1').first()
            t2 = MembershipConfig.query.filter_by(name='T2').first()
            t3 = MembershipConfig.query.filter_by(name='T3').first()

            assert t1.concurrent_limit == 2
            assert t2.concurrent_limit == 5
            assert float(t3.price) == 88

    def test_update_membership_config_zero_price(self, app, db_session):
        """测试设置价格为0（免费）"""
        with app.app_context():
            update_membership_config({
                'T2': {'price': 0}
            })

            updated = MembershipConfig.query.filter_by(name='T2').first()
            assert float(updated.price) == 0
