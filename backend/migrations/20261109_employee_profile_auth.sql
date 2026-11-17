ALTER TABLE employees ADD COLUMN IF NOT EXISTS middle_name VARCHAR(100);
ALTER TABLE employees ADD COLUMN IF NOT EXISTS gender VARCHAR(30);
ALTER TABLE employees ADD COLUMN IF NOT EXISTS marital_status VARCHAR(30);
ALTER TABLE users ADD COLUMN IF NOT EXISTS must_change_password BOOLEAN NOT NULL DEFAULT FALSE;
ALTER TABLE notifications ADD COLUMN IF NOT EXISTS recipient_user_id UUID REFERENCES users(id) ON DELETE CASCADE;
CREATE INDEX IF NOT EXISTS ix_notifications_recipient_user_id ON notifications (recipient_user_id);
