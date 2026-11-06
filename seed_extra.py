from app.database import SessionLocal, engine, Base, get_password_hash
from app.models.department import Department
from app.models.employee import Employee
from app.models.user import User
from app.models.contract import Contract
import uuid
import datetime

Base.metadata.create_all(bind=engine)
db = SessionLocal()

# 1. Ensure Departments exist
departments = ["TECH", "FINANCE", "SALES", "ADMINISTRATION"]
for code in departments:
    if not db.query(Department).filter(Department.code == code).first():
        db.add(Department(id=uuid.uuid4(), code=code, name=code.title()))
db.commit()

# 2. Create a fake HOD and Employee (if they don't exist)
if db.query(Employee).count() < 3:
    tech_dept = db.query(Department).filter(Department.code == "TECH").first()
    
    # HOD
    hod = Employee(id=uuid.uuid4(), employee_number="EMP-1001", first_name="John", last_name="Doe", job_title="Head of Tech", department_id=tech_dept.id, status="ACTIVE")
    db.add(hod)
    db.commit()
    db.add(User(id=uuid.uuid4(), email="hod@chapchapafrica.com", password_hash=get_password_hash("admin123"), role="HOD", employee_id=hod.id))
    
    # Normal Employee
    emp = Employee(id=uuid.uuid4(), employee_number="EMP-1002", first_name="Jane", last_name="Smith", job_title="Software Engineer", department_id=tech_dept.id, status="ACTIVE")
    db.add(emp)
    db.commit()
    db.add(User(id=uuid.uuid4(), email="jane@chapchapafrica.com", password_hash=get_password_hash("admin123"), role="EMPLOYEE", employee_id=emp.id))
    
    # Contract for Jane
    contract = Contract(id=uuid.uuid4(), employee_id=emp.id, contract_type="PERMANENT", start_date=datetime.date.today(), base_salary=5000000, status="ACTIVE")
    db.add(contract)
    
    db.commit()
    print("✅ Dummy employees and contracts created!")
else:
    print("✅ Data already exists.")
