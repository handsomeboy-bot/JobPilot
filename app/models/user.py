from datetime import datetime, timezone

from sqlalchemy import Column, Integer, String, Text, DateTime
from sqlalchemy.orm import relationship

from app.database import Base
import hashlib
import secrets

def hash_password(password: str) -> str:
    """SHA-256 + 随机盐（纯 Python，无需编译依赖）"""
    salt = secrets.token_hex(16)
    h = hashlib.sha256(f"{salt}:{password}".encode()).hexdigest()
    return f"{salt}:{h}"

def verify_password(plain: str, hashed: str) -> bool:
    try:
        salt, h = hashed.split(":", 1)
        return hashlib.sha256(f"{salt}:{plain}".encode()).hexdigest() == h
    except (ValueError, AttributeError):
        return False


class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    username = Column(String(100), nullable=False)
    hashed_password = Column(String(255), nullable=False)
    is_admin = Column(Integer, default=0)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    applications = relationship("Application", back_populates="user", cascade="all, delete-orphan")
