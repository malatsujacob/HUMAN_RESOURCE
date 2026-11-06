from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from uuid import UUID
from app.database import SessionLocal
from app.models.recruitment import Candidate
from app.models.employee import Employee
from app.models.department import Department
import uuid
import datetime

router = APIRouter()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

class OnboardCreate(BaseModel):
    national_id: str
    tin_number: str
    nssf_number: str
    bank_name: str
    account_number: str

@router.get("/pending")
def get_pending_candidates(db: Session = Depends(get_db)):
    # Candidates who have OFFERED status need onboarding
    candidates = db.query(Candidate).filter(Candidate.status == "OFFERED").all()
    return candidates

@router.post("/{candidate_id}/convert")
def convert_to_employee(candidate_id: str, req: OnboardCreate, db: Session = Depends(get_db)):
    candidate = db.query(Candidate).filter(Candidate.id == candidate_id).first()
    if not candidate:
        raise HTTPException(status_code=404, detail="Candidate not found")

    # 1. Create the Employee record
    new_emp = Employee(
        id=uuid.uuid4(),
        employee_number=f"EMP-{int(datetime.datetime.now().timestamp())}",
        first_name=candidate.first_name,
        last_name=candidate.last_name,
        personal_email=candidate.email,
        phone_number=candidate.phone_number,
        national_id=req.national_id,
        tin_number=req.tin_number,
        nssf_number=req.nssf_number,
        bank_name=req.bank_name,
        account_number=req.account_number,
        job_title="New Hire", # Will be updated when contract is made
        department_id=candidate.requisition.department_id if candidate.requisition else None,
        hire_date=datetime.date.today(),
        status="PROBATION"
    )
    db.add(new_emp)
    
    # 2. Mark candidate as HIRED and link them
    candidate.status = "HIRED"
    candidate.employee_id = new_emp.id
    db.commit()
    
    return {"message": "Candidate successfully converted to Employee"}
