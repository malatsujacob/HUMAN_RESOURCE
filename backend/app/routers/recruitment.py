import hashlib
import logging
import os
import secrets
import smtplib
import ssl
import uuid
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
from email.message import EmailMessage
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session, joinedload

from app.database import SessionLocal
from app.models.department import Department
from app.models.employee import Employee
from app.models.employee_document import EmployeeDocument
from app.models.recruitment import Candidate, JobRequisition
from app.models.user import User
from app.routers.attendance import get_current_user
from app.constants.departments import (
    canonical_department_code,
    canonical_department_name,
)

router = APIRouter()
logger = logging.getLogger(__name__)
HR_ROLES = {"HR", "HR_ADMIN", "ADMIN", "MANAGEMENT", "DEVELOPER"}
UPLOAD_ROOT = Path(__file__).resolve().parents[3] / "uploads" / "cvs"
MAX_CV_SIZE = 5 * 1024 * 1024
ALLOWED_CV_SUFFIXES = {".pdf", ".doc", ".docx"}
EDUCATION_RANK = {
    "certificate": 1,
    "diploma": 2,
    "bachelor": 3,
    "master": 4,
    "phd": 5,
    "doctorate": 5,
}


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


def require_requisition_creator(user: User = Depends(get_current_user)) -> User:
    if (user.role or "").upper() not in HR_ROLES | {"HOD"}:
        raise HTTPException(status_code=403, detail="HOD or HR access is required.")
    if user.role.upper() == "HOD" and (not user.employee or not user.employee.department_id):
        raise HTTPException(status_code=403, detail="Your HOD account must be linked to a department.")
    return user


class RequisitionCreate(BaseModel):
    department_code: str = Field(min_length=1, max_length=30)
    job_title: str = Field(min_length=1, max_length=100)
    min_education: str = Field(min_length=1, max_length=50)
    min_experience: int = Field(ge=0)
    description: str = Field(min_length=1)
    max_applicants: int = Field(default=50, ge=1)


class RequisitionStatusUpdate(BaseModel):
    status: str
    max_applicants: Optional[int] = Field(default=None, ge=1)


class PublicApplyCreate(BaseModel):
    requisition_id: uuid.UUID
    first_name: str = Field(min_length=1, max_length=100)
    last_name: str = Field(min_length=1, max_length=100)
    email: str = Field(min_length=3, max_length=100)
    phone_number: str = Field(min_length=1, max_length=30)
    education_level: str = Field(min_length=1, max_length=50)
    experience_years: int = Field(ge=0)
    cover_letter: str = Field(min_length=1)


class InterviewUpdate(BaseModel):
    interview_date: datetime
    interviewer_name: str = Field(min_length=1, max_length=100)
    location: str = Field(min_length=1, max_length=255)


class GradeUpdate(BaseModel):
    grade: str
    reason: Optional[str] = None


class OfferUpdate(BaseModel):
    status: str
    requirements: Optional[str] = None
    salary: Optional[Decimal] = Field(default=None, ge=0)
    required_documents: Optional[str] = None
    reason: Optional[str] = None


class OfferResponse(BaseModel):
    reason: Optional[str] = None


class StatusUpdate(BaseModel):
    status: str
    reason: Optional[str] = None


class BulkEmail(BaseModel):
    candidate_ids: list[uuid.UUID] = Field(min_length=1)
    email_type: str
    subject: str = Field(min_length=1, max_length=200)
    message: str = Field(min_length=1)


def send_candidate_email(candidate: Candidate, subject: str, body: str) -> bool:
    host = os.getenv("SMTP_HOST")
    sender = os.getenv("SMTP_FROM")
    if not host or not sender:
        logger.warning("Email not sent to %s: SMTP_HOST and SMTP_FROM are required.", candidate.email)
        return False

    message = EmailMessage()
    message["From"] = sender
    message["To"] = candidate.email
    message["Subject"] = subject
    message.set_content(body)

    try:
        port = int(os.getenv("SMTP_PORT", "587"))
        username = os.getenv("SMTP_USERNAME")
        password = os.getenv("SMTP_PASSWORD")
        with smtplib.SMTP(host, port, timeout=20) as server:
            server.starttls(context=ssl.create_default_context())
            if username and password:
                server.login(username, password)
            server.send_message(message)
    except (OSError, smtplib.SMTPException, ValueError):
        logger.exception("Could not send recruitment email to %s.", candidate.email)
        return False
    return True


