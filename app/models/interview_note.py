from datetime import datetime, timezone

from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship

from app.database import Base


class InterviewNote(Base):
    __tablename__ = "interview_notes"
    id = Column(Integer, primary_key=True, index=True)
    interview_id = Column(Integer, ForeignKey("interviews.id"), nullable=False)
    application_id = Column(Integer, ForeignKey("applications.id"), nullable=False)
    questions_answers = Column(Text, default="[]")
    reflection = Column(Text, default="")
    tags = Column(String(200), default="")
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    interview = relationship("Interview", back_populates="interview_notes")
