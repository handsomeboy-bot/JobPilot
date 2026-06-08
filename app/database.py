"""
数据库引擎、会话、Base
"""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

from app.config import DB_URL

# SQLite 需要 check_same_thread, PostgreSQL 需要 utf8 编码
_is_sqlite = DB_URL.startswith("sqlite")
_connect_args = {"check_same_thread": False} if _is_sqlite else {"client_encoding": "utf8"}
engine = create_engine(DB_URL, connect_args=_connect_args)
SessionLocal = sessionmaker(bind=engine, autoflush=False)
Base = declarative_base()

_ = Base  # noqa: F841


def get_db():
    """FastAPI 依赖：获取数据库会话"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
