from app.database import SessionLocal, engine, Base, get_password_hash
from app.models.department import Department
from app.models.employee import Employee
from app.models.user import User
from app.models.contract import Contract
from sqlalchemy import text
import uuid
import datetime

db = SessionLocal()

# 1. FORCE DELETE ALL OLD DATA (Fixes the duplicate error)
db.execute(text("TRUNCATE TABLE users, employees, contracts, departments CASCADE;"))
db.commit()
print('Old data wiped.')

# 2. Create Departments
departments = ["TECH", "FINANCE", "SALES", "ADMINISTRATION"]
dept_ids = {}
for code in departments:
    new_dept = Department(id=uuid.uuid4(), code=code, name=code.title())
    db.add(new_dept)
    db.commit()
    dept_ids[code] = new_dept.id

# 3. Create HOD (John Doe)
hod = Employee(id=uuid.uuid4(), employee_number="EMP-1001", first_name="John", last_name="Doe", job_title="Head of Tech", department_id=dept_ids["TECH"], status="ACTIVE")
db.add(hod)
db.commit()
db.add(User(id=uuid.uuid4(), email="hod@chapchapafrica.com", password_hash=get_password_hash("admin123"), role="HOD", employee_id=hod.id))
db.commit()

# 4. Create Employee (Jane Smith)
emp = Employee(id=uuid.uuid4(), employee_number="EMP-1002", first_name="Jane", last_name="Smith", job_title="Software Engineer", department_id=dept_ids["TECH"], status="ACTIVE")
db.add(emp)
db.commit()
db.add(User(id=uuid.uuid4(), email="jane@chapchapafrica.com", password_hash=get_password_hash("admin123"), role="EMPLOYEE", employee_id=emp.id))
db.commit()

# 5. Create Contract for Jane
contract = Contract(id=uuid.uuid4(), employee_id=emp.id, contract_type="PERMANENT", start_date=datetime.date.today(), base_salary=5000000, status="ACTIVE")
db.add(contract)
db.commit()

# 6. Create Admin (just in case)
admin = Employee(id=uuid.uuid4(), employee_number="EMP-0000", first_name="System", last_name="Admin", job_title="HR Manager", department_id=dept_ids["ADMINISTRATION"], status="ACTIVE")
db.add(admin)
db.commit()
db.add(User(id=uuid.uuid4(), email="admin@chapchapafrica.com", password_hash=get_password_hash("admin123"), role="MANAGEMENT", employee_id=admin.id))
db.commit()

print('✅ SUCCESS! Database cleaned and seeded perfectly.')
