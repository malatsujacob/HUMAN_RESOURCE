ALTER TABLE job_requisitions
    ADD COLUMN IF NOT EXISTS description TEXT;

ALTER TABLE candidates
    ADD COLUMN IF NOT EXISTS education_level VARCHAR(50),
    ADD COLUMN IF NOT EXISTS experience_years INTEGER,
    ADD COLUMN IF NOT EXISTS cover_letter TEXT,
    ADD COLUMN IF NOT EXISTS cv_path VARCHAR(255),
    ADD COLUMN IF NOT EXISTS interview_grade VARCHAR(30),
    ADD COLUMN IF NOT EXISTS interview_date TIMESTAMPTZ,
    ADD COLUMN IF NOT EXISTS interviewer_name VARCHAR(100),
    ADD COLUMN IF NOT EXISTS interview_location VARCHAR(255),
    ADD COLUMN IF NOT EXISTS offer_salary NUMERIC(12, 2),
    ADD COLUMN IF NOT EXISTS onboarding_requirements TEXT,
    ADD COLUMN IF NOT EXISTS offer_response_token_hash VARCHAR(64),
    ADD COLUMN IF NOT EXISTS offer_expires_at TIMESTAMPTZ,
    ADD COLUMN IF NOT EXISTS offer_accepted_at TIMESTAMPTZ,
    ADD COLUMN IF NOT EXISTS rejection_reason TEXT,
    ADD COLUMN IF NOT EXISTS rejection_type VARCHAR(40),
    ADD COLUMN IF NOT EXISTS employee_id UUID REFERENCES employees(id);
