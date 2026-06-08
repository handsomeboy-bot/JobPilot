from datetime import datetime, timezone

from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship

from app.database import Base


class Interview(Base):
    __tablename__ = "interviews"
    id = Column(Integer, primary_key=True, index=True)
    application_id = Column(Integer, ForeignKey("applications.id"), nullable=False)
    round = Column(String(50), default="一面")
    scheduled_time = Column(DateTime, nullable=True)
    interviewer = Column(String(100), default="")
    interview_type = Column(String(50), default="技术面")
    interview_status = Column(String(20), default="scheduled")
    notes = Column(Text, default="")
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    application = relationship("Application", back_populates="interviews")
    interview_notes = relationship("InterviewNote", back_populates="interview", cascade="all, delete-orphan")
