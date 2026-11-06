from app.database import SessionLocal, engine, get_password_hash
from sqlalchemy import text
import app.models.department, app.models.employee, app.models.user, app.models.contract
from app.models.department import Department
from app.models.employee import Employee
from app.models.user import User
from app.models.contract import Contract
from app.database import Base
import uuid
import datetime

# 1. NUKE THE ENTIRE SCHEMA (Drops all tables completely)
print("Dropping schema...")
with engine.connect() as conn:
    conn.execute(text("DROP SCHEMA public CASCADE;"))
    conn.execute(text("CREATE SCHEMA public;"))
    conn.commit()
print("Schema dropped and recreated.")

# 2. REBUILD ALL TABLES
print("Rebuilding tables...")
Base.metadata.create_all(bind=engine)

# 3. INSERT DATA
db = SessionLocal()
print("Seeding data...")

# Create Departments
departments = ["TECH", "FINANCE", "SALES", "ADMINISTRATION"]
dept_ids = {}
for code in departments:
    new_dept = Department(id=uuid.uuid4(), code=code, name=code.title())
    db.add(new_dept)
    db.commit()
    dept_ids[code] = new_dept.id

# Create HOD (John Doe)
hod = Employee(id=uuid.uuid4(), employee_number="EMP-1001", first_name="John", last_name="Doe", job_title="Head of Tech", department_id=dept_ids["TECH"], status="ACTIVE")
db.add(hod)
db.commit()
db.add(User(id=uuid.uuid4(), email="hod@chapchapafrica.com", password_hash=get_password_hash("admin123"), role="HOD", employee_id=hod.id))
db.commit()

# Create Employee (Jane Smith)
emp = Employee(id=uuid.uuid4(), employee_number="EMP-1002", first_name="Jane", last_name="Smith", job_title="Software Engineer", department_id=dept_ids["TECH"], status="ACTIVE")
db.add(emp)
db.commit()
db.add(User(id=uuid.uuid4(), email="jane@chapchapafrica.com", password_hash=get_password_hash("admin123"), role="EMPLOYEE", employee_id=emp.id))
db.commit()

# Create Contract for Jane
contract = Contract(id=uuid.uuid4(), employee_id=emp.id, contract_type="PERMANENT", start_date=datetime.date.today(), base_salary=5000000, status="ACTIVE")
db.add(contract)
db.commit()

# Create Admin (System Admin)
admin = Employee(id=uuid.uuid4(), employee_number="EMP-0000", first_name="System", last_name="Admin", job_title="HR Manager", department_id=dept_ids["ADMINISTRATION"], status="ACTIVE")
db.add(admin)
db.commit()
db.add(User(id=uuid.uuid4(), email="admin@chapchapafrica.com", password_hash=get_password_hash("admin123"), role="MANAGEMENT", employee_id=admin.id))
db.commit()

print('✅ SUCCESS! Schema rebuilt and data seeded perfectly.')
