import uuid
from sqlalchemy import Column, String, Integer, Numeric, ForeignKey, TIMESTAMP, func, Date
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.database import Base

class PayrollRun(Base):
    __tablename__ = "payroll_runs"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    pay_period = Column(String(50), nullable=False)
    target_audience = Column(String(100), default="Entire Company")
    status = Column(String(30), default="DRAFT") # DRAFT, PENDING_APPROVAL, APPROVED, PAID
    total_gross = Column(Numeric(15, 2), default=0.0)
    total_net = Column(Numeric(15, 2), default=0.0)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())

class Payslip(Base):
    __tablename__ = "payslips"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    run_id = Column(UUID(as_uuid=True), ForeignKey("payroll_runs.id"))
    employee_id = Column(UUID(as_uuid=True), ForeignKey("employees.id"))
    basic_salary = Column(Numeric(15, 2))
    allowances = Column(Numeric(15, 2), default=0.0)
    overtime = Column(Numeric(15, 2), default=0.0)
    gross_pay = Column(Numeric(15, 2))
    paye_tax = Column(Numeric(15, 2))
    nssf_deduction = Column(Numeric(15, 2))
    other_deductions = Column(Numeric(15, 2), default=0.0)
    net_pay = Column(Numeric(15, 2))
    status = Column(String(30), default="GENERATED")