def requisition_payload(requisition: JobRequisition) -> dict:
    return {
        "id": requisition.id,
        "department_id": requisition.department_id,
        "department_code": (
            canonical_department_code(requisition.department.code)
            if requisition.department else None
        ),
        "department_name": (
            canonical_department_name(requisition.department.code)
            if requisition.department else None
        ),
        "job_title": requisition.job_title,
        "min_education": requisition.min_education,
        "min_experience": requisition.min_experience,
        "description": requisition.description,
        "status": requisition.status,
        "max_applicants": requisition.max_applicants,
    }


def candidate_payload(candidate: Candidate) -> dict:
    return {
        "id": candidate.id,
        "requisition_id": candidate.requisition_id,
        "job_title": candidate.requisition.job_title if candidate.requisition else None,
        "first_name": candidate.first_name,
        "last_name": candidate.last_name,
        "email": candidate.email,
        "phone_number": candidate.phone_number,
        "education_level": candidate.education_level,
        "experience_years": candidate.experience_years,
        "cover_letter": candidate.cover_letter,
        "has_cv": bool(candidate.cv_path),
        "status": candidate.status,
        "interview_grade": candidate.interview_grade,
        "interview_date": candidate.interview_date,
        "interviewer_name": candidate.interviewer_name,
        "interview_location": candidate.interview_location,
        "offer_salary": candidate.offer_salary,
        "onboarding_requirements": candidate.onboarding_requirements,
        "offer_expires_at": candidate.offer_expires_at,
        "offer_accepted_at": candidate.offer_accepted_at,
        "rejection_reason": candidate.rejection_reason,
        "rejection_type": candidate.rejection_type,
        "employee_id": candidate.employee_id,
        "onboarding_documents_required": (candidate.onboarding_documents_required or "").splitlines(),
    }


def create_candidate(
    req: PublicApplyCreate,
    db: Session,
    cv_path: Optional[str] = None,
) -> tuple[Candidate, str]:
    if not PORTAL_IS_OPEN:
        raise HTTPException(status_code=403, detail="The application portal is currently closed.")

    job = db.query(JobRequisition).filter(JobRequisition.id == req.requisition_id).with_for_update().first()
    if not job or job.status != "APPROVED":
        raise HTTPException(status_code=404, detail="This job is not accepting applications.")

    current_applicants = db.query(Candidate).filter(Candidate.requisition_id == job.id).count()
    if current_applicants >= (job.max_applicants or 50):
        raise HTTPException(status_code=403, detail="Application portal closed: Maximum number of applicants reached.")

    rejection_reasons = []
    if req.experience_years < (job.min_experience or 0):
        rejection_reasons.append(f"Requires {job.min_experience} years of experience.")
    candidate_education = EDUCATION_RANK.get(req.education_level.strip().lower())
    required_education = EDUCATION_RANK.get((job.min_education or "").strip().lower())
    if candidate_education is not None and required_education is not None:
        if candidate_education < required_education:
            rejection_reasons.append(f"Requires at least {job.min_education} education.")
    elif req.education_level.strip().lower() != (job.min_education or "").strip().lower():
        rejection_reasons.append(f"Requires {job.min_education} education.")

    rejected = bool(rejection_reasons)
    candidate = Candidate(
        requisition_id=job.id,
        first_name=req.first_name.strip(),
        last_name=req.last_name.strip(),
        email=req.email.strip(),
        phone_number=req.phone_number.strip(),
        education_level=req.education_level.strip(),
        experience_years=req.experience_years,
        cover_letter=req.cover_letter.strip(),
        cv_path=cv_path,
        status="REJECTED" if rejected else "IN_PIPELINE",
        rejection_type="NOT_QUALIFIED" if rejected else None,
        rejection_reason=" ".join(rejection_reasons) if rejected else None,
    )
    db.add(candidate)
    db.commit()
    db.refresh(candidate)
    return candidate, "REJECTED" if rejected else "IN_PIPELINE"


