from typing import Optional
from datetime import date, datetime, timezone
from decimal import Decimal
import csv
import io
import re
import secrets
import string
import uuid
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, File, Form, UploadFile
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, joinedload
from fastapi.responses import StreamingResponse, FileResponse
from pathlib import Path
from app.models.employee_document import EmployeeDocument
from app.models.payroll import PayrollAuditEvent

from app.database import SessionLocal, get_password_hash
from app.models.employee import Employee
from app.models.user import User
from app.models.department import Department
from app.routers.attendance import get_current_user

router = APIRouter()
HR_ROLES = {"HR", "HR_ADMIN", "ADMIN", "MANAGEMENT", "DEVELOPER"}
ALLOWED_USER_ROLES = {"EMPLOYEE", "HOD", "HR", "HR_ADMIN", "MANAGEMENT", "ADMIN", "DEVELOPER"}


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def require_hr(user: User = Depends(get_current_user)) -> User:
    if (user.role or "").upper() not in HR_ROLES:
        raise HTTPException(status_code=403, detail="HR access is required.")
    return user


def normalize_role(value: str | None) -> str:
    role = (value or "EMPLOYEE").strip().upper().replace("-", "_")
    aliases = {"EMPLOYEE": "EMPLOYEE", "ASSISTANT HR": "HR_ADMIN", "ASSISTANT_HR": "HR_ADMIN",
               "CEO": "MANAGEMENT", "MD": "MANAGEMENT", "SYSTEM ADMINISTRATOR": "ADMIN",
               "SYSTEM_ADMINISTRATOR": "ADMIN", "DEVELOPER": "DEVELOPER", "HEAD OF DEPARTMENT": "HOD"}
    return aliases.get(role, role if role in ALLOWED_USER_ROLES else "EMPLOYEE")


def temporary_password(length: int = 14) -> str:
    alphabet = string.ascii_letters + string.digits + "!@#$%"
    while True:
        value = "".join(secrets.choice(alphabet) for _ in range(length))
        if (any(ch.islower() for ch in value) and any(ch.isupper() for ch in value)
                and any(ch.isdigit() for ch in value) and any(ch in "!@#$%" for ch in value)):
            return value


def employee_payload(employee: Employee) -> dict:
    user = employee.user_account
    return {
        "id": str(employee.id), "employee_number": employee.employee_number,
        "legacy_employee_id": employee.legacy_employee_id, "legacy_role": employee.legacy_role,
        "legacy_department": employee.legacy_department,
        "first_name": employee.first_name, "middle_name": employee.middle_name,
        "last_name": employee.last_name,
        "full_name": " ".join(part for part in [employee.first_name, employee.middle_name, employee.last_name] if part),
        "personal_email": employee.personal_email, "work_email": employee.work_email,
        "phone_number": employee.phone_number, "home_address": employee.home_address,
        "physical_address": employee.home_address,
        "gender": employee.gender, "marital_status": employee.marital_status,
        "date_of_birth": employee.date_of_birth, "nationality": employee.nationality,
        "father_name": employee.father_name, "mother_name": employee.mother_name,
        "next_of_kin_name": employee.next_of_kin_name,
        "next_of_kin_relationship": employee.next_of_kin_relationship,
        "next_of_kin_phone": employee.next_of_kin_phone,
        "next_of_kin_address": employee.next_of_kin_address,
        "national_id": employee.national_id, "tin_number": employee.tin_number,
        "nssf_number": employee.nssf_number, "bank_name": employee.bank_name,
        "account_number": employee.account_number,
        "has_profile_photo": bool(employee.profile_photo_path),
        "department_id": str(employee.department_id) if employee.department_id else None,
        "department_code": employee.department.code if employee.department else None,
        "department_name": employee.department.name if employee.department else None,
        "job_title": employee.job_title, "reporting_manager": employee.reporting_manager,
        "work_location": employee.work_location,
        "cost_center": employee.cost_center,
        "jurisdiction_address": employee.jurisdiction_address,
        "jurisdiction_updated_at": employee.jurisdiction_updated_at,
        "tax_form_updated_at": employee.tax_form_updated_at,
        "hire_date": employee.hire_date,
        "employment_type": employee.employment_type, "probation_period": employee.probation_period,
        "notice_period": employee.notice_period, "contract_end_date": employee.contract_end_date,
        "status": employee.status, "base_salary": str(employee.base_salary) if employee.base_salary is not None else None,
        "has_account": bool(user), "account_email": user.email if user else None,
        "account_role": user.role if user else employee.legacy_role,
        "must_change_password": bool(user.must_change_password) if user else False,
        "documents": [{"id": str(doc.id), "document_type": doc.document_type, "file_name": doc.file_name,
                       "status": doc.status, "submitted_at": doc.submitted_at}
                      for doc in sorted(employee.documents or [], key=lambda row: row.created_at or datetime.min.replace(tzinfo=timezone.utc))],
    }


