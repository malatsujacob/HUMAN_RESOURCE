import os

# 1. Create the Training Models
os.makedirs('app/models', exist_ok=True)
model_code = '''import uuid
from sqlalchemy import Column, String, Integer, ForeignKey, TIMESTAMP, func, Date
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.database import Base

class Course(Base):
    __tablename__ = "courses"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title = Column(String(100), nullable=False)
    description = Column(String(500))
    is_mandatory = Column(String(10), default="NO")
    duration_hours = Column(Integer, default=2)

class TrainingSession(Base):
    __tablename__ = "training_sessions"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    course_id = Column(UUID(as_uuid=True), ForeignKey("courses.id"))
    target_audience = Column(String(100)) # Whole Company, Dept, Specific
    trainer = Column(String(100))
    venue_link = Column(String(255))
    scheduled_date = Column(Date)
    status = Column(String(30), default="SCHEDULED")

class Enrollment(Base):
    __tablename__ = "enrollments"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id = Column(UUID(as_uuid=True), ForeignKey("training_sessions.id"))
    employee_id = Column(UUID(as_uuid=True), ForeignKey("employees.id"))
    status = Column(String(30), default="ENROLLED") # ENROLLED, ATTENDED, CERTIFIED
    score = Column(Integer)
    certificate_path = Column(String(255))
'''
with open('app/models/training.py', 'w', encoding='utf-8') as f:
    f.write(model_code)
print("✅ Training Database Models created!")

# 2. Create the Training API
api_code = '''from fastapi import APIRouter, Depends, HTTPException
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
'''
with open('app/api/training.py', 'w', encoding='utf-8') as f:
    f.write(api_code)
print("✅ Training API created!")

# 3. Register in main.py
with open('main.py', 'r', encoding='utf-8') as f:
    main = f.read()
if 'training' not in main:
    main = main.replace("from app.api import", "from app.api import training,")
    main = main.replace("app.include_router(onboarding.router", "app.include_router(training.router, prefix='/api/training', tags=['Training'])\napp.include_router(onboarding.router")
    with open('main.py', 'w', encoding='utf-8') as f:
        f.write(main)
    print("✅ main.py updated to register Training router!")

# 4. Build Database Tables
from app.database import engine, Base
Base.metadata.create_all(bind=engine)
print("✅ Database tables created!")
