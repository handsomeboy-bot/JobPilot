"""投递 CRUD 测试"""
import pytest


class TestApplications:
    @pytest.fixture(autouse=True)
    def setup(self, auth_client):
        self.client, self.uid = auth_client

    def test_create_and_list(self):
        """创建投递并列出"""
        r = self.client.post("/api/applications", data={
            "company": "字节跳动", "position": "后端",
        })
        assert r.json()["ok"] is True
        assert r.json()["data"]["id"] == 1

        r = self.client.get("/api/applications")
        assert r.json()["ok"] is True
        assert len(r.json()["data"]) == 1
        app = r.json()["data"][0]
        assert app["company"] == "字节跳动"
        assert app["position"] == "后端"

    def test_update_status(self):
        """拖拽换状态"""
        self.client.post("/api/applications", data={
            "company": "字节跳动", "position": "后端",
        })
        r = self.client.put("/api/applications/1", json={"status": "interview"})
        assert r.json()["ok"] is True

        r = self.client.get("/api/applications")
        assert r.json()["data"][0]["status"] == "interview"

    def test_delete(self):
        """删除投递"""
        self.client.post("/api/applications", data={
            "company": "字节跳动", "position": "后端",
        })
        r = self.client.delete("/api/applications/1")
        assert r.json()["ok"] is True

        r = self.client.get("/api/applications")
        assert len(r.json()["data"]) == 0

    def test_user_isolation(self, client):
        """用户只能看到自己的投递"""
        # 注册用户A
        client.post("/api/auth/register", data={
            "email": "userA@test.com", "username": "A", "password": "123456",
        })
        r = client.post("/api/auth/login", data={
            "email": "userA@test.com", "password": "123456",
        })
        client.cookies.set("jobpilot_token", r.cookies.get("jobpilot_token"))
        client.post("/api/applications", data={
            "company": "A的公司", "position": "后端",
        })

        # 注册用户B
        client2 = client.__class__(client.app)  # 新客户端
        client2.post("/api/auth/register", data={
            "email": "userB@test.com", "username": "B", "password": "123456",
        })
        r = client2.post("/api/auth/login", data={
            "email": "userB@test.com", "password": "123456",
        })
        client2.cookies.set("jobpilot_token", r.cookies.get("jobpilot_token"))
        r = client2.get("/api/applications")
        assert len(r.json()["data"]) == 0  # B看不到A的投递
