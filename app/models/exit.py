import uuid

from sqlalchemy import Column, Date, ForeignKey, String
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

    employee = relationship("Employee")
