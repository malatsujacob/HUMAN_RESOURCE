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
