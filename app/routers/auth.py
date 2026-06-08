"""
认证路由：注册、登录、登出
"""
from fastapi import APIRouter, Request, Form, Depends
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from app.database import get_db
from app.auth import get_current_user
from app.models.user import User, pwd_ctx
from app.config import load_invite_config, find_valid_invite, mark_invite_used, TOKEN_EXPIRE_DAYS, SECRET_KEY, ALGORITHM
from datetime import datetime, timedelta, timezone
from jose import jwt

router = APIRouter(prefix="/api/auth", tags=["auth"])


def hash_password(password: str) -> str:
    return pwd_ctx.hash(password)


def verify_password(plain: str, hashed: str) -> bool:
    return pwd_ctx.verify(plain, hashed)


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
            # 已有有效码，重发邮件
            code = inv["code"]
            send_email(to_email, "你的 JobPilot 邀请码 🚀", f"""<h2>📨 你的 JobPilot 邀请码</h2><p>你的专属邀请码：<b style="font-size:1.4rem;color:#4F46E5;">{code}</b></p><p>点击下方链接直接注册：</p><p><a href="http://127.0.0.1:8000/register?code={code}">http://127.0.0.1:8000/register?code={code}</a></p><p style="color:#64748B;font-size:.85rem;">此邀请码仅限 {to_email} 使用</p><hr><p>JobPilot — 用数据优化你的求职策略 🚀</p>""")
            return {"ok": True, "msg": "邀请码已重新发送，请查收邮件", "code_exists": True}

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
    send_email(to_email, "你的 JobPilot 邀请码 🚀", email_body)

    return {"ok": True, "msg": "邀请码已发送，请查收邮件"}


@router.post("/register-with-invite")
async def api_register_with_invite(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
    invite_code: str = Form(...),
    db: Session = Depends(get_db),
):
    """邀请码注册：用户名+密码+邀请码 → 从邀请码获取邮箱 → 创建账号"""
    if len(password) < 6:
        return JSONResponse({"ok": False, "msg": "密码至少6位"}, 400)

    # 验证邀请码并获取邮箱
    valid = find_valid_invite(invite_code)
    if not valid:
        return JSONResponse({"ok": False, "msg": "邀请码无效或已被使用"}, 403)

    email = valid["email"]
    if not email or email == "通用邀请码":
        return JSONResponse({"ok": False, "msg": "此邀请码未绑定邮箱，请使用邮箱专属邀请码"}, 400)

    # 检查邮箱是否已注册
    if db.query(User).filter(User.email == email).first():
        return JSONResponse({"ok": False, "msg": "该邮箱已注册"}, 400)

    # 检查用户名
    if db.query(User).filter(User.username == username).first():
        return JSONResponse({"ok": False, "msg": "该昵称已被使用，请换一个"}, 400)

    # 创建用户
    user = User(email=email, username=username, hashed_password=hash_password(password))
    db.add(user)
    db.commit()
    db.refresh(user)

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
