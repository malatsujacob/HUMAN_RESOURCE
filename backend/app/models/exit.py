import uuid

from sqlalchemy import Column, Date, DateTime, ForeignKey, String, Text
from sqlalchemy.sql import func
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
    clearance_note = Column(Text)
    clearance_reviewed_by = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    clearance_reviewed_at = Column(DateTime(timezone=True))

    employee = relationship("Employee")
    clearance_items = relationship("ExitClearanceItem", back_populates="exit_record", cascade="all, delete-orphan")


class ExitClearanceItem(Base):
    __tablename__ = "exit_clearance_items"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    exit_id = Column(UUID(as_uuid=True), ForeignKey("employee_exits.id", ondelete="CASCADE"), nullable=False)
    item_code = Column(String(30), nullable=False)
    item_name = Column(String(100), nullable=False)
    status = Column(String(20), nullable=False, default="PENDING")
    cleared_by_user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    cleared_at = Column(DateTime(timezone=True))
    notes = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    exit_record = relationship("EmployeeExit", back_populates="clearance_items")
    cleared_by = relationship("User", foreign_keys=[cleared_by_user_id])
