"""
页面路由
"""
from fastapi import APIRouter, Request, Depends
from fastapi.responses import HTMLResponse

from app.auth import get_current_user
from app.models.user import User
from app.template import render

router = APIRouter(include_in_schema=False)


@router.get("/", response_class=HTMLResponse)
def page_home(request: Request):
    return render("index.html", {"request": request, "user": None})


@router.get("/login", response_class=HTMLResponse)
def page_login(request: Request):
    return render("login.html", {"user": None})


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
def page_forum_list(request: Request, user: User = Depends(get_current_user)):
    return render("forum_list.html", {"request": request, "user": user})


@router.get("/forum/{post_id}", response_class=HTMLResponse)
def page_forum_detail(request: Request, post_id: int, user: User = Depends(get_current_user)):
    return render("forum_detail.html", {"request": request, "user": user, "post_id": post_id})