def add_employee_payroll_audit(db: Session, user: User, target: str, action_type: str, before_value=None, after_value=None) -> None:
    db.add(PayrollAuditEvent(
        pay_period=date.today().strftime("%Y-%m"),
        actor_id=user.id,
        actor_email=user.email,
        action_type=action_type,
        target=target,
        before_value=str(before_value) if before_value is not None else None,
        after_value=str(after_value) if after_value is not None else None,
    ))


class EmployeeCreate(BaseModel):
    first_name: str = Field(min_length=1, max_length=100)
    middle_name: Optional[str] = Field(default=None, max_length=100)
    last_name: str = Field(min_length=1, max_length=100)
    personal_email: Optional[EmailStr] = None
    work_email: Optional[EmailStr] = None
    phone_number: Optional[str] = Field(default=None, max_length=30)
    home_address: Optional[str] = Field(default=None, max_length=500)
    date_of_birth: Optional[date] = None
    gender: Optional[str] = Field(default=None, max_length=30)
    nationality: Optional[str] = Field(default=None, max_length=100)
    marital_status: Optional[str] = Field(default=None, max_length=30)
    father_name: Optional[str] = Field(default=None, max_length=200)
    mother_name: Optional[str] = Field(default=None, max_length=200)
    next_of_kin_name: Optional[str] = Field(default=None, max_length=200)
    next_of_kin_relationship: Optional[str] = Field(default=None, max_length=100)
    next_of_kin_phone: Optional[str] = Field(default=None, max_length=30)
    next_of_kin_address: Optional[str] = Field(default=None, max_length=500)
    national_id: Optional[str] = Field(default=None, max_length=30)
    tin_number: Optional[str] = Field(default=None, max_length=20)
    nssf_number: Optional[str] = Field(default=None, max_length=20)
    bank_name: Optional[str] = Field(default=None, max_length=100)
    account_number: Optional[str] = Field(default=None, max_length=50)
    base_salary: Optional[Decimal] = None
    job_title: str = Field(min_length=1, max_length=100)
    reporting_manager: Optional[str] = Field(default=None, max_length=200)
    work_location: Optional[str] = Field(default=None, max_length=200)
    cost_center: Optional[str] = Field(default=None, max_length=100)
    jurisdiction_address: Optional[str] = Field(default=None, max_length=500)
    jurisdiction_updated_at: Optional[date] = None
    tax_form_updated_at: Optional[date] = None
    hire_date: Optional[date] = None
    employment_type: Optional[str] = Field(default=None, max_length=30)
    probation_period: Optional[str] = Field(default=None, max_length=50)
    notice_period: Optional[str] = Field(default=None, max_length=50)
    contract_end_date: Optional[date] = None
    status: str = "ACTIVE"
    department_code: str
    role: str = "EMPLOYEE"


class EmployeeUpdate(BaseModel):
    first_name: Optional[str] = Field(default=None, min_length=1, max_length=100)
    middle_name: Optional[str] = Field(default=None, max_length=100)
    last_name: Optional[str] = Field(default=None, min_length=1, max_length=100)
    personal_email: Optional[EmailStr] = None
    work_email: Optional[EmailStr] = None
    phone_number: Optional[str] = Field(default=None, max_length=30)
    home_address: Optional[str] = Field(default=None, max_length=500)
    date_of_birth: Optional[date] = None
    gender: Optional[str] = Field(default=None, max_length=30)
    nationality: Optional[str] = Field(default=None, max_length=100)
    marital_status: Optional[str] = Field(default=None, max_length=30)
    father_name: Optional[str] = Field(default=None, max_length=200)
    mother_name: Optional[str] = Field(default=None, max_length=200)
    next_of_kin_name: Optional[str] = Field(default=None, max_length=200)
    next_of_kin_relationship: Optional[str] = Field(default=None, max_length=100)
    next_of_kin_phone: Optional[str] = Field(default=None, max_length=30)
    next_of_kin_address: Optional[str] = Field(default=None, max_length=500)
    national_id: Optional[str] = Field(default=None, max_length=30)
    tin_number: Optional[str] = Field(default=None, max_length=20)
    nssf_number: Optional[str] = Field(default=None, max_length=20)
    bank_name: Optional[str] = Field(default=None, max_length=100)
    account_number: Optional[str] = Field(default=None, max_length=50)
    base_salary: Optional[Decimal] = None
    job_title: Optional[str] = Field(default=None, max_length=100)
    reporting_manager: Optional[str] = Field(default=None, max_length=200)
    work_location: Optional[str] = Field(default=None, max_length=200)
    cost_center: Optional[str] = Field(default=None, max_length=100)
    jurisdiction_address: Optional[str] = Field(default=None, max_length=500)
    jurisdiction_updated_at: Optional[date] = None
    tax_form_updated_at: Optional[date] = None
    hire_date: Optional[date] = None
    employment_type: Optional[str] = Field(default=None, max_length=30)
    probation_period: Optional[str] = Field(default=None, max_length=50)
    notice_period: Optional[str] = Field(default=None, max_length=50)
    contract_end_date: Optional[date] = None
    department_code: Optional[str] = None
    status: Optional[str] = None
    role: Optional[str] = None


@router.get("/")
def get_employees(db: Session = Depends(get_db), _user: User = Depends(require_hr)):
    employees = db.query(Employee).options(
        joinedload(Employee.department), joinedload(Employee.user_account), joinedload(Employee.documents)
    ).filter(Employee.status != "EXITED").order_by(Employee.last_name, Employee.first_name).all()
    return [employee_payload(item) for item in employees]


@router.get("/departments")
def get_departments(db: Session = Depends(get_db), _user: User = Depends(require_hr)):
    return [{"code": item.code, "name": item.name} for item in db.query(Department).order_by(Department.name).all()]


