from datetime import datetime, timezone

from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship

from app.database import Base


class Application(Base):
    __tablename__ = "applications"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    company = Column(String(200), nullable=False)
    position = Column(String(200), nullable=False)
    location = Column(String(100), default="")
    salary_range = Column(String(100), default="")
    source = Column(String(50), default="其他")
    jd_link = Column(String(500), default="")
    priority = Column(Integer, default=3)
    status = Column(String(20), default="applied", index=True)
    job_category = Column(String(50), default="")
    rejection_reason = Column(String(50), default="")
    offer_salary = Column(String(50), default="")
    notes = Column(Text, default="")
    applied_date = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc),
                        onupdate=lambda: datetime.now(timezone.utc))
    user = relationship("User", back_populates="applications")
    interviews = relationship("Interview", back_populates="application", cascade="all, delete-orphan")
