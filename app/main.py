"""
JobPilot 主应用入口
"""
import os

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.config import BASE_DIR
from app.database import Base, engine
from app.services.interview_reminder import start_reminder_thread

# 导入所有模型，确保 create_all 能发现
from app.models.user import User  # noqa: F401
from app.models.application import Application  # noqa: F401
from app.models.interview import Interview  # noqa: F401
from app.models.interview_note import InterviewNote  # noqa: F401
from app.models.forum import ForumPost, ForumComment, ForumNotification  # noqa: F401

# 导入所有路由
from app.routers import auth, applications, interviews, notes, settings, pages, analytics, forum

app = FastAPI(title="JobPilot", version="0.2.0")

# 静态文件
app.mount("/static", StaticFiles(directory=os.path.join(BASE_DIR, "static")), name="static")

# 注册路由
app.include_router(auth.router)
app.include_router(applications.router)
app.include_router(interviews.router)
app.include_router(notes.router)
app.include_router(settings.router)
app.include_router(analytics.router)
app.include_router(forum.router)
app.include_router(pages.router)


@app.on_event("startup")
def startup():
    Base.metadata.create_all(bind=engine)

    # 确保管理员账号存在
    from app.database import SessionLocal
    from app.models.user import User, hash_password
    db = SessionLocal()
    try:
        admin = db.query(User).filter(User.email == "boss@jobpilot.com").first()
        if not admin:
            db.add(User(
                email="boss@jobpilot.com",
                username="老板",
                hashed_password=hash_password("boss123456"),
                is_admin=1,
            ))
            db.commit()
            print("✅ 管理员账号已创建: boss@jobpilot.com")
    finally:
        db.close()

    start_reminder_thread()
    print("🚀 JobPilot v0.3.0 已启动")
