-- Exit module full build
-- Adds due-process fields, exit interview table, final pay table

-- 1. Add fields to employee_exits
ALTER TABLE employee_exits
    ADD COLUMN IF NOT EXISTS exit_type VARCHAR(30) DEFAULT 'RESIGNATION',
    ADD COLUMN IF NOT EXISTS resignation_date DATE,
    ADD COLUMN IF NOT EXISTS notice_period_days INTEGER,
    ADD COLUMN IF NOT EXISTS notice_served BOOLEAN NOT NULL DEFAULT FALSE,
    ADD COLUMN IF NOT EXISTS rehire_eligible BOOLEAN,
    ADD COLUMN IF NOT EXISTS access_revoked BOOLEAN NOT NULL DEFAULT FALSE,
    ADD COLUMN IF NOT EXISTS access_revoked_at TIMESTAMPTZ;

CREATE INDEX IF NOT EXISTS ix_exit_type ON employee_exits (exit_type);

-- 2. Exit interviews table
CREATE TABLE IF NOT EXISTS exit_interviews (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    exit_id UUID NOT NULL UNIQUE REFERENCES employee_exits(id) ON DELETE CASCADE,
    conducted_by_user_id UUID REFERENCES users(id),
    interview_date DATE,
    reason_category VARCHAR(50),
    feedback_notes TEXT,
    would_recommend BOOLEAN,
    rehire_eligible BOOLEAN,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS ix_interview_exit ON exit_interviews (exit_id);

-- 3. Exit final pay table
CREATE TABLE IF NOT EXISTS exit_final_pay (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    exit_id UUID NOT NULL UNIQUE REFERENCES employee_exits(id) ON DELETE CASCADE,
    basic_salary NUMERIC(12,2) NOT NULL DEFAULT 0,
    leave_payout NUMERIC(12,2) NOT NULL DEFAULT 0,
    gratuity NUMERIC(12,2) NOT NULL DEFAULT 0,
    notice_pay NUMERIC(12,2) NOT NULL DEFAULT 0,
    other_earnings NUMERIC(12,2) NOT NULL DEFAULT 0,
    loan_deduction NUMERIC(12,2) NOT NULL DEFAULT 0,
    advance_deduction NUMERIC(12,2) NOT NULL DEFAULT 0,
    asset_deduction NUMERIC(12,2) NOT NULL DEFAULT 0,
    other_deductions NUMERIC(12,2) NOT NULL DEFAULT 0,
    net_pay NUMERIC(12,2) NOT NULL DEFAULT 0,
    payment_date DATE,
    paid BOOLEAN NOT NULL DEFAULT FALSE,
    calculated_by_user_id UUID REFERENCES users(id),
    notes TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS ix_final_pay_exit ON exit_final_pay (exit_id);