def send_application_rejection(candidate: Candidate) -> bool:
    job_title = candidate.requisition.job_title if candidate.requisition else "the position"
    return send_candidate_email(
        candidate,
        "Update on your job application",
        f"Dear {candidate.first_name},\n\nThank you for applying for {job_title}. "
        f"We are unable to proceed because: {candidate.rejection_reason}\n\nRegards,\nHuman Resources",
    )


def find_candidate(candidate_id: uuid.UUID, db: Session) -> Candidate:
    candidate = (
        db.query(Candidate)
        .options(joinedload(Candidate.requisition))
        .filter(Candidate.id == candidate_id)
        .first()
    )
    if candidate is None:
        raise HTTPException(status_code=404, detail="Candidate not found.")
    return candidate


def find_candidate_by_offer_token(token: str, db: Session) -> Candidate:
    token_hash = hashlib.sha256(token.encode("utf-8")).hexdigest()
    candidate = (
        db.query(Candidate)
        .options(joinedload(Candidate.requisition))
        .filter(Candidate.offer_response_token_hash == token_hash)
        .with_for_update()
        .first()
    )
    if not candidate or candidate.status != "OFFERED":
        raise HTTPException(status_code=404, detail="This offer link is invalid or has already been used.")
    if candidate.offer_expires_at:
        expiry = candidate.offer_expires_at
        if expiry.tzinfo is None:
            expiry = expiry.replace(tzinfo=timezone.utc)
        if expiry <= datetime.now(timezone.utc):
            raise HTTPException(status_code=410, detail="This offer link has expired. Please contact Human Resources.")
    return candidate


# In-memory toggle for the public application portal.
PORTAL_IS_OPEN = True


@router.post("/toggle-portal")
def toggle_portal(_user: User = Depends(require_hr)):
    global PORTAL_IS_OPEN
    PORTAL_IS_OPEN = not PORTAL_IS_OPEN
    return {"portal_is_open": PORTAL_IS_OPEN}


@router.get("/portal-status")
def portal_status():
    return {"portal_is_open": PORTAL_IS_OPEN}


@router.post("/requisitions")
def create_requisition(req: RequisitionCreate, db: Session = Depends(get_db), user: User = Depends(require_requisition_creator)):
    department_code = req.department_code
    if user.role.upper() == "HOD":
        department = db.query(Department).filter(Department.id == user.employee.department_id).first()
        department_code = canonical_department_code(department.code) if department else ""
    department_code = canonical_department_code(department_code)
    dept = db.query(Department).filter(Department.code == department_code).first()
    if not dept:
        raise HTTPException(status_code=400, detail="Department not found.")
    new_req = JobRequisition(
        department_id=dept.id,
        job_title=req.job_title.strip(),
        min_education=req.min_education.strip(),
        min_experience=req.min_experience,
        description=req.description.strip(),
        max_applicants=req.max_applicants,
        status="PENDING_HR",
    )
    db.add(new_req)
    db.commit()
    db.refresh(new_req)
    return {"message": "Requisition submitted for HR approval.", "id": new_req.id}


@router.get("/requisitions")
def get_requisitions(db: Session = Depends(get_db), _user: User = Depends(require_hr)):
    requisitions = (
        db.query(JobRequisition)
        .options(joinedload(JobRequisition.department))
        .order_by(JobRequisition.job_title)
        .all()
    )
    return [requisition_payload(item) for item in requisitions]


@router.get("/requisitions/active")
def get_active_requisitions(db: Session = Depends(get_db)):
    if not PORTAL_IS_OPEN:
        return []
    requisitions = (
        db.query(JobRequisition)
        .options(joinedload(JobRequisition.department))
        .filter(JobRequisition.status == "APPROVED")
        .order_by(JobRequisition.job_title)
        .all()
    )
    return [
        requisition_payload(item)
        for item in requisitions
        if db.query(Candidate).filter(Candidate.requisition_id == item.id).count()
        < (item.max_applicants or 50)
    ]


