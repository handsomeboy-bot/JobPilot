"""论坛 API 测试"""
import pytest


def _cookie(token):
    """用 Cookie header 传 token，避免 TestClient cookies.set 的 bug"""
    return {"Cookie": f"jobpilot_token={token}"}


class TestForum:
    def test_create_and_list_posts(self, auth_client):
        client, uid = auth_client

        r = client.post("/api/forum/posts", json={
            "title": "字节跳动一面面经",
            "content": "问了很多算法题...",
            "tags": "算法, 字节",
            "is_anonymous": 0,
        })
        assert r.status_code == 200
        assert r.json()["ok"] is True
        post_id = r.json()["data"]["id"]

        r = client.get("/api/forum/posts")
        d = r.json()
        assert d["ok"] is True
        assert len(d["data"]) >= 1
        assert d["data"][0]["title"] == "字节跳动一面面经"

        r = client.get(f"/api/forum/posts/{post_id}")
        assert r.json()["ok"] is True
        detail = r.json()["data"]
        assert detail["title"] == "字节跳动一面面经"
        assert detail["author_name"] == "tester"

    def test_anonymous_post(self, auth_client):
        client, uid = auth_client
        r = client.post("/api/forum/posts", json={
            "title": "匿名面经", "content": "不想透露公司...",
            "tags": "", "is_anonymous": 1,
        })
        post_id = r.json()["data"]["id"]
        r = client.get(f"/api/forum/posts/{post_id}")
        assert r.json()["data"]["author_name"] == "匿名用户"

    def test_comment_and_tree(self, auth_client):
        client, uid = auth_client

        r = client.post("/api/forum/posts", json={
            "title": "测试评论", "content": "正文", "tags": "", "is_anonymous": 0,
        })
        post_id = r.json()["data"]["id"]

        r = client.post(f"/api/forum/posts/{post_id}/comments", json={
            "content": "感谢分享！", "is_anonymous": 0,
        })
        assert r.json()["ok"] is True
        c1_id = r.json()["data"]["id"]

        r = client.post(f"/api/forum/posts/{post_id}/comments", json={
            "content": "不客气！", "parent_id": c1_id, "is_anonymous": 0,
        })
        assert r.json()["ok"] is True

        r = client.get(f"/api/forum/posts/{post_id}")
        comments = r.json()["data"]["comments"]
        assert len(comments) == 1
        assert len(comments[0]["children"]) == 1

    def test_delete_own_post(self, auth_client):
        client, uid = auth_client
        r = client.post("/api/forum/posts", json={
            "title": "待删除", "content": "xxx", "tags": "", "is_anonymous": 0,
        })
        post_id = r.json()["data"]["id"]
        r = client.delete(f"/api/forum/posts/{post_id}")
        assert r.json()["ok"] is True
        r = client.get(f"/api/forum/posts/{post_id}")
        assert r.status_code == 404

    def test_cannot_delete_others_post(self, client):
        """普通用户不能删别人的帖子"""
        r = client.post("/api/auth/register", data={
            "email": "a@b.com", "username": "user_a", "password": "123456",
        })
        assert r.json()["ok"]
        r = client.post("/api/auth/login", data={
            "email": "a@b.com", "password": "123456",
        })
        t1 = r.cookies.get("jobpilot_token")

        r = client.post("/api/forum/posts", json={
            "title": "A的帖子", "content": "xxx", "tags": "", "is_anonymous": 0,
        }, headers=_cookie(t1))
        post_id = r.json()["data"]["id"]

        r = client.post("/api/auth/register", data={
            "email": "c@d.com", "username": "user_b", "password": "123456",
        })
        assert r.json()["ok"]
        r = client.post("/api/auth/login", data={
            "email": "c@d.com", "password": "123456",
        })
        t2 = r.cookies.get("jobpilot_token")

        r = client.delete(f"/api/forum/posts/{post_id}", headers=_cookie(t2))
        assert r.status_code == 403

    def test_comment_triggers_notification(self, client):
        """评论触发通知"""
        r = client.post("/api/auth/register", data={
            "email": "u1@t.com", "username": "u1", "password": "123456",
        })
        assert r.json()["ok"]
        r = client.post("/api/auth/login", data={
            "email": "u1@t.com", "password": "123456",
        })
        t1 = r.cookies.get("jobpilot_token")

        r = client.post("/api/forum/posts", json={
            "title": "通知测试", "content": "test", "tags": "", "is_anonymous": 0,
        }, headers=_cookie(t1))
        post_id = r.json()["data"]["id"]

        r = client.post("/api/auth/register", data={
            "email": "u2@t.com", "username": "u2", "password": "123456",
        })
        assert r.json()["ok"]
        r = client.post("/api/auth/login", data={
            "email": "u2@t.com", "password": "123456",
        })
        t2 = r.cookies.get("jobpilot_token")

        r = client.post(f"/api/forum/posts/{post_id}/comments", json={
            "content": "great post!", "is_anonymous": 0,
        }, headers=_cookie(t2))
        assert r.json()["ok"] is True

        r = client.get("/api/forum/notifications", headers=_cookie(t1))
        notifs = r.json()["data"]
        assert len(notifs) >= 1
        assert notifs[0]["type"] == "post_reply"

    def test_unread_count(self, auth_client):
        client, uid = auth_client
        r = client.get("/api/forum/notifications/unread-count")
        assert r.json()["ok"] is True
        assert "count" in r.json()

    def test_read_notification(self, auth_client):
        client, uid = auth_client
        r = client.get("/api/forum/notifications")
        notifs = r.json().get("data", [])
        for n in notifs:
            r = client.post(f"/api/forum/notifications/{n['id']}/read")
            assert r.json()["ok"] is True

    def test_read_all_notifications(self, auth_client):
        client, uid = auth_client
        r = client.post("/api/forum/notifications/read-all")
        assert r.json()["ok"] is True

    def test_empty_content_rejected(self, auth_client):
        client, uid = auth_client
        r = client.post("/api/forum/posts", json={
            "title": "", "content": "", "tags": "", "is_anonymous": 0,
        })
        assert r.json()["ok"] is False

    def test_comment_on_nonexistent_post(self, auth_client):
        client, uid = auth_client
        r = client.post("/api/forum/posts/99999/comments", json={
            "content": "test", "is_anonymous": 0,
        })
        assert r.status_code == 404
