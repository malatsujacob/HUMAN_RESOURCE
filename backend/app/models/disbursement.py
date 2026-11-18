import uuid
from sqlalchemy import Column, String, Numeric, Integer, Date, ForeignKey, DateTime, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base


class PayrollDisbursement(Base):
    __tablename__ = "payroll_disbursements"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    payroll_cycle_id = Column(UUID(as_uuid=True), ForeignKey("payroll_cycles.id"), nullable=False)
    status = Column(String(20), nullable=False, default="DRAFT")
    payment_date = Column(Date)
    currency = Column(String(10), default="UGX")
    batch_reference = Column(String(100))
    total_amount = Column(Numeric(15, 2), default=0)
    employee_count = Column(Integer, default=0)
    generated_at = Column(DateTime(timezone=True), server_default=func.now())
    generated_by_employee_id = Column(UUID(as_uuid=True), ForeignKey("employees.id"))
    approved_by_employee_id = Column(UUID(as_uuid=True), ForeignKey("employees.id"))
    approved_at = Column(DateTime(timezone=True))
    bank_file_path = Column(String(500))
    confirmed_at = Column(DateTime(timezone=True))
    failure_reason = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    generated_by = relationship("Employee", foreign_keys=[generated_by_employee_id])
    approved_by = relationship("Employee", foreign_keys=[approved_by_employee_id])
    items = relationship("PayrollDisbursementItem", back_populates="disbursement", cascade="all, delete-orphan")


class PayrollDisbursementItem(Base):
    __tablename__ = "payroll_disbursement_items"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    disbursement_id = Column(UUID(as_uuid=True), ForeignKey("payroll_disbursements.id", ondelete="CASCADE"), nullable=False)
    employee_id = Column(UUID(as_uuid=True), ForeignKey("employees.id"), nullable=False)
    employee_number = Column(String(50))
    employee_name = Column(String(200))
    account_number = Column(String(50))
    account_name = Column(String(100))
    bank_name = Column(String(100))
    bank_code = Column(String(20))
    branch_code = Column(String(20))
    payment_method = Column(String(20), default="BANK")
    mobile_number = Column(String(20))
    net_pay = Column(Numeric(15, 2), nullable=False)
    payment_reference = Column(String(100))
    status = Column(String(20), default="PENDING")
    failure_reason = Column(Text)
    paid_at = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    disbursement = relationship("PayrollDisbursement", back_populates="items")
    employee = relationship("Employee")
