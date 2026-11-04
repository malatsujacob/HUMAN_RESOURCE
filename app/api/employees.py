from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr
from app.database import SessionLocal, get_password_hash
from app.models.employee import Employee
from app.models.user import User
from app.models.department import Department

router = APIRouter()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

class EmployeeCreate(BaseModel):
    first_name: str
    last_name: str
    personal_email: EmailStr
    job_title: str
    department_code: str
    role: str = "EMPLOYEE"

@router.get("/")
def get_employees(db: Session = Depends(get_db)):
    return db.query(Employee).all()

@router.post("/")
def create_employee(emp: EmployeeCreate, db: Session = Depends(get_db)):
    dept = db.query(Department).filter(Department.code == emp.department_code).first()
    if not dept:
        raise HTTPException(status_code=400, detail="Department not found")

    new_emp = Employee(
        employee_number="EMP-" + str(int(Employee.__table__.count().execute().scalar() or 0) + 1000),
        first_name=emp.first_name, last_name=emp.last_name, personal_email=emp.personal_email,
        job_title=emp.job_title, department_id=dept.id, status="ACTIVE"
    )
    db.add(new_emp)
    db.commit()
    db.refresh(new_emp)

    new_user = User(
        email=emp.personal_email, password_hash=get_password_hash("Welcome123!"),
        role=emp.role, employee_id=new_emp.id
    )
    db.add(new_user)
    db.commit()

    return {"message": "Employee created successfully", "employee_id": new_emp.id}
