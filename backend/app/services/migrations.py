from pathlib import Path

from sqlalchemy import text

from app.database import engine

MIGRATIONS_DIR = Path(__file__).resolve().parents[2] / "migrations"


def upgrade_recruitment_pipeline() -> None:
    migration_path = MIGRATIONS_DIR / "20261104_recruitment_pipeline.sql"
    statements = migration_path.read_text(encoding="utf-8").split(";")
    with engine.begin() as connection:
        for statement in statements:
            if statement.strip():
                connection.execute(text(statement))


def upgrade_recruitment_workflow() -> None:
    migration_path = MIGRATIONS_DIR / "20261106_recruitment_workflow.sql"
    statements = migration_path.read_text(encoding="utf-8").split(";")
    with engine.begin() as connection:
        for statement in statements:
            if statement.strip():
                connection.execute(text(statement))


def upgrade_onboarding_contracts() -> None:
    migration_path = MIGRATIONS_DIR / "20261104_onboarding_contracts.sql"
    statements = migration_path.read_text(encoding="utf-8").split(";")
    with engine.begin() as connection:
        for statement in statements:
            if statement.strip():
                connection.execute(text(statement))


def upgrade_leave_approval() -> None:
    with engine.begin() as connection:
        connection.execute(
            text(
                "ALTER TABLE leave_requests "
                "ADD COLUMN IF NOT EXISTS approved_by UUID REFERENCES users(id)"
            )
        )


def upgrade_recruitment_onboarding() -> None:
    migration_path = MIGRATIONS_DIR / "20261109_recruitment_onboarding.sql"
    statements = migration_path.read_text(encoding="utf-8").split(";")
    with engine.begin() as connection:
        for statement in statements:
            if statement.strip():
                connection.execute(text(statement))


def upgrade_monthly_performance() -> None:
    migration_path = MIGRATIONS_DIR / "20261109_monthly_performance.sql"
    statements = migration_path.read_text(encoding="utf-8").split(";")
    with engine.begin() as connection:
        for statement in statements:
            if statement.strip():
                connection.execute(text(statement))


def upgrade_employee_profile_auth() -> None:
    migration_path = MIGRATIONS_DIR / "20261109_employee_profile_auth.sql"
    statements = migration_path.read_text(encoding="utf-8").split(";")
    with engine.begin() as connection:
        for statement in statements:
            if statement.strip():
                connection.execute(text(statement))


def upgrade_leave_audit() -> None:
    migration_path = MIGRATIONS_DIR / "20261109_leave_audit.sql"
    statements = migration_path.read_text(encoding="utf-8").split(";")
    with engine.begin() as connection:
        for statement in statements:
            if statement.strip():
                connection.execute(text(statement))


def upgrade_legacy_employee_profile() -> None:
    migration_path = MIGRATIONS_DIR / "20261110_legacy_employee_profile.sql"
    statements = migration_path.read_text(encoding="utf-8").split(";")
    with engine.begin() as connection:
        for statement in statements:
            if statement.strip():
                connection.execute(text(statement))


def upgrade_employee_profile_photo() -> None:
    migration_path = MIGRATIONS_DIR / "20261110_employee_profile_photo.sql"
    with engine.begin() as connection:
        connection.execute(text(migration_path.read_text(encoding="utf-8")))


def upgrade_contract_workflow() -> None:
    migration_path = MIGRATIONS_DIR / "20261110_contract_workflow.sql"
    statements = migration_path.read_text(encoding="utf-8").split(";")
    with engine.begin() as connection:
        for statement in statements:
            if statement.strip():
                connection.execute(text(statement))


def upgrade_hr_action_queues() -> None:
    migration_path = MIGRATIONS_DIR / "20261110_hr_action_queues.sql"
    statements = migration_path.read_text(encoding="utf-8").split(";")
    with engine.begin() as connection:
        for statement in statements:
            if statement.strip():
                connection.execute(text(statement))


def upgrade_payroll_controls() -> None:
    migration_path = MIGRATIONS_DIR / "20261117_payroll_controls.sql"
    statements = migration_path.read_text(encoding="utf-8").split(";")
    with engine.begin() as connection:
        for statement in statements:
            if statement.strip():
                connection.execute(text(statement))
        connection.execute(text(
            "CREATE OR REPLACE FUNCTION prevent_payroll_audit_mutation() "
            "RETURNS trigger LANGUAGE plpgsql AS $$ BEGIN "
            "RAISE EXCEPTION 'Payroll audit events are immutable'; END; $$"
        ))
        connection.execute(text("DROP TRIGGER IF EXISTS payroll_audit_immutable ON payroll_audit_events"))
        connection.execute(text(
            "CREATE TRIGGER payroll_audit_immutable BEFORE UPDATE OR DELETE ON payroll_audit_events "
            "FOR EACH ROW EXECUTE FUNCTION prevent_payroll_audit_mutation()"
        ))


def upgrade_performance_nominations() -> None:
    migration_path = MIGRATIONS_DIR / "20261118_performance_nominations.sql"
    statements = migration_path.read_text(encoding="utf-8").split(";")
    with engine.begin() as connection:
        for statement in statements:
            if statement.strip():
                connection.execute(text(statement))
def upgrade_disbursement() -> None:
    migration_path = MIGRATIONS_DIR / "20261119_disbursement.sql"
    statements = migration_path.read_text(encoding="utf-8").split(";")
    with engine.begin() as connection:
        for statement in statements:
            if statement.strip():
                connection.execute(text(statement))
