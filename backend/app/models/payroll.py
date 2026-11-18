import uuid
from sqlalchemy import Column, String, Numeric, ForeignKey, Date, DateTime, JSON, Text, UniqueConstraint, event, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.database import Base


class Payslip(Base):
    __tablename__ = "payslips"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    employee_id = Column(UUID(as_uuid=True), ForeignKey("employees.id"), nullable=False)
    pay_period = Column(String(7), nullable=False)
    gross_salary = Column(Numeric(15, 2), nullable=False)
    paye_tax = Column(Numeric(15, 2), nullable=False)
    nssf_deduction = Column(Numeric(15, 2), nullable=False)
    net_salary = Column(Numeric(15, 2), nullable=False)
    employer_contribution = Column(Numeric(15, 2), nullable=False, default=0)
    employer_pension = Column(Numeric(15, 2), nullable=False, default=0)
    employer_social_contribution = Column(Numeric(15, 2), nullable=False, default=0)
    bonus_amount = Column(Numeric(15, 2), nullable=False, default=0)
    overtime_amount = Column(Numeric(15, 2), nullable=False, default=0)
    retro_amount = Column(Numeric(15, 2), nullable=False, default=0)
    retro_reason = Column(String(500))
    retro_source = Column(String(500))
    retro_verified = Column(String(20), nullable=False, default="PENDING")
    pay_code = Column(String(40), nullable=False, default="BASE_WAGES")
    employee = relationship("Employee")


class PayrollCycle(Base):
    __tablename__ = "payroll_cycles"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    pay_period = Column(String(7), unique=True, nullable=False, index=True)
    stage = Column(String(20), nullable=False, default="DATA_ENTRY")
    approval_deadline = Column(Date)
    posting_deadline = Column(Date)
    updated_by = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    updated_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())


class PayrollReconciliation(Base):
    __tablename__ = "payroll_reconciliations"
    __table_args__ = (
        UniqueConstraint("pay_period", "reconciliation_type", name="uq_payroll_reconciliation_period_type"),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    pay_period = Column(String(7), nullable=False, index=True)
    reconciliation_type = Column(String(20), nullable=False)
    status = Column(String(20), nullable=False)
    details = Column(JSON, nullable=False, default=dict)
    updated_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    updated_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())


class PayrollAuditEvent(Base):
    __tablename__ = "payroll_audit_events"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    pay_period = Column(String(7), nullable=False, index=True)
    actor_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    actor_email = Column(String(255), nullable=False)
    action_type = Column(String(50), nullable=False)
    target = Column(String(100), nullable=False)
    before_value = Column(Text)
    after_value = Column(Text)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), index=True)


@event.listens_for(PayrollAuditEvent, "before_update")
def prevent_payroll_audit_update(mapper, connection, target):
    raise ValueError("Payroll audit events are immutable")


@event.listens_for(PayrollAuditEvent, "before_delete")
def prevent_payroll_audit_delete(mapper, connection, target):
    raise ValueError("Payroll audit events are immutable")
