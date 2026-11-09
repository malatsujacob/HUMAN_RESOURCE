import uuid

from sqlalchemy import Column, DateTime, ForeignKey, String, Text, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.database import Base


class EmployeeDocument(Base):
    __tablename__ = "employee_documents"
    __table_args__ = (UniqueConstraint("employee_id", "document_type", name="uq_employee_document_type"),)

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    employee_id = Column(UUID(as_uuid=True), ForeignKey("employees.id", ondelete="CASCADE"), nullable=False)
    document_type = Column(String(120), nullable=False)
    file_name = Column(String(255))
    file_path = Column(String(500))
    status = Column(String(30), nullable=False, default="MISSING")
    review_note = Column(Text)
    submitted_at = Column(DateTime(timezone=True))
    reviewed_at = Column(DateTime(timezone=True))
    reviewed_by = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())

    employee = relationship("Employee", back_populates="documents")
