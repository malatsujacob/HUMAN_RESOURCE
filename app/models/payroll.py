import uuid
from sqlalchemy import Column, String, Date, Numeric, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.database import Base

class Payslip(Base):
    __tablename__ = "payslips"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    employee_id = Column(UUID(as_uuid=True), ForeignKey("employees.id"))
    pay_period = Column(String(50)) # e.g., "2026-03"
    gross_salary = Column(Numeric(15, 2))
    paye_tax = Column(Numeric(15, 2))
    nssf_deduction = Column(Numeric(15, 2))
    net_salary = Column(Numeric(15, 2))
    employee = relationship("Employee")
