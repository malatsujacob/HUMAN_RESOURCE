from datetime import date, datetime, timezone
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session, joinedload

from app.database import SessionLocal
from app.models.employee import Employee
from app.models.leave import LeaveRequest
from app.models.notification import Notification
from app.models.user import User
from app.routers.attendance import get_current_user

router = APIRouter()
HR_ROLES = {"HR", "HR_ADMIN", "ADMIN", "MANAGEMENT", "DEVELOPER"}
HOD_ROLES = {"HOD", "DEVELOPER"}


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


class LeaveCreate(BaseModel):
    leave_type: str = Field(min_length=1, max_length=50)
    start_date: date
    end_date: date
    reason: str = Field(min_length=5, max_length=255)


class LeaveReview(BaseModel):
    note: str = Field(min_length=5, max_length=255)


def employee_name(employee: Employee) -> str:
    return " ".join(part for part in (employee.first_name, employee.middle_name, employee.last_name) if part)


def serialize_leave(item: LeaveRequest) -> dict:
    employee = item.employee
    approver = item.approver
    return {
        "id": str(item.id), "employee_id": str(item.employee_id),
        "employee_name": employee_name(employee) if employee else "Unknown employee",
        "employee_number": employee.employee_number if employee else None,
        "department_id": str(employee.department_id) if employee and employee.department_id else None,
        "department_name": employee.department.name if employee and employee.department else None,
        "leave_type": item.leave_type, "start_date": item.start_date,
        "end_date": item.end_date, "reason": item.reason, "status": item.status,
        "decision_note": item.decision_note,
        "approved_by": str(item.approved_by) if item.approved_by else None,
        "approved_by_name": (" ".join(part for part in (approver.employee.first_name, approver.employee.middle_name, approver.employee.last_name) if part)
                              if approver and approver.employee else (approver.email if approver else None)),
        "decided_at": item.decided_at,
    }


def notify_users(db: Session, users: list[User], *, title: str, message: str, details: dict, kind: str) -> None:
    seen = set()
    for recipient in users:
        if recipient.id in seen:
            continue
        seen.add(recipient.id)
        db.add(Notification(recipient_user_id=recipient.id, type=kind, title=title,
                            message=message[:255], details=details, is_read=False))


def hr_users(db: Session) -> list[User]:
    return db.query(User).filter(User.is_active.is_(True), User.role.in_(HR_ROLES)).all()


def hod_users(db: Session, department_id) -> list[User]:
    if not department_id:
        return []
    return (db.query(User).join(Employee, User.employee_id == Employee.id)
            .filter(User.is_active.is_(True), User.role == "HOD", Employee.department_id == department_id).all())


def get_leave_for_update(db: Session, leave_id: UUID) -> LeaveRequest:
    item = (db.query(LeaveRequest).options(joinedload(LeaveRequest.employee).joinedload(Employee.department),
                                             joinedload(LeaveRequest.approver).joinedload(User.employee))
            .filter(LeaveRequest.id == leave_id).with_for_update().first())
    if not item:
        raise HTTPException(status_code=404, detail="Leave request not found.")
    return item


