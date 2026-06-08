"""
测试配置 — SQLite 内存数据库 + TestClient
"""
import json

import pytest
from fastapi.testclient import TestClient

# 必须在 import app 之前覆盖配置
import app.config as _cfg
import tempfile, os
_cfg.DB_URL = f"sqlite:///{tempfile.mkdtemp()}/test.db"
_cfg.load_invite_config = lambda: {"enabled": False, "code": "jobpilot2026"}
_cfg.load_email_config = lambda: {"enabled": False, "smtp_host": "smtp.qq.com",
    "smtp_port": 587, "sender": "", "password": "", "receiver": ""}

import app.models.user  # noqa 注册模型
import app.models.application  # noqa
import app.models.interview  # noqa
import app.models.interview_note  # noqa
import app.models.forum  # noqa

from app.database import Base, engine, SessionLocal, get_db  # noqa: E402
from app.main import app  # noqa: E402

# 替换依赖
def _test_get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = _test_get_db


def create_tables():
    Base.metadata.create_all(bind=engine)


def drop_tables():
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def client():
    # 每次 test 前后重建表
    create_tables()
    yield TestClient(app)
    drop_tables()


@pytest.fixture
def auth_client(client):
    """已登录的 client"""
    r = client.post("/api/auth/register", data={
        "email": "test@test.com",
        "username": "tester",
        "password": "123456",
    })
    assert r.json()["ok"], f"注册失败: {r.json()}"
    r = client.post("/api/auth/login", data={
        "email": "test@test.com",
        "password": "123456",
    })
    cookie = r.cookies.get("jobpilot_token")
    client.cookies.set("jobpilot_token", cookie)
    from app.auth import SECRET_KEY, ALGORITHM
    from jose import jwt
    payload = jwt.decode(cookie, SECRET_KEY, algorithms=[ALGORITHM])
    return client, int(payload["sub"])
