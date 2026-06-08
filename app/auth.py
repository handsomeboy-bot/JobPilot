"""
认证依赖：get_current_user, get_admin
"""
from fastapi import Request, Depends, HTTPException
from sqlalchemy.orm import Session
from jose import jwt, JWTError

from app.config import SECRET_KEY, ALGORITHM
from app.database import get_db
from app.models.user import User


def get_current_user(request: Request, db: Session = Depends(get_db)) -> User:
    token = request.cookies.get("jobpilot_token")
    if not token:
        raise HTTPException(401)
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = int(payload["sub"])
    except JWTError:
        raise HTTPException(401)
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(401)
    return user


def get_admin(user: User = Depends(get_current_user)) -> User:
    if not user.is_admin:
        raise HTTPException(403, detail="需要管理员权限")
    return user
