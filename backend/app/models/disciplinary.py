import uuid
from sqlalchemy import Column, String, Date, ForeignKey, DateTime, Text, Boolean, Integer, Numeric
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base


class DisciplinaryCase(Base):
    __tablename__ = "disciplinary_cases"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    employee_id = Column(UUID(as_uuid=True), ForeignKey("employees.id"), nullable=False)
    incident_date = Column(Date, nullable=False)
    description = Column(String(500), nullable=False)
    action_taken = Column(String(255))
    status = Column(String(30), nullable=False, default="OPEN")
    resolution_note = Column(Text)
    resolved_by = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    resolved_at = Column(DateTime(timezone=True))

    # New columns (added via migration 20261119)
    case_number = Column(String(30), unique=True)
    case_type = Column(String(30), default="DISCIPLINARY")
    category = Column(String(50))
    severity = Column(String(20))
    hr_officer_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    policy_breached = Column(String(255))
    confidential = Column(Boolean, nullable=False, default=False)
    warning_level = Column(String(20))
    expires_at = Column(DateTime(timezone=True))

    # Relationships
    employee = relationship("Employee", foreign_keys=[employee_id])
    hr_officer = relationship("User", foreign_keys=[hr_officer_id])
    resolver = relationship("User", foreign_keys=[resolved_by])
    evidence = relationship("DisciplinaryEvidence", back_populates="case", cascade="all, delete-orphan")
    outcome = relationship("DisciplinaryOutcome", back_populates="case", uselist=False, cascade="all, delete-orphan")


class DisciplinaryEvidence(Base):
    __tablename__ = "disciplinary_evidence"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    case_id = Column(UUID(as_uuid=True), ForeignKey("disciplinary_cases.id", ondelete="CASCADE"), nullable=False)
    file_name = Column(String(255), nullable=False)
    file_path = Column(String(500), nullable=False)
    file_type = Column(String(50))
    file_size = Column(Integer)
    description = Column(Text)
    uploaded_by_user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    uploaded_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    case = relationship("DisciplinaryCase", back_populates="evidence")
    uploaded_by = relationship("User", foreign_keys=[uploaded_by_user_id])


class DisciplinaryOutcome(Base):
    __tablename__ = "disciplinary_outcomes"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    case_id = Column(UUID(as_uuid=True), ForeignKey("disciplinary_cases.id", ondelete="CASCADE"), nullable=False, unique=True)
    outcome_type = Column(String(30), nullable=False)
    warning_level = Column(String(20))
    effective_date = Column(Date)
    expiry_date = Column(Date)
    suspension_days = Column(Integer)
    payroll_deduction = Column(Boolean, nullable=False, default=False)
    deduction_amount = Column(Numeric(10, 2))
    decision_by_user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    decision_notes = Column(Text)
    appeal_lodged = Column(Boolean, nullable=False, default=False)
    appeal_date = Column(Date)
    appeal_grounds = Column(Text)
    appeal_outcome = Column(String(30))
    appeal_notes = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    case = relationship("DisciplinaryCase", back_populates="outcome")
    decision_by = relationship("User", foreign_keys=[decision_by_user_id])
