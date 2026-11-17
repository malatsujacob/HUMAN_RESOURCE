import uuid
from sqlalchemy import Column, String, Date, Numeric, ForeignKey, Integer, DateTime, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.database import Base

class Contract(Base):
    __tablename__ = "contracts"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    employee_id = Column(UUID(as_uuid=True), ForeignKey("employees.id"))
    contract_type = Column(String(50))
    start_date = Column(Date)
    end_date = Column(Date)
    base_salary = Column(Numeric(15, 2))
    job_title = Column(String(100))
    work_location = Column(String(200))
    employment_type = Column(String(30))
    probation_period = Column(String(50))
    notice_period = Column(String(50))
    payment_frequency = Column(String(50))
    responsibilities = Column(Text)
    benefits = Column(Text)
    terms_and_conditions = Column(Text)
    expiry_reminder_days = Column(Integer)
    expiry_alert_sent_at = Column(DateTime(timezone=True))
    signing_method = Column(String(20), nullable=False, default="DIGITAL")
    employer_signature_name = Column(String(200))
    employer_signed_by = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    employer_signed_at = Column(DateTime(timezone=True))
    employee_signature_name = Column(String(200))
    employee_signed_by = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    employee_signed_at = Column(DateTime(timezone=True))
    generated_file_path = Column(String(500))
    signed_file_path = Column(String(500))
    status = Column(String(30), default="DRAFT", nullable=False)
    employee = relationship("Employee")
