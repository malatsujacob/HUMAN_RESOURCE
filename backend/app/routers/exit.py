from datetime import date, datetime, timezone
from typing import Literal, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.routers.attendance import get_current_user, get_db
from app.models.contract import Contract
from app.models.employee import Employee
from app.models.exit import EmployeeExit, ExitClearanceItem, ExitInterview, ExitFinalPay
from app.models.user import User

router = APIRouter()
HR_ROLES = {"HR", "HR_ADMIN", "ADMIN", "MANAGEMENT", "DEVELOPER"}


class ExitCreate(BaseModel):
    employee_id: UUID
    last_working_day: date
    reason: str = Field(min_length=1, max_length=500)

class ClearanceReview(BaseModel):
    clearance_status: Literal["IN_PROGRESS", "CLEARED", "BLOCKED"]
    note: str = Field(min_length=5, max_length=1000)


class ExitResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    employee_id: UUID
    last_working_day: date
    reason: str
    clearance_status: str
    clearance_note: Optional[str] = None
    clearance_reviewed_by: Optional[UUID] = None
    clearance_reviewed_at: Optional[datetime] = None


def require_hr(user: User) -> None:
    if user.role.upper() not in HR_ROLES:
        raise HTTPException(status_code=403, detail="Only HR can manage employee exits")


