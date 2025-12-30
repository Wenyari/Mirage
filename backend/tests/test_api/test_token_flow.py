"""
Token 流程集成测试
验证登录返回的 token 能够访问受保护的接口 (/api/tasks/{task_id})
"""
import json
import pytest


def test_login_and_access_task(client, db_session, test_task, admin_user):
    # 1. 登录获取 token
    resp = client.post(
        "/api/auth/login",
        json={"email": "admin@example.com", "password": "admin123"}
    )
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["code"] == 200
    token = data["data"]["token"]
    assert token and isinstance(token, str)

    # 2. 使用 token 访问受保护接口
    headers = {"Authorization": f"Bearer {token}"}
    resp2 = client.get(f"/api/tasks/{test_task.id}", headers=headers)
    assert resp2.status_code == 200
    body = resp2.get_json()
    assert body["code"] == 200
    assert "data" in body


def test_invalid_token_gets_401(client, db_session, test_task):
    # 使用无效 token 访问应该返回 401
    headers = {"Authorization": "Bearer invalid.token.here"}
    resp = client.get(f"/api/tasks/{test_task.id}", headers=headers)
    assert resp.status_code == 401
    body = resp.get_json()
    # flask_jwt_extended 通常返回 401 状态，body 里可能包含 msg 或 description
    assert body is not None
    assert resp.status_code == 401


