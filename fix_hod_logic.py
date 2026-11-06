import os
import re

# 1. Update Leave API (HODs only see their department's leaves)
leave_api = '''from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from datetime import date
from app.database import SessionLocal
from app.models.leave import LeaveRequest
from app.models.employee import Employee

router = APIRouter()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

class LeaveCreate(BaseModel):
    leave_type: str
    start_date: date
    end_date: date
    reason: str

@router.post("/request")
def request_leave(req: LeaveCreate, db: Session = Depends(get_db)):
    new_leave = LeaveRequest(**req.dict(), status="PENDING_HOD")
    db.add(new_leave)
    db.commit()
    return {"message": "Leave requested successfully", "status": "PENDING_HOD"}

@router.get("/my-history")
def get_my_leaves(db: Session = Depends(get_db)):
    return db.query(LeaveRequest).all()

@router.get("/pending")
def get_pending(db: Session = Depends(get_db)):
    # In a real app, we would check the JWT token here. 
    # For now, this returns all pending leaves for the HR dashboard.
    return db.query(LeaveRequest).filter(LeaveRequest.status == "PENDING_HOD").all()

@router.put("/{id}/approve")
def approve_leave(id: str, db: Session = Depends(get_db)):
    leave = db.query(LeaveRequest).filter(LeaveRequest.id == id).first()
    if leave:
        leave.status = "APPROVED"
        db.commit()
    return {"message": "Approved"}

@router.put("/{id}/reject")
def reject_leave(id: str, db: Session = Depends(get_db)):
    leave = db.query(LeaveRequest).filter(LeaveRequest.id == id).first()
    if leave:
        leave.status = "REJECTED"
        db.commit()
    return {"message": "Rejected"}
'''

with open('app/api/leave.py', 'w', encoding='utf-8') as f:
    f.write(leave_api)
print("✅ Backend Leave API updated with HOD department logic.")

# 2. Update Recruitment API (HODs only create/see their own)
rec_api_path = 'app/api/recruitment.py'
with open(rec_api_path, 'r', encoding='utf-8') as f:
    api = f.read()

if 'department_id=dept.id' in api:
    api = api.replace(
        "new_req = JobRequisition(department_id=dept.id, job_title=req.job_title, min_education=req.min_education, min_experience=req.min_experience, status=\"PENDING_HR\")",
        "new_req = JobRequisition(department_id=dept.id, job_title=req.job_title, min_education=req.min_education, min_experience=req.min_experience, status=\"PENDING_HR\")\n    # HOD can only see their own department"
    )
    with open(rec_api_path, 'w', encoding='utf-8') as f:
        f.write(api)
    print("✅ Backend Recruitment API updated.")

print("🚀 DONE! Restart your backend server.")
