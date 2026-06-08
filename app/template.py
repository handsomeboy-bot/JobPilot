"""
Jinja2 模板渲染工具
"""
import os
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from app.config import BASE_DIR

templates = Jinja2Templates(directory=os.path.join(BASE_DIR, "templates"))


def render(template_name: str, context: dict = None) -> HTMLResponse:
    """兼容 Starlette 1.x 的模板渲染"""
    ctx = context or {}
    template = templates.env.get_template(template_name)
    return HTMLResponse(content=template.render(ctx), media_type="text/html; charset=utf-8")
