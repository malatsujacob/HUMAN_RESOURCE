from datetime import date, datetime, timezone
from typing import Literal, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session, joinedload

from app.database import SessionLocal
from app.models.employee import Employee
from app.models.training import TrainingCourse, TrainingEnrollment, TrainingSession
from app.models.user import User
from app.routers.attendance import get_current_user

router = APIRouter()
HR_ROLES = {"HR", "HR_ADMIN", "ADMIN", "MANAGEMENT", "DEVELOPER"}


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def require_hr(user: User = Depends(get_current_user)) -> User:
    if (user.role or "").upper() not in HR_ROLES:
        raise HTTPException(status_code=403, detail="HR access is required to manage training.")
    return user


class CourseCreate(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    description: str = Field(min_length=1, max_length=5000)
    is_mandatory: str = Field(pattern=r"^(YES|NO)$")


class SessionCreate(BaseModel):
    course_id: Optional[UUID] = None
    course_title: Optional[str] = Field(default=None, min_length=1, max_length=200)
    course_description: Optional[str] = Field(default=None, min_length=1, max_length=5000)
    course_is_mandatory: Literal["YES", "NO"] = "NO"
    target_audience: Literal["Whole Company", "Specific Department", "HODs Only", "Specific Individuals"]
    trainer: str = Field(min_length=1, max_length=200)
    venue_link: str = Field(min_length=1, max_length=500)
    scheduled_date: date


class EnrollEmployees(BaseModel):
    employee_ids: list[UUID] = Field(min_length=1)


def course_payload(course: TrainingCourse) -> dict:
    return {
        "id": str(course.id),
        "title": course.title,
        "description": course.description,
        "is_mandatory": course.is_mandatory,
    }


def session_payload(session: TrainingSession) -> dict:
    return {
        "id": str(session.id),
        "course_id": str(session.course_id),
        "course_title": session.course.title,
        "date": session.scheduled_date.isoformat(),
        "scheduled_date": session.scheduled_date.isoformat(),
        "trainer": session.trainer,
        "audience": session.target_audience,
        "target_audience": session.target_audience,
        "venue_link": session.venue_link,
        "enrollment_count": len(session.enrollments),
    }


@router.get("/mine")
def get_my_training(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    if not user.employee_id:
        raise HTTPException(status_code=403, detail="Your account is not linked to an employee record.")
    rows = (
        db.query(TrainingEnrollment)
        .join(TrainingSession)
        .options(joinedload(TrainingEnrollment.session).joinedload(TrainingSession.course))
        .filter(TrainingEnrollment.employee_id == user.employee_id)
        .order_by(TrainingSession.scheduled_date.desc())
        .all()
    )
    return [
        {
            **session_payload(row.session),
            "status": row.status,
            "enrolled_at": row.enrolled_at,
            "completed_at": row.completed_at,
        }
        for row in rows
    ]


@router.post("/sessions/{session_id}/complete")
def complete_my_training(
    session_id: UUID,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    if not user.employee_id:
        raise HTTPException(status_code=403, detail="Your account is not linked to an employee record.")
    enrollment = db.query(TrainingEnrollment).filter(
        TrainingEnrollment.session_id == session_id,
        TrainingEnrollment.employee_id == user.employee_id,
    ).first()
    if enrollment is None:
        raise HTTPException(status_code=404, detail="This training is not assigned to your account.")
    if enrollment.status != "COMPLETED":
        enrollment.status = "COMPLETED"
        enrollment.completed_at = datetime.now(timezone.utc)
        db.commit()
        db.refresh(enrollment)
    return {"session_id": str(session_id), "status": enrollment.status, "completed_at": enrollment.completed_at}


@router.get("/courses")
def get_courses(db: Session = Depends(get_db), _user: User = Depends(require_hr)):
    return [course_payload(course) for course in db.query(TrainingCourse).filter(TrainingCourse.is_active.is_(True)).order_by(TrainingCourse.title).all()]


@router.post("/courses")
def create_course(request: CourseCreate, db: Session = Depends(get_db), _user: User = Depends(require_hr)):
    course = TrainingCourse(
        title=request.title.strip(),
        description=request.description.strip(),
        is_mandatory=request.is_mandatory,
    )
    db.add(course)
    db.commit()
    db.refresh(course)
    return course_payload(course)


@router.get("/sessions")
def get_sessions(db: Session = Depends(get_db), _user: User = Depends(require_hr)):
    rows = (
        db.query(TrainingSession)
        .options(joinedload(TrainingSession.course), joinedload(TrainingSession.enrollments))
        .order_by(TrainingSession.scheduled_date.desc())
        .all()
    )
    return [session_payload(row) for row in rows]


@router.post("/sessions")
def create_session(
    request: SessionCreate,
    db: Session = Depends(get_db),
    user: User = Depends(require_hr),
):
    if request.course_id is None:
        title = (request.course_title or "").strip()
        description = (request.course_description or "").strip()
        if not title or not description:
            raise HTTPException(status_code=422, detail="Enter a course title and description, or select a catalog course.")
        course = TrainingCourse(
            title=title,
            description=description,
            is_mandatory=request.course_is_mandatory,
        )
        db.add(course)
        db.flush()
    else:
        if request.course_title is not None or request.course_description is not None:
            raise HTTPException(status_code=422, detail="Select a catalog course or enter a new course, not both.")
        course = db.query(TrainingCourse).filter(
            TrainingCourse.id == request.course_id,
            TrainingCourse.is_active.is_(True),
        ).first()
        if course is None:
            raise HTTPException(status_code=404, detail="Training course not found.")
    session = TrainingSession(
        course_id=course.id,
        target_audience=request.target_audience.strip(),
        trainer=request.trainer.strip(),
        venue_link=request.venue_link.strip(),
        scheduled_date=request.scheduled_date,
        created_by_user_id=user.id,
    )
    db.add(session)
    db.flush()

    audience = session.target_audience.casefold()
    if audience == "whole company":
        employees = db.query(Employee).filter(Employee.status == "ACTIVE").all()
        for employee in employees:
            db.add(TrainingEnrollment(
                session_id=session.id,
                employee_id=employee.id,
                assigned_by_user_id=user.id,
                enrolled_at=datetime.now(timezone.utc),
            ))
    elif audience == "hods only":
        hods = db.query(User).filter(User.role == "HOD", User.is_active.is_(True), User.employee_id.isnot(None)).all()
        for hod in hods:
            db.add(TrainingEnrollment(
                session_id=session.id,
                employee_id=hod.employee_id,
                assigned_by_user_id=user.id,
                enrolled_at=datetime.now(timezone.utc),
            ))
    db.commit()
    return {"id": str(session.id), "message": "Training session scheduled."}


@router.post("/sessions/{session_id}/enroll")
def enroll_employees(
    session_id: UUID,
    request: EnrollEmployees,
    db: Session = Depends(get_db),
    user: User = Depends(require_hr),
):
    session = db.query(TrainingSession).filter(TrainingSession.id == session_id).first()
    if session is None:
        raise HTTPException(status_code=404, detail="Training session not found.")
    employees = db.query(Employee).filter(
        Employee.id.in_(set(request.employee_ids)),
        Employee.status == "ACTIVE",
    ).all()
    if len({employee.id for employee in employees}) != len(set(request.employee_ids)):
        raise HTTPException(status_code=422, detail="One or more selected employees are missing or inactive.")
    existing_ids = {
        row[0] for row in db.query(TrainingEnrollment.employee_id).filter(
            TrainingEnrollment.session_id == session.id,
            TrainingEnrollment.employee_id.in_(set(request.employee_ids)),
        ).all()
    }
    new_enrollments = [
        TrainingEnrollment(
            session_id=session.id,
            employee_id=employee.id,
            assigned_by_user_id=user.id,
            enrolled_at=datetime.now(timezone.utc),
        )
        for employee in employees if employee.id not in existing_ids
    ]
    db.add_all(new_enrollments)
    db.commit()
    return {"message": f"{len(new_enrollments)} employee(s) enrolled.", "enrolled_count": len(new_enrollments)}
