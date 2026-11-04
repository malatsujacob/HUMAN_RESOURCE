import uuid
from sqlalchemy import Column, String, TIMESTAMP, func
from sqlalchemy.dialects.postgresql import UUID
from app.database import Base

class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    actor_email = Column(String(255))
    action = Column(String(100))
    target = Column(String(100))
    ip_address = Column(String(50))
    timestamp = Column(TIMESTAMP(timezone=True), server_default=func.now())
