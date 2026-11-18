ALTER TABLE employees ADD COLUMN IF NOT EXISTS account_name VARCHAR(100);
ALTER TABLE employees ADD COLUMN IF NOT EXISTS bank_code VARCHAR(20);
ALTER TABLE employees ADD COLUMN IF NOT EXISTS branch_code VARCHAR(20);
ALTER TABLE employees ADD COLUMN IF NOT EXISTS payment_method VARCHAR(20) DEFAULT 'BANK';
ALTER TABLE employees ADD COLUMN IF NOT EXISTS mobile_money_number VARCHAR(20);
ALTER TABLE employees ADD COLUMN IF NOT EXISTS cacco_number VARCHAR(50);
ALTER TABLE employees ADD COLUMN IF NOT EXISTS cacco_name VARCHAR(100);

CREATE TABLE IF NOT EXISTS payroll_disbursements (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    payroll_cycle_id UUID NOT NULL REFERENCES payroll_cycles(id) ON DELETE CASCADE,
    status VARCHAR(20) NOT NULL DEFAULT 'DRAFT',
    payment_date DATE,
    currency VARCHAR(10) DEFAULT 'UGX',
    batch_reference VARCHAR(100),
    total_amount NUMERIC(15,2) DEFAULT 0,
    employee_count INTEGER DEFAULT 0,
    generated_at TIMESTAMPTZ DEFAULT NOW(),
    generated_by_employee_id UUID REFERENCES employees(id),
    approved_by_employee_id UUID REFERENCES employees(id),
    approved_at TIMESTAMPTZ,
    bank_file_path VARCHAR(500),
    confirmed_at TIMESTAMPTZ,
    failure_reason TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS payroll_disbursement_items (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    disbursement_id UUID NOT NULL REFERENCES payroll_disbursements(id) ON DELETE CASCADE,
    employee_id UUID NOT NULL REFERENCES employees(id),
    employee_number VARCHAR(50),
    employee_name VARCHAR(200),
    account_number VARCHAR(50),
    account_name VARCHAR(100),
    bank_name VARCHAR(100),
    bank_code VARCHAR(20),
    branch_code VARCHAR(20),
    payment_method VARCHAR(20) DEFAULT 'BANK',
    mobile_number VARCHAR(20),
    net_pay NUMERIC(15,2) NOT NULL,
    payment_reference VARCHAR(100),
    status VARCHAR(20) DEFAULT 'PENDING',
    failure_reason TEXT,
    paid_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS ix_disb_cycle ON payroll_disbursements(payroll_cycle_id);
CREATE INDEX IF NOT EXISTS ix_disb_item_disb ON payroll_disbursement_items(disbursement_id);
CREATE INDEX IF NOT EXISTS ix_disb_item_emp ON payroll_disbursement_items(employee_id);
