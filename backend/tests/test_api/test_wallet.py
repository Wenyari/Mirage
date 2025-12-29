"""
钱包 API 测试
"""
import pytest
import json


@pytest.mark.api
class TestWalletAPI:
    """钱包 API 测试类"""

    def test_redeem_cdk_success(self, client, db_session, auth_headers, test_user, test_cdk):
        """测试 CDK 兑换成功"""
        response = client.post(
            '/api/wallet/redeem',
            data=json.dumps({
                'code': test_cdk.code
            }),
            headers=auth_headers
        )

        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['code'] == 200
        assert data['data']['added_points'] == test_cdk.points
        assert data['data']['current_balance'] > 0

    def test_redeem_cdk_invalid_code(self, client, db_session, auth_headers):
        """测试无效 CDK"""
        response = client.post(
            '/api/wallet/redeem',
            data=json.dumps({
                'code': 'INVALID-CODE'
            }),
            headers=auth_headers
        )

        assert response.status_code == 400

    def test_redeem_cdk_missing_code(self, client, db_session, auth_headers):
        """测试缺少 CDK 参数"""
        response = client.post(
            '/api/wallet/redeem',
            data=json.dumps({}),
            headers=auth_headers
        )

        assert response.status_code == 400

    def test_redeem_cdk_no_auth(self, client, db_session, test_cdk):
        """测试未认证"""
        response = client.post(
            '/api/wallet/redeem',
            data=json.dumps({
                'code': test_cdk.code
            }),
            content_type='application/json'
        )

        assert response.status_code == 401

    def test_get_transactions_success(self, client, db_session, auth_headers, test_user):
        """测试获取流水成功"""
        from app.models import Transaction

        # 创建一些流水记录
        for i in range(3):
            transaction = Transaction(
                user_id=test_user.id,
                type='recharge',
                amount=100.00,
                balance_snapshot=1000.00 + (i * 100)
            )
            db_session.session.add(transaction)
        db_session.session.commit()

        response = client.get(
            '/api/wallet/transactions?page=1&size=20',
            headers=auth_headers
        )

        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['code'] == 200
        assert 'list' in data['data']
        assert 'total' in data['data']

    def test_get_balance_success(self, client, db_session, auth_headers, test_user):
        """测试获取余额"""
        response = client.get(
            '/api/wallet/balance',
            headers=auth_headers
        )

        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['code'] == 200
        assert 'balance' in data['data']
