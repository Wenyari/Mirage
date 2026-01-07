import json
from flask_jwt_extended import create_access_token


def test_redeem_cdk_api_success(app, client, db_session, redis_db, test_user, test_cdk):
    with app.app_context():
        # create token and store in redis as login_required expects
        token = create_access_token(identity=test_user.id)
        redis_db.setex(f"auth:token:{test_user.id}", 3600, token)

        # call redeem endpoint
        # set CDK to grant higher level to test upgrade
        from app.models.wallet import CDK
        db_cdk = CDK.query.filter_by(code=test_cdk.code).first()
        db_cdk.grant_level = 4
        db_session.session.commit()

        response = client.post(
            '/api/wallet/redeem',
            headers={'Authorization': f'Bearer {token}'},
            json={'code': test_cdk.code}
        )

        assert response.status_code == 200
        data = response.get_json()
        assert data['code'] == 200
        assert 'data' in data
        assert 'added_points' in data['data']
        assert 'current_balance' in data['data']

        # DB side effects: CDK should be marked used and user balance increased
        from app.models.wallet import CDK, Transaction
        db_session.session.refresh(test_cdk)
        db_cdk = CDK.query.filter_by(code=test_cdk.code).first()
        assert db_cdk.status == 1
        assert db_cdk.used_by == test_user.id

        # transaction record exists
        tx = Transaction.query.filter_by(related_id=str(db_cdk.id)).first()
        assert tx is not None
        assert tx.type == 'recharge'
        # user should be upgraded to level 4
        db_session.session.refresh(test_user)
        assert test_user.level == 4


def test_redeem_cdk_api_invalid_code(app, client, db_session, redis_db, test_user):
    with app.app_context():
        token = create_access_token(identity=test_user.id)
        redis_db.setex(f"auth:token:{test_user.id}", 3600, token)

        response = client.post(
            '/api/wallet/redeem',
            headers={'Authorization': f'Bearer {token}'},
            json={'code': 'INVALID-CODE'}
        )

        assert response.status_code == 400
        data = response.get_json()
        assert data['code'] == 400


