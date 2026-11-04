import uuid
from sqlalchemy import Column, String, Integer, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.database import Base

class PerformanceReview(Base):
    __tablename__ = "performance_reviews"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    employee_id = Column(UUID(as_uuid=True), ForeignKey("employees.id"))
    review_period = Column(String(50)) # e.g., Q1 2026
    self_rating = Column(Integer)
    hod_rating = Column(Integer)
    hod_comments = Column(String(500))
    employee = relationship("Employee")
