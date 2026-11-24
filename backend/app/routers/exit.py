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
from app.models.exit import EmployeeExit, ExitClearanceItem
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
