import hashlib
import json
import os
import secrets
import uuid
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session, joinedload

from app.database import SessionLocal, get_password_hash
from app.models.employee import Employee
from app.models.employee_document import EmployeeDocument
from app.models.recruitment import Candidate
from app.models.user import User
from app.constants.departments import canonical_department_name
from app.routers.attendance import get_current_user
from app.routers.recruitment import send_candidate_email

router = APIRouter()
UPLOAD_ROOT = Path(__file__).resolve().parents[3] / "uploads" / "onboarding"
MAX_FILE_SIZE = 10 * 1024 * 1024
ALLOWED_SUFFIXES = {".pdf", ".doc", ".docx", ".csv", ".png", ".jpg", ".jpeg"}
HR_ROLES = {"HR", "HR_ADMIN", "ADMIN", "MANAGEMENT", "DEVELOPER"}


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


class DocumentReview(BaseModel):
    status: str
    note: Optional[str] = None


def candidate_by_onboarding_token(token: str, db: Session) -> Candidate:
    token_hash = hashlib.sha256(token.encode("utf-8")).hexdigest()
    candidate = (
        db.query(Candidate)
        .options(joinedload(Candidate.requisition))
        .filter(Candidate.onboarding_token_hash == token_hash)
        .first()
    )
    # Employee is loaded separately because employee_id is a scalar FK, not a relationship.
    if not candidate or not candidate.employee_id:
        raise HTTPException(status_code=404, detail="This onboarding link is invalid or has already been used.")
    expiry = candidate.onboarding_expires_at
    if expiry and expiry.tzinfo is None:
        expiry = expiry.replace(tzinfo=timezone.utc)
    if not expiry or expiry <= datetime.now(timezone.utc):
        raise HTTPException(status_code=410, detail="This onboarding link has expired. Contact Human Resources.")
    candidate._onboarding_employee = db.query(Employee).filter(Employee.id == candidate.employee_id).first()
    return candidate


def serialize_document(document: EmployeeDocument) -> dict:
    return {
        "id": str(document.id), "document_type": document.document_type,
        "file_name": document.file_name, "status": document.status,
        "review_note": document.review_note, "submitted_at": document.submitted_at,
    }


def serialize_onboarding(candidate: Candidate, db: Session) -> dict:
    employee = db.query(Employee).filter(Employee.id == candidate.employee_id).first()
    docs = db.query(EmployeeDocument).filter(EmployeeDocument.employee_id == candidate.employee_id).order_by(EmployeeDocument.created_at).all()
    return {
        "candidate_id": str(candidate.id), "employee_id": str(employee.id),
        "employee_number": employee.employee_number, "first_name": candidate.first_name,
        "middle_name": employee.middle_name, "last_name": candidate.last_name, "email": candidate.email,
        "phone_number": candidate.phone_number, "job_title": employee.job_title,
        "department_name": (
            canonical_department_name(candidate.requisition.department.code)
            or candidate.requisition.department.name
            if candidate.requisition and candidate.requisition.department else None
        ),
        "status": candidate.status, "documents": [serialize_document(doc) for doc in docs],
        "personal_details": {
            "personal_email": employee.personal_email, "work_email": employee.work_email,
            "middle_name": employee.middle_name, "gender": employee.gender,
            "marital_status": employee.marital_status, "home_address": employee.home_address,
            "father_name": employee.father_name,
            "mother_name": employee.mother_name, "national_id": employee.national_id,
            "tin_number": employee.tin_number, "nssf_number": employee.nssf_number,
            "bank_name": employee.bank_name, "account_number": employee.account_number,
            "account_name": employee.account_name, "bank_code": employee.bank_code,
            "branch_code": employee.branch_code, "payment_method": employee.payment_method,
            "mobile_money_number": employee.mobile_money_number,
            "cacco_number": employee.cacco_number, "cacco_name": employee.cacco_name,
            "next_of_kin_name": employee.next_of_kin_name,
            "next_of_kin_relationship": employee.next_of_kin_relationship,
            "next_of_kin_phone": employee.next_of_kin_phone,
            "next_of_kin_address": employee.next_of_kin_address,
        },
    }


@router.get("/candidate/{token}")
def get_candidate_onboarding(token: str, db: Session = Depends(get_db)):
    candidate = candidate_by_onboarding_token(token, db)
    return serialize_onboarding(candidate, db)


