import uuid
from sqlalchemy import Column, String, Boolean, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String(255), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    role = Column(String(50), nullable=False, default="EMPLOYEE")
    is_active = Column(Boolean, default=True)
    
    employee_id = Column(UUID(as_uuid=True), ForeignKey("employees.id"), unique=True)
    employee = relationship("Employee", back_populates="user_account")
