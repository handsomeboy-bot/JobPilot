"""面试 CRUD 测试"""
import pytest


class TestInterviews:
    @pytest.fixture(autouse=True)
    def setup(self, auth_client):
        self.client, self.uid = auth_client
        # 先建一个投递
        self.client.post("/api/applications", data={
            "company": "字节跳动", "position": "后端",
        })

    def test_create_interview(self):
        """为投递添加面试"""
        r = self.client.post("/api/applications/1/interviews", data={
            "round": "一面",
            "scheduled_time": "2026-06-10T10:00",
            "interviewer": "张工",
            "interview_type": "技术面",
        })
        assert r.json()["ok"] is True

        r = self.client.get("/api/interviews")
        assert len(r.json()["data"]) == 1
        iv = r.json()["data"][0]
        assert iv["company"] == "字节跳动"
        assert iv["round"] == "一面"

    def test_update_interview_status(self):
        """标记面试完成"""
        self.client.post("/api/applications/1/interviews", data={
            "round": "一面", "scheduled_time": "2026-06-10T10:00",
        })
        r = self.client.put("/api/interviews/1", json={"interview_status": "done"})
        assert r.json()["ok"] is True

        r = self.client.get("/api/interviews")
        assert r.json()["data"][0]["interview_status"] == "done"

    def test_delete_interview(self):
        """删除面试"""
        self.client.post("/api/applications/1/interviews", data={
            "round": "一面", "scheduled_time": "2026-06-10T10:00",
        })
        r = self.client.delete("/api/interviews/1")
        assert r.json()["ok"] is True
        assert len(self.client.get("/api/interviews").json()["data"]) == 0

    def test_upcoming(self):
        """即将到来的面试"""
        self.client.post("/api/applications/1/interviews", data={
            "round": "一面",
            "scheduled_time": "2099-12-31T10:00",
        })
        r = self.client.get("/api/interviews/upcoming")
        assert len(r.json()["data"]) == 1
