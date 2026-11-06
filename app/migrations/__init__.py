from pathlib import Path

from sqlalchemy import text

from app.database import engine


def upgrade_recruitment_pipeline() -> None:
    migration_path = Path(__file__).with_name("20261104_recruitment_pipeline.sql")
    statements = migration_path.read_text(encoding="utf-8").split(";")
    with engine.begin() as connection:
        for statement in statements:
            if statement.strip():
                connection.execute(text(statement))


def upgrade_onboarding_contracts() -> None:
    migration_path = Path(__file__).with_name("20261104_onboarding_contracts.sql")
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
