import uuid
from sqlalchemy import Column, String, Date, Numeric, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.database import Base

class Contract(Base):
    __tablename__ = "contracts"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    employee_id = Column(UUID(as_uuid=True), ForeignKey("employees.id"))
    contract_type = Column(String(50))
    start_date = Column(Date)
    end_date = Column(Date)
    base_salary = Column(Numeric(15, 2))
    status = Column(String(30), default="DRAFT", nullable=False)
    employee = relationship("Employee")
