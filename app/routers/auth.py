"""
认证路由：注册、登录、登出
"""
from fastapi import APIRouter, Request, Form, Depends
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from app.database import get_db
from app.auth import get_current_user
from app.models.user import User, hash_password, verify_password
from app.config import (
    load_invite_config, find_valid_invite, mark_invite_used,
    TOKEN_EXPIRE_DAYS, SECRET_KEY, ALGORITHM,
    load_resets, save_resets, find_reset, mark_reset_used,
)
from datetime import datetime, timedelta, timezone
from jose import jwt

router = APIRouter(prefix="/api/auth", tags=["auth"])


def create_token(user_id: int) -> str:
    expire = datetime.now(timezone.utc) + timedelta(days=TOKEN_EXPIRE_DAYS)
    return jwt.encode({"sub": str(user_id), "exp": expire}, SECRET_KEY, algorithm=ALGORITHM)


@router.post("/register")
async def api_register(
    request: Request,
    email: str = Form(...),
    username: str = Form(...),
    password: str = Form(...),
    invite_code: str = Form(""),
    db: Session = Depends(get_db),
):
    if len(password) < 6:
        return JSONResponse({"ok": False, "msg": "密码至少6位"}, 400)

    invite_cfg = load_invite_config()
    if invite_cfg["enabled"]:
        valid = find_valid_invite(invite_code)
        if not valid:
            return JSONResponse({"ok": False, "msg": "邀请码错误，请联系管理员获取"}, 403)

    if db.query(User).filter(User.email == email).first():
        return JSONResponse({"ok": False, "msg": "该邮箱已注册"}, 400)

    user = User(email=email, username=username, hashed_password=hash_password(password))
    db.add(user)
    db.commit()
    db.refresh(user)

    if invite_code:
        mark_invite_used(invite_code)

    token = create_token(user.id)
    resp = JSONResponse({"ok": True, "msg": "注册成功"})
    resp.set_cookie("jobpilot_token", token, max_age=TOKEN_EXPIRE_DAYS * 86400, httponly=True)
    return resp


@router.post("/request-invite")
async def api_request_invite(request: Request):
    """自服务：用户输入邮箱，获取邀请码（60秒倒计时）"""
    import secrets, string
    from app.config import load_invite_config, load_invites, save_invites
    from app.services.email_service import send_email

    body = await request.json()
    to_email = body.get("email", "").strip()
    if not to_email:
        return JSONResponse({"ok": False, "msg": "请输入邮箱"}, 400)

    # 检查邀请码是否已开启
    invite_cfg = load_invite_config()
    if not invite_cfg["enabled"]:
        return JSONResponse({"ok": False, "msg": "当前不需要邀请码即可注册"}, 400)

    # 检查是否已有未使用的邀请码
    invites = load_invites()
    for inv in invites:
        if inv["email"] == to_email and not inv.get("used", False):
            code = inv["code"]
            mail_ok = send_email(to_email, "你的 JobPilot 邀请码 🚀", f"""<h2>📨 你的 JobPilot 邀请码</h2><p>你的专属邀请码：<b style="font-size:1.4rem;color:#4F46E5;">{code}</b></p><p>点击下方链接直接注册：</p><p><a href="http://127.0.0.1:8000/register?code={code}">http://127.0.0.1:8000/register?code={code}</a></p><p style="color:#64748B;font-size:.85rem;">此邀请码仅限 {to_email} 使用</p><hr><p>JobPilot — 用数据优化你的求职策略 🚀</p>""")
            return {"ok": True, "msg": "邀请码已重新发送，请查收邮件", "code": code, "mail_sent": mail_ok}

    # 生成新邀请码
    suffix = ''.join(secrets.choice(string.ascii_uppercase + string.digits) for _ in range(8))
    code = f"JOB-{suffix}"

    invites.append({
        "code": code,
        "email": to_email,
        "used": False,
        "created_at": __import__("datetime").datetime.now().strftime("%Y-%m-%d %H:%M"),
    })
    save_invites(invites)

    # 发送邮件
    invite_url = f"http://127.0.0.1:8000/register?code={code}"
    email_body = f"""
    <h2>📨 你的 JobPilot 邀请码</h2>
    <p>你的专属邀请码：<b style="font-size:1.4rem;color:#4F46E5;">{code}</b></p>
    <p>或点击下方链接直接注册：</p>
    <p><a href="{invite_url}" style="color:#4F46E5;">{invite_url}</a></p>
    <p style="color:#64748B;font-size:.85rem;">此邀请码仅限 {to_email} 使用</p>
    <hr>
    <p style="color:#64748B;font-size:.85rem;">JobPilot — 用数据优化你的求职策略 🚀</p>
    """
    mail_ok = send_email(to_email, "你的 JobPilot 邀请码 🚀", email_body)

    return {"ok": True, "msg": "邀请码已发送，请查收邮件", "code": code, "mail_sent": mail_ok}


