import json


def test_register_and_login_flow(client, db_session, redis_db):
    """
    测试完整注册 -> 登录 -> 获取当前用户流程
    """
    email = "newuser@example.com"
    password = "securePass123"
    code = "123456"

    # 将验证码写入 Redis（模拟 send_verify_code 已发送）
    verify_key = f"verify:email:{email}"
    # redis_db fixture may be None if Redis not available; monkeypatch in that case
    from app.services import auth_service

    class _DummyRedis:
        def __init__(self):
            self.store = {}
        def setex(self, key, ex, value):
            self.store[key] = value
        def get(self, key):
            return self.store.get(key)
        def delete(self, key):
            self.store.pop(key, None)

    if redis_db:
        redis_db.setex(verify_key, 300, code)
    else:
        auth_service.redis_client = _DummyRedis()
        auth_service.redis_client.setex(verify_key, 300, code)

    # 调用注册接口
    resp = client.post("/api/auth/register", json={
        "email": email,
        "code": code,
        "password": password
    })
    assert resp.status_code == 200
    body = resp.get_json()
    assert body["code"] == 200
    user_id = body["data"]["user_id"]
    assert isinstance(user_id, int)

    # 登录接口
    resp2 = client.post("/api/auth/login", json={"email": email, "password": password})
    assert resp2.status_code == 200
    body2 = resp2.get_json()
    assert body2["code"] == 200
    token = body2["data"]["token"]
    assert token

    # 使用 token 调用 /api/auth/me 验证服务端可用
    headers = {"Authorization": f"Bearer {token}"}
    resp3 = client.get("/api/auth/me", headers=headers)
    assert resp3.status_code == 200
    body3 = resp3.get_json()
    assert body3["code"] == 200

    # 进一步通过解析 token 获取 user_id 并在数据库中验证 email
    import jwt
    payload = jwt.decode(token, options={"verify_signature": False})
    user_id = payload.get("sub") or payload.get("identity") or payload.get("user_id")
    from app.models import User
    user = User.query.get(int(user_id))
    assert user.email == email


