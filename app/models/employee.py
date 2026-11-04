import uuid
from sqlalchemy import Column, String, Date, Numeric, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.database import Base

class Employee(Base):
    __tablename__ = "employees"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    employee_number = Column(String(20), unique=True, index=True, nullable=False)
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    personal_email = Column(String(255))
    phone_number = Column(String(30))
    national_id = Column(String(30), unique=True)
    department_id = Column(UUID(as_uuid=True), ForeignKey("departments.id"))
    job_title = Column(String(100))
    hire_date = Column(Date)
    status = Column(String(30), default="ACTIVE")
    tin_number = Column(String(20))
    nssf_number = Column(String(20))
    bank_name = Column(String(100))
    account_number = Column(String(50))
    base_salary = Column(Numeric(15, 2))
    
    department = relationship("Department")
    user_account = relationship("User", back_populates="employee", uselist=False)
