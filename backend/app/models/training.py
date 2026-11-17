import uuid

from sqlalchemy import Boolean, Column, Date, DateTime, ForeignKey, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.database import Base


class TrainingCourse(Base):
    __tablename__ = "training_courses"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=False)
    is_mandatory = Column(String(3), nullable=False, default="NO")
    is_active = Column(Boolean, nullable=False, default=True)


class TrainingSession(Base):
    __tablename__ = "training_sessions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    course_id = Column(UUID(as_uuid=True), ForeignKey("training_courses.id"), nullable=False)
    target_audience = Column(String(50), nullable=False)
    trainer = Column(String(200), nullable=False)
    venue_link = Column(String(500), nullable=False)
    scheduled_date = Column(Date, nullable=False)
    created_by_user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)

    course = relationship("TrainingCourse")
    enrollments = relationship("TrainingEnrollment", back_populates="session", cascade="all, delete-orphan")


class TrainingEnrollment(Base):
    __tablename__ = "training_enrollments"
    __table_args__ = (UniqueConstraint("session_id", "employee_id", name="uq_training_session_employee"),)

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id = Column(UUID(as_uuid=True), ForeignKey("training_sessions.id"), nullable=False)
    employee_id = Column(UUID(as_uuid=True), ForeignKey("employees.id"), nullable=False)
    assigned_by_user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    status = Column(String(20), nullable=False, default="ASSIGNED")
    enrolled_at = Column(DateTime(timezone=True), nullable=False)
    completed_at = Column(DateTime(timezone=True))

    session = relationship("TrainingSession", back_populates="enrollments")
    employee = relationship("Employee")
