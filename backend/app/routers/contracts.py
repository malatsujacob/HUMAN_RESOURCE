import html
import uuid
from datetime import date, datetime, timezone
from decimal import Decimal
from pathlib import Path
from typing import Literal, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile
from fastapi.responses import FileResponse, HTMLResponse
from pydantic import BaseModel, Field, field_validator
from sqlalchemy.orm import Session, joinedload

from app.database import SessionLocal
from app.models.contract import Contract
from app.models.employee import Employee
from app.models.employee_document import EmployeeDocument
from app.models.notification import Notification
from app.models.user import User
from app.routers.attendance import get_current_user
from app.constants.departments import canonical_department_name

router = APIRouter()
HR_ROLES = {"HR", "HR_ADMIN", "ADMIN", "MANAGEMENT", "DEVELOPER"}
CONTRACT_ROOT = Path(__file__).resolve().parents[3] / "uploads" / "employees"
UPLOAD_TYPES = {".pdf", ".doc", ".docx", ".png", ".jpg", ".jpeg"}
MAX_UPLOAD_SIZE = 20 * 1024 * 1024


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


class ContractCreate(BaseModel):
    employee_id: UUID
    contract_type: str = Field(min_length=1, max_length=50)
    start_date: date
    end_date: Optional[date] = None
    base_salary: Decimal = Field(ge=0)
    job_title: str = Field(min_length=1, max_length=100)
    work_location: Optional[str] = Field(default=None, max_length=200)
    employment_type: Optional[str] = Field(default=None, max_length=30)
    probation_period: Optional[str] = Field(default=None, max_length=50)
    notice_period: Optional[str] = Field(default=None, max_length=50)
    payment_frequency: Optional[str] = Field(default="Monthly", max_length=50)
    responsibilities: Optional[str] = Field(default=None, max_length=5000)
    benefits: Optional[str] = Field(default=None, max_length=5000)
    terms_and_conditions: str = Field(min_length=1, max_length=12000)
    expiry_reminder_days: Optional[int] = Field(default=None, ge=0, le=365)

    @field_validator("contract_type", "job_title", "terms_and_conditions")
    @classmethod
    def require_non_blank(cls, value: str) -> str:
        normalized = value.strip()
        if not normalized:
            raise ValueError("This field cannot be blank.")
        return normalized


class IssueContract(BaseModel):
    employer_signature_name: str = Field(min_length=2, max_length=200)

    @field_validator("employer_signature_name")
    @classmethod
    def require_signature_name(cls, value: str) -> str:
        normalized = value.strip()
        if len(normalized) < 2:
            raise ValueError("Enter the employer signatory's full name.")
        return normalized


class EmployeeContractSignature(BaseModel):
    employee_signature_name: str = Field(min_length=2, max_length=200)
    accepted: bool

    @field_validator("employee_signature_name")
    @classmethod
    def require_signature_name(cls, value: str) -> str:
        normalized = value.strip()
        if len(normalized) < 2:
            raise ValueError("Enter your full name.")
        return normalized


def employee_name(employee: Employee) -> str:
    return " ".join(part for part in (employee.first_name, employee.middle_name, employee.last_name) if part)


def contract_document_type(contract: Contract, suffix: str = "") -> str:
    return f"Employment contract {contract.id}{suffix}"


def directory_document(
    db: Session, contract: Contract, document_type: str, file_path: str,
    file_name: str, status: str, reviewed_by: Optional[User] = None,
) -> None:
    row = db.query(EmployeeDocument).filter(
        EmployeeDocument.employee_id == contract.employee_id,
        EmployeeDocument.document_type == document_type,
    ).first()
    if row is None:
        row = EmployeeDocument(employee_id=contract.employee_id, document_type=document_type)
        db.add(row)
    row.file_name = file_name
    row.file_path = file_path
    row.status = status
    row.submitted_at = datetime.now(timezone.utc)
    if reviewed_by:
        row.reviewed_by = reviewed_by.id
        row.reviewed_at = row.submitted_at


