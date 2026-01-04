"""
CDK管理服务测试
测试CDK的生成、查询、作废等功能
"""
import pytest
from app.services.admin.cdk_service import (
    generate_cdk_batch,
    get_cdk_list,
    void_cdk_batch,
    generate_cdk_code,
    generate_batch_no
)
from app.models import CDK, User


@pytest.mark.unit
class TestCDKService:
    """CDK管理服务测试类"""

    def test_generate_cdk_code_format(self, app):
        """测试CDK码格式"""
        with app.app_context():
            code = generate_cdk_code()

            # 验证格式：CDK- + 20位字符
            assert code.startswith('CDK-')
            assert len(code) == 24  # CDK- (4) + 20字符
            # 验证不包含易混淆字符
            assert 'O' not in code
            assert 'I' not in code
            assert '0' not in code[4:]  # CDK-后面的部分
            assert '1' not in code[4:]

    def test_generate_cdk_code_unique(self, app):
        """测试CDK码唯一性"""
        with app.app_context():
            codes = [generate_cdk_code() for _ in range(100)]
            # 验证100个码都不相同
            assert len(set(codes)) == 100

    def test_generate_batch_no_format(self, app):
        """测试批次号格式"""
        with app.app_context():
            batch_no = generate_batch_no()

            # 验证格式：BATCH + YYYYMMDD + 3位序号
            assert batch_no.startswith('BATCH')
            assert len(batch_no) == 16  # BATCH(5) + 8位日期 + 3位序号 = 16

    def test_generate_cdk_batch_success(self, app, db_session):
        """测试成功批量生成CDK"""
        with app.app_context():
            amount = 500
            count = 10
            batch_name = "测试活动"

            result = generate_cdk_batch(
                amount=amount,
                count=count,
                type='once',
                batch_name=batch_name
            )

            # 验证返回结果
            assert 'batch_no' in result
            assert 'batch_name' in result
            assert 'cdks' in result
            assert result['batch_name'] == batch_name
            assert len(result['cdks']) == count

            # 验证每个CDK
            for cdk in result['cdks']:
                assert cdk['value'] == amount
                assert cdk['type'] == 'once'
                assert cdk['status'] == 'unused'
                assert cdk['code'].startswith('CDK-')

            # 验证数据库记录
            db_cdks = CDK.query.all()
            assert len(db_cdks) == count

    def test_generate_cdk_batch_multi_type(self, app, db_session):
        """测试生成multi类型CDK（对应数据库的universal）"""
        with app.app_context():
            result = generate_cdk_batch(
                amount=100,
                count=5,
                type='multi'
            )

            # 验证返回的type是multi
            for cdk in result['cdks']:
                assert cdk['type'] == 'multi'

            # 验证数据库存储的是universal
            db_cdks = CDK.query.all()
            for cdk in db_cdks:
                assert cdk.type == 'universal'

    def test_generate_cdk_batch_invalid_amount(self, app, db_session):
        """测试无效的面额"""
        with app.app_context():
            with pytest.raises(ValueError, match="Amount must be positive"):
                generate_cdk_batch(amount=0, count=10)

            with pytest.raises(ValueError, match="Amount must be positive"):
                generate_cdk_batch(amount=-100, count=10)

    def test_generate_cdk_batch_invalid_count(self, app, db_session):
        """测试无效的数量"""
        with app.app_context():
            with pytest.raises(ValueError, match="Count must be between 1 and 1000"):
                generate_cdk_batch(amount=100, count=0)

            with pytest.raises(ValueError, match="Count must be between 1 and 1000"):
                generate_cdk_batch(amount=100, count=1001)

    def test_generate_cdk_batch_invalid_type(self, app, db_session):
        """测试无效的类型"""
        with app.app_context():
            with pytest.raises(ValueError, match="Type must be"):
                generate_cdk_batch(amount=100, count=10, type='invalid')

    def test_get_cdk_list_empty(self, app, db_session):
        """测试空列表"""
        with app.app_context():
            result = get_cdk_list()

            assert result['total'] == 0
            assert result['page'] == 1
            assert result['items'] == []

    def test_get_cdk_list_with_cdks(self, app, db_session):
        """测试获取CDK列表"""
        with app.app_context():
            # 生成测试数据
            generate_cdk_batch(amount=100, count=5)
            generate_cdk_batch(amount=200, count=3)

            result = get_cdk_list()

            assert result['total'] == 8
            assert len(result['items']) == 8

    def test_get_cdk_list_pagination(self, app, db_session):
        """测试分页功能"""
        with app.app_context():
            # 生成25个CDK
            generate_cdk_batch(amount=100, count=25)

            # 获取第一页（每页10条）
            result = get_cdk_list(page=1, limit=10)
            assert result['total'] == 25
            assert result['page'] == 1
            assert result['limit'] == 10
            assert len(result['items']) == 10

            # 获取第三页
            result = get_cdk_list(page=3, limit=10)
            assert result['page'] == 3
            assert len(result['items']) == 5

    def test_get_cdk_list_filter_by_batch_no(self, app, db_session):
        """测试按批次号筛选"""
        with app.app_context():
            # 生成两批CDK
            batch1 = generate_cdk_batch(amount=100, count=5, batch_name="批次1")
            batch2 = generate_cdk_batch(amount=200, count=3, batch_name="批次2")

            batch1_no = batch1['batch_no']
            batch2_no = batch2['batch_no']

            # 筛选批次1
            result = get_cdk_list(batch_no=batch1_no)
            assert result['total'] == 5

            # 筛选批次2
            result = get_cdk_list(batch_no=batch2_no)
            assert result['total'] == 3

    def test_get_cdk_list_filter_by_status(self, app, db_session):
        """测试按状态筛选"""
        with app.app_context():
            # 生成CDK
            generate_cdk_batch(amount=100, count=10)

            # 手动设置一些CDK为已使用
            cdks = CDK.query.limit(3).all()
            for cdk in cdks:
                cdk.status = 1
            db_session.session.commit()

            # 手动设置一些CDK为已作废
            cdks = CDK.query.offset(3).limit(2).all()
            for cdk in cdks:
                cdk.status = 2
            db_session.session.commit()

            # 筛选未使用的
            result = get_cdk_list(status='unused')
            assert result['total'] == 5

            # 筛选已使用的
            result = get_cdk_list(status='used')
            assert result['total'] == 3

            # 筛选已作废的
            result = get_cdk_list(status='void')
            assert result['total'] == 2

    def test_get_cdk_list_with_user_email(self, app, db_session, test_user):
        """测试CDK列表包含使用者邮箱"""
        with app.app_context():
            # 生成CDK
            generate_cdk_batch(amount=100, count=5)

            # 设置一个CDK为已使用
            cdk = CDK.query.first()
            cdk.status = 1
            cdk.used_by = test_user.id
            db_session.session.commit()

            # 获取列表
            result = get_cdk_list(status='used')

            assert result['total'] == 1
            assert result['items'][0]['used_by'] == test_user.email

    def test_void_cdk_batch_by_batch_no(self, app, db_session):
        """测试按批次号作废CDK"""
        with app.app_context():
            # 生成两批CDK
            batch1 = generate_cdk_batch(amount=100, count=10, batch_name="批次1")
            batch2 = generate_cdk_batch(amount=200, count=5, batch_name="批次2")

            batch1_no = batch1['batch_no']

            # 作废批次1
            result = void_cdk_batch(batch_no=batch1_no)

            assert result['voided_count'] == 10

            # 验证数据库
            voided_cdks = CDK.query.filter_by(status=2).count()
            assert voided_cdks == 10

            # 批次2应该未受影响
            batch2_unused = CDK.query.filter(
                CDK.batch_no.like(f"{batch2['batch_no']}%"),
                CDK.status == 0
            ).count()
            assert batch2_unused == 5

    def test_void_cdk_batch_by_ids(self, app, db_session):
        """测试按ID作废CDK"""
        with app.app_context():
            # 生成CDK
            generate_cdk_batch(amount=100, count=10)

            # 获取前3个CDK的ID
            cdks = CDK.query.limit(3).all()
            ids = [cdk.id for cdk in cdks]

            # 作废
            result = void_cdk_batch(ids=ids)

            assert result['voided_count'] == 3

            # 验证数据库
            voided_cdks = CDK.query.filter_by(status=2).count()
            assert voided_cdks == 3

    def test_void_cdk_batch_skip_used(self, app, db_session):
        """测试作废时跳过已使用的CDK"""
        with app.app_context():
            # 生成CDK
            batch = generate_cdk_batch(amount=100, count=10)

            # 设置一些CDK为已使用
            cdks = CDK.query.limit(3).all()
            for cdk in cdks:
                cdk.status = 1
            db_session.session.commit()

            # 尝试作废整个批次
            result = void_cdk_batch(batch_no=batch['batch_no'])

            # 应该只作废了未使用的7个
            assert result['voided_count'] == 7

    def test_void_cdk_batch_no_params(self, app, db_session):
        """测试未提供参数"""
        with app.app_context():
            with pytest.raises(ValueError, match="Either batch_no or ids must be provided"):
                void_cdk_batch()

    def test_void_cdk_batch_both_params(self, app, db_session):
        """测试同时提供两种参数"""
        with app.app_context():
            with pytest.raises(ValueError, match="Cannot specify both"):
                void_cdk_batch(batch_no="BATCH001", ids=[1, 2, 3])

    def test_cdk_api_format_conversion(self, app, db_session):
        """测试CDK API格式转换"""
        with app.app_context():
            # 生成once类型CDK
            batch1 = generate_cdk_batch(amount=100, count=2, type='once', batch_name="测试1")

            # 验证返回格式
            cdk = batch1['cdks'][0]
            assert 'value' in cdk  # 接口使用value
            assert 'points' not in cdk  # 不应该有points
            assert cdk['type'] == 'once'
            assert cdk['status'] == 'unused'
            assert cdk['batch_name'] == "测试1"

            # 生成multi类型CDK
            batch2 = generate_cdk_batch(amount=200, count=2, type='multi')

            # 验证类型转换
            cdk = batch2['cdks'][0]
            assert cdk['type'] == 'multi'

            # 验证数据库存储
            db_cdk = CDK.query.filter_by(code=cdk['code']).first()
            assert db_cdk.type == 'universal'  # 数据库存储为universal
            assert db_cdk.points == 200  # 数据库使用points

    def test_get_cdk_list_invalid_status(self, app, db_session):
        """测试无效的status参数"""
        with app.app_context():
            with pytest.raises(ValueError, match="Invalid status"):
                get_cdk_list(status='invalid')
