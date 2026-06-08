"""认证测试"""
import pytest


class TestAuth:
    def test_register_login_logout(self, client):
        """正常注册→登录→登出流程"""
        # 注册
        r = client.post("/api/auth/register", data={
            "email": "a@b.com", "username": "test", "password": "123456",
        })
        assert r.status_code == 200
        assert r.json()["ok"] is True

        # 重复注册
        r = client.post("/api/auth/register", data={
            "email": "a@b.com", "username": "test2", "password": "123456",
        })
        assert r.json()["ok"] is False
        assert "已注册" in r.json()["msg"]

        # 登录
        r = client.post("/api/auth/login", data={
            "email": "a@b.com", "password": "123456",
        })
        assert r.json()["ok"] is True
        assert r.cookies.get("jobpilot_token")

        # 登出
        r = client.post("/api/auth/logout")
        assert r.json()["ok"] is True

    def test_login_wrong_password(self, client):
        """错误密码"""
        client.post("/api/auth/register", data={
            "email": "a@b.com", "username": "test", "password": "123456",
        })
        r = client.post("/api/auth/login", data={
            "email": "a@b.com", "password": "wrong",
        })
        assert r.json()["ok"] is False

    def test_short_password(self, client):
        """密码太短"""
        r = client.post("/api/auth/register", data={
            "email": "a@b.com", "username": "test", "password": "123",
        })
        assert r.json()["ok"] is False

    def test_protected_route_no_auth(self, client):
        """未登录无法访问 /app"""
        r = client.get("/app")
        assert r.status_code == 401

    def test_protected_route_with_auth(self, auth_client):
        """登录后可访问 /app"""
        client, uid = auth_client
        r = client.get("/app")
        assert r.status_code == 200
