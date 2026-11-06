import os

# 1. Create the Notification Model (since it was missing)
os.makedirs('app/models', exist_ok=True)
with open('app/models/notification.py', 'w', encoding='utf-8') as f:
    f.write('''import uuid
from sqlalchemy import Column, String, Boolean, TIMESTAMP, func
from sqlalchemy.dialects.postgresql import UUID
from app.database import Base

class Notification(Base):
    __tablename__ = "notifications"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    recipient_employee_id = Column(UUID(as_uuid=True))
    type = Column(String(50))
    title = Column(String(100))
    message = Column(String(255))
    is_read = Column(Boolean, default=False)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
''')
print("✅ Notification model created!")

# 2. Safely add the max_applicants column using raw SQL (No data loss)
from app.database import engine
from sqlalchemy import text

with engine.connect() as conn:
    try:
        conn.execute(text("ALTER TABLE job_requisitions ADD COLUMN max_applicants INTEGER DEFAULT 50;"))
        conn.commit()
        print("✅ Added max_applicants column to database!")
    except Exception as e:
        print("ℹ️ Column already exists or error:", e)
        
    try:
        # Create notifications table safely
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS notifications (
                id UUID PRIMARY KEY,
                recipient_employee_id UUID,
                type VARCHAR(50),
                title VARCHAR(100),
                message VARCHAR(255),
                is_read BOOLEAN DEFAULT FALSE,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
            );
        """))
        conn.commit()
        print("✅ Created notifications table in database!")
    except Exception as e:
        print("ℹ️ Notifications table error:", e)

print("🚀 DONE! Database is fully updated.")
