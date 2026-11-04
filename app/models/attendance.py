import uuid
from sqlalchemy import Column, String, Date, Time, ForeignKey, Numeric
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.database import Base

class Attendance(Base):
    __tablename__ = "attendance"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    employee_id = Column(UUID(as_uuid=True), ForeignKey("employees.id"))
    date = Column(Date)
    check_in = Column(Time)
    check_out = Column(Time)
    status = Column(String(30))
    overtime_hours = Column(Numeric(5, 2), default=0)
    employee = relationship("Employee")
