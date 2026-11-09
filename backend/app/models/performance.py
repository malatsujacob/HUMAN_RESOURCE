import uuid
from sqlalchemy import Column, String, Integer, ForeignKey, Boolean, DateTime, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.database import Base

class PerformanceReview(Base):
    __tablename__ = "performance_reviews"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    employee_id = Column(UUID(as_uuid=True), ForeignKey("employees.id"), nullable=False)
    review_period = Column(String(50), nullable=False)
    self_rating = Column(Integer)
    hod_rating = Column(Integer)
    hod_comments = Column(String(1000))
    self_comment = Column(Text)
    punctuality = Column(String(30))
    overtime_worked = Column(Boolean, nullable=False, default=False)
    task_completion = Column(String(30))
    efficiency = Column(String(30))
    quality_of_work = Column(String(30))
    teamwork = Column(String(30))
    behavior_rating = Column(Integer)
    submitted_at = Column(DateTime(timezone=True))
    rated_at = Column(DateTime(timezone=True))
    employee = relationship("Employee")
