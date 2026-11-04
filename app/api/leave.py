from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from uuid import UUID
from datetime import date
from app.database import SessionLocal
from app.models.leave import LeaveRequest

router = APIRouter()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

class LeaveCreate(BaseModel):
    employee_id: UUID
    leave_type: str
    start_date: date
    end_date: date
    reason: str

@router.post("/request")
def request_leave(req: LeaveCreate, db: Session = Depends(get_db)):
    new_leave = LeaveRequest(**req.dict())
    db.add(new_leave)
    db.commit()
    return {"message": "Leave requested successfully", "status": "PENDING_HOD"}

@router.post("/{leave_id}/approve")
def approve_leave(leave_id: UUID, db: Session = Depends(get_db)):
    leave = db.query(LeaveRequest).filter(LeaveRequest.id == leave_id).first()
    if not leave:
        raise HTTPException(status_code=404, detail="Leave not found")
    leave.status = "APPROVED"
    db.commit()
    return {"message": "Leave approved"}