@router.post("/candidate/{token}/submit")
async def submit_candidate_onboarding(
    token: str,
    application: str = Form(...),
    document_types: list[str] = Form(default=[]),
    documents: list[UploadFile] = File(default=[]),
    db: Session = Depends(get_db),
):
    candidate = candidate_by_onboarding_token(token, db)
    if candidate.status != "HIRED":
        raise HTTPException(status_code=409, detail="This onboarding submission has already been completed.")
    try:
        details = json.loads(application)
    except (TypeError, json.JSONDecodeError) as exc:
        raise HTTPException(status_code=422, detail="Personal details are invalid.") from exc
    employee = db.query(Employee).filter(Employee.id == candidate.employee_id).first()
    editable = {
        "middle_name", "personal_email", "work_email", "phone_number", "home_address",
        "gender", "marital_status", "father_name", "mother_name",
        "national_id", "tin_number", "nssf_number", "bank_name", "account_number",
        "next_of_kin_name", "next_of_kin_relationship", "next_of_kin_phone", "next_of_kin_address",
    }
    for key, value in details.items():
        if key in editable:
            setattr(employee, key, str(value).strip() if value is not None else None)

    if len(documents) != len(document_types):
        raise HTTPException(status_code=422, detail="Each uploaded file must have a selected document type.")
    UPLOAD_ROOT.mkdir(parents=True, exist_ok=True)
    written_paths = []
    try:
        for doc_type, upload in zip(document_types, documents):
            doc_type = doc_type.strip()
            if not doc_type:
                raise HTTPException(status_code=422, detail="Document type cannot be blank.")
            suffix = Path(upload.filename or "").suffix.lower()
            if suffix not in ALLOWED_SUFFIXES:
                raise HTTPException(status_code=400, detail="Documents must be PDF, DOC, DOCX, CSV, PNG, JPG, or JPEG files.")
            contents = await upload.read(MAX_FILE_SIZE + 1)
            if not contents or len(contents) > MAX_FILE_SIZE:
                raise HTTPException(status_code=400, detail="Each document must be smaller than 10 MB.")
            stored = UPLOAD_ROOT / f"{uuid.uuid4()}{suffix}"
            stored.write_bytes(contents)
            written_paths.append(stored)
            row = db.query(EmployeeDocument).filter(
                EmployeeDocument.employee_id == employee.id,
                EmployeeDocument.document_type == doc_type,
            ).first()
            if row is None:
                row = EmployeeDocument(employee_id=employee.id, document_type=doc_type)
                db.add(row)
            elif row.file_path:
                old_path = (UPLOAD_ROOT.parents[1] / row.file_path).resolve()
                if old_path.is_relative_to(UPLOAD_ROOT.resolve()):
                    old_path.unlink(missing_ok=True)
            row.file_name = Path(upload.filename or "document").name
            row.file_path = stored.relative_to(UPLOAD_ROOT.parents[1]).as_posix()
            row.status = "SUBMITTED"
            row.review_note = None
            row.submitted_at = datetime.now(timezone.utc)
            row.reviewed_at = None
            row.reviewed_by = None

        db.commit()
    except Exception:
        db.rollback()
        for path in written_paths:
            path.unlink(missing_ok=True)
        raise

    docs = db.query(EmployeeDocument).filter(EmployeeDocument.employee_id == employee.id).all()
    missing = [doc.document_type for doc in docs if doc.status in {"MISSING", "REJECTED"}]
    frontend_url = os.getenv("FRONTEND_URL", "http://localhost:5173").rstrip("/")
    if missing:
        token_next = secrets.token_urlsafe(32)
        candidate.onboarding_token_hash = hashlib.sha256(token_next.encode("utf-8")).hexdigest()
        candidate.onboarding_expires_at = datetime.now(timezone.utc) + timedelta(days=30)
        db.commit()
        link = f"{frontend_url}/onboarding-response?token={token_next}"
        email_sent = send_candidate_email(
            candidate, "Onboarding documents still required",
            f"Dear {candidate.first_name},\n\nWe received your onboarding details. Please submit or replace these documents: "
            f"{', '.join(missing)}.\n\nContinue securely here: {link}\n\nRegards,\nHuman Resources",
        )
    else:
        email_sent = send_candidate_email(candidate, "Onboarding submission received", f"Dear {candidate.first_name},\n\nYour onboarding details and documents were received. Human Resources will review them and contact you if anything else is needed.\n\nRegards,\nHuman Resources")
    return {"message": "Your onboarding details and documents were received.", "missing_documents": missing, "email_sent": email_sent}


@router.get("/pending")
def get_pending_candidates(db: Session = Depends(get_db), _user: User = Depends(require_hr)):
    candidates = (
        db.query(Candidate).join(Employee, Candidate.employee_id == Employee.id)
        .options(joinedload(Candidate.requisition))
        .filter(Candidate.status == "HIRED", Employee.status == "ONBOARDING")
        .order_by(Candidate.offer_accepted_at.desc()).all()
    )
    return [serialize_onboarding(candidate, db) for candidate in candidates]


@router.get("/documents/{document_id}/download")
def download_document(document_id: uuid.UUID, db: Session = Depends(get_db), _user: User = Depends(require_hr)):
    from fastapi.responses import FileResponse
    document = db.query(EmployeeDocument).filter(EmployeeDocument.id == document_id).first()
    if not document or not document.file_path:
        raise HTTPException(status_code=404, detail="Submitted document was not found.")
    path = (UPLOAD_ROOT.parents[1] / document.file_path).resolve()
    if not path.is_relative_to(UPLOAD_ROOT.resolve()) or not path.is_file():
        raise HTTPException(status_code=404, detail="Submitted document was not found.")
    return FileResponse(path, filename=document.file_name or path.name)


