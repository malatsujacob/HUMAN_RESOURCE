import uuid
from sqlalchemy import Column, String, Date, Time, ForeignKey, Numeric, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.database import Base


class Attendance(Base):
    __tablename__ = "attendance"

    __table_args__ = (
        UniqueConstraint("employee_id", "date", name="uq_attendance_employee_date"),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    employee_id = Column(UUID(as_uuid=True), ForeignKey("employees.id"), nullable=False)
    date = Column(Date, nullable=False)
    check_in = Column(Time)
    check_out = Column(Time)
    status = Column(String(30), nullable=False, default="PRESENT")
    overtime_hours = Column(Numeric(5, 2), nullable=False, default=0)
    employee = relationship("Employee")