@router.get("/me")
def get_my_employee_profile(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    employee = db.query(Employee).options(joinedload(Employee.department)).filter(Employee.id == user.employee_id).first()
    if not employee:
        raise HTTPException(status_code=404, detail="Your account is not linked to an employee profile.")
    return employee_payload(employee)


@router.post("/")
def create_employee(emp: EmployeeCreate, db: Session = Depends(get_db), user: User = Depends(require_hr)):
    role = normalize_role(emp.role)
    if role not in ALLOWED_USER_ROLES:
        raise HTTPException(status_code=422, detail="Select a valid employee, HOD, or HR role.")
    dept = db.query(Department).filter(Department.code == emp.department_code).first()
    if not dept:
        raise HTTPException(status_code=400, detail="Department not found.")
    login_email = str(emp.work_email or emp.personal_email or "").lower()
    if not login_email:
        raise HTTPException(status_code=422, detail="Enter a work or personal email to create the employee login.")
    if db.query(User.id).filter(User.email == login_email).first():
        raise HTTPException(status_code=409, detail="An account already uses this login email.")

    password = temporary_password()
    employee = Employee(
        employee_number=f"EMP-{uuid.uuid4().hex[:8].upper()}", legacy_role=role,
        first_name=emp.first_name.strip(), middle_name=emp.middle_name.strip() if emp.middle_name else None,
        last_name=emp.last_name.strip(), personal_email=str(emp.personal_email).lower() if emp.personal_email else None,
        work_email=str(emp.work_email).lower() if emp.work_email else None,
        phone_number=emp.phone_number.strip() if emp.phone_number else None,
        home_address=emp.home_address.strip() if emp.home_address else None,
        date_of_birth=emp.date_of_birth, gender=emp.gender, nationality=emp.nationality,
        marital_status=emp.marital_status, father_name=emp.father_name, mother_name=emp.mother_name,
        next_of_kin_name=emp.next_of_kin_name, next_of_kin_relationship=emp.next_of_kin_relationship,
        next_of_kin_phone=emp.next_of_kin_phone, next_of_kin_address=emp.next_of_kin_address,
        national_id=emp.national_id, tin_number=emp.tin_number, nssf_number=emp.nssf_number,
        bank_name=emp.bank_name, account_number=emp.account_number, base_salary=emp.base_salary,
        job_title=emp.job_title.strip(), reporting_manager=emp.reporting_manager,
        work_location=emp.work_location, cost_center=emp.cost_center,
        hire_date=emp.hire_date, employment_type=emp.employment_type,
        jurisdiction_address=emp.jurisdiction_address, jurisdiction_updated_at=emp.jurisdiction_updated_at,
        tax_form_updated_at=emp.tax_form_updated_at,
        probation_period=emp.probation_period, notice_period=emp.notice_period,
        contract_end_date=emp.contract_end_date, department_id=dept.id, status=emp.status.upper(),
    )
    db.add(employee)
    db.flush()
    initial_payroll_data = {
        "base_salary": employee.base_salary,
        "department_id": employee.department_id,
        "cost_center": employee.cost_center,
        "tin_number": employee.tin_number,
        "nssf_number": employee.nssf_number,
        "bank_name": employee.bank_name,
        "account_number": f"****{employee.account_number[-4:]}" if employee.account_number else None,
    }
    add_employee_payroll_audit(db, user, str(employee.id), "EMPLOYEE_PAYROLL_DATA_CREATED", None, initial_payroll_data)
    account = User(email=login_email, password_hash=get_password_hash(password), role=role,
                   employee_id=employee.id, must_change_password=True)
    db.add(account)
    try:
        db.commit()
    except IntegrityError as error:
        db.rollback()
        raise HTTPException(status_code=409, detail="Employee, statutory ID, or login details already exist.") from error
    return {"message": "Employee and login account created.", "employee_id": str(employee.id),
            "employee_number": employee.employee_number, "login_email": login_email,
            "temporary_password": password, "must_change_password": True}


@router.put("/{employee_id}")
def update_employee(employee_id: UUID, update: EmployeeUpdate,
                    db: Session = Depends(get_db), user: User = Depends(require_hr)):
    employee = db.query(Employee).options(joinedload(Employee.user_account)).filter(Employee.id == employee_id).first()
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found.")
    changes = update.model_dump(exclude_unset=True)
    department_code = changes.pop("department_code", None)
    requested_role = changes.pop("role", None)
    audit_fields = {
        "base_salary", "tin_number", "nssf_number", "bank_name", "account_number",
        "cost_center", "jurisdiction_address", "jurisdiction_updated_at", "tax_form_updated_at", "work_location", "status",
    }
    before_payroll_values = {field: getattr(employee, field) for field in changes if field in audit_fields}
    if department_code is not None:
        before_payroll_values["department_id"] = employee.department_id
    if department_code:
        department = db.query(Department).filter(Department.code == department_code).first()
        if not department:
            raise HTTPException(status_code=400, detail="Department not found.")
        employee.department_id = department.id
        employee.legacy_department = None
    if requested_role:
        role = normalize_role(requested_role)
        if role not in ALLOWED_USER_ROLES:
            raise HTTPException(status_code=422, detail="Select a valid employee, HOD, or HR role.")
        employee.legacy_role = role
        if employee.user_account:
            employee.user_account.role = role
    nullable_fields = {
        "middle_name", "personal_email", "work_email", "phone_number", "home_address", "date_of_birth",
        "gender", "nationality", "marital_status", "father_name", "mother_name", "next_of_kin_name",
        "next_of_kin_relationship", "next_of_kin_phone", "next_of_kin_address", "national_id", "tin_number",
        "nssf_number", "bank_name", "account_number", "base_salary", "reporting_manager", "work_location",
        "hire_date", "employment_type", "probation_period", "notice_period", "contract_end_date",
        "cost_center", "jurisdiction_address", "jurisdiction_updated_at", "tax_form_updated_at",
    }
    for field, value in changes.items():
        if isinstance(value, str):
            value = value.strip()
        if value == "" and field in nullable_fields:
            value = None
        setattr(employee, field, value)
    if employee.user_account:
        login_email = (employee.work_email or employee.personal_email or "").lower()
        if not login_email:
            raise HTTPException(status_code=422, detail="An employee with an account must keep a work or personal email.")
        duplicate = db.query(User.id).filter(User.email == login_email, User.id != employee.user_account.id).first()
        if duplicate:
            raise HTTPException(status_code=409, detail="Another account already uses the selected work or personal email.")
        employee.user_account.email = login_email
    after_payroll_values = {field: getattr(employee, field) for field in before_payroll_values if field != "department_id"}
    if "department_id" in before_payroll_values:
        after_payroll_values["department_id"] = employee.department_id
    if before_payroll_values != after_payroll_values:
        safe_before = dict(before_payroll_values)
        safe_after = dict(after_payroll_values)
        for values in (safe_before, safe_after):
            if values.get("account_number"):
                values["account_number"] = f"****{str(values['account_number'])[-4:]}"
        add_employee_payroll_audit(
            db, user, str(employee.id), "EMPLOYEE_PAYROLL_DATA_CHANGED", safe_before, safe_after
        )
    try:
        db.commit()
    except IntegrityError as error:
        db.rollback()
        raise HTTPException(status_code=409, detail="The profile conflicts with another employee record.") from error
    db.refresh(employee)
    return {"message": "Employee profile updated.", "employee": employee_payload(employee)}


@router.post("/{employee_id}/generate-login")
def generate_employee_login(employee_id: UUID, db: Session = Depends(get_db), _user: User = Depends(require_hr)):
    employee = db.query(Employee).options(joinedload(Employee.user_account)).filter(Employee.id == employee_id).first()
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found.")
    login_email = (employee.work_email or employee.personal_email or "").lower()
    if not login_email:
        raise HTTPException(status_code=409, detail="Add a work or personal email before generating login details.")
    account = employee.user_account
    if account is None:
        role = normalize_role(employee.legacy_role)
        account = User(email=login_email, role=role, employee_id=employee.id, is_active=True)
        db.add(account)
    else:
        duplicate = db.query(User.id).filter(User.email == login_email, User.id != account.id).first()
        if duplicate:
            raise HTTPException(status_code=409, detail="Another account already uses this email.")
        account.email = login_email
        account.is_active = True
    password = temporary_password()
    account.password_hash = get_password_hash(password)
    account.must_change_password = True
    db.commit()
    return {"message": "Temporary login generated. Share it with the employee securely.",
            "login_email": login_email, "temporary_password": password, "must_change_password": True}


LEGACY_UPLOAD_MAX = 10 * 1024 * 1024
EMPLOYEE_DOC_ROOT = Path(__file__).resolve().parents[3] / "uploads" / "employees"
EMPLOYEE_DOC_TYPES = {".pdf", ".doc", ".docx", ".csv", ".png", ".jpg", ".jpeg"}
PROFILE_PHOTO_ROOT = Path(__file__).resolve().parents[3] / "uploads" / "profile_photos"
PROFILE_PHOTO_TYPES = {".png", ".jpg", ".jpeg", ".webp"}
PROFILE_PHOTO_MAX = 5 * 1024 * 1024


@router.get("/me/photo")
def get_my_profile_photo(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    employee = db.query(Employee).filter(Employee.id == user.employee_id).first()
    if not employee or not employee.profile_photo_path:
        raise HTTPException(status_code=404, detail="No profile photo has been uploaded.")
    path = (PROFILE_PHOTO_ROOT.parents[1] / employee.profile_photo_path).resolve()
    if not path.is_relative_to(PROFILE_PHOTO_ROOT.resolve()) or not path.is_file():
        raise HTTPException(status_code=404, detail="Profile photo is unavailable.")
    return FileResponse(path, filename=path.name)


@router.put("/me/photo")
async def update_my_profile_photo(file: UploadFile = File(...), db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    employee = db.query(Employee).filter(Employee.id == user.employee_id).first()
    if not employee:
        raise HTTPException(status_code=404, detail="Your account is not linked to an employee profile.")
    suffix = Path(file.filename or "").suffix.lower()
    if suffix not in PROFILE_PHOTO_TYPES:
        raise HTTPException(status_code=400, detail="Use a PNG, JPG, JPEG, or WEBP profile photo.")
    data = await file.read(PROFILE_PHOTO_MAX + 1)
    if not data or len(data) > PROFILE_PHOTO_MAX:
        raise HTTPException(status_code=413, detail="Profile photo must be smaller than 5 MB.")
    PROFILE_PHOTO_ROOT.mkdir(parents=True, exist_ok=True)
    stored = PROFILE_PHOTO_ROOT / f"{employee.id}{suffix}"
    stored.write_bytes(data)
    old_path = employee.profile_photo_path
    employee.profile_photo_path = stored.relative_to(PROFILE_PHOTO_ROOT.parents[1]).as_posix()
    if old_path and old_path != employee.profile_photo_path:
        previous = (PROFILE_PHOTO_ROOT.parents[1] / old_path).resolve()
        if previous.is_relative_to(PROFILE_PHOTO_ROOT.resolve()):
            previous.unlink(missing_ok=True)
    db.commit()
    return {"message": "Profile photo updated."}


def legacy_date(value: str | None):
    value = (value or "").strip()
    if not value:
        return None
    try:
        return date.fromisoformat(value[:10])
    except ValueError as error:
        raise ValueError(f"Invalid date: {value}") from error


def csv_value(row: dict, *keys: str):
    for key in keys:
        value = row.get(key)
        if value is not None and str(value).strip() and str(value).strip().lower() not in {"null", "none"}:
            return str(value).strip()
    return None


@router.post("/import-legacy")
async def import_legacy_employee_csv(file: UploadFile = File(...), db: Session = Depends(get_db), _user: User = Depends(require_hr)):
    if not (file.filename or "").lower().endswith(".csv"):
        raise HTTPException(status_code=415, detail="Choose the employee CSV exported from the previous directory.")
    content = await file.read(LEGACY_UPLOAD_MAX + 1)
    if len(content) > LEGACY_UPLOAD_MAX:
        raise HTTPException(status_code=413, detail="Employee CSV must be smaller than 10 MB.")
    try:
        text = content.decode("utf-8-sig")
        rows = list(csv.DictReader(io.StringIO(text)))
    except (UnicodeDecodeError, csv.Error) as error:
        raise HTTPException(status_code=400, detail="The uploaded file is not a readable UTF-8 CSV.") from error
    if not rows:
        raise HTTPException(status_code=400, detail="The employee CSV contains no data rows.")

    departments = db.query(Department).all()
    created = updated = skipped = 0
    errors = []
    for line, raw_row in enumerate(rows, start=2):
        row = {(key or "").strip().lower(): (value or "").strip() for key, value in raw_row.items() if key}
        try:
            old_id = int(csv_value(row, "employee_id", "legacy_employee_id") or "")
            first_name = csv_value(row, "first_name")
            last_name = csv_value(row, "last_name")
            if not first_name or not last_name:
                raise ValueError("First and last name are required.")
            department_name = csv_value(row, "department")
            department = next((d for d in departments if department_name and department_name.casefold() in {d.code.casefold(), d.name.casefold()}), None)
            if department_name and department is None:
                code = re.sub(r"[^A-Z0-9]+", "_", department_name.upper()).strip("_")[:30] or f"LEGACY_{old_id}"
                department = db.query(Department).filter(Department.code == code).first()
                if department is None:
                    department = Department(code=code, name=department_name[:100])
                    db.add(department)
                    db.flush()
                    departments.append(department)
            employee = db.query(Employee).filter(Employee.legacy_employee_id == old_id).first()
            was_created = employee is None
            if was_created:
                employee = Employee(legacy_employee_id=old_id, employee_number=f"LEG-{old_id}", first_name=first_name, last_name=last_name)
                db.add(employee)
            employee.first_name = first_name
            employee.middle_name = csv_value(row, "middle_name")
            employee.last_name = last_name
            employee.date_of_birth = legacy_date(csv_value(row, "date_of_birth"))
            employee.gender = csv_value(row, "gender")
            employee.nationality = csv_value(row, "nationality")
            employee.marital_status = csv_value(row, "marital_status")
            employee.personal_email = csv_value(row, "personal_email")
            employee.work_email = csv_value(row, "work_email")
            employee.phone_number = csv_value(row, "phone_number")
            employee.home_address = csv_value(row, "physical_address", "home_address")
            employee.next_of_kin_name = csv_value(row, "next_of_kin_name")
            employee.next_of_kin_relationship = csv_value(row, "next_of_kin_relationship")
            employee.next_of_kin_phone = csv_value(row, "next_of_kin_phone")
            employee.next_of_kin_address = csv_value(row, "next_of_kin_address")
            employee.department_id = department.id if department else None
            employee.legacy_department = None if department else department_name
            employee.job_title = csv_value(row, "job_title")
            employee.reporting_manager = csv_value(row, "reporting_manager")
            employee.work_location = csv_value(row, "work_location")
            employee.hire_date = legacy_date(csv_value(row, "hire_date"))
            employee.employment_type = csv_value(row, "employment_type")
            employee.status = (csv_value(row, "status") or "ACTIVE").upper().replace(" ", "_")
            employee.legacy_role = csv_value(row, "role", "system_role") or employee.legacy_role
            employee.national_id = csv_value(row, "national_id")
            employee.tin_number = csv_value(row, "tin_number", "tax_identification_number")
            employee.nssf_number = csv_value(row, "nssf_number", "social_security_number")
            employee.bank_name = csv_value(row, "bank_name")
            employee.account_number = csv_value(row, "account_number")
            employee.base_salary = csv_value(row, "base_salary")
            employee.probation_period = csv_value(row, "probation_period")
            employee.notice_period = csv_value(row, "notice_period")
            employee.contract_end_date = legacy_date(csv_value(row, "contract_end_date"))
            db.flush()
            db.commit()
            if was_created: created += 1
            else: updated += 1
        except Exception as error:
            db.rollback()
            skipped += 1
            errors.append({"row": line, "reason": str(error)[:200]})
            # Re-open a transaction after a row-level database failure.
            continue
    return {"message": "Legacy employee import completed. Existing logins and passwords were not changed.",
            "created": created, "updated": updated, "skipped": skipped, "errors": errors[:50]}


@router.get("/export")
def export_employees(db: Session = Depends(get_db), _user: User = Depends(require_hr)):
    records = db.query(Employee).options(joinedload(Employee.department)).filter(Employee.status != "EXITED").order_by(Employee.employee_number).all()
    fields = ["employee_id", "employee_number", "role", "first_name", "middle_name", "last_name", "date_of_birth", "gender", "nationality", "marital_status", "personal_email", "work_email", "phone_number", "physical_address", "next_of_kin_name", "next_of_kin_relationship", "next_of_kin_phone", "next_of_kin_address", "department", "job_title", "reporting_manager", "work_location", "hire_date", "employment_type", "probation_period", "notice_period", "contract_end_date", "status", "base_salary", "national_id", "tin_number", "nssf_number", "bank_name", "account_number"]
    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=fields)
    writer.writeheader()
    for employee in records:
        payload = employee_payload(employee)
        writer.writerow({"employee_id": employee.legacy_employee_id or employee.employee_number,
                         "employee_number": employee.employee_number, "role": payload["account_role"],
                         "first_name": employee.first_name, "middle_name": employee.middle_name,
                         "last_name": employee.last_name, "date_of_birth": employee.date_of_birth,
                         "gender": employee.gender, "nationality": employee.nationality,
                         "marital_status": employee.marital_status, "personal_email": employee.personal_email,
                         "work_email": employee.work_email, "phone_number": employee.phone_number,
                         "physical_address": employee.home_address, "next_of_kin_name": employee.next_of_kin_name,
                         "next_of_kin_relationship": employee.next_of_kin_relationship,
                         "next_of_kin_phone": employee.next_of_kin_phone, "next_of_kin_address": employee.next_of_kin_address,
                         "department": employee.department.name if employee.department else employee.legacy_department,
                         "job_title": employee.job_title, "reporting_manager": employee.reporting_manager,
                         "work_location": employee.work_location, "hire_date": employee.hire_date,
                         "employment_type": employee.employment_type, "probation_period": employee.probation_period,
                         "notice_period": employee.notice_period, "contract_end_date": employee.contract_end_date,
                         "status": employee.status, "base_salary": employee.base_salary, "national_id": employee.national_id,
                         "tin_number": employee.tin_number, "nssf_number": employee.nssf_number,
                         "bank_name": employee.bank_name, "account_number": employee.account_number})
    output.seek(0)
    return StreamingResponse(iter([output.getvalue()]), media_type="text/csv",
                             headers={"Content-Disposition": "attachment; filename=hrms_employee_directory.csv"})


@router.delete("/{employee_id}")
def archive_employee(employee_id: UUID, db: Session = Depends(get_db), user: User = Depends(require_hr)):
    employee = db.query(Employee).options(joinedload(Employee.user_account)).filter(Employee.id == employee_id).first()
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found.")
    previous_status = employee.status
    employee.status = "EXITED"
    if employee.user_account:
        employee.user_account.is_active = False
    add_employee_payroll_audit(db, user, str(employee.id), "EMPLOYEE_STATUS_CHANGED", previous_status, employee.status)
    db.commit()
    return {"message": "Employee archived as exited. Their profile and history remain available."}


@router.post("/{employee_id}/documents")
async def upload_employee_document(employee_id: UUID, document_type: str = Form(...), file: UploadFile = File(...),
                                  db: Session = Depends(get_db), user: User = Depends(require_hr)):
    employee = db.query(Employee).filter(Employee.id == employee_id).first()
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found.")
    suffix = Path(file.filename or "").suffix.lower()
    if suffix not in EMPLOYEE_DOC_TYPES:
        raise HTTPException(status_code=400, detail="Upload a PDF, DOC, DOCX, CSV, PNG, JPG, or JPEG file.")
    data = await file.read(LEGACY_UPLOAD_MAX + 1)
    if not data or len(data) > LEGACY_UPLOAD_MAX:
        raise HTTPException(status_code=413, detail="Each employee document must be smaller than 10 MB.")
    EMPLOYEE_DOC_ROOT.mkdir(parents=True, exist_ok=True)
    stored = EMPLOYEE_DOC_ROOT / f"{uuid.uuid4()}{suffix}"
    stored.write_bytes(data)
    doc_type = document_type.strip()[:120]
    if not doc_type:
        stored.unlink(missing_ok=True)
        raise HTTPException(status_code=422, detail="Enter the document type.")
    row = db.query(EmployeeDocument).filter(EmployeeDocument.employee_id == employee.id,
                                              EmployeeDocument.document_type == doc_type).first()
    before_document = f"{doc_type}:{row.file_name}" if row and row.file_name else None
    if row is None:
        row = EmployeeDocument(employee_id=employee.id, document_type=doc_type)
        db.add(row)
    elif row.file_path:
        old_path = (EMPLOYEE_DOC_ROOT.parents[1] / row.file_path).resolve()
        if old_path.is_relative_to(EMPLOYEE_DOC_ROOT.resolve()):
            old_path.unlink(missing_ok=True)
    row.file_name = Path(file.filename or "document").name
    row.file_path = stored.relative_to(EMPLOYEE_DOC_ROOT.parents[1]).as_posix()
    row.status = "VERIFIED"
    row.submitted_at = datetime.now(timezone.utc)
    row.reviewed_at = row.submitted_at
    row.reviewed_by = user.id
    add_employee_payroll_audit(db, user, str(employee.id), "EMPLOYEE_DOCUMENT_UPLOADED",
                               before_document, f"{doc_type}:{row.file_name}")
    try:
        db.commit()
    except Exception:
        db.rollback()
        stored.unlink(missing_ok=True)
        raise
    return {"message": "Employee document uploaded.", "document": {"id": str(row.id), "file_name": row.file_name, "document_type": row.document_type}}


@router.get("/documents/{document_id}/download")
def download_employee_document(document_id: UUID, db: Session = Depends(get_db), _user: User = Depends(require_hr)):
    row = db.query(EmployeeDocument).filter(EmployeeDocument.id == document_id).first()
    if not row or not row.file_path:
        raise HTTPException(status_code=404, detail="Employee document not found.")
    path = (EMPLOYEE_DOC_ROOT.parents[1] / row.file_path).resolve()
    if not path.is_relative_to(EMPLOYEE_DOC_ROOT.resolve()) or not path.is_file():
        raise HTTPException(status_code=404, detail="Stored document is unavailable.")
    return FileResponse(path, filename=row.file_name or path.name)
