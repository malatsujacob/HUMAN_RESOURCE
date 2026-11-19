-- Disciplinary module enhancements
-- Adds case management fields to disciplinary_cases
-- Adds evidence and structured outcomes tables

-- 1. Add new columns to disciplinary_cases (all nullable, backward-compatible)
ALTER TABLE disciplinary_cases
    ADD COLUMN IF NOT EXISTS case_number VARCHAR(30) UNIQUE,
    ADD COLUMN IF NOT EXISTS case_type VARCHAR(30) DEFAULT 'DISCIPLINARY',
    ADD COLUMN IF NOT EXISTS category VARCHAR(50),
    ADD COLUMN IF NOT EXISTS severity VARCHAR(20),
    ADD COLUMN IF NOT EXISTS hr_officer_id UUID REFERENCES users(id),
    ADD COLUMN IF NOT EXISTS policy_breached VARCHAR(255),
    ADD COLUMN IF NOT EXISTS confidential BOOLEAN NOT NULL DEFAULT FALSE,
    ADD COLUMN IF NOT EXISTS warning_level VARCHAR(20),
    ADD COLUMN IF NOT EXISTS expires_at TIMESTAMPTZ;

-- 2. Backfill case_number for existing rows (via CTE — window function safe)
WITH numbered AS (
    SELECT id,
           'DISC-' || TO_CHAR(incident_date, 'YYYY') || '-' ||
           LPAD(ROW_NUMBER() OVER (ORDER BY incident_date, id)::text, 4, '0') AS new_case_number
    FROM disciplinary_cases
    WHERE case_number IS NULL
)
UPDATE disciplinary_cases dc
SET case_number = numbered.new_case_number
FROM numbered
WHERE dc.id = numbered.id;

-- 3. Add indexes for query performance
CREATE INDEX IF NOT EXISTS ix_disciplinary_category ON disciplinary_cases (category);
CREATE INDEX IF NOT EXISTS ix_disciplinary_severity ON disciplinary_cases (severity);
CREATE INDEX IF NOT EXISTS ix_disciplinary_status ON disciplinary_cases (status);
CREATE INDEX IF NOT EXISTS ix_disciplinary_expires ON disciplinary_cases (expires_at);

-- 4. Evidence attachments table
CREATE TABLE IF NOT EXISTS disciplinary_evidence (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    case_id UUID NOT NULL REFERENCES disciplinary_cases(id) ON DELETE CASCADE,
    file_name VARCHAR(255) NOT NULL,
    file_path VARCHAR(500) NOT NULL,
    file_type VARCHAR(50),
    file_size INTEGER,
    description TEXT,
    uploaded_by_user_id UUID REFERENCES users(id),
    uploaded_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS ix_evidence_case ON disciplinary_evidence (case_id);

-- 5. Structured outcomes table (one per case)
CREATE TABLE IF NOT EXISTS disciplinary_outcomes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    case_id UUID NOT NULL UNIQUE REFERENCES disciplinary_cases(id) ON DELETE CASCADE,
    outcome_type VARCHAR(30) NOT NULL,
    warning_level VARCHAR(20),
    effective_date DATE,
    expiry_date DATE,
    suspension_days INTEGER,
    payroll_deduction BOOLEAN NOT NULL DEFAULT FALSE,
    deduction_amount NUMERIC(10,2),
    decision_by_user_id UUID REFERENCES users(id),
    decision_notes TEXT,
    appeal_lodged BOOLEAN NOT NULL DEFAULT FALSE,
    appeal_date DATE,
    appeal_grounds TEXT,
    appeal_outcome VARCHAR(30),
    appeal_notes TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS ix_outcome_case ON disciplinary_outcomes (case_id);
CREATE INDEX IF NOT EXISTS ix_outcome_type ON disciplinary_outcomes (outcome_type);