"""
JobPilot v0.3.0 — 求职追踪器 + AI 洞察 + 论坛
启动方式: python main.py  或  uvicorn app.main:app --reload
"""
import os
import uvicorn

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    # 云平台（Render/Railway）会设 PORT 环境变量，需要监听 0.0.0.0
    is_cloud = bool(os.getenv("PORT") or os.getenv("RENDER") or os.getenv("RAILWAY_ENV"))
    host = "0.0.0.0" if is_cloud else "127.0.0.1"
    uvicorn.run("app.main:app", host=host, port=port, reload=not is_cloud)
