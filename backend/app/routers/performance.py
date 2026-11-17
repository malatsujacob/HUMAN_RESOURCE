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
from app.models.performance_nomination import MonthlyNomination, QuarterlyResult
from app.models.department import Department

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
    department_name = employee.department.name if employee.department else "Unassigned"
    hr_users = db.query(User).filter(
        User.role.in_(HR_ROLES), User.is_active.is_(True), User.id != user.id,
    ).all()
    for hr_user in hr_users:
        db.add(Notification(
            recipient_user_id=hr_user.id,
            type="PERFORMANCE_SELF_SUBMITTED",
            title="Employee submitted a performance self-rating",
            message=f"{employee.first_name} {employee.last_name} submitted a self-rating for {period} ({department_name}).",
            details={
                "event": "Employee self-assessment submitted",
                "employee_id": str(employee.id),
                "employee_name": f"{employee.first_name} {employee.last_name}",
                "department": department_name,
                "review_period": period,
                "self_rating": review.self_rating,
                "self_comment": review.self_comment,
            },
            is_read=False,
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
    employee = review.employee
    department_name = employee.department.name if employee.department else "Unassigned"
    hr_users = db.query(User).filter(
        User.role.in_(HR_ROLES), User.is_active.is_(True), User.id != user.id,
    ).all()
    for hr_user in hr_users:
        db.add(Notification(
            recipient_user_id=hr_user.id,
            type="PERFORMANCE_HOD_RATED",
            title="HOD completed an employee performance rating",
            message=f"{employee.first_name} {employee.last_name} received a HOD rating for {review.review_period} ({department_name}).",
            details={
                "event": "HOD monthly review completed",
                "employee_id": str(employee.id),
                "employee_name": f"{employee.first_name} {employee.last_name}",
                "department": department_name,
                "review_period": review.review_period,
                "self_rating": review.self_rating,
                "hod_rating": review.hod_rating,
                "behavior_rating": review.behavior_rating,
                "hod_comments": review.hod_comments,
                "rated_at": review.rated_at.isoformat(),
            },
            is_read=False,
        ))
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


# ===========================================================================
# MONTHLY NOMINATIONS + QUARTERLY WEIGHTED RESULTS
# ===========================================================================

class MonthlyNominationIn(BaseModel):
    review_period: str = Field(pattern=r"^\d{4}-(0[1-9]|1[0-2])$")
    nominee_employee_id: UUID
    weight: float = Field(gt=0, le=100)
    notes: Optional[str] = Field(default=None, max_length=1000)


def _quarter_to_months(quarter: str) -> list[str]:
    year, qtr = int(quarter[:4]), int(quarter[-1])
    first = (qtr - 1) * 3 + 1
    return [f"{year}-{first + i:02d}" for i in range(3)]


def _hod_department(user: User, db: Session) -> Department:
    employee = current_employee(user)
    if not employee.department_id:
        raise HTTPException(status_code=403, detail="HOD is not assigned to a department.")
    dept = db.query(Department).filter(Department.id == employee.department_id).first()
    if not dept:
        raise HTTPException(status_code=404, detail="Department not found.")
    return dept


def _nomination_payload(row: MonthlyNomination) -> dict:
    return {
        "id": str(row.id),
        "department_id": str(row.department_id),
        "review_period": row.review_period,
        "nominee_employee_id": str(row.nominee_employee_id),
        "nominee_name": f"{row.nominee.first_name} {row.nominee.last_name}" if row.nominee else None,
        "weight": float(row.weight),
        "monthly_score": float(row.monthly_score),
        "notes": row.notes,
        "created_at": row.created_at.isoformat() if row.created_at else None,
    }


@router.post("/monthly-nomination")
def create_monthly_nomination(
    payload: MonthlyNominationIn,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    role = (user.role or "").upper()
    if role != "HOD":
        raise HTTPException(status_code=403, detail="Only HODs can nominate a monthly best performer.")
    hod_emp = current_employee(user)
    dept = _hod_department(user, db)

    nominee = db.query(Employee).filter(
        Employee.id == payload.nominee_employee_id,
        Employee.department_id == dept.id,
    ).first()
    if not nominee:
        raise HTTPException(status_code=404, detail="Nominee not found in your department.")

    review = db.query(PerformanceReview).filter(
        PerformanceReview.employee_id == nominee.id,
        PerformanceReview.review_period == payload.review_period,
        PerformanceReview.hod_rating.isnot(None),
    ).first()
    if not review:
        raise HTTPException(
            status_code=409,
            detail="Nominee must have a completed HOD review for this month before being nominated.",
        )

    monthly_score = float(review.hod_rating)

    existing = db.query(MonthlyNomination).filter(
        MonthlyNomination.department_id == dept.id,
        MonthlyNomination.review_period == payload.review_period,
    ).first()

    if existing:
        existing.nominee_employee_id = nominee.id
        existing.weight = payload.weight
        existing.monthly_score = monthly_score
        existing.notes = payload.notes
        existing.nominated_by_employee_id = hod_emp.id
        db.commit()
        db.refresh(existing)
        return _nomination_payload(existing)

    row = MonthlyNomination(
        department_id=dept.id,
        review_period=payload.review_period,
        nominee_employee_id=nominee.id,
        weight=payload.weight,
        monthly_score=monthly_score,
        nominated_by_employee_id=hod_emp.id,
        notes=payload.notes,
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return _nomination_payload(row)


@router.get("/monthly-nominations")
def list_monthly_nominations(
    quarter: str = Query(pattern=r"^\d{4}-Q[1-4]$"),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    role = (user.role or "").upper()
    months = _quarter_to_months(quarter)
    query = db.query(MonthlyNomination).filter(MonthlyNomination.review_period.in_(months))
    if role == "HOD":
        dept = _hod_department(user, db)
        query = query.filter(MonthlyNomination.department_id == dept.id)
    elif role in HR_ROLES:
        pass
    else:
        raise HTTPException(status_code=403, detail="HOD or HR access required.")
    rows = query.order_by(MonthlyNomination.review_period.asc()).all()
    return {"quarter": quarter, "nominations": [_nomination_payload(r) for r in rows]}


@router.get("/quarterly-weighted")
def quarterly_weighted(
    quarter: str = Query(pattern=r"^\d{4}-Q[1-4]$"),
    department_id: Optional[UUID] = None,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    role = (user.role or "").upper()
    months = _quarter_to_months(quarter)
    query = db.query(MonthlyNomination).filter(MonthlyNomination.review_period.in_(months))
    if role == "HOD":
        dept = _hod_department(user, db)
        query = query.filter(MonthlyNomination.department_id == dept.id)
    elif role in HR_ROLES:
        if department_id:
            query = query.filter(MonthlyNomination.department_id == department_id)
    else:
        raise HTTPException(status_code=403, detail="HOD or HR access required.")

    rows = query.all()
    totals: dict = {}
    for row in rows:
        key = (str(row.department_id), str(row.nominee_employee_id))
        entry = totals.setdefault(key, {
            "department_id": str(row.department_id),
            "department_name": row.nominee.department.name if row.nominee and row.nominee.department else None,
            "employee_id": str(row.nominee_employee_id),
            "employee_name": f"{row.nominee.first_name} {row.nominee.last_name}",
            "weighted_total": 0.0,
            "total_weight": 0.0,
            "months": [],
        })
        weighted = float(row.monthly_score) * (float(row.weight) / 100.0)
        entry["weighted_total"] += weighted
        entry["total_weight"] += float(row.weight)
        entry["months"].append({
            "review_period": row.review_period,
            "monthly_score": float(row.monthly_score),
            "weight": float(row.weight),
            "weighted_contribution": round(weighted, 2),
        })

    ranked = sorted(totals.values(), key=lambda r: r["weighted_total"], reverse=True)
    for idx, row in enumerate(ranked, 1):
        row["rank"] = idx
        row["weighted_total"] = round(row["weighted_total"], 2)
    return {"quarter": quarter, "ranking": ranked}


@router.post("/quarterly-submit")
def submit_quarterly_result(
    quarter: str = Query(pattern=r"^\d{4}-Q[1-4]$"),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    role = (user.role or "").upper()
    if role != "HOD":
        raise HTTPException(status_code=403, detail="Only HODs can submit a quarterly best performer.")
    dept = _hod_department(user, db)
    hod_emp = current_employee(user)

    months = _quarter_to_months(quarter)
    nominations = db.query(MonthlyNomination).filter(
        MonthlyNomination.department_id == dept.id,
        MonthlyNomination.review_period.in_(months),
    ).all()
    if not nominations:
        raise HTTPException(status_code=409, detail="Nominate at least one monthly performer first.")

    total_weight = sum(float(n.weight) for n in nominations)
    if abs(total_weight - 100.0) > 0.5:
        raise HTTPException(
            status_code=422,
            detail=f"Monthly weights must total 100%. Currently {total_weight:.2f}%.",
        )

    totals: dict = {}
    for n in nominations:
        key = str(n.nominee_employee_id)
        entry = totals.setdefault(key, {"score": 0.0, "name": f"{n.nominee.first_name} {n.nominee.last_name}"})
        entry["score"] += float(n.monthly_score) * (float(n.weight) / 100.0)

    winner_id, winner = max(totals.items(), key=lambda kv: kv[1]["score"])

    existing = db.query(QuarterlyResult).filter(
        QuarterlyResult.department_id == dept.id,
        QuarterlyResult.quarter == quarter,
    ).first()
    if existing:
        existing.best_performer_employee_id = winner_id
        existing.weighted_score = winner["score"]
        existing.total_weight = total_weight
        existing.submitted_by_employee_id = hod_emp.id
    else:
        db.add(QuarterlyResult(
            department_id=dept.id,
            quarter=quarter,
            best_performer_employee_id=winner_id,
            weighted_score=winner["score"],
            total_weight=total_weight,
            submitted_by_employee_id=hod_emp.id,
        ))
    db.commit()
    return {
        "quarter": quarter,
        "department_id": str(dept.id),
        "department_name": dept.name,
        "best_performer_employee_id": winner_id,
        "best_performer_name": winner["name"],
        "weighted_score": round(winner["score"], 2),
        "total_weight": round(total_weight, 2),
    }


@router.get("/quarterly-results")
def list_quarterly_results(
    quarter: str = Query(pattern=r"^\d{4}-Q[1-4]$"),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    role = (user.role or "").upper()
    if role not in HR_ROLES | {"HOD"}:
        raise HTTPException(status_code=403, detail="HOD or HR access required.")
    query = db.query(QuarterlyResult).filter(QuarterlyResult.quarter == quarter)
    if role == "HOD":
        dept = _hod_department(user, db)
        query = query.filter(QuarterlyResult.department_id == dept.id)
    rows = query.order_by(QuarterlyResult.submitted_at.desc()).all()
    return {
        "quarter": quarter,
        "results": [
            {
                "department_id": str(r.department_id),
                "department_name": r.best_performer.department.name if r.best_performer and r.best_performer.department else None,
                "best_performer_employee_id": str(r.best_performer_employee_id),
                "best_performer_name": f"{r.best_performer.first_name} {r.best_performer.last_name}" if r.best_performer else None,
                "weighted_score": float(r.weighted_score),
                "total_weight": float(r.total_weight),
                "submitted_at": r.submitted_at.isoformat() if r.submitted_at else None,
            }
            for r in rows
        ],
    }
