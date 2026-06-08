"""
系统设置：邮件配置 + 邀请码管理
"""
from fastapi import APIRouter, Request, Depends
from fastapi.responses import JSONResponse

import secrets
import string

from app.config import (
    load_email_config, save_email_config,
    load_invite_config, save_invite_config,
    load_invites, save_invites, find_valid_invite,
)
from app.services.email_service import send_email
from app.auth import get_current_user, get_admin
from app.models.user import User

router = APIRouter(prefix="/api", tags=["settings"])


# — 邀请码配置 —
@router.get("/invite-config")
def api_get_invite_config(user: User = Depends(get_current_user)):
    cfg = load_invite_config()
    return {"ok": True, "data": {
        "enabled": cfg["enabled"],
        "code": cfg["code"] if cfg["enabled"] else "***",
    }}


@router.get("/invite-required")
def api_invite_required():
    cfg = load_invite_config()
    return {"ok": True, "required": cfg["enabled"]}


@router.post("/invite-config")
async def api_save_invite_config(request: Request, admin: User = Depends(get_admin)):
    body = await request.json()
    cfg = load_invite_config()
    cfg["enabled"] = body.get("enabled", cfg["enabled"])
    cfg["code"] = body.get("code", cfg["code"])
    save_invite_config(cfg)
    return {"ok": True, "msg": "邀请码配置已保存"}


# — 邮箱邀请码管理 —
def _gen_code() -> str:
    """生成 8 位邀请码，如 JOB-X8K2PV3F"""
    suffix = ''.join(secrets.choice(string.ascii_uppercase + string.digits) for _ in range(8))
    return f"JOB-{suffix}"


@router.get("/invites")
def api_list_invites(admin: User = Depends(get_admin)):
    """列出所有邀请码（管理员）"""
    invites = load_invites()
    return {"ok": True, "data": invites}


@router.post("/invites")
async def api_send_invite(request: Request, admin: User = Depends(get_admin)):
    """给指定邮箱发送邀请码"""
    body = await request.json()
    to_email = body.get("email", "").strip()
    if not to_email:
        return JSONResponse({"ok": False, "msg": "请输入邮箱"}, 400)

    code = _gen_code()
    invites = load_invites()
    invites.append({
        "code": code,
        "email": to_email,
        "used": False,
        "created_at": __import__("datetime").datetime.now().strftime("%Y-%m-%d %H:%M"),
    })
    save_invites(invites)

    # 发送邀请邮件
    invite_url = f"http://127.0.0.1:8000/register?code={code}"
    email_body = f"""
    <h2>📨 你已被邀请使用 JobPilot！</h2>
    <p>你的专属邀请码：<b style="font-size:1.4rem;color:#4F46E5;">{code}</b></p>
    <p>点击下方链接直接注册：</p>
    <p><a href="{invite_url}" style="color:#4F46E5;">{invite_url}</a></p>
    <hr>
    <p style="color:#64748B;font-size:.85rem;">JobPilot — 用数据优化你的求职策略 🚀</p>
    """
    send_email(to_email, "你被邀请使用 JobPilot 🚀", email_body)

    return {"ok": True, "msg": f"邀请码已发送到 {to_email}", "data": {"code": code, "email": to_email}}


@router.delete("/invites/{code}")
def api_revoke_invite(code: str, admin: User = Depends(get_admin)):
    """撤销一个邀请码（管理员）"""
    invites = load_invites()
    invites = [i for i in invites if i["code"] != code]
    save_invites(invites)
    return {"ok": True, "msg": "邀请码已撤销"}


# — 邮件配置 —
@router.get("/email-config")
def api_get_email_config(user: User = Depends(get_current_user)):
    cfg = load_email_config()
    return {"ok": True, "data": {
        "enabled": cfg["enabled"],
        "smtp_host": cfg["smtp_host"],
        "smtp_port": cfg["smtp_port"],
        "sender": cfg["sender"],
        "receiver": cfg.get("receiver", ""),
        "has_password": bool(cfg.get("password")),
    }}


@router.post("/email-config")
async def api_save_email_config(
    request: Request,
    user: User = Depends(get_current_user),
):
    body = await request.json()
    cfg = load_email_config()
    cfg["enabled"] = body.get("enabled", cfg["enabled"])
    cfg["smtp_host"] = body.get("smtp_host", cfg["smtp_host"])
    cfg["smtp_port"] = int(body.get("smtp_port", cfg["smtp_port"]))
    cfg["sender"] = body.get("sender", cfg["sender"])
    cfg["receiver"] = body.get("receiver", cfg.get("receiver", ""))
    if body.get("password"):
        cfg["password"] = body["password"]
    save_email_config(cfg)
    return {"ok": True, "msg": "邮件配置已保存"}


@router.post("/email-test")
async def api_test_email(user: User = Depends(get_current_user)):
    cfg = load_email_config()
    if not cfg["enabled"]:
        return {"ok": False, "msg": "邮件通知未启用"}
    ok = send_email(
        cfg.get("receiver", cfg["sender"]),
        "🧪 JobPilot 测试邮件",
        "<h2>测试邮件</h2><p>如果你收到这封邮件，说明邮件配置正确！</p><p>你的面试提醒将会在面试前1小时自动发送。</p>"
    )
    return {"ok": ok, "msg": "测试邮件已发送" if ok else "发送失败，请检查配置"}
