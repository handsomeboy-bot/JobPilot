"""
JobPilot v0.3.0 — 求职追踪器 + AI 洞察 + 论坛
启动方式: python main.py  或  uvicorn app.main:app --reload
"""
import os
import uvicorn

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    host = "0.0.0.0" if os.getenv("RAILWAY_ENV") else "127.0.0.1"
    uvicorn.run("app.main:app", host=host, port=port, reload=host == "127.0.0.1")
