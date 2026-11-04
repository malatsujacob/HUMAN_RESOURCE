from app.database import SessionLocal, engine, Base, get_password_hash
from app.models.department import Department
from app.models.employee import Employee
from app.models.user import User
import uuid
import datetime

Base.metadata.create_all(bind=engine)
db = SessionLocal()

# Create Departments
departments = ["TECH", "FINANCE", "CUSTOMER_SUPPORT", "SALES", "CATERING", "SECURITY", "ADMINISTRATION"]
for code in departments:
    if not db.query(Department).filter(Department.code == code).first():
        db.add(Department(id=uuid.uuid4(), code=code, name=code.title()))

db.commit()

# Create Admin with Hashed Password
admin_email = "admin@chapchapafrica.com"
if not db.query(User).filter(User.email == admin_email).first():
    admin_dept = db.query(Department).filter(Department.code == "ADMINISTRATION").first()
    
    admin_emp = Employee(
        id=uuid.uuid4(), employee_number="EMP-0000", first_name="System", last_name="Admin",
        department_id=admin_dept.id, job_title="HR Manager", hire_date=datetime.date.today(), status="ACTIVE"
    )
    db.add(admin_emp)
    db.commit()

    admin_user = User(
        id=uuid.uuid4(), email=admin_email, password_hash=get_password_hash("admin123"), 
        role="MANAGEMENT", employee_id=admin_emp.id
    )
    db.add(admin_user)
    db.commit()
    print("Admin created with email: admin@chapchapafrica.com and password: admin123")
else:
    print("Admin already exists.")
