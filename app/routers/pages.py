"""
页面路由
"""
from fastapi import APIRouter, Request, Depends
from fastapi.responses import HTMLResponse, RedirectResponse

from app.auth import get_current_user
from app.models.user import User
from app.template import render
from app.database import SessionLocal
from jose import jwt, JWTError
from app.config import SECRET_KEY, ALGORITHM

router = APIRouter(include_in_schema=False)


def _try_get_user(request: Request) -> User | None:
    """尝试获取用户，不报 401"""
    token = request.cookies.get("jobpilot_token")
    if not token:
        return None
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        db = SessionLocal()
        user = db.query(User).filter(User.id == int(payload["sub"])).first()
        db.close()
        return user
    except (JWTError, ValueError):
        return None


def _redirect_login():
    return RedirectResponse(url="/login", status_code=302)


@router.get("/", response_class=HTMLResponse)
def page_home(request: Request):
    return render("index.html", {"request": request, "user": None})


@router.get("/login", response_class=HTMLResponse)
def page_login(request: Request):
    return render("login.html", {"user": None})


@router.get("/forgot-password", response_class=HTMLResponse)
def page_forgot(request: Request):
    return render("forgot_password.html", {"request": request, "user": None})


@router.get("/register", response_class=HTMLResponse)
def page_register(request: Request):
    return render("register.html", {"request": request, "user": None})


@router.get("/invite", response_class=HTMLResponse)
def page_invite(request: Request):
    return render("invite.html", {"request": request, "user": None})


@router.get("/app", response_class=HTMLResponse)
def page_dashboard(request: Request, user: User = Depends(get_current_user)):
    return render("dashboard.html", {"request": request, "user": user})


@router.get("/forum", response_class=HTMLResponse)
def page_forum_list(request: Request):
    user = _try_get_user(request)
    if not user:
        return _redirect_login()
    return render("forum_list.html", {"request": request, "user": user})


@router.get("/forum/{post_id}", response_class=HTMLResponse)
def page_forum_detail(request: Request, post_id: int):
    user = _try_get_user(request)
    if not user:
        return _redirect_login()
    return render("forum_detail.html", {"request": request, "user": user, "post_id": post_id})
