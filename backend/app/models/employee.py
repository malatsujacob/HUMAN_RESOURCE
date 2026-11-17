import uuid
from sqlalchemy import Column, String, Date, Numeric, ForeignKey, Integer
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.database import Base

class Employee(Base):
    __tablename__ = "employees"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    employee_number = Column(String(20), unique=True, index=True, nullable=False)
    legacy_employee_id = Column(Integer, unique=True, index=True)
    legacy_role = Column(String(50))
    legacy_department = Column(String(100))
    first_name = Column(String(100), nullable=False)
    middle_name = Column(String(100))
    last_name = Column(String(100), nullable=False)
    personal_email = Column(String(255))
    work_email = Column(String(255))
    phone_number = Column(String(30))
    home_address = Column(String(500))
    gender = Column(String(30))
    marital_status = Column(String(30))
    date_of_birth = Column(Date)
    nationality = Column(String(100))
    father_name = Column(String(200))
    mother_name = Column(String(200))
    next_of_kin_name = Column(String(200))
    next_of_kin_relationship = Column(String(100))
    next_of_kin_phone = Column(String(30))
    next_of_kin_address = Column(String(500))
    national_id = Column(String(30), unique=True)
    department_id = Column(UUID(as_uuid=True), ForeignKey("departments.id"))
    job_title = Column(String(100))
    reporting_manager = Column(String(200))
    work_location = Column(String(200))
    employment_type = Column(String(30))
    probation_period = Column(String(50))
    notice_period = Column(String(50))
    contract_end_date = Column(Date)
    hire_date = Column(Date)
    status = Column(String(30), default="ACTIVE")
    tin_number = Column(String(20))
    nssf_number = Column(String(20))
    bank_name = Column(String(100))
    account_number = Column(String(50))
    base_salary = Column(Numeric(15, 2))
    profile_photo_path = Column(String(500))
    
    department = relationship("Department")
    user_account = relationship("User", back_populates="employee", uselist=False)
    documents = relationship("EmployeeDocument", back_populates="employee", cascade="all, delete-orphan")