@router.patch("/requisitions/{requisition_id}/status")
def update_requisition_status(
    requisition_id: uuid.UUID,
    update: RequisitionStatusUpdate,
    db: Session = Depends(get_db),
    _user: User = Depends(require_hr),
):
    requisition = db.query(JobRequisition).filter(JobRequisition.id == requisition_id).first()
    if not requisition:
        raise HTTPException(status_code=404, detail="Requisition not found.")
    if update.status not in {"APPROVED", "REJECTED"}:
        raise HTTPException(status_code=422, detail="Status must be APPROVED or REJECTED.")
    if requisition.status != "PENDING_HR":
        raise HTTPException(status_code=409, detail="Only pending requisitions can be reviewed.")
    if update.status == "APPROVED":
        if update.max_applicants is None:
            raise HTTPException(status_code=422, detail="Set the applicant limit before publishing this job.")
        requisition.max_applicants = update.max_applicants
    requisition.status = update.status
    db.commit()
    return {"message": f"Requisition {update.status.lower()}.", "status": requisition.status}


@router.post("/apply")
def apply_for_job(req: PublicApplyCreate, db: Session = Depends(get_db)):
    candidate, status = create_candidate(req, db)
    if status == "REJECTED":
        email_sent = send_application_rejection(candidate)
        return {
            "message": "Application received, but it does not meet the minimum job requirements.",
            "status": status,
            "email_sent": email_sent,
        }
    return {"message": "Application submitted successfully.", "status": status}


