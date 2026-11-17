-- Performance monthly nominations + quarterly results
-- HOD nominates the best performer per month with a weight.
-- At quarter-end, weighted scores determine the department best performer.
-- HR sees results on master dashboard (read-only).

CREATE TABLE IF NOT EXISTS performance_monthly_nominations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    department_id UUID NOT NULL REFERENCES departments(id) ON DELETE CASCADE,
    review_period VARCHAR(7) NOT NULL,
    nominee_employee_id UUID NOT NULL REFERENCES employees(id) ON DELETE CASCADE,
    weight NUMERIC(5,2) NOT NULL CHECK (weight > 0 AND weight <= 100),
    monthly_score NUMERIC(5,2) NOT NULL,
    nominated_by_employee_id UUID NOT NULL REFERENCES employees(id),
    notes TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_dept_period_nomination UNIQUE (department_id, review_period)
);

CREATE INDEX IF NOT EXISTS ix_monthly_nom_dept_period
    ON performance_monthly_nominations (department_id, review_period);

CREATE INDEX IF NOT EXISTS ix_monthly_nom_nominee
    ON performance_monthly_nominations (nominee_employee_id);

CREATE TABLE IF NOT EXISTS performance_quarterly_results (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    department_id UUID NOT NULL REFERENCES departments(id) ON DELETE CASCADE,
    quarter VARCHAR(7) NOT NULL,
    best_performer_employee_id UUID NOT NULL REFERENCES employees(id),
    weighted_score NUMERIC(5,2) NOT NULL,
    total_weight NUMERIC(5,2) NOT NULL,
    submitted_by_employee_id UUID NOT NULL REFERENCES employees(id),
    submitted_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_dept_quarter_result UNIQUE (department_id, quarter)
);

CREATE INDEX IF NOT EXISTS ix_quarterly_result_quarter
    ON performance_quarterly_results (quarter);