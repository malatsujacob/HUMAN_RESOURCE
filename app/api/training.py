from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List
from uuid import UUID
from datetime import date
from app.database import SessionLocal
from app.models.training import Course, TrainingSession, Enrollment
from app.models.employee import Employee
import uuid

router = APIRouter()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

class CourseCreate(BaseModel):
    title: str
    description: str
    is_mandatory: str

class SessionCreate(BaseModel):
    course_id: UUID
    target_audience: str
    trainer: str
    venue_link: str
    scheduled_date: date

class EnrollCreate(BaseModel):
    employee_ids: List[UUID]

@router.post("/courses")
def create_course(req: CourseCreate, db: Session = Depends(get_db)):
    new_course = Course(title=req.title, description=req.description, is_mandatory=req.is_mandatory)
    db.add(new_course)
    db.commit()
    return {"message": "Course added to catalog", "id": new_course.id}

@router.get("/courses")
def get_courses(db: Session = Depends(get_db)):
    return db.query(Course).all()

@router.post("/sessions")
def schedule_session(req: SessionCreate, db: Session = Depends(get_db)):
    new_session = TrainingSession(**req.dict(), status="SCHEDULED")
    db.add(new_session)
    db.commit()
    return {"message": "Session scheduled", "id": new_session.id}

@router.get("/sessions")
def get_sessions(db: Session = Depends(get_db)):
    sessions = db.query(TrainingSession).all()
    # Attach course title for frontend
    results = []
    for s in sessions:
        c = db.query(Course).filter(Course.id == s.course_id).first()
        results.append({
            "id": s.id, "course_title": c.title if c else "Unknown",
            "trainer": s.trainer, "date": s.scheduled_date, "audience": s.target_audience
        })
    return results

@router.post("/sessions/{session_id}/enroll")
def enroll_employees(session_id: str, req: EnrollCreate, db: Session = Depends(get_db)):
    for emp_id in req.employee_ids:
        # Step 5: Enroll
        new_enroll = Enrollment(session_id=session_id, employee_id=emp_id, status="ENROLLED")
        db.add(new_enroll)
        # Step 6: Notify (Mock)
        emp = db.query(Employee).filter(Employee.id == emp_id).first()
        if emp:
            print(f"[EMAIL MOCK] Sent to {emp.personal_email}: You have been enrolled in training.")
    db.commit()
    return {"message": f"Successfully enrolled {len(req.employee_ids)} employees"}

@router.get("/my-training")
def get_my_training(db: Session = Depends(get_db)):
    # Mocking current employee ID for now
    return db.query(Enrollment).all()
