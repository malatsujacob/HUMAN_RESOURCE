-- Exit clearance items table
-- Each exit gets 5 auto-created items tracked individually.

CREATE TABLE IF NOT EXISTS exit_clearance_items (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    exit_id UUID NOT NULL REFERENCES employee_exits(id) ON DELETE CASCADE,
    item_code VARCHAR(30) NOT NULL,
    item_name VARCHAR(100) NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'PENDING',
    cleared_by_user_id UUID REFERENCES users(id),
    cleared_at TIMESTAMPTZ,
    notes TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_exit_item UNIQUE (exit_id, item_code)
);

CREATE INDEX IF NOT EXISTS ix_exit_item_exit ON exit_clearance_items (exit_id);
CREATE INDEX IF NOT EXISTS ix_exit_item_status ON exit_clearance_items (status);

-- Backfill items for any existing exits
INSERT INTO exit_clearance_items (exit_id, item_code, item_name)
SELECT e.id, v.code, v.name
FROM employee_exits e
CROSS JOIN (
    VALUES
        ('IT', 'IT equipment & access'),
        ('FINANCE', 'Finance clearance'),
        ('HR', 'HR exit interview'),
        ('DEPT', 'Department handover'),
        ('STORE', 'Store & assets return')
) AS v(code, name)
WHERE NOT EXISTS (
    SELECT 1 FROM exit_clearance_items WHERE exit_id = e.id
);