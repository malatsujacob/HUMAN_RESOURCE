from datetime import datetime, timezone
from decimal import Decimal, ROUND_HALF_UP
from typing import Literal, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session, joinedload

from app.routers.attendance import get_current_user, get_db
from app.models.employee import Employee
from app.models.notification import Notification
from app.models.performance import PerformanceReview
from app.models.user import User

router = APIRouter()
HR_ROLES = {"HR", "HR_ADMIN", "ADMIN", "MANAGEMENT", "DEVELOPER"}
PUNCTUALITY_SCORES = {"EARLY": 5, "ON_TIME": 4, "OCCASIONALLY_LATE": 3, "FREQUENTLY_LATE": 1}
TASK_SCORES = {"AHEAD_OF_DEADLINE": 5, "ON_TIME": 4, "DELAYED": 2, "INCOMPLETE": 1}
EFFICIENCY_SCORES = {"HIGHLY_EFFICIENT": 5, "EFFICIENT": 4, "NEEDS_SUPPORT": 3, "SLOW": 2}
QUALITY_SCORES = {"EXCEEDS_EXPECTATIONS": 5, "MEETS_EXPECTATIONS": 4, "NEEDS_IMPROVEMENT": 2, "UNSATISFACTORY": 1}
TEAMWORK_SCORES = {"EXCELLENT": 5, "GOOD": 4, "DEVELOPING": 3, "UNSATISFACTORY": 1}


class SelfReviewSubmission(BaseModel):
    review_period: str = Field(pattern=r"^\d{4}-(0[1-9]|1[0-2])$")
    self_rating: int = Field(ge=1, le=5)
    self_comment: Optional[str] = Field(default=None, max_length=1000)


class HODReviewSubmission(BaseModel):
    punctuality: Literal["EARLY", "ON_TIME", "OCCASIONALLY_LATE", "FREQUENTLY_LATE"]
    overtime_worked: bool = False
    task_completion: Literal["AHEAD_OF_DEADLINE", "ON_TIME", "DELAYED", "INCOMPLETE"]
    efficiency: Literal["HIGHLY_EFFICIENT", "EFFICIENT", "NEEDS_SUPPORT", "SLOW"]
    quality_of_work: Literal["EXCEEDS_EXPECTATIONS", "MEETS_EXPECTATIONS", "NEEDS_IMPROVEMENT", "UNSATISFACTORY"]
    teamwork: Literal["EXCELLENT", "GOOD", "DEVELOPING", "UNSATISFACTORY"]
    hod_rating: int = Field(ge=1, le=5)
    hod_comments: str = Field(min_length=1, max_length=1000)


def current_employee(user: User) -> Employee:
    if user.employee is None:
        raise HTTPException(status_code=403, detail="Your account is not linked to an employee record.")
    return user.employee


def review_query(db: Session):
    return db.query(PerformanceReview).options(
        joinedload(PerformanceReview.employee).joinedload(Employee.department)
    )


def review_payload(review: PerformanceReview) -> dict:
    employee = review.employee
    return {
        "id": str(review.id), "employee_id": str(review.employee_id),
        "employee_name": f"{employee.first_name} {employee.last_name}" if employee else "Employee",
        "department_name": employee.department.name if employee and employee.department else None,
        "review_period": review.review_period, "self_rating": review.self_rating,
        "self_comment": review.self_comment, "punctuality": review.punctuality,
        "overtime_worked": review.overtime_worked, "task_completion": review.task_completion,
        "efficiency": review.efficiency, "quality_of_work": review.quality_of_work,
        "teamwork": review.teamwork, "behavior_rating": review.behavior_rating,
        "hod_rating": review.hod_rating, "hod_comments": review.hod_comments,
        "submitted_at": review.submitted_at, "rated_at": review.rated_at,
    }


def behavior_score(request: HODReviewSubmission) -> int:
    scores = [PUNCTUALITY_SCORES[request.punctuality], TASK_SCORES[request.task_completion],
              EFFICIENCY_SCORES[request.efficiency], QUALITY_SCORES[request.quality_of_work],
              TEAMWORK_SCORES[request.teamwork]]
    return int((Decimal(sum(scores)) / Decimal(len(scores))).quantize(Decimal("1"), rounding=ROUND_HALF_UP))


@router.post("/self")
def submit_self_review(request: SelfReviewSubmission, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    employee = current_employee(user)
    period = request.review_period.strip()
    review = db.query(PerformanceReview).filter(
        PerformanceReview.employee_id == employee.id,
        PerformanceReview.review_period == period,
    ).with_for_update().first()
    if review is None:
        review = PerformanceReview(employee_id=employee.id, review_period=period)
        db.add(review)
        db.flush()
    elif review.self_rating is not None:
        raise HTTPException(status_code=409, detail="Your self assessment for this month has already been submitted.")

    review.self_rating = request.self_rating
    review.self_comment = request.self_comment.strip() if request.self_comment else None
    review.submitted_at = datetime.now(timezone.utc)
    hod_users = db.query(User).join(Employee, User.employee_id == Employee.id).filter(
        User.role == "HOD", Employee.department_id == employee.department_id,
        Employee.id != employee.id, User.is_active.is_(True),
    ).all()
    for hod_user in hod_users:
        db.add(Notification(
            recipient_employee_id=hod_user.employee_id,
            type="PERFORMANCE_SELF_SUBMITTED",
            title="Monthly self assessment submitted",
            message=f"{employee.first_name} {employee.last_name} submitted a self assessment for {period}.",
        ))
    try:
        db.commit()
    except SQLAlchemyError:
        db.rollback()
        raise
    db.refresh(review)
    return review_payload(review)


@router.post("/{review_id}/hod-review")
def submit_hod_review(review_id: UUID, request: HODReviewSubmission,
                      db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    role = (user.role or "").upper()
    if role not in HR_ROLES | {"HOD"}:
        raise HTTPException(status_code=403, detail="HOD or HR access is required to complete a performance review.")
    review = db.query(PerformanceReview).filter(PerformanceReview.id == review_id).with_for_update().first()
    if not review:
        raise HTTPException(status_code=404, detail="Performance review not found.")
    if review.self_rating is None:
        raise HTTPException(status_code=409, detail="The employee must submit their self assessment first.")
    if review.hod_rating is not None:
        raise HTTPException(status_code=409, detail="This monthly review has already been completed.")
    if not request.hod_comments.strip():
        raise HTTPException(status_code=422, detail="Add a comment before completing the review.")
    if role == "HOD":
        manager = current_employee(user)
        if not manager.department_id or review.employee.department_id != manager.department_id:
            raise HTTPException(status_code=403, detail="HODs can review only employees in their department.")
    review.punctuality = request.punctuality
    review.overtime_worked = request.overtime_worked
    review.task_completion = request.task_completion
    review.efficiency = request.efficiency
    review.quality_of_work = request.quality_of_work
    review.teamwork = request.teamwork
    review.behavior_rating = behavior_score(request)
    review.hod_rating = request.hod_rating
    review.hod_comments = request.hod_comments.strip()
    review.rated_at = datetime.now(timezone.utc)
    try:
        db.commit()
    except SQLAlchemyError:
        db.rollback()
        raise
    db.refresh(review)
    return review_payload(review)


@router.get("/mine")
def list_my_reviews(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    employee = current_employee(user)
    query = review_query(db).filter(PerformanceReview.employee_id == employee.id)
    return [review_payload(item) for item in query.order_by(PerformanceReview.review_period.desc()).all()]


@router.get("/pending")
def list_pending_reviews(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    role = (user.role or "").upper()
    query = review_query(db).filter(PerformanceReview.self_rating.isnot(None), PerformanceReview.hod_rating.is_(None))
    if role == "HOD":
        manager = current_employee(user)
        if manager.department_id is None:
            raise HTTPException(status_code=403, detail="HOD is not assigned to a department.")
        query = query.join(Employee, PerformanceReview.employee_id == Employee.id).filter(Employee.department_id == manager.department_id)
    elif role not in HR_ROLES:
        raise HTTPException(status_code=403, detail="HOD or HR access is required.")
    return [review_payload(item) for item in query.order_by(PerformanceReview.submitted_at.asc()).all()]


@router.get("/notifications")
def list_performance_notifications(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    role = (user.role or "").upper()
    query = db.query(Notification).filter(Notification.type == "PERFORMANCE_SELF_SUBMITTED")
    if role == "HOD":
        query = query.filter(Notification.recipient_employee_id == current_employee(user).id)
    elif role not in HR_ROLES:
        raise HTTPException(status_code=403, detail="HOD or HR access is required.")
    return [{"id": str(item.id), "title": item.title, "message": item.message,
             "is_read": item.is_read, "created_at": item.created_at}
            for item in query.order_by(Notification.created_at.desc()).limit(50).all()]


@router.post("/notifications/{notification_id}/read")
def mark_notification_read(notification_id: UUID, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    role = (user.role or "").upper()
    if role not in HR_ROLES | {"HOD"}:
        raise HTTPException(status_code=403, detail="HOD or HR access is required.")
    notification = db.query(Notification).filter(
        Notification.id == notification_id, Notification.type == "PERFORMANCE_SELF_SUBMITTED"
    ).first()
    if not notification:
        raise HTTPException(status_code=404, detail="Notification not found.")
    if role == "HOD" and notification.recipient_employee_id != user.employee_id:
        raise HTTPException(status_code=403, detail="You cannot update another HOD's notification.")
    notification.is_read = True
    db.commit()
    return {"message": "Notification marked as read."}


@router.get("/quarterly-ranking")
def quarterly_ranking(quarter: str = Query(pattern=r"^\d{4}-Q[1-4]$"),
                     db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    year, qtr = int(quarter[:4]), int(quarter[-1])
    first_month = (qtr - 1) * 3 + 1
    start, end = f"{year}-{first_month:02d}", f"{year}-{first_month + 2:02d}"
    role = (user.role or "").upper()
    query = review_query(db).filter(PerformanceReview.review_period >= start,
                                    PerformanceReview.review_period <= end,
                                    PerformanceReview.hod_rating.isnot(None))
    if role == "HOD":
        manager = current_employee(user)
        query = query.join(Employee, PerformanceReview.employee_id == Employee.id).filter(Employee.department_id == manager.department_id)
    elif role == "EMPLOYEE":
        query = query.filter(PerformanceReview.employee_id == current_employee(user).id)
    elif role not in HR_ROLES:
        raise HTTPException(status_code=403, detail="Role is not allowed to view quarterly performance.")
    totals = {}
    for review in query.all():
        entry = totals.setdefault(review.employee_id, {
            "employee_id": str(review.employee_id),
            "employee_name": f"{review.employee.first_name} {review.employee.last_name}",
            "department_name": review.employee.department.name if review.employee.department else None,
            "total": 0, "months_completed": 0,
        })
        entry["total"] += review.hod_rating
        entry["months_completed"] += 1
    ranking = sorted(totals.values(), key=lambda row: (row["total"] / row["months_completed"], row["months_completed"]), reverse=True)
    for rank, row in enumerate(ranking, 1):
        row["rank"] = rank
        row["quarter_rating"] = float((Decimal(row["total"]) / Decimal(row["months_completed"])).quantize(Decimal("0.01")))
        del row["total"]
    return {"quarter": quarter, "ranking": ranking}


@router.get("/")
def list_reviews(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    role = (user.role or "").upper()
    query = review_query(db)
    if role == "EMPLOYEE":
        query = query.filter(PerformanceReview.employee_id == current_employee(user).id)
    elif role == "HOD":
        manager = current_employee(user)
        if manager.department_id is None:
            raise HTTPException(status_code=403, detail="HOD is not assigned to a department.")
        query = query.join(Employee, PerformanceReview.employee_id == Employee.id).filter(Employee.department_id == manager.department_id)
    elif role not in HR_ROLES:
        raise HTTPException(status_code=403, detail="Role is not allowed to view performance reviews.")
    return [review_payload(item) for item in query.order_by(PerformanceReview.review_period.desc()).all()]
