import uuid

from sqlalchemy import Column, DateTime, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.database import Base


class JobRequisition(Base):
    __tablename__ = "job_requisitions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    department_id = Column(UUID(as_uuid=True), ForeignKey("departments.id"))
    job_title = Column(String(100))
    min_education = Column(String(50))
    min_experience = Column(Integer)
    description = Column(Text)
    status = Column(String(30), default="PENDING_HR")
    max_applicants = Column(Integer, default=50)
    department = relationship("Department")


class Candidate(Base):
    __tablename__ = "candidates"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    requisition_id = Column(UUID(as_uuid=True), ForeignKey("job_requisitions.id"))
    first_name = Column(String(100))
    last_name = Column(String(100))
    email = Column(String(100))
    phone_number = Column(String(30))
    education_level = Column(String(50))
    experience_years = Column(Integer)
    cover_letter = Column(Text)
    cv_path = Column(String(255))
    status = Column(String(30), default="APPLIED")
    interview_grade = Column(String(30))
    interview_date = Column(DateTime(timezone=True))
    interviewer_name = Column(String(100))
    interview_location = Column(String(255))
    offer_salary = Column(Numeric(12, 2))
    onboarding_requirements = Column(Text)
    offer_response_token_hash = Column(String(64))
    offer_expires_at = Column(DateTime(timezone=True))
    offer_accepted_at = Column(DateTime(timezone=True))
    onboarding_documents_required = Column(Text)
    onboarding_token_hash = Column(String(64))
    onboarding_expires_at = Column(DateTime(timezone=True))
    rejection_reason = Column(Text)
    rejection_type = Column(String(40))
    employee_id = Column(UUID(as_uuid=True), ForeignKey("employees.id"))
    requisition = relationship("JobRequisition")