@router.post("/", response_model=ExitResponse, status_code=201)
def initiate_exit(
    request: ExitCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    require_hr(user)
    employee = db.query(Employee).filter(Employee.id == request.employee_id).first()
    if employee is None:
        raise HTTPException(status_code=404, detail="Employee not found")
    existing_exit = db.query(EmployeeExit.id).filter(
        EmployeeExit.employee_id == employee.id,
        EmployeeExit.clearance_status != "CLEARED",
    ).first()
    if existing_exit:
        raise HTTPException(status_code=409, detail="An exit process is already in progress for this employee.")

    contracts = (
        db.query(Contract)
        .filter(
            Contract.employee_id == employee.id,
            Contract.status.in_(("SIGNED", "ACTIVE")),
        )
        .with_for_update()
        .all()
    )
    if any(contract.start_date and request.last_working_day < contract.start_date for contract in contracts):
        raise HTTPException(
            status_code=422,
            detail="The last working day cannot be before an active contract's start date.",
        )

    employee_exit = EmployeeExit(
        employee_id=employee.id,
        last_working_day=request.last_working_day,
        reason=request.reason.strip(),
        clearance_status="PENDING",
    )
    if not employee_exit.reason:
        raise HTTPException(status_code=422, detail="Reason cannot be blank")
    for contract in contracts:
        if contract.end_date is None or request.last_working_day < contract.end_date:
            contract.end_date = request.last_working_day
        contract.status = "TERMINATED"
    db.add(employee_exit)
    db.flush()

    # Auto-create 5 clearance items
    for code, name in DEFAULT_CLEARANCE_ITEMS:
        db.add(ExitClearanceItem(
            exit_id=employee_exit.id,
            item_code=code,
            item_name=name,
            status="PENDING",
        ))

    try:
        db.commit()
    except SQLAlchemyError:
        db.rollback()
        raise
    db.refresh(employee_exit)
    return employee_exit


@router.get("/", response_model=list[ExitResponse])
def list_exits(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    require_hr(user)
    return db.query(EmployeeExit).order_by(EmployeeExit.last_working_day.desc()).all()


@router.put("/{exit_id}/clearance", response_model=ExitResponse)
def review_clearance(
    exit_id: UUID,
    request: ClearanceReview,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    require_hr(user)
    employee_exit = db.query(EmployeeExit).filter(EmployeeExit.id == exit_id).with_for_update().first()
    if employee_exit is None:
        raise HTTPException(status_code=404, detail="Employee exit record not found.")
    if employee_exit.clearance_status == "CLEARED":
        raise HTTPException(status_code=409, detail="This employee's clearance has already been completed.")
    employee_exit.clearance_status = request.clearance_status
    employee_exit.clearance_note = request.note.strip()
    if not employee_exit.clearance_note:
        raise HTTPException(status_code=422, detail="Clearance note cannot be blank.")
    employee_exit.clearance_reviewed_by = user.id
    employee_exit.clearance_reviewed_at = datetime.now(timezone.utc)
    try:
        db.commit()
    except SQLAlchemyError:
        db.rollback()
        raise
    db.refresh(employee_exit)
    return employee_exit


# ===========================================================================
# EXIT CLEARANCE ITEMS (Phase 1c)
# ===========================================================================

DEFAULT_CLEARANCE_ITEMS = [
    ("IT", "IT equipment & access"),
    ("FINANCE", "Finance clearance"),
    ("HR", "HR exit interview"),
    ("DEPT", "Department handover"),
    ("STORE", "Store & assets return"),
]


class ClearanceItemUpdate(BaseModel):
    status: Literal["PENDING", "CLEARED", "BLOCKED"]
    notes: Optional[str] = Field(default=None, max_length=1000)


def clearance_item_payload(item: ExitClearanceItem) -> dict:
    return {
        "id": str(item.id),
        "exit_id": str(item.exit_id),
        "item_code": item.item_code,
        "item_name": item.item_name,
        "status": item.status,
        "cleared_by_user_id": str(item.cleared_by_user_id) if item.cleared_by_user_id else None,
        "cleared_at": item.cleared_at.isoformat() if item.cleared_at else None,
        "notes": item.notes,
        "created_at": item.created_at.isoformat() if item.created_at else None,
    }


@router.get("/{exit_id}/clearance-items")
def list_clearance_items(
    exit_id: UUID,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    require_hr(user)
    exit_record = db.query(EmployeeExit).filter(EmployeeExit.id == exit_id).first()
    if not exit_record:
        raise HTTPException(status_code=404, detail="Exit record not found.")
    items = db.query(ExitClearanceItem).filter(ExitClearanceItem.exit_id == exit_id).order_by(ExitClearanceItem.item_code).all()
    return [clearance_item_payload(i) for i in items]


@router.put("/clearance-items/{item_id}")
def update_clearance_item(
    item_id: UUID,
    request: ClearanceItemUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    require_hr(user)
    item = db.query(ExitClearanceItem).filter(ExitClearanceItem.id == item_id).with_for_update().first()
    if not item:
        raise HTTPException(status_code=404, detail="Clearance item not found.")
    item.status = request.status
    item.notes = request.notes
    if request.status == "CLEARED":
        item.cleared_by_user_id = user.id
        item.cleared_at = datetime.now(timezone.utc)
    else:
        item.cleared_by_user_id = None
        item.cleared_at = None
    db.commit()
    db.refresh(item)

    # Update parent exit's overall status
    siblings = db.query(ExitClearanceItem).filter(ExitClearanceItem.exit_id == item.exit_id).all()
    all_cleared = all(s.status == "CLEARED" for s in siblings)
    any_blocked = any(s.status == "BLOCKED" for s in siblings)
    parent = db.query(EmployeeExit).filter(EmployeeExit.id == item.exit_id).first()
    if parent:
        if all_cleared:
            parent.clearance_status = "CLEARED"
        elif any_blocked:
            parent.clearance_status = "BLOCKED"
        elif any(s.status == "CLEARED" for s in siblings):
            parent.clearance_status = "IN_PROGRESS"
        else:
            parent.clearance_status = "PENDING"
        db.commit()

    return clearance_item_payload(item)


@router.get("/{exit_id}/clearance-progress")
def clearance_progress(
    exit_id: UUID,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    require_hr(user)
    items = db.query(ExitClearanceItem).filter(ExitClearanceItem.exit_id == exit_id).all()
    total = len(items)
    cleared = sum(1 for i in items if i.status == "CLEARED")
    blocked = sum(1 for i in items if i.status == "BLOCKED")
    pending = sum(1 for i in items if i.status == "PENDING")
    return {
        "exit_id": str(exit_id),
        "total": total,
        "cleared": cleared,
        "pending": pending,
        "blocked": blocked,
        "percent": round((cleared / total * 100) if total > 0 else 0, 1),
    }


@router.delete("/clearance-items/{item_id}")
def delete_clearance_item(
    item_id: UUID,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    require_hr(user)
    item = db.query(ExitClearanceItem).filter(ExitClearanceItem.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Clearance item not found.")
    db.delete(item)
    db.commit()
    return {"message": "Clearance item deleted."}


# ===========================================================================
# EXIT PHASE 2 — Detail, Interview, Final Pay
# ===========================================================================

class ExitUpdate(BaseModel):
    exit_type: Optional[str] = None
    resignation_date: Optional[date] = None
    notice_period_days: Optional[int] = None
    notice_served: Optional[bool] = None
    rehire_eligible: Optional[bool] = None
    access_revoked: Optional[bool] = None


class InterviewUpsert(BaseModel):
    conducted_by_user_id: Optional[UUID] = None
    interview_date: Optional[date] = None
    reason_category: Optional[str] = None
    feedback_notes: Optional[str] = None
    would_recommend: Optional[bool] = None
    rehire_eligible: Optional[bool] = None


class FinalPayUpsert(BaseModel):
    basic_salary: float = 0
    leave_payout: float = 0
    gratuity: float = 0
    notice_pay: float = 0
    other_earnings: float = 0
    loan_deduction: float = 0
    advance_deduction: float = 0
    asset_deduction: float = 0
    other_deductions: float = 0
    payment_date: Optional[date] = None
    paid: bool = False
    notes: Optional[str] = None


def exit_full_payload(e: EmployeeExit) -> dict:
    return {
        "id": str(e.id),
        "employee_id": str(e.employee_id),
        "last_working_day": e.last_working_day.isoformat() if e.last_working_day else None,
        "reason": e.reason,
        "exit_type": e.exit_type,
        "resignation_date": e.resignation_date.isoformat() if e.resignation_date else None,
        "notice_period_days": e.notice_period_days,
        "notice_served": e.notice_served,
        "rehire_eligible": e.rehire_eligible,
        "access_revoked": e.access_revoked,
        "access_revoked_at": e.access_revoked_at.isoformat() if e.access_revoked_at else None,
        "clearance_status": e.clearance_status,
        "clearance_note": e.clearance_note,
        "clearance_items": [
            {
                "id": str(i.id),
                "item_code": i.item_code,
                "item_name": i.item_name,
                "status": i.status,
                "cleared_by_user_id": str(i.cleared_by_user_id) if i.cleared_by_user_id else None,
                "cleared_at": i.cleared_at.isoformat() if i.cleared_at else None,
                "notes": i.notes,
            }
            for i in e.clearance_items
        ],
        "interview": (
            {
                "id": str(e.interview.id),
                "conducted_by_user_id": str(e.interview.conducted_by_user_id) if e.interview.conducted_by_user_id else None,
                "interview_date": e.interview.interview_date.isoformat() if e.interview.interview_date else None,
                "reason_category": e.interview.reason_category,
                "feedback_notes": e.interview.feedback_notes,
                "would_recommend": e.interview.would_recommend,
                "rehire_eligible": e.interview.rehire_eligible,
            }
            if e.interview else None
        ),
        "final_pay": (
            {
                "id": str(e.final_pay.id),
                "basic_salary": float(e.final_pay.basic_salary),
                "leave_payout": float(e.final_pay.leave_payout),
                "gratuity": float(e.final_pay.gratuity),
                "notice_pay": float(e.final_pay.notice_pay),
                "other_earnings": float(e.final_pay.other_earnings),
                "loan_deduction": float(e.final_pay.loan_deduction),
                "advance_deduction": float(e.final_pay.advance_deduction),
                "asset_deduction": float(e.final_pay.asset_deduction),
                "other_deductions": float(e.final_pay.other_deductions),
                "net_pay": float(e.final_pay.net_pay),
                "payment_date": e.final_pay.payment_date.isoformat() if e.final_pay.payment_date else None,
                "paid": e.final_pay.paid,
                "notes": e.final_pay.notes,
            }
            if e.final_pay else None
        ),
    }


@router.get("/{exit_id}")
def get_exit_detail(
    exit_id: UUID,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    require_hr(user)
    exit_record = db.query(EmployeeExit).filter(EmployeeExit.id == exit_id).first()
    if not exit_record:
        raise HTTPException(status_code=404, detail="Exit record not found.")
    return exit_full_payload(exit_record)


@router.put("/{exit_id}")
def update_exit(
    exit_id: UUID,
    request: ExitUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    require_hr(user)
    exit_record = db.query(EmployeeExit).filter(EmployeeExit.id == exit_id).first()
    if not exit_record:
        raise HTTPException(status_code=404, detail="Exit record not found.")
    for field, value in request.model_dump(exclude_unset=True).items():
        setattr(exit_record, field, value)
    if request.access_revoked and not exit_record.access_revoked_at:
        exit_record.access_revoked_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(exit_record)
    return exit_full_payload(exit_record)


@router.post("/{exit_id}/interview")
def upsert_interview(
    exit_id: UUID,
    request: InterviewUpsert,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    require_hr(user)
    exit_record = db.query(EmployeeExit).filter(EmployeeExit.id == exit_id).first()
    if not exit_record:
        raise HTTPException(status_code=404, detail="Exit record not found.")
    interview = db.query(ExitInterview).filter(ExitInterview.exit_id == exit_id).first()
    if not interview:
        interview = ExitInterview(exit_id=exit_id)
        db.add(interview)
    for field, value in request.model_dump(exclude_unset=True).items():
        if value is not None:
            setattr(interview, field, value)
    if not interview.conducted_by_user_id:
        interview.conducted_by_user_id = user.id
    db.commit()
    db.refresh(exit_record)
    return exit_full_payload(exit_record)


@router.post("/{exit_id}/final-pay")
def upsert_final_pay(
    exit_id: UUID,
    request: FinalPayUpsert,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    require_hr(user)
    exit_record = db.query(EmployeeExit).filter(EmployeeExit.id == exit_id).first()
    if not exit_record:
        raise HTTPException(status_code=404, detail="Exit record not found.")
    fp = db.query(ExitFinalPay).filter(ExitFinalPay.exit_id == exit_id).first()
    if not fp:
        fp = ExitFinalPay(exit_id=exit_id)
        db.add(fp)
    data = request.model_dump(exclude_unset=True)
    for key in ["basic_salary", "leave_payout", "gratuity", "notice_pay", "other_earnings",
                "loan_deduction", "advance_deduction", "asset_deduction", "other_deductions",
                "payment_date", "paid", "notes"]:
        if key in data:
            setattr(fp, key, data[key])
    fp.net_pay = (
        float(fp.basic_salary) + float(fp.leave_payout) + float(fp.gratuity) +
        float(fp.notice_pay) + float(fp.other_earnings)
        - float(fp.loan_deduction) - float(fp.advance_deduction)
        - float(fp.asset_deduction) - float(fp.other_deductions)
    )
    if not fp.calculated_by_user_id:
        fp.calculated_by_user_id = user.id
    db.commit()
    db.refresh(exit_record)
    return exit_full_payload(exit_record)


@router.post("/{exit_id}/revoke-access")
def revoke_access(
    exit_id: UUID,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    require_hr(user)
    exit_record = db.query(EmployeeExit).filter(EmployeeExit.id == exit_id).first()
    if not exit_record:
        raise HTTPException(status_code=404, detail="Exit record not found.")
    exit_record.access_revoked = True
    exit_record.access_revoked_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(exit_record)
    return exit_full_payload(exit_record)


@router.delete("/{exit_id}/interview")
def delete_interview(
    exit_id: UUID,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    require_hr(user)
    interview = db.query(ExitInterview).filter(ExitInterview.exit_id == exit_id).first()
    if not interview:
        raise HTTPException(status_code=404, detail="Interview not found.")
    db.delete(interview)
    db.commit()
    return {"message": "Interview deleted."}


@router.delete("/{exit_id}/final-pay")
def delete_final_pay(
    exit_id: UUID,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    require_hr(user)
    fp = db.query(ExitFinalPay).filter(ExitFinalPay.exit_id == exit_id).first()
    if not fp:
        raise HTTPException(status_code=404, detail="Final pay not found.")
    db.delete(fp)
    db.commit()
    return {"message": "Final pay deleted."}


@router.get("/{exit_id}/complete-check")
def complete_check(
    exit_id: UUID,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    require_hr(user)
    e = db.query(EmployeeExit).filter(EmployeeExit.id == exit_id).first()
    if not e:
        raise HTTPException(status_code=404, detail="Exit record not found.")
    items_total = len(e.clearance_items)
    items_cleared = sum(1 for i in e.clearance_items if i.status == "CLEARED")
    return {
        "exit_id": str(e.id),
        "clearance_items_done": items_total > 0 and items_cleared == items_total,
        "interview_done": e.interview is not None,
        "final_pay_done": e.final_pay is not None and e.final_pay.paid,
        "access_revoked": e.access_revoked,
        "fully_complete": (
            items_total > 0 and items_cleared == items_total
            and e.interview is not None
            and e.final_pay is not None and e.final_pay.paid
            and e.access_revoked
        ),
    }