@router.post("/apply-with-cv")
async def apply_for_job_with_cv(
    application: str = Form(...),
    cv: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    try:
        req = PublicApplyCreate.model_validate_json(application)
    except ValueError as error:
        raise HTTPException(status_code=422, detail="Application details are invalid.") from error

    suffix = Path(cv.filename or "").suffix.lower()
    if suffix not in ALLOWED_CV_SUFFIXES:
        raise HTTPException(status_code=400, detail="CV must be a PDF, DOC, or DOCX file.")
    contents = await cv.read(MAX_CV_SIZE + 1)
    if not contents or len(contents) > MAX_CV_SIZE:
        raise HTTPException(status_code=400, detail="CV must be smaller than 5 MB.")

    UPLOAD_ROOT.mkdir(parents=True, exist_ok=True)
    cv_path = UPLOAD_ROOT / f"{uuid.uuid4()}{suffix}"
    cv_path.write_bytes(contents)
    relative_path = cv_path.relative_to(UPLOAD_ROOT.parents[1]).as_posix()
    try:
        candidate, status = create_candidate(req, db, relative_path)
    except (HTTPException, SQLAlchemyError):
        cv_path.unlink(missing_ok=True)
        raise
    email_sent = send_application_rejection(candidate) if status == "REJECTED" else None
    message = (
        "Application received, but it does not meet the minimum job requirements."
        if status == "REJECTED"
        else "Application submitted successfully."
    )
    return {"message": message, "status": status, "email_sent": email_sent, "candidate_id": candidate.id}


@router.get("/candidates")
def get_candidates(db: Session = Depends(get_db), _user: User = Depends(require_hr)):
    candidates = (
        db.query(Candidate)
        .options(joinedload(Candidate.requisition))
        .filter(Candidate.status == "IN_PIPELINE")
        .order_by(Candidate.last_name, Candidate.first_name)
        .all()
    )
    return [candidate_payload(item) for item in candidates]


@router.get("/candidates/all")
def get_all_candidates(db: Session = Depends(get_db), _user: User = Depends(require_hr)):
    candidates = (
        db.query(Candidate)
        .options(joinedload(Candidate.requisition))
        .order_by(Candidate.last_name, Candidate.first_name)
        .all()
    )
    return [candidate_payload(item) for item in candidates]


@router.get("/candidates/{candidate_id}/cv")
def download_candidate_cv(candidate_id: uuid.UUID, db: Session = Depends(get_db), _user: User = Depends(require_hr)):
    candidate = find_candidate(candidate_id, db)
    if not candidate.cv_path:
        raise HTTPException(status_code=404, detail="No CV was uploaded for this candidate.")
    cv_path = (UPLOAD_ROOT.parents[1] / candidate.cv_path).resolve()
    if not cv_path.is_relative_to(UPLOAD_ROOT.resolve()) or not cv_path.is_file():
        raise HTTPException(status_code=404, detail="Candidate CV could not be found.")
    return FileResponse(cv_path, filename=f"{candidate.first_name}-{candidate.last_name}-CV{cv_path.suffix}")


@router.put("/candidates/{candidate_id}/status")
def update_candidate_status(
    candidate_id: uuid.UUID,
    update: StatusUpdate,
    db: Session = Depends(get_db),
    _user: User = Depends(require_hr),
):
    candidate = find_candidate(candidate_id, db)
    if update.status != "REJECTED":
        raise HTTPException(status_code=422, detail="Only rejection is supported by this action.")
    if candidate.status != "IN_PIPELINE":
        raise HTTPException(status_code=409, detail="Only active pipeline candidates can be rejected here.")
    candidate.status = "REJECTED"
    candidate.rejection_type = "PIPELINE_REJECTED"
    candidate.rejection_reason = (update.reason or "Rejected by HR.").strip()
    email_sent = send_application_rejection(candidate)
    db.commit()
    return {"message": "Candidate rejected.", "email_sent": email_sent}


@router.put("/candidates/{candidate_id}/interview")
def schedule_interview(
    candidate_id: uuid.UUID,
    req: InterviewUpdate,
    db: Session = Depends(get_db),
    _user: User = Depends(require_hr),
):
    candidate = find_candidate(candidate_id, db)
    if candidate.status != "IN_PIPELINE":
        raise HTTPException(status_code=409, detail="Only active pipeline candidates can be scheduled.")
    candidate.status = "INTERVIEW_SCHEDULED"
    candidate.interview_date = req.interview_date
    candidate.interviewer_name = req.interviewer_name.strip()
    candidate.interview_location = req.location.strip()
    job_title = candidate.requisition.job_title if candidate.requisition else "the position"
    email_sent = send_candidate_email(
        candidate,
        f"Interview invitation: {job_title}",
        f"Dear {candidate.first_name},\n\nYou are invited to interview for {job_title}.\n"
        f"Date and time: {req.interview_date:%d %B %Y, %H:%M}\n"
        f"Interviewer: {req.interviewer_name}\nLocation: {req.location}\n\nRegards,\nHuman Resources",
    )
    db.commit()
    return {"message": "Interview scheduled.", "email_sent": email_sent}


@router.put("/candidates/{candidate_id}/grade")
def grade_candidate(
    candidate_id: uuid.UUID,
    update: GradeUpdate,
    db: Session = Depends(get_db),
    _user: User = Depends(require_hr),
):
    candidate = find_candidate(candidate_id, db)
    if candidate.status != "INTERVIEW_SCHEDULED":
        raise HTTPException(status_code=409, detail="Only scheduled interviews can be graded.")
    grade = update.grade.strip().upper()
    if grade not in {"OUTSTANDING", "PASSED", "FAILED"}:
        raise HTTPException(status_code=422, detail="Grade must be OUTSTANDING, PASSED, or FAILED.")
    if grade == "FAILED" and not (update.reason and update.reason.strip()):
        raise HTTPException(status_code=422, detail="A reason is required for a failed interview result.")
    candidate.interview_grade = grade
    if grade == "FAILED":
        candidate.status = "REJECTED"
        candidate.rejection_type = "INTERVIEW_FAILED"
        candidate.rejection_reason = (update.reason or "Did not meet the interview requirements.").strip()
        email_sent = send_candidate_email(
            candidate,
            "Update on your interview",
            f"Dear {candidate.first_name},\n\nThank you for interviewing for "
            f"{candidate.requisition.job_title if candidate.requisition else 'the position'}. "
            f"We regret to inform you that you were not selected.\n\nFeedback: {candidate.rejection_reason}\n\nRegards,\nHuman Resources",
        )
    else:
        candidate.status = "PASSED"
        candidate.rejection_reason = None
        job_title = candidate.requisition.job_title if candidate.requisition else "the position"
        email_sent = send_candidate_email(
            candidate,
            f"Interview result: {grade.title()}",
            f"Dear {candidate.first_name},\n\nCongratulations on your {grade.lower()} interview result for {job_title}. "
            "Human Resources will be in touch with the next steps regarding an employment offer.\n\nRegards,\nHuman Resources",
        )
    db.commit()
    return {"message": "Interview grade recorded.", "email_sent": email_sent}


@router.put("/candidates/{candidate_id}/offer")
def handle_offer(
    candidate_id: uuid.UUID,
    update: OfferUpdate,
    db: Session = Depends(get_db),
    _user: User = Depends(require_hr),
):
    candidate = find_candidate(candidate_id, db)
    if update.status == "OFFERED":
        if candidate.status not in {"PASSED", "OFFERED"}:
            raise HTTPException(status_code=409, detail="Only candidates who passed can receive offers.")
        if not update.requirements or not update.requirements.strip():
            raise HTTPException(status_code=422, detail="Onboarding requirements are required.")
        candidate.status = "OFFERED"
        candidate.onboarding_requirements = update.requirements.strip()
        docs = [line.strip(" -•\t") for line in (update.required_documents or "").splitlines() if line.strip(" -•\t")]
        candidate.onboarding_documents_required = "\n".join(dict.fromkeys(docs))
        candidate.offer_salary = update.salary
        token = secrets.token_urlsafe(32)
        candidate.offer_response_token_hash = hashlib.sha256(token.encode("utf-8")).hexdigest()
        candidate.offer_expires_at = datetime.now(timezone.utc) + timedelta(days=14)
        job_title = candidate.requisition.job_title if candidate.requisition else "the position"
        salary_text = f"\nProposed salary: UGX {update.salary:,.0f}" if update.salary is not None else ""
        frontend_url = os.getenv("FRONTEND_URL", "http://localhost:5173").rstrip("/")
        response_url = f"{frontend_url}/offer-response?token={token}"
        documents_text = "\n".join(f"- {name}" for name in docs) or "To be confirmed by Human Resources"
        email_sent = send_candidate_email(
            candidate,
            f"Offer of employment: {job_title}",
            f"Dear {candidate.first_name},\n\nWe are pleased to offer you the role of {job_title}."
            f"{salary_text}\n\nOnboarding instructions:\n{update.requirements.strip()}\n\n"
            f"Documents to submit:\n{documents_text}\n\n"
            f"Review and respond to this offer by {candidate.offer_expires_at:%d %B %Y}:\n{response_url}\n\n"
            "After you accept, Human Resources will contact you to complete onboarding.\n\n"
            "Regards,\nHuman Resources",
        )
    elif update.status == "DECLINED":
        if candidate.status != "OFFERED":
            raise HTTPException(status_code=409, detail="Only candidates with an active offer can decline it.")
        if not update.reason or not update.reason.strip():
            raise HTTPException(status_code=422, detail="A reason is required when an offer is declined.")
        candidate.status = "REJECTED"
        candidate.rejection_type = "OFFER_FAILED"
        candidate.rejection_reason = update.reason.strip()
        candidate.offer_response_token_hash = None
        candidate.offer_expires_at = None
        email_sent = False
    else:
        raise HTTPException(status_code=422, detail="Status must be OFFERED or DECLINED.")
    db.commit()
    return {"message": f"Offer {update.status.lower()}.", "email_sent": email_sent}


@router.post("/offers/{token}/accept")
def accept_offer(token: str, db: Session = Depends(get_db)):
    candidate = find_candidate_by_offer_token(token, db)
    if candidate.employee_id is not None:
        raise HTTPException(status_code=409, detail="An employee record already exists for this offer.")

    employee = Employee(
        id=uuid.uuid4(),
        employee_number=f"EMP-{uuid.uuid4().hex[:8].upper()}",
        first_name=candidate.first_name,
        last_name=candidate.last_name,
        personal_email=candidate.email,
        phone_number=candidate.phone_number,
        job_title=candidate.requisition.job_title if candidate.requisition else "New Hire",
        department_id=candidate.requisition.department_id if candidate.requisition else None,
        base_salary=candidate.offer_salary,
        status="ONBOARDING",
    )
    db.add(employee)
    db.flush()

    required_documents = [
        item.strip() for item in (candidate.onboarding_documents_required or "").splitlines() if item.strip()
    ] or ["National ID (NIN)", "Education certificates", "TIN details", "Bank account proof", "NSSF details"]
    for document_type in required_documents:
        db.add(EmployeeDocument(employee_id=employee.id, document_type=document_type, status="MISSING"))

    onboarding_token = secrets.token_urlsafe(32)
    candidate.status = "HIRED"
    candidate.employee_id = employee.id
    candidate.offer_accepted_at = datetime.now(timezone.utc)
    candidate.offer_response_token_hash = None
    candidate.offer_expires_at = None
    candidate.onboarding_token_hash = hashlib.sha256(onboarding_token.encode("utf-8")).hexdigest()
    candidate.onboarding_expires_at = datetime.now(timezone.utc) + timedelta(days=30)
    db.commit()

    frontend_url = os.getenv("FRONTEND_URL", "http://localhost:5173").rstrip("/")
    onboarding_url = f"{frontend_url}/onboarding-response?token={onboarding_token}"
    email_sent = send_candidate_email(
        candidate,
        "Congratulations — offer accepted",
        f"Dear {candidate.first_name},\n\nCongratulations, and thank you for accepting our offer for "
        f"{candidate.requisition.job_title if candidate.requisition else 'the position'}. "
        f"Your employee record ({employee.employee_number}) has been created.\n\n"
        "Please complete your personal details and upload the requested documents using this secure link:\n"
        f"{onboarding_url}\n\nThe link is available for 30 days. Human Resources will review your submission and contact you if anything is missing.\n\n"
        "Regards,\nHuman Resources",
    )
    return {
        "message": "Offer accepted. Your employee record is ready for onboarding.",
        "email_sent": email_sent,
        "employee_id": str(employee.id),
        "employee_number": employee.employee_number,
        "onboarding_url": onboarding_url,
    }


@router.post("/offers/{token}/decline")
def decline_offer(token: str, update: OfferResponse, db: Session = Depends(get_db)):
    candidate = find_candidate_by_offer_token(token, db)
    candidate.status = "REJECTED"
    if not update.reason or not update.reason.strip():
        raise HTTPException(status_code=422, detail="A reason is required when declining an offer.")
    candidate.rejection_type = "OFFER_FAILED"
    candidate.rejection_reason = update.reason.strip()
    candidate.offer_response_token_hash = None
    candidate.offer_expires_at = None
    db.commit()
    email_sent = send_candidate_email(
        candidate,
        "Offer response received",
        f"Dear {candidate.first_name},\n\nWe have recorded your decision regarding our offer "
        f"for {candidate.requisition.job_title if candidate.requisition else 'the position'}. "
        "Thank you for letting us know.\n\nRegards,\nHuman Resources",
    )
    return {"message": "Your decision has been recorded.", "email_sent": email_sent}


@router.post("/send-email")
def send_bulk_email(req: BulkEmail, db: Session = Depends(get_db), _user: User = Depends(require_hr)):
    candidates = (
        db.query(Candidate)
        .filter(Candidate.id.in_(req.candidate_ids))
        .all()
    )
    if len(candidates) != len(set(req.candidate_ids)):
        raise HTTPException(status_code=404, detail="One or more selected candidates could not be found.")
    sent_count = 0
    for candidate in candidates:
        body = req.message.replace("{{first_name}}", candidate.first_name or "")
        body = body.replace("{{job_title}}", candidate.requisition.job_title if candidate.requisition else "the position")
        if send_candidate_email(candidate, req.subject, body):
            sent_count += 1
    return {
        "message": f"Email sent to {sent_count} of {len(candidates)} selected candidates.",
        "sent_count": sent_count,
        "failed_count": len(candidates) - sent_count,
    }
