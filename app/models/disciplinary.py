import uuid
from sqlalchemy import Column, String, Date, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.database import Base

class DisciplinaryCase(Base):
    __tablename__ = "disciplinary_cases"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    employee_id = Column(UUID(as_uuid=True), ForeignKey("employees.id"), nullable=False)
    incident_date = Column(Date, nullable=False)
    description = Column(String(500), nullable=False)
    action_taken = Column(String(255))
    status = Column(String(30), nullable=False, default="OPEN")
    employee = relationship("Employee")
