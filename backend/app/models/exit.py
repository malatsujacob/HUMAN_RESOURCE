import uuid

from sqlalchemy import Column, Boolean, Date, DateTime, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.sql import func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.database import Base


class EmployeeExit(Base):
    __tablename__ = "employee_exits"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    employee_id = Column(UUID(as_uuid=True), ForeignKey("employees.id"), nullable=False)
    last_working_day = Column(Date, nullable=False)
    reason = Column(String(500), nullable=False)
    clearance_status = Column(String(30), nullable=False, default="PENDING")
    clearance_note = Column(Text)
    clearance_reviewed_by = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    clearance_reviewed_at = Column(DateTime(timezone=True))

    exit_type = Column(String(30), default="RESIGNATION")
    resignation_date = Column(Date)
    notice_period_days = Column(Integer)
    notice_served = Column(Boolean, nullable=False, default=False)
    rehire_eligible = Column(Boolean)
    access_revoked = Column(Boolean, nullable=False, default=False)
    access_revoked_at = Column(DateTime(timezone=True))

    employee = relationship("Employee")
    clearance_items = relationship("ExitClearanceItem", back_populates="exit_record", cascade="all, delete-orphan")
    interview = relationship("ExitInterview", back_populates="exit_record", uselist=False, cascade="all, delete-orphan")
    final_pay = relationship("ExitFinalPay", back_populates="exit_record", uselist=False, cascade="all, delete-orphan")


class ExitClearanceItem(Base):
    __tablename__ = "exit_clearance_items"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    exit_id = Column(UUID(as_uuid=True), ForeignKey("employee_exits.id", ondelete="CASCADE"), nullable=False)
    item_code = Column(String(30), nullable=False)
    item_name = Column(String(100), nullable=False)
    status = Column(String(20), nullable=False, default="PENDING")
    cleared_by_user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    cleared_at = Column(DateTime(timezone=True))
    notes = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    exit_record = relationship("EmployeeExit", back_populates="clearance_items")
    cleared_by = relationship("User", foreign_keys=[cleared_by_user_id])


class ExitInterview(Base):
    __tablename__ = "exit_interviews"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    exit_id = Column(UUID(as_uuid=True), ForeignKey("employee_exits.id", ondelete="CASCADE"), nullable=False, unique=True)
    conducted_by_user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    interview_date = Column(Date)
    reason_category = Column(String(50))
    feedback_notes = Column(Text)
    would_recommend = Column(Boolean)
    rehire_eligible = Column(Boolean)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    exit_record = relationship("EmployeeExit", back_populates="interview")
    conducted_by = relationship("User", foreign_keys=[conducted_by_user_id])


class ExitFinalPay(Base):
    __tablename__ = "exit_final_pay"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    exit_id = Column(UUID(as_uuid=True), ForeignKey("employee_exits.id", ondelete="CASCADE"), nullable=False, unique=True)
    basic_salary = Column(Numeric(12, 2), nullable=False, default=0)
    leave_payout = Column(Numeric(12, 2), nullable=False, default=0)
    gratuity = Column(Numeric(12, 2), nullable=False, default=0)
    notice_pay = Column(Numeric(12, 2), nullable=False, default=0)
    other_earnings = Column(Numeric(12, 2), nullable=False, default=0)
    loan_deduction = Column(Numeric(12, 2), nullable=False, default=0)
    advance_deduction = Column(Numeric(12, 2), nullable=False, default=0)
    asset_deduction = Column(Numeric(12, 2), nullable=False, default=0)
    other_deductions = Column(Numeric(12, 2), nullable=False, default=0)
    net_pay = Column(Numeric(12, 2), nullable=False, default=0)
    payment_date = Column(Date)
    paid = Column(Boolean, nullable=False, default=False)
    calculated_by_user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    notes = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    exit_record = relationship("EmployeeExit", back_populates="final_pay")
    calculated_by = relationship("User", foreign_keys=[calculated_by_user_id])