def remove_obsolete_file(contract: Contract, stored_path: Optional[str]) -> None:
    if not stored_path or stored_path in {contract.generated_file_path, contract.signed_file_path}:
        return
    path = (CONTRACT_ROOT.parents[1] / stored_path).resolve()
    if path.is_relative_to(CONTRACT_ROOT.resolve()):
        path.unlink(missing_ok=True)


def contract_html(contract: Contract, employee: Employee) -> str:
    safe = lambda value: html.escape(str(value)) if value is not None else "Not specified"
    responsibilities = safe(contract.responsibilities).replace("\n", "<br>")
    benefits = safe(contract.benefits).replace("\n", "<br>")
    terms = safe(contract.terms_and_conditions).replace("\n", "<br>")
    employer_signature = safe(contract.employer_signature_name)
    employee_signature = safe(contract.employee_signature_name)
    employer_date = contract.employer_signed_at.date().isoformat() if contract.employer_signed_at else "Pending"
    employee_date = contract.employee_signed_at.date().isoformat() if contract.employee_signed_at else "Pending"
    period = f"{contract.start_date.isoformat()} to {contract.end_date.isoformat()}" if contract.end_date else f"From {contract.start_date.isoformat()} (open-ended)"
    if contract.status == "DRAFT":
        banner = "INTERNAL DRAFT — HR and legal review required before issue. This template is not legal advice."
    elif contract.status == "PENDING_EMPLOYEE_SIGNATURE":
        banner = "ISSUED FOR SIGNATURE — Please review the completed terms before signing."
    elif contract.signing_method == "MANUAL":
        banner = "MANUALLY SIGNED — The uploaded signed copy is stored separately in the employee directory."
    else:
        banner = "DIGITALLY SIGNED — Typed signatures record in-app consent and are not independently identity-verified."
    return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>Employment agreement - {safe(employee_name(employee))}</title>