@router.post("/register-with-invite")
async def api_register_with_invite(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
    invite_code: str = Form(...),
    email: str = Form(""),
    db: Session = Depends(get_db),
):
    """邀请码注册：用户名+密码+邀请码 → 从邀请码获取邮箱 → 创建账号"""
    if len(password) < 6:
        return JSONResponse({"ok": False, "msg": "密码至少6位"}, 400)

    valid = find_valid_invite(invite_code)
    if not valid:
        return JSONResponse({"ok": False, "msg": "邀请码无效或已被使用"}, 403)

    invite_email = valid.get("email", "")
    is_global = valid.get("type") == "global" or invite_email == "通用邀请码"

    if is_global:
        # 通用邀请码：用户必须提供邮箱
        if not email:
            return JSONResponse({"ok": False, "msg": "请填写邮箱"}, 400)
    else:
        email = invite_email  # 邮箱专属码：用邀请码绑定的邮箱

    if db.query(User).filter(User.email == email).first():
        return JSONResponse({"ok": False, "msg": "该邮箱已注册"}, 400)

    if db.query(User).filter(User.username == username).first():
        return JSONResponse({"ok": False, "msg": "该昵称已被使用，请换一个"}, 400)

    user = User(email=email, username=username, hashed_password=hash_password(password))
    db.add(user)
    db.commit()
    db.refresh(user)

    if not is_global:
        mark_invite_used(invite_code)

    token = create_token(user.id)
    resp = JSONResponse({"ok": True, "msg": "注册成功"})
    resp.set_cookie("jobpilot_token", token, max_age=TOKEN_EXPIRE_DAYS * 86400, httponly=True)
    return resp


@router.post("/login")
async def api_login(
    request: Request,
    email: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db),
):
    user = db.query(User).filter(User.email == email).first()
    if not user or not verify_password(password, user.hashed_password):
        return JSONResponse({"ok": False, "msg": "邮箱或密码错误"}, 401)

    token = create_token(user.id)
    resp = JSONResponse({"ok": True, "msg": "登录成功"})
    resp.set_cookie("jobpilot_token", token, max_age=TOKEN_EXPIRE_DAYS * 86400, httponly=True)
    return resp


@router.post("/logout")
async def api_logout():
    resp = JSONResponse({"ok": True})
    resp.delete_cookie("jobpilot_token")
    return resp


@router.post("/change-password")
async def api_change_password(
    request: Request,
    old_password: str = Form(...),
    new_password: str = Form(...),
    new_password2: str = Form(...),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """修改密码：输入旧密码 + 新密码（两次）"""
    if not verify_password(old_password, user.hashed_password):
        return JSONResponse({"ok": False, "msg": "旧密码错误"}, 400)
    if len(new_password) < 6:
        return JSONResponse({"ok": False, "msg": "新密码至少6位"}, 400)
    if new_password != new_password2:
        return JSONResponse({"ok": False, "msg": "两次新密码不一致"}, 400)
    if old_password == new_password:
        return JSONResponse({"ok": False, "msg": "新密码不能与旧密码相同"}, 400)

    user.hashed_password = hash_password(new_password)
    db.commit()
    return {"ok": True, "msg": "密码修改成功"}


@router.post("/forgot-password")
async def api_forgot_password(request: Request):
    """忘记密码 — 发送验证码到邮箱"""
    import secrets, string
    from app.services.email_service import send_email

    body = await request.json()
    email = body.get("email", "").strip()
    if not email:
        return JSONResponse({"ok": False, "msg": "请输入邮箱"}, 400)

    # 检查邮箱是否已注册
    db = next(get_db())
    user = db.query(User).filter(User.email == email).first()
    db.close()
    if not user:
        return JSONResponse({"ok": False, "msg": "该邮箱未注册"}, 404)

    # 生成 6 位验证码
    code = ''.join(secrets.choice(string.digits) for _ in range(6))

    # 存储
    resets = load_resets()
    # 使该邮箱之前的重置码失效
    for r in resets:
        if r["email"] == email:
            r["used"] = True
    resets.append({
        "email": email,
        "code": code,
        "used": False,
        "created_at": __import__("datetime").datetime.now().strftime("%Y-%m-%d %H:%M"),
        "expires_at": (__import__("datetime").datetime.now() + __import__("datetime").timedelta(minutes=10)).isoformat(),
    })
    save_resets(resets)

    # 发送邮件（本地能用，Render 上会失败但不影响）
    email_body = f"""
    <h2>🔐 JobPilot 密码重置</h2>
    <p>你的验证码：<b style="font-size:1.6rem;color:#4F46E5;letter-spacing:4px;">{code}</b></p>
    <p style="color:#64748B;">验证码 10 分钟内有效，请勿转发给他人。</p>
    <hr>
    <p style="color:#64748B;font-size:.85rem;">如果不是你本人操作，请忽略此邮件。</p>
    """
    mail_ok = send_email(email, "JobPilot 密码重置验证码 🔐", email_body)

    return {"ok": True, "msg": "验证码已发送，请查收邮件", "code": code, "mail_sent": mail_ok}


@router.post("/reset-password")
async def api_reset_password(request: Request):
    """重置密码 — 验证码 + 新密码"""
    body = await request.json()
    email = body.get("email", "").strip()
    code = body.get("code", "").strip()
    new_password = body.get("new_password", "").strip()

    if not email or not code or not new_password:
        return JSONResponse({"ok": False, "msg": "请填写完整信息"}, 400)
    if len(new_password) < 6:
        return JSONResponse({"ok": False, "msg": "新密码至少6位"}, 400)

    # 验证重置码
    reset = find_reset(email, code)
    if not reset:
        return JSONResponse({"ok": False, "msg": "验证码错误或已过期"}, 400)

    # 重置密码
    db = next(get_db())
    user = db.query(User).filter(User.email == email).first()
    if not user:
        db.close()
        return JSONResponse({"ok": False, "msg": "用户不存在"}, 404)

    user.hashed_password = hash_password(new_password)
    mark_reset_used(email, code)
    db.commit()
    db.close()

    return {"ok": True, "msg": "密码重置成功，请登录"}
