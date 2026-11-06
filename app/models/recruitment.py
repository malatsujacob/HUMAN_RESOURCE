import uuid

from sqlalchemy import Column, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID

from app.database import Base


class JobRequisition(Base):
    __tablename__ = "job_requisitions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    department_id = Column(UUID(as_uuid=True), ForeignKey("departments.id"))
    job_title = Column(String(100))
    min_education = Column(String(50))
    min_experience = Column(Integer)
    status = Column(String(30), default="PENDING_HR")
    max_applicants = Column(Integer, default=50)


class Candidate(Base):
    __tablename__ = "candidates"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    requisition_id = Column(UUID(as_uuid=True), ForeignKey("job_requisitions.id"))
    first_name = Column(String(100))
    last_name = Column(String(100))
    email = Column(String(100))
    phone_number = Column(String(30))
    phone = Column(String(30))
    education_level = Column(String(50))
    experience_years = Column(Integer)
    cover_letter = Column(Text)
    cv_path = Column(String(255))
    status = Column(String(30), default="APPLIED")
    interview_grade = Column(String(30))
    onboarding_requirements = Column(String(500))
    phone_number = Column(String(30))
    rejection_reason = Column(Text)
