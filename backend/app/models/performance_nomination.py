import uuid
from sqlalchemy import Column, String, Numeric, ForeignKey, DateTime, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base


class MonthlyNomination(Base):
    __tablename__ = "performance_monthly_nominations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    department_id = Column(UUID(as_uuid=True), ForeignKey("departments.id"), nullable=False)
    review_period = Column(String(7), nullable=False)
    nominee_employee_id = Column(UUID(as_uuid=True), ForeignKey("employees.id"), nullable=False)
    weight = Column(Numeric(5, 2), nullable=False)
    monthly_score = Column(Numeric(5, 2), nullable=False)
    nominated_by_employee_id = Column(UUID(as_uuid=True), ForeignKey("employees.id"), nullable=False)
    notes = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    nominee = relationship("Employee", foreign_keys=[nominee_employee_id])
    nominated_by = relationship("Employee", foreign_keys=[nominated_by_employee_id])


class QuarterlyResult(Base):
    __tablename__ = "performance_quarterly_results"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    department_id = Column(UUID(as_uuid=True), ForeignKey("departments.id"), nullable=False)
    quarter = Column(String(7), nullable=False)
    best_performer_employee_id = Column(UUID(as_uuid=True), ForeignKey("employees.id"), nullable=False)
    weighted_score = Column(Numeric(5, 2), nullable=False)
    total_weight = Column(Numeric(5, 2), nullable=False)
    submitted_by_employee_id = Column(UUID(as_uuid=True), ForeignKey("employees.id"), nullable=False)
    submitted_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    best_performer = relationship("Employee", foreign_keys=[best_performer_employee_id])
    submitted_by = relationship("Employee", foreign_keys=[submitted_by_employee_id])
