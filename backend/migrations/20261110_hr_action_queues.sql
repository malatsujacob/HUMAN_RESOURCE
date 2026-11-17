ALTER TABLE disciplinary_cases
    ADD COLUMN IF NOT EXISTS resolution_note TEXT,
    ADD COLUMN IF NOT EXISTS resolved_by UUID REFERENCES users(id),
    ADD COLUMN IF NOT EXISTS resolved_at TIMESTAMPTZ;

ALTER TABLE employee_exits
    ADD COLUMN IF NOT EXISTS clearance_note TEXT,
    ADD COLUMN IF NOT EXISTS clearance_reviewed_by UUID REFERENCES users(id),
    ADD COLUMN IF NOT EXISTS clearance_reviewed_at TIMESTAMPTZ;
