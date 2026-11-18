from pathlib import Path
import uuid

from sqlalchemy import MetaData, Table, inspect, text, update

from app.database import engine
from app.constants.departments import (
    DEPARTMENT_CATALOG,
    canonical_department_code,
)

MIGRATIONS_DIR = Path(__file__).resolve().parents[2] / "migrations"


def upgrade_department_catalog() -> None:
    with engine.begin() as connection:
        rows = connection.execute(
            text("SELECT id, code, name FROM departments")
        ).mappings().all()
        classified = {
            row["id"]: canonical_department_code(row["code"])
            or canonical_department_code(row["name"])
            for row in rows
        }
        metadata = MetaData()
        inspector = inspect(connection)

        def reassign_department_references(source_id, target_id) -> None:
            for table_name in inspector.get_table_names():
                for foreign_key in inspector.get_foreign_keys(table_name):
                    if foreign_key.get("referred_table") != "departments":
                        continue
                    for column_name, referred_column in zip(
                        foreign_key.get("constrained_columns") or [],
                        foreign_key.get("referred_columns") or [],
                    ):
                        if referred_column != "id":
                            continue
                        table = Table(table_name, metadata, autoload_with=connection)
                        connection.execute(
                            update(table)
                            .where(table.c[column_name] == source_id)
                            .values({column_name: target_id})
                        )

        for department in DEPARTMENT_CATALOG:
            code = department["code"]
            matching_rows = [
                row for row in rows if classified[row["id"]] == code
            ]
            matching_rows.sort(key=lambda row: row["code"] != code)

            if not matching_rows:
                department_id = uuid.uuid4()
                connection.execute(
                    text(
                        "INSERT INTO departments (id, code, name) "
                        "VALUES (:id, :code, :name)"
                    ),
                    {"id": department_id, **department},
                )
                rows.append({"id": department_id, **department})
                classified[department_id] = code
                continue

            canonical_row = matching_rows[0]
            for duplicate in matching_rows[1:]:
                reassign_department_references(duplicate["id"], canonical_row["id"])
                connection.execute(
                    text("DELETE FROM departments WHERE id = :id"),
                    {"id": duplicate["id"]},
                )

            connection.execute(
                text("UPDATE departments SET code = :code, name = :name WHERE id = :id"),
                {"id": canonical_row["id"], **department},
            )


def upgrade_notification_center() -> None:
    with engine.begin() as connection:
        connection.execute(text(
            "ALTER TABLE notifications "
            "ADD COLUMN IF NOT EXISTS sender_user_id UUID "
            "REFERENCES users(id) ON DELETE SET NULL"
        ))
        connection.execute(text(
            "ALTER TABLE notifications "
            "ADD COLUMN IF NOT EXISTS in_reply_to_id UUID "
            "REFERENCES notifications(id) ON DELETE CASCADE"
        ))
        connection.execute(text(
            "CREATE INDEX IF NOT EXISTS ix_notifications_sender_user_id "
            "ON notifications(sender_user_id)"
        ))
        connection.execute(text(
            "CREATE INDEX IF NOT EXISTS ix_notifications_in_reply_to_id "
            "ON notifications(in_reply_to_id)"
        ))


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
