from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.api.attendance import get_current_user, get_db
from app.models.employee import Employee
from app.models.performance import PerformanceReview
from app.models.user import User

router = APIRouter()
HR_ROLES = {"HR", "HR_ADMIN", "MANAGEMENT"}


class ReviewSubmission(BaseModel):
    review_period: str = Field(min_length=1, max_length=50, pattern=r".*\S.*")
    employee_id: Optional[UUID] = None
    self_rating: Optional[int] = Field(default=None, ge=1, le=5)
    hod_rating: Optional[int] = Field(default=None, ge=1, le=5)
    hod_comments: Optional[str] = Field(default=None, max_length=500)


class ReviewResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    employee_id: UUID
    review_period: str
    self_rating: Optional[int]
    hod_rating: Optional[int]
    hod_comments: Optional[str]


def current_employee(user: User) -> Employee:
    if user.employee is None:
        raise HTTPException(status_code=403, detail="User is not linked to an employee record")
    return user.employee


@router.post("/", response_model=ReviewResponse, status_code=201)
def submit_review(
    request: ReviewSubmission,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    role = user.role.upper()
    if role == "EMPLOYEE":
        employee = current_employee(user)
        if request.employee_id is not None and request.employee_id != employee.id:
            raise HTTPException(status_code=403, detail="Employees can only submit their own review")
        if request.self_rating is None or request.hod_rating is not None or request.hod_comments is not None:
            raise HTTPException(status_code=422, detail="Employees must submit only a self rating")
        target_employee_id = employee.id
    elif role == "HOD":
        manager = current_employee(user)
        if manager.department_id is None:
            raise HTTPException(status_code=403, detail="HOD is not assigned to a department")
        if request.employee_id is None or request.hod_rating is None or request.self_rating is not None:
            raise HTTPException(status_code=422, detail="HODs must provide an employee and HOD rating")
        target = db.query(Employee).filter(Employee.id == request.employee_id).first()
        if target is None:
            raise HTTPException(status_code=404, detail="Employee not found")
        if target.department_id != manager.department_id:
            raise HTTPException(status_code=403, detail="HODs can only review employees in their department")
        target_employee_id = target.id
    else:
        raise HTTPException(status_code=403, detail="Role is not allowed to submit performance reviews")

    review = (
        db.query(PerformanceReview)
        .filter(
            PerformanceReview.employee_id == target_employee_id,
            PerformanceReview.review_period == request.review_period.strip(),
        )
        .with_for_update()
        .first()
    )
    if review is None:
        review = PerformanceReview(
            employee_id=target_employee_id,
            review_period=request.review_period.strip(),
        )
        db.add(review)

    if role == "EMPLOYEE":
        if review.self_rating is not None:
            raise HTTPException(status_code=409, detail="Self rating already submitted for this period")
        review.self_rating = request.self_rating
    else:
        review.hod_rating = request.hod_rating
        review.hod_comments = request.hod_comments.strip() if request.hod_comments else None

    try:
        db.commit()
    except SQLAlchemyError:
        db.rollback()
        raise
    db.refresh(review)
    return review


@router.get("/", response_model=list[ReviewResponse])
def list_reviews(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    role = user.role.upper()
    query = db.query(PerformanceReview)

    if role == "EMPLOYEE":
        query = query.filter(PerformanceReview.employee_id == current_employee(user).id)
    elif role == "HOD":
        manager = current_employee(user)
        if manager.department_id is None:
            raise HTTPException(status_code=403, detail="HOD is not assigned to a department")
        query = query.join(Employee).filter(Employee.department_id == manager.department_id)
    elif role not in HR_ROLES:
        raise HTTPException(status_code=403, detail="Role is not allowed to view performance reviews")

    return query.order_by(PerformanceReview.review_period.desc()).all()
