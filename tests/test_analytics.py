"""数据分析测试"""
import pytest


class TestAnalytics:
    @pytest.fixture(autouse=True)
    def setup(self, auth_client):
        self.client, self.uid = auth_client
        # 建一些测试数据
        apps = [
            ("字节跳动", "后端", "BOSS直聘"),
            ("腾讯", "前端", "内推"),
            ("阿里", "数据", "猎聘"),
            ("字节跳动", "算法", "BOSS直聘"),
        ]
        for i, (co, pos, src) in enumerate(apps):
            self.client.post("/api/applications", data={
                "company": co, "position": pos, "source": src,
            })

    def test_stats(self):
        """基础统计"""
        r = self.client.get("/api/analytics/stats")
        assert r.json()["ok"] is True
        assert r.json()["total"] == 4
        assert len(r.json()["by_source"]) > 0

    def test_funnel(self):
        """转化漏斗"""
        r = self.client.get("/api/analytics/funnel")
        data = r.json()["data"]
        assert len(data) == 5  # applied → offer
        assert data[0]["stage"] == "applied"
        assert data[0]["count"] == 4

    def test_channels_empty_data(self):
        """无面试数据时的渠道分析"""
        r = self.client.get("/api/analytics/channels")
        assert r.json()["ok"] is True
        assert len(r.json()["data"]) > 0

    def test_companies_grouping(self):
        """公司维度 — 同一公司投递多次应该合并"""
        r = self.client.get("/api/analytics/companies")
        companies = {c["company"]: c for c in r.json()["data"]}
        assert companies["字节跳动"]["total_applications"] == 2
        assert companies["腾讯"]["total_applications"] == 1

    def test_summary(self):
        """综合洞察"""
        r = self.client.get("/api/analytics/summary")
        data = r.json()["data"]
        assert data["total"] == 4
        assert data["top_company"] == "字节跳动"
        assert len(data["insights"]) >= 3

    def test_timeline(self):
        """时间趋势"""
        r = self.client.get("/api/analytics/timeline?granularity=month")
        assert r.json()["ok"] is True
        assert len(r.json()["data"]) > 0

    def test_export(self):
        """CSV导出"""
        r = self.client.get("/api/analytics/export")
        assert r.status_code == 200
        assert "公司" in r.text  # header
        assert "字节跳动" in r.text

    def test_empty_data(self, client):
        """空数据不会报错"""
        client.post("/api/auth/register", data={
            "email": "empty@test.com", "username": "empty", "password": "123456",
        })
        r = client.post("/api/auth/login", data={
            "email": "empty@test.com", "password": "123456",
        })
        client.cookies.set("jobpilot_token", r.cookies.get("jobpilot_token"))

        for endpoint in ["/api/analytics/funnel", "/api/analytics/channels",
                          "/api/analytics/timeline", "/api/analytics/companies",
                          "/api/analytics/summary"]:
            r = client.get(endpoint)
            assert r.json()["ok"] is True
