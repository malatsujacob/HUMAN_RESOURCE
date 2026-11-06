from fastapi import APIRouter, Depends, HTTPException
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
