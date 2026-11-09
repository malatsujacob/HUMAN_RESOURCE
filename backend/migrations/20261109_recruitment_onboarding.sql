ALTER TABLE candidates ADD COLUMN IF NOT EXISTS onboarding_documents_required TEXT;
ALTER TABLE candidates ADD COLUMN IF NOT EXISTS onboarding_token_hash VARCHAR(64);
ALTER TABLE candidates ADD COLUMN IF NOT EXISTS onboarding_expires_at TIMESTAMPTZ;
ALTER TABLE employees ADD COLUMN IF NOT EXISTS work_email VARCHAR(255);
ALTER TABLE employees ADD COLUMN IF NOT EXISTS home_address VARCHAR(500);
ALTER TABLE employees ADD COLUMN IF NOT EXISTS father_name VARCHAR(200);
ALTER TABLE employees ADD COLUMN IF NOT EXISTS mother_name VARCHAR(200);
ALTER TABLE employees ADD COLUMN IF NOT EXISTS next_of_kin_name VARCHAR(200);
ALTER TABLE employees ADD COLUMN IF NOT EXISTS next_of_kin_relationship VARCHAR(100);
ALTER TABLE employees ADD COLUMN IF NOT EXISTS next_of_kin_phone VARCHAR(30);
ALTER TABLE employees ADD COLUMN IF NOT EXISTS next_of_kin_address VARCHAR(500);
CREATE TABLE IF NOT EXISTS employee_documents (
    id UUID PRIMARY KEY,
    employee_id UUID NOT NULL REFERENCES employees(id) ON DELETE CASCADE,
    document_type VARCHAR(120) NOT NULL,
    file_name VARCHAR(255),
    file_path VARCHAR(500),
    status VARCHAR(30) NOT NULL DEFAULT 'MISSING',
    review_note TEXT,
    submitted_at TIMESTAMPTZ,
    reviewed_at TIMESTAMPTZ,
    reviewed_by UUID REFERENCES users(id),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_employee_document_type UNIQUE (employee_id, document_type)
);