@router.post("/request")
def request_leave(req: LeaveCreate, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    employee = db.query(Employee).options(joinedload(Employee.department)).filter(Employee.id == user.employee_id).first()
    if not employee:
        raise HTTPException(status_code=403, detail="Your account is not linked to an employee profile.")
    if req.end_date < req.start_date:
        raise HTTPException(status_code=422, detail="End date must be on or after the start date.")
    item = LeaveRequest(employee_id=employee.id, leave_type=req.leave_type.strip().upper(),
                       start_date=req.start_date, end_date=req.end_date, reason=req.reason.strip(), status="PENDING_HOD")
    db.add(item)
    db.flush()
    details = {
        "event": "Leave request submitted", "employee_name": employee_name(employee),
        "employee_number": employee.employee_number, "department": employee.department.name if employee.department else "Unassigned",
        "leave_type": item.leave_type, "start_date": item.start_date.isoformat(), "end_date": item.end_date.isoformat(),
        "employee_reason": item.reason, "status": item.status, "submitted_at": datetime.now(timezone.utc).isoformat(),
    }
    notify_users(db, hr_users(db), title="New leave request", message=f"{employee_name(employee)} submitted a {item.leave_type.lower()} leave request.", details=details, kind="LEAVE_REQUEST_SUBMITTED")
    notify_users(db, hod_users(db, employee.department_id), title="Leave request needs your review", message=f"{employee_name(employee)} submitted a {item.leave_type.lower()} leave request.", details=details, kind="LEAVE_REQUEST_SUBMITTED")
    db.commit()
    return {"message": "Leave request submitted to your department HOD and HR.", "status": item.status, "id": str(item.id)}


@router.get("/my-history")
def get_my_leaves(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    rows = (db.query(LeaveRequest).options(joinedload(LeaveRequest.employee).joinedload(Employee.department),
                                            joinedload(LeaveRequest.approver).joinedload(User.employee))
            .filter(LeaveRequest.employee_id == user.employee_id).order_by(LeaveRequest.start_date.desc()).all())
    return [serialize_leave(item) for item in rows]


@router.get("/pending")
def get_pending(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    role = (user.role or "").upper()
    if role not in HOD_ROLES and role not in HR_ROLES:
        raise HTTPException(status_code=403, detail="HOD access is required to review leave requests.")
    query = (db.query(LeaveRequest).join(Employee, LeaveRequest.employee_id == Employee.id)
             .options(joinedload(LeaveRequest.employee).joinedload(Employee.department))
             .filter(LeaveRequest.status == "PENDING_HOD"))
    if role == "HOD":
        if not user.employee or not user.employee.department_id:
            raise HTTPException(status_code=403, detail="Your HOD account needs a linked department.")
        query = query.filter(Employee.department_id == user.employee.department_id)
    return [serialize_leave(item) for item in query.order_by(LeaveRequest.start_date).all()]


def decide(leave_id: UUID, decision: str, req: LeaveReview, db: Session, user: User):
    role = (user.role or "").upper()
    if role not in HOD_ROLES and role not in HR_ROLES:
        raise HTTPException(status_code=403, detail="HOD or HR access is required to decide leave requests.")
    item = get_leave_for_update(db, leave_id)
    if item.status != "PENDING_HOD":
        raise HTTPException(status_code=409, detail="This leave request has already been decided.")
    if role == "HOD":
        if not user.employee or not user.employee.department_id or user.employee.department_id != item.employee.department_id:
            raise HTTPException(status_code=403, detail="You can only decide leave requests from your department.")
    item.status = decision
    item.approved_by = user.id
    item.decision_note = req.note.strip()
    item.decided_at = datetime.now(timezone.utc)
    db.flush()
    decided_by = employee_name(user.employee) if user.employee else user.email
    department = item.employee.department.name if item.employee.department else "Unassigned"
    details = {
        "event": "Leave request decision", "employee_name": employee_name(item.employee),
        "employee_number": item.employee.employee_number, "department": department,
        "leave_type": item.leave_type, "start_date": item.start_date.isoformat(), "end_date": item.end_date.isoformat(),
        "employee_reason": item.reason, "decision": decision, "decision_note": item.decision_note,
        "approved_by": decided_by, "decided_at": item.decided_at.isoformat(),
    }
    notify_users(db, hr_users(db), title=f"Leave {decision.lower()}",
                 message=f"{employee_name(item.employee)}'s leave request was {decision.lower()} by {decided_by} ({department}).",
                 details=details, kind="LEAVE_REQUEST_DECIDED")
    db.commit()
    return {"message": f"Leave request {decision.lower()}.", "leave": serialize_leave(item)}


@router.put("/{leave_id}/approve")
def approve_leave(leave_id: UUID, req: LeaveReview, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return decide(leave_id, "APPROVED", req, db, user)


@router.put("/{leave_id}/reject")
def reject_leave(leave_id: UUID, req: LeaveReview, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return decide(leave_id, "REJECTED", req, db, user)
