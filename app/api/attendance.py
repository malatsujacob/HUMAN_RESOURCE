from datetime import date, datetime, time, timedelta
from decimal import Decimal
from typing import Optional
from uuid import UUID
from zoneinfo import ZoneInfo

from fastapi import APIRouter, Depends, Header, HTTPException, Query
from jose import JWTError, jwt
from pydantic import BaseModel, ConfigDict
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.database import ALGORITHM, SECRET_KEY, SessionLocal
from app.models.attendance import Attendance
from app.models.employee import Employee
from app.models.user import User

router = APIRouter()
LOCAL_TIMEZONE = ZoneInfo("Africa/Kampala")
STANDARD_WORKDAY = timedelta(hours=8)
HR_ROLES = {"HR", "HR_ADMIN", "MANAGEMENT"}


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_current_user(
    authorization: Optional[str] = Header(default=None),
    db: Session = Depends(get_db),
) -> User:
    if not authorization:
        raise HTTPException(
            status_code=401,
            detail="Bearer token required",
            headers={"WWW-Authenticate": "Bearer"},
        )

    scheme, _, token = authorization.partition(" ")
    if scheme.lower() != "bearer" or not token.strip():
        raise HTTPException(
            status_code=401,
            detail="Bearer token required",
            headers={"WWW-Authenticate": "Bearer"},
        )
    token = token.strip()
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email = payload.get("sub")
        if not email:
            raise HTTPException(
                status_code=401,
                detail="Invalid authentication credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
    except JWTError:
        raise HTTPException(
            status_code=401,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user = db.query(User).filter(User.email == email).first()
    if user is None or not user.is_active:
        raise HTTPException(
            status_code=401,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user


class AttendanceResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    employee_id: UUID
    date: date
    check_in: Optional[time]
    check_out: Optional[time]
    status: str
    overtime_hours: Decimal


def get_own_employee(user: User) -> Employee:
    if user.role.upper() not in HR_ROLES | {"HOD", "EMPLOYEE"}:
        raise HTTPException(status_code=403, detail="Role is not allowed to access attendance")
    if user.employee is None:
        raise HTTPException(status_code=403, detail="User is not linked to an employee record")
    return user.employee


@router.get("/", response_model=list[AttendanceResponse])
def list_attendance(
    date_from: Optional[date] = Query(default=None),
    date_to: Optional[date] = Query(default=None),
    employee_id: Optional[UUID] = Query(default=None),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    if date_from and date_to and date_from > date_to:
        raise HTTPException(status_code=400, detail="date_from must not be after date_to")

    query = db.query(Attendance)
    role = user.role.upper()

    if role in HR_ROLES:
        pass
    elif role == "HOD":
        employee = get_own_employee(user)
        if employee.department_id is None:
            raise HTTPException(status_code=403, detail="HOD is not assigned to a department")
        query = query.join(Employee).filter(Employee.department_id == employee.department_id)
    elif role == "EMPLOYEE":
        employee = get_own_employee(user)
        if employee_id is not None and employee_id != employee.id:
            raise HTTPException(status_code=403, detail="Employees can only view their own attendance")
        query = query.filter(Attendance.employee_id == employee.id)
    else:
        raise HTTPException(status_code=403, detail="Role is not allowed to access attendance")

    if employee_id is not None:
        query = query.filter(Attendance.employee_id == employee_id)
    if date_from is not None:
        query = query.filter(Attendance.date >= date_from)
    if date_to is not None:
        query = query.filter(Attendance.date <= date_to)
    return query.order_by(Attendance.date.desc(), Attendance.check_in.desc()).all()


@router.post("/check-in", response_model=AttendanceResponse, status_code=201)
def check_in(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    employee = get_own_employee(user)
    db.query(Employee).filter(Employee.id == employee.id).with_for_update().first()
    now = datetime.now(LOCAL_TIMEZONE)
    today = now.date()
    check_in_time = now.time().replace(tzinfo=None, microsecond=0)

    existing = db.query(Attendance).filter(
        Attendance.employee_id == employee.id,
        Attendance.date == today,
    ).first()
    if existing is not None:
        raise HTTPException(status_code=409, detail="Attendance has already been recorded for today")

    record = Attendance(
        employee_id=employee.id,
        date=today,
        check_in=check_in_time,
        status="PRESENT",
        overtime_hours=Decimal("0.00"),
    )
    db.add(record)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        existing = db.query(Attendance).filter(
            Attendance.employee_id == employee.id,
            Attendance.date == today,
        ).first()
        if existing is not None:
            raise HTTPException(status_code=409, detail="Attendance has already been recorded for today")
        raise
    db.refresh(record)
    return record


@router.post("/check-out", response_model=AttendanceResponse)
def check_out(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    employee = get_own_employee(user)
    today = datetime.now(LOCAL_TIMEZONE).date()
    record = (
        db.query(Attendance)
        .filter(Attendance.employee_id == employee.id, Attendance.date == today)
        .with_for_update()
        .first()
    )
    if record is None:
        raise HTTPException(status_code=404, detail="No check-in found for today")
    if record.check_in is None:
        raise HTTPException(status_code=409, detail="Attendance record has no check-in time")
    if record.check_out is not None:
        raise HTTPException(status_code=409, detail="Attendance has already been checked out")

    check_out_time = datetime.now(LOCAL_TIMEZONE).time().replace(tzinfo=None, microsecond=0)
    started_at = datetime.combine(record.date, record.check_in)
    ended_at = datetime.combine(record.date, check_out_time)
    if ended_at < started_at:
        ended_at += timedelta(days=1)
    worked = ended_at - started_at
    overtime = max(worked - STANDARD_WORKDAY, timedelta())

    record.check_out = check_out_time
    record.overtime_hours = Decimal(str(overtime.total_seconds() / 3600)).quantize(Decimal("0.01"))
    db.commit()
    db.refresh(record)
    return record
