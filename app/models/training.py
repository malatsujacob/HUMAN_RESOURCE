import uuid
from sqlalchemy import Column, String, Integer, ForeignKey, TIMESTAMP, func, Date
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.database import Base

class Course(Base):
    __tablename__ = "courses"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title = Column(String(100), nullable=False)
    description = Column(String(500))
    is_mandatory = Column(String(10), default="NO")
    duration_hours = Column(Integer, default=2)

class TrainingSession(Base):
    __tablename__ = "training_sessions"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    course_id = Column(UUID(as_uuid=True), ForeignKey("courses.id"))
    target_audience = Column(String(100)) # Whole Company, Dept, Specific
    trainer = Column(String(100))
    venue_link = Column(String(255))
    scheduled_date = Column(Date)
    status = Column(String(30), default="SCHEDULED")

class Enrollment(Base):
    __tablename__ = "enrollments"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id = Column(UUID(as_uuid=True), ForeignKey("training_sessions.id"))
    employee_id = Column(UUID(as_uuid=True), ForeignKey("employees.id"))
    status = Column(String(30), default="ENROLLED") # ENROLLED, ATTENDED, CERTIFIED
    score = Column(Integer)
    certificate_path = Column(String(255))
