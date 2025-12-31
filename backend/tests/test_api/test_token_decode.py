import pytest
import jwt


def test_login_token_decode(client, db_session):
    # login
    resp = client.post("/api/auth/login", json={"email": "admin@example.com", "password": "admin123"})
    assert resp.status_code == 200
    data = resp.get_json()
    token = data["data"]["token"]

    # decode without verify to inspect payload
    payload = jwt.decode(token, options={"verify_signature": False})
    assert "email" in payload

    # verify with app secret
    from app.config import Config
    from flask import current_app
    # in test context, Config.JWT_SECRET_KEY set in TestConfig; use that
    # Try to decode with the config secret
    secret = current_app.config.get("JWT_SECRET_KEY", Config.JWT_SECRET_KEY)
    decoded = jwt.decode(token, secret, algorithms=["HS256"])
    assert decoded["email"] == "admin@example.com"