@router.put("/{candidate_id}/documents/{document_id}")
def review_document(candidate_id: uuid.UUID, document_id: uuid.UUID, review: DocumentReview, db: Session = Depends(get_db), user: User = Depends(require_hr)):
    candidate = db.query(Candidate).filter(Candidate.id == candidate_id, Candidate.status == "HIRED").first()
    document = db.query(EmployeeDocument).filter(EmployeeDocument.id == document_id).first()
    if not candidate or not document or document.employee_id != candidate.employee_id:
        raise HTTPException(status_code=404, detail="Onboarding document was not found.")
    status = review.status.strip().upper()
    if status not in {"VERIFIED", "REJECTED"}:
        raise HTTPException(status_code=422, detail="Document status must be VERIFIED or REJECTED.")
    if status == "REJECTED" and not (review.note and review.note.strip()):
        raise HTTPException(status_code=422, detail="Provide a reason when rejecting a document.")
    if status == "VERIFIED" and not document.file_path:
        raise HTTPException(status_code=409, detail="A document must be submitted before it can be verified.")
    document.status = status
    document.review_note = review.note.strip() if review.note else None
    document.reviewed_at = datetime.now(timezone.utc)
    document.reviewed_by = user.id
    db.commit()
    if status == "REJECTED":
        token = secrets.token_urlsafe(32)
        candidate.onboarding_token_hash = hashlib.sha256(token.encode("utf-8")).hexdigest()
        candidate.onboarding_expires_at = datetime.now(timezone.utc) + timedelta(days=30)
        db.commit()
        link = f"{os.getenv('FRONTEND_URL', 'http://localhost:5173').rstrip('/')}/onboarding-response?token={token}"
        send_candidate_email(candidate, "Please replace an onboarding document", f"Dear {candidate.first_name},\n\nHuman Resources could not verify {document.document_type}. Reason: {document.review_note}\n\nPlease upload a replacement here: {link}\n\nRegards,\nHuman Resources")
    return {"message": f"Document {status.lower()}.", "document": serialize_document(document)}


@router.post("/{candidate_id}/finalize")
def finalize_onboarding(candidate_id: uuid.UUID, db: Session = Depends(get_db), _user: User = Depends(require_hr)):
    candidate = db.query(Candidate).filter(Candidate.id == candidate_id, Candidate.status == "HIRED").first()
    employee = db.query(Employee).filter(Employee.id == candidate.employee_id).first() if candidate else None
    if not candidate or not employee:
        raise HTTPException(status_code=404, detail="Onboarding record was not found.")
    docs = db.query(EmployeeDocument).filter(EmployeeDocument.employee_id == employee.id).all()
    if not docs or any(doc.status != "VERIFIED" for doc in docs):
        raise HTTPException(status_code=409, detail="All required documents must be submitted and verified first.")
    required_fields = [employee.personal_email, employee.work_email, employee.phone_number,
                       employee.home_address, employee.national_id, employee.tin_number,
                       employee.nssf_number, employee.bank_name, employee.account_number,
                       employee.next_of_kin_name, employee.next_of_kin_relationship,
                       employee.next_of_kin_phone]
    if any(not value or not str(value).strip() for value in required_fields):
        raise HTTPException(status_code=409, detail="Complete all required personal, contact, statutory, and bank details first.")
    employee.hire_date = date.today()
    employee.status = "PROBATION"
    login_email = (employee.work_email or employee.personal_email or "").strip().lower()
    if not login_email:
        raise HTTPException(status_code=409, detail="Add a personal or work email before finalizing the employee record.")
    account = db.query(User).filter(User.employee_id == employee.id).first()
    temporary_password = None
    if account is None:
        if db.query(User).filter(User.email == login_email).first():
            raise HTTPException(status_code=409, detail="That email already belongs to another HRMS account. Resolve it in the Employee Directory first.")
        temporary_password = secrets.token_urlsafe(12)
        db.add(User(email=login_email, password_hash=get_password_hash(temporary_password), role="EMPLOYEE",
                    employee_id=employee.id, is_active=True, must_change_password=True))
    candidate.onboarding_token_hash = None
    candidate.onboarding_expires_at = None
    db.commit()
    send_candidate_email(candidate, "Onboarding completed", f"Dear {candidate.first_name},\n\nYour onboarding review is complete. Welcome to Chap Chap Africa.\n\nRegards,\nHuman Resources")
    return {"message": "Onboarding verified and employee record finalized.", "employee_id": str(employee.id), "employee_number": employee.employee_number, "status": employee.status,
            "login_email": login_email, "temporary_password": temporary_password, "must_change_password": bool(temporary_password)}
