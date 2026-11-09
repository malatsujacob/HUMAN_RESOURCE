import uuid
from sqlalchemy import Column, String, Numeric, ForeignKey
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
    employee = relationship("Employee")
