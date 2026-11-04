import uuid
from sqlalchemy import Column, String, Date, Integer, ForeignKey
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
    status = Column(String(30), default="PENDING_HR")

class Candidate(Base):
    __tablename__ = "candidates"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    requisition_id = Column(UUID(as_uuid=True), ForeignKey("job_requisitions.id"))
    first_name = Column(String(100))
    last_name = Column(String(100))
    email = Column(String(100))
    cv_path = Column(String(255))
    status = Column(String(30), default="APPLIED") # APPLIED, SHORTLISTED, INTERVIEWED, OFFERED, REJECTED, HIRED
