from app.database import SessionLocal, engine, Base, get_password_hash
from app.models.employee import Employee
from app.models.user import User
from app.models.department import Department
import uuid
import datetime

Base.metadata.create_all(bind=engine)
db = SessionLocal()

email = "malatsujacob@gmail.com"
password = "Jack.02.+ma"
first_name = "malatsu"
last_name = "jacob"

# 1. Create or find the Developer/Admin Employee
dev_emp = db.query(Employee).filter(Employee.personal_email == email).first()
if not dev_emp:
    admin_dept = db.query(Department).filter(Department.code == "ADMINISTRATION").first()
    if not admin_dept:
        admin_dept = Department(id=uuid.uuid4(), code="ADMINISTRATION", name="Administration")
        db.add(admin_dept)
        db.commit()

    dev_emp = Employee(
        id=uuid.uuid4(), 
        employee_number="DEV-0001", 
        first_name=first_name, 
        last_name=last_name, 
        personal_email=email,
        department_id=admin_dept.id, 
        job_title="System Developer", 
        hire_date=datetime.date.today(), 
        status="ACTIVE"
    )
    db.add(dev_emp)
    db.commit()
    print("✅ Developer Employee Profile Created.")

# 2. Create or update the User Account
dev_user = db.query(User).filter(User.email == email).first()
if not dev_user:
    dev_user = User(
        id=uuid.uuid4(), 
        email=email, 
        password_hash=get_password_hash(password), 
        role="MANAGEMENT", # Developer has full system access
        employee_id=dev_emp.id
    )
    db.add(dev_user)
    db.commit()
    print("✅ Developer User Account Created.")
else:
    dev_user.password_hash = get_password_hash(password)
    dev_user.role = "MANAGEMENT"
    dev_user.employee_id = dev_emp.id
    db.commit()
    print("✅ Developer User Account Updated.")

print(f"🚀 Done! Log in with: {email} | {password}")