<style>
body{{font:15px/1.55 Arial,sans-serif;color:#172b3a;max-width:850px;margin:32px auto;padding:0 28px}}
h1,h2{{color:#173d59}}h1{{text-align:center;font-size:25px;margin-bottom:4px}}h2{{font-size:17px;border-bottom:1px solid #ccd7df;padding-bottom:5px;margin-top:24px}}
.draft{{padding:10px;background:#fff6d8;border:1px solid #e6ca70;text-align:center;font-weight:bold}}
table{{width:100%;border-collapse:collapse}}td{{padding:7px;border-bottom:1px solid #e3e9ee;vertical-align:top}}td:first-child{{width:34%;font-weight:bold}}
.signatures{{display:grid;grid-template-columns:1fr 1fr;gap:40px;margin-top:48px}}.signature{{border-top:1px solid #334b5d;padding-top:8px;min-height:84px}}
.print{{position:fixed;right:20px;top:20px;background:#1f739b;color:white;border:0;border-radius:6px;padding:10px 16px;cursor:pointer}}
@media print{{body{{margin:0 auto;padding:0 14mm}}.print{{display:none}}}}
@media(max-width:600px){{.signatures{{grid-template-columns:1fr}}}}
</style></head><body>
<button class="print" onclick="window.print()">Print / Save as PDF</button>
<h1>EMPLOYMENT AGREEMENT</h1>
<p style="text-align:center">Chap Chap Africa</p>
<p class="draft">{safe(banner)}</p>
<p>This agreement is between Chap Chap Africa (the Employer) and <strong>{safe(employee_name(employee))}</strong> (the Employee).</p>
<h2>1. Employee and appointment details</h2>
<table>
<tr><td>Employee number</td><td>{safe(employee.employee_number)}</td></tr>
<tr><td>Position</td><td>{safe(contract.job_title or employee.job_title)}</td></tr>
<tr><td>Department</td><td>{safe((canonical_department_name(employee.department.code) or employee.department.name) if employee.department else employee.legacy_department)}</td></tr>
<tr><td>Work location</td><td>{safe(contract.work_location or employee.work_location)}</td></tr>
<tr><td>Employment type</td><td>{safe(contract.employment_type or contract.contract_type)}</td></tr>
<tr><td>Term</td><td>{safe(period)}</td></tr>
<tr><td>Probation</td><td>{safe(contract.probation_period)}</td></tr>
<tr><td>Notice period</td><td>{safe(contract.notice_period)}</td></tr>
<tr><td>Salary</td><td>UGX {safe(f"{contract.base_salary:,.2f}")} gross, paid {safe(contract.payment_frequency or "Monthly")}</td></tr>
<tr><td>Benefits</td><td>{benefits}</td></tr></table>
<h2>2. Duties and responsibilities</h2><p>{responsibilities}</p>
<h2>3. Terms and conditions</h2><p>{terms}</p>
<h2>4. Confidentiality and company property</h2><p>The Employee must protect confidential company and client information, use company property responsibly, and return company property when employment ends. Any applicable legal obligations should be reviewed and completed by HR/legal before issue.</p>
<h2>5. Changes and governing requirements</h2><p>Changes to this agreement must be recorded in writing and signed by both parties. The parties should confirm applicable local employment law and resolve any required additions with HR/legal before signing.</p>
<p>By signing below, each party confirms that they have read and agree to the completed terms of this agreement.</p>
<div class="signatures"><div class="signature"><strong>For the Employer</strong><br>Name: {employer_signature}<br>Date: {safe(employer_date)}<br>Signature: {employer_signature if employer_signature != "Not specified" else "________________________"}</div>
<div class="signature"><strong>Employee</strong><br>Name: {employee_signature if employee_signature != "Not specified" else safe(employee_name(employee))}<br>Date: {safe(employee_date)}<br>Signature: {employee_signature if employee_signature != "Not specified" else "________________________"}</div></div>
<p style="margin-top:42px;font-size:11px;color:#687887">Generated by the Chap Chap Africa HRMS. Typed signatures represent recorded in-app consent and are not independently identity-verified.</p>
</body></html>"""


def save_generated_contract(db: Session, contract: Contract, employee: Employee) -> Path:
    CONTRACT_ROOT.mkdir(parents=True, exist_ok=True)
    path = CONTRACT_ROOT / f"contract-{contract.id}-{uuid.uuid4()}.html"
    path.write_text(contract_html(contract, employee), encoding="utf-8")
    contract.generated_file_path = path.relative_to(CONTRACT_ROOT.parents[1]).as_posix()
    doc_type = contract_document_type(contract)
    status = "SIGNED" if contract.status == "SIGNED" else contract.status
    directory_document(db, contract, doc_type, contract.generated_file_path, path.name, status)
    return path


def contract_payload(contract: Contract) -> dict:
    employee = contract.employee
    days_to_expiry = (contract.end_date - date.today()).days if contract.end_date else None
    return {
        "id": str(contract.id), "employee_id": str(contract.employee_id),
        "employee_name": employee_name(employee), "employee_number": employee.employee_number,
        "employee_email": employee.work_email or employee.personal_email,
        "department_name": (
            canonical_department_name(employee.department.code) or employee.department.name
            if employee.department else employee.legacy_department
        ),
        "contract_type": contract.contract_type, "start_date": contract.start_date,
        "end_date": contract.end_date, "base_salary": str(contract.base_salary) if contract.base_salary is not None else None,
        "job_title": contract.job_title or employee.job_title, "work_location": contract.work_location,
        "employment_type": contract.employment_type, "probation_period": contract.probation_period,
        "notice_period": contract.notice_period, "payment_frequency": contract.payment_frequency,
        "responsibilities": contract.responsibilities, "benefits": contract.benefits,
        "terms_and_conditions": contract.terms_and_conditions,
        "expiry_reminder_days": contract.expiry_reminder_days,
        "days_to_expiry": days_to_expiry, "signing_method": contract.signing_method,
        "employer_signature_name": contract.employer_signature_name,
        "employer_signed_by": str(contract.employer_signed_by) if contract.employer_signed_by else None,
        "employer_signed_at": contract.employer_signed_at,
        "employee_signature_name": contract.employee_signature_name,
        "employee_signed_by": str(contract.employee_signed_by) if contract.employee_signed_by else None,
        "employee_signed_at": contract.employee_signed_at, "status": contract.status,
        "has_generated_document": bool(contract.generated_file_path),
        "has_signed_document": bool(contract.signed_file_path),
        "signed_file_extension": Path(contract.signed_file_path).suffix if contract.signed_file_path else None,
    }


def get_contract(db: Session, contract_id: UUID) -> Contract:
    contract = db.query(Contract).options(
        joinedload(Contract.employee).joinedload(Employee.department)
    ).filter(Contract.id == contract_id).first()
    if contract is None:
        raise HTTPException(status_code=404, detail="Contract not found.")
    return contract


def create_expiry_notifications(db: Session, contracts: list[Contract]) -> None:
    hr_users = db.query(User).filter(User.is_active.is_(True), User.role.in_(HR_ROLES)).all()
    changed = False
    for contract in contracts:
        if contract.status not in {"SIGNED", "ACTIVE", "EXPIRED"} or contract.end_date is None:
            continue
        days = (contract.end_date - date.today()).days
        if (contract.expiry_reminder_days is not None and days <= contract.expiry_reminder_days
                and contract.expiry_alert_sent_at is None and hr_users):
            department = (
                canonical_department_name(contract.employee.department.code) or contract.employee.department.name
                if contract.employee.department else contract.employee.legacy_department
            )
            message = (
                f"{employee_name(contract.employee)}'s contract expired {abs(days)} day(s) ago."
                if days < 0 else
                f"{employee_name(contract.employee)}'s contract ends in {days} day(s)."
            )
            for recipient in hr_users:
                db.add(Notification(
                    recipient_user_id=recipient.id, type="CONTRACT_EXPIRY_REMINDER",
                    title="Employment contract expiry alert",
                    message=message,
                    details={"contract_id": str(contract.id), "employee_id": str(contract.employee_id),
                             "employee_name": employee_name(contract.employee), "department": department or "Unassigned",
                             "end_date": contract.end_date.isoformat(), "days_to_expiry": days,
                             "reminder_days": contract.expiry_reminder_days},
                    is_read=False,
                ))
            contract.expiry_alert_sent_at = datetime.now(timezone.utc)
            changed = True
        if days < 0 and contract.status != "EXPIRED":
            contract.status = "EXPIRED"
            changed = True
    if changed:
        db.commit()


@router.post("/")
def create_contract(req: ContractCreate, db: Session = Depends(get_db), _user: User = Depends(require_hr)):
    employee = db.query(Employee).options(joinedload(Employee.department)).filter(Employee.id == req.employee_id).first()
    if employee is None:
        raise HTTPException(status_code=404, detail="Employee not found.")
    if req.end_date is not None and req.end_date < req.start_date:
        raise HTTPException(status_code=422, detail="Contract end date must be on or after its start date.")
    contract = Contract(
        id=uuid.uuid4(), employee_id=employee.id, contract_type=req.contract_type.strip().upper(),
        start_date=req.start_date, end_date=req.end_date, base_salary=req.base_salary,
        job_title=req.job_title.strip(), work_location=req.work_location,
        employment_type=req.employment_type, probation_period=req.probation_period,
        notice_period=req.notice_period, payment_frequency=req.payment_frequency,
        responsibilities=req.responsibilities, benefits=req.benefits,
        terms_and_conditions=req.terms_and_conditions.strip(),
        expiry_reminder_days=req.expiry_reminder_days, status="DRAFT", signing_method="DIGITAL",
    )
    db.add(contract)
    db.flush()
    path = save_generated_contract(db, contract, employee)
    try:
        db.commit()
    except Exception:
        db.rollback()
        path.unlink(missing_ok=True)
        raise
    return {"message": "Draft contract generated and added to the employee directory.", "contract": contract_payload(contract)}


@router.get("/")
def get_all_contracts(db: Session = Depends(get_db), _user: User = Depends(require_hr)):
    contracts = db.query(Contract).options(
        joinedload(Contract.employee).joinedload(Employee.department)
    ).order_by(Contract.end_date.asc().nullslast()).with_for_update(of=Contract).all()
    create_expiry_notifications(db, contracts)
    return [contract_payload(contract) for contract in contracts]


@router.get("/mine")
def get_my_contracts(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    if not user.employee_id:
        return []
    contracts = db.query(Contract).options(
        joinedload(Contract.employee).joinedload(Employee.department)
    ).filter(
        Contract.employee_id == user.employee_id, Contract.status != "DRAFT",
    ).order_by(Contract.start_date.desc()).all()
    return [contract_payload(contract) for contract in contracts]


@router.get("/{contract_id}/document", response_class=HTMLResponse)
def view_contract_document(contract_id: UUID, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    contract = get_contract(db, contract_id)
    if (user.role or "").upper() not in HR_ROLES and user.employee_id != contract.employee_id:
        raise HTTPException(status_code=403, detail="You cannot access this contract.")
    if contract.status == "DRAFT" and (user.role or "").upper() not in HR_ROLES:
        raise HTTPException(status_code=403, detail="This contract has not been issued to you.")
    if not contract.generated_file_path:
        raise HTTPException(status_code=404, detail="Generated contract document is unavailable.")
    path = (CONTRACT_ROOT.parents[1] / contract.generated_file_path).resolve()
    if not path.is_relative_to(CONTRACT_ROOT.resolve()) or not path.is_file():
        raise HTTPException(status_code=404, detail="Generated contract document is unavailable.")
    return HTMLResponse(path.read_text(encoding="utf-8"))


@router.get("/{contract_id}/download")
def download_contract(
    contract_id: UUID, copy: Literal["generated", "signed"] = Query(default="generated"),
    db: Session = Depends(get_db), user: User = Depends(get_current_user),
):
    contract = get_contract(db, contract_id)
    if (user.role or "").upper() not in HR_ROLES and user.employee_id != contract.employee_id:
        raise HTTPException(status_code=403, detail="You cannot access this contract.")
    if contract.status == "DRAFT" and (user.role or "").upper() not in HR_ROLES:
        raise HTTPException(status_code=403, detail="This contract has not been issued to you.")
    stored_path = contract.signed_file_path if copy == "signed" and contract.signed_file_path else contract.generated_file_path
    if not stored_path:
        raise HTTPException(status_code=404, detail="Contract document is unavailable.")
    path = (CONTRACT_ROOT.parents[1] / stored_path).resolve()
    if not path.is_relative_to(CONTRACT_ROOT.resolve()) or not path.is_file():
        raise HTTPException(status_code=404, detail="Contract document is unavailable.")
    stem = f"employment-contract-{contract.employee.employee_number}"
    suffix = path.suffix
    return FileResponse(path, filename=f"{stem}-{'signed' if copy == 'signed' else 'draft'}{suffix}")


@router.put("/{contract_id}/issue")
def issue_contract(
    contract_id: UUID, request: IssueContract, db: Session = Depends(get_db),
    user: User = Depends(require_hr),
):
    contract = get_contract(db, contract_id)
    if contract.status != "DRAFT":
        raise HTTPException(status_code=409, detail="Only draft contracts can be issued.")
    contract.employer_signature_name = request.employer_signature_name.strip()
    contract.employer_signed_by = user.id
    contract.employer_signed_at = datetime.now(timezone.utc)
    contract.status = "PENDING_EMPLOYEE_SIGNATURE"
    previous_path = contract.generated_file_path
    path = save_generated_contract(db, contract, contract.employee)
    try:
        db.commit()
    except Exception:
        db.rollback()
        path.unlink(missing_ok=True)
        raise
    remove_obsolete_file(contract, previous_path)
    return {"message": "Contract issued for the employee's review and signature.", "contract": contract_payload(contract)}


@router.post("/{contract_id}/sign")
def sign_contract(
    contract_id: UUID, request: EmployeeContractSignature, db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    contract = get_contract(db, contract_id)
    if not user.employee_id or user.employee_id != contract.employee_id:
        raise HTTPException(status_code=403, detail="Only the employee named in this contract can sign it.")
    if contract.status != "PENDING_EMPLOYEE_SIGNATURE":
        raise HTTPException(status_code=409, detail="This contract is not awaiting your signature.")
    if not request.accepted:
        raise HTTPException(status_code=422, detail="Confirm that you have read and agree to the contract.")
    if request.employee_signature_name.strip().casefold() != employee_name(contract.employee).casefold():
        raise HTTPException(status_code=422, detail="Enter your full name as it appears on your employee profile.")
    contract.employee_signature_name = request.employee_signature_name.strip()
    contract.employee_signed_by = user.id
    contract.employee_signed_at = datetime.now(timezone.utc)
    contract.signing_method = "DIGITAL"
    contract.status = "SIGNED"
    previous_path = contract.generated_file_path
    path = save_generated_contract(db, contract, contract.employee)
    contract.signed_file_path = contract.generated_file_path
    hr_users = db.query(User).filter(User.is_active.is_(True), User.role.in_(HR_ROLES)).all()
    for recipient in hr_users:
        db.add(Notification(
            recipient_user_id=recipient.id, sender_user_id=user.id, type="CONTRACT_SIGNED",
            title="Employee signed an employment contract",
            message=f"{employee_name(contract.employee)} signed their {contract.contract_type.lower()} contract.",
            details={"contract_id": str(contract.id), "employee_id": str(contract.employee_id),
                     "employee_name": employee_name(contract.employee),
                     "department": (
                         canonical_department_name(contract.employee.department.code) or contract.employee.department.name
                         if contract.employee.department else "Unassigned"
                     )},
            is_read=False,
        ))
    try:
        db.commit()
    except Exception:
        db.rollback()
        path.unlink(missing_ok=True)
        raise
    remove_obsolete_file(contract, previous_path)
    return {"message": "Your contract has been signed and is available to download.", "contract": contract_payload(contract)}


@router.post("/{contract_id}/signed-copy")
async def upload_signed_contract(
    contract_id: UUID, file: UploadFile = File(...), db: Session = Depends(get_db),
    user: User = Depends(require_hr),
):
    contract = get_contract(db, contract_id)
    if contract.status not in {"DRAFT", "PENDING_EMPLOYEE_SIGNATURE", "SIGNED", "ACTIVE"}:
        raise HTTPException(status_code=409, detail="This contract cannot accept a signed copy.")
    suffix = Path(file.filename or "").suffix.lower()
    if suffix not in UPLOAD_TYPES:
        raise HTTPException(status_code=415, detail="Upload a PDF, DOC, DOCX, PNG, JPG, or JPEG signed contract.")
    data = await file.read(MAX_UPLOAD_SIZE + 1)
    if not data or len(data) > MAX_UPLOAD_SIZE:
        raise HTTPException(status_code=413, detail="Signed contract must be smaller than 20 MB.")
    CONTRACT_ROOT.mkdir(parents=True, exist_ok=True)
    path = CONTRACT_ROOT / f"contract-{contract.id}-signed-{uuid.uuid4()}{suffix}"
    path.write_bytes(data)
    previous_path = contract.signed_file_path
    contract.signed_file_path = path.relative_to(CONTRACT_ROOT.parents[1]).as_posix()
    contract.signing_method = "MANUAL"
    contract.status = "SIGNED"
    directory_document(
        db, contract, contract_document_type(contract, " signed copy"),
        contract.signed_file_path, Path(file.filename or path.name).name, "SIGNED", user,
    )
    try:
        db.commit()
    except Exception:
        db.rollback()
        path.unlink(missing_ok=True)
        raise
    remove_obsolete_file(contract, previous_path)
    return {"message": "Signed contract uploaded and stored in the employee directory.", "contract": contract_payload(contract)}


@router.put("/{contract_id}/activate")
def activate_contract(contract_id: UUID, db: Session = Depends(get_db), _user: User = Depends(require_hr)):
    contract = get_contract(db, contract_id)
    if contract.status != "SIGNED":
        raise HTTPException(status_code=409, detail="Only signed contracts can be activated.")
    contract.status = "ACTIVE"
    db.commit()
    return {"message": "Signed contract activated.", "contract": contract_payload(contract)}
