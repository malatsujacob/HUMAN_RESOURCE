from datetime import date, datetime, timezone
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.routers.attendance import get_current_user, get_db
from app.models.disciplinary import DisciplinaryCase, DisciplinaryEvidence, DisciplinaryOutcome
from app.models.employee import Employee
from app.models.user import User
from typing import List
from datetime import date as DateType

router = APIRouter()
HR_ROLES = {"HR", "HR_ADMIN", "ADMIN", "MANAGEMENT", "DEVELOPER"}


class DisciplinaryCaseCreate(BaseModel):
    employee_id: UUID
    incident_date: date
    description: str = Field(min_length=1, max_length=500)
    action_taken: Optional[str] = Field(default=None, max_length=255)

class DisciplinaryCaseResolution(BaseModel):
    resolution_note: str = Field(min_length=5, max_length=1000)


class DisciplinaryCaseResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    employee_id: UUID
    incident_date: date
    description: str
    action_taken: Optional[str]
    status: str
    resolution_note: Optional[str] = None
    resolved_by: Optional[UUID] = None
    resolved_at: Optional[datetime] = None


def require_hr(user: User) -> None:
    if user.role.upper() not in HR_ROLES:
        raise HTTPException(status_code=403, detail="Only HR can manage disciplinary cases")


@router.post("/", response_model=DisciplinaryCaseResponse, status_code=201)
def create_case(
    request: DisciplinaryCaseCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    require_hr(user)
    if db.query(Employee.id).filter(Employee.id == request.employee_id).first() is None:
        raise HTTPException(status_code=404, detail="Employee not found")

    case = DisciplinaryCase(
        employee_id=request.employee_id,
        incident_date=request.incident_date,
        description=request.description.strip(),
        action_taken=request.action_taken.strip() if request.action_taken else None,
        status="OPEN",
    )
    if not case.description:
        raise HTTPException(status_code=422, detail="Description cannot be blank")
    db.add(case)
    try:
        db.commit()
    except SQLAlchemyError:
        db.rollback()
        raise
    db.refresh(case)
    return case


@router.get("/", response_model=list[DisciplinaryCaseResponse])
def list_cases(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    require_hr(user)
    return db.query(DisciplinaryCase).order_by(DisciplinaryCase.incident_date.desc()).all()


@router.put("/{case_id}/resolve", response_model=DisciplinaryCaseResponse)
def resolve_case(
    case_id: UUID,
    request: DisciplinaryCaseResolution,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    require_hr(user)
    case = db.query(DisciplinaryCase).filter(DisciplinaryCase.id == case_id).with_for_update().first()
    if case is None:
        raise HTTPException(status_code=404, detail="Disciplinary case not found.")
    if case.status != "OPEN":
        raise HTTPException(status_code=409, detail="Only open disciplinary cases can be resolved.")
    case.resolution_note = request.resolution_note.strip()
    if not case.resolution_note:
        raise HTTPException(status_code=422, detail="Resolution note cannot be blank.")
    case.status = "RESOLVED"
    case.resolved_by = user.id
    case.resolved_at = datetime.now(timezone.utc)
    try:
        db.commit()
    except SQLAlchemyError:
        db.rollback()
        raise
    db.refresh(case)
    return case


# ===========================================================================
# ENHANCED DISCIPLINARY ENDPOINTS (Step 4)
# ===========================================================================

class EvidenceCreate(BaseModel):
    file_name: str = Field(min_length=1, max_length=255)
    file_path: str = Field(min_length=1, max_length=500)
    file_type: Optional[str] = Field(default=None, max_length=50)
    file_size: Optional[int] = None
    description: Optional[str] = None


class OutcomeCreate(BaseModel):
    outcome_type: str = Field(min_length=1, max_length=30)
    warning_level: Optional[str] = Field(default=None, max_length=20)
    effective_date: Optional[DateType] = None
    expiry_date: Optional[DateType] = None
    suspension_days: Optional[int] = None
    payroll_deduction: bool = False
    deduction_amount: Optional[float] = None
    decision_notes: Optional[str] = None


class AppealUpdate(BaseModel):
    appeal_lodged: bool
    appeal_date: Optional[DateType] = None
    appeal_grounds: Optional[str] = None
    appeal_outcome: Optional[str] = Field(default=None, max_length=30)
    appeal_notes: Optional[str] = None


def evidence_payload(e: DisciplinaryEvidence) -> dict:
    return {
        "id": str(e.id),
        "case_id": str(e.case_id),
        "file_name": e.file_name,
        "file_path": e.file_path,
        "file_type": e.file_type,
        "file_size": e.file_size,
        "description": e.description,
        "uploaded_at": e.uploaded_at.isoformat() if e.uploaded_at else None,
    }


def outcome_payload(o: DisciplinaryOutcome) -> dict:
    return {
        "id": str(o.id),
        "case_id": str(o.case_id),
        "outcome_type": o.outcome_type,
        "warning_level": o.warning_level,
        "effective_date": o.effective_date.isoformat() if o.effective_date else None,
        "expiry_date": o.expiry_date.isoformat() if o.expiry_date else None,
        "suspension_days": o.suspension_days,
        "payroll_deduction": o.payroll_deduction,
        "deduction_amount": float(o.deduction_amount) if o.deduction_amount else None,
        "decision_notes": o.decision_notes,
        "appeal_lodged": o.appeal_lodged,
        "appeal_date": o.appeal_date.isoformat() if o.appeal_date else None,
        "appeal_grounds": o.appeal_grounds,
        "appeal_outcome": o.appeal_outcome,
        "appeal_notes": o.appeal_notes,
        "created_at": o.created_at.isoformat() if o.created_at else None,
    }


@router.get("/analytics")
def disciplinary_analytics(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    require_hr(user)
    from sqlalchemy import func as sql_func
    total = db.query(sql_func.count(DisciplinaryCase.id)).scalar() or 0
    by_status = dict(db.query(DisciplinaryCase.status, sql_func.count(DisciplinaryCase.id)).group_by(DisciplinaryCase.status).all())
    by_category = dict(db.query(DisciplinaryCase.category, sql_func.count(DisciplinaryCase.id)).filter(DisciplinaryCase.category.isnot(None)).group_by(DisciplinaryCase.category).all())
    by_severity = dict(db.query(DisciplinaryCase.severity, sql_func.count(DisciplinaryCase.id)).filter(DisciplinaryCase.severity.isnot(None)).group_by(DisciplinaryCase.severity).all())
    by_type = dict(db.query(DisciplinaryCase.case_type, sql_func.count(DisciplinaryCase.id)).filter(DisciplinaryCase.case_type.isnot(None)).group_by(DisciplinaryCase.case_type).all())
    return {
        "total_cases": total,
        "by_status": by_status,
        "by_category": by_category,
        "by_severity": by_severity,
        "by_type": by_type,
    }


@router.get("/{case_id}")
def get_case_detail(
    case_id: UUID,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    require_hr(user)
    case = db.query(DisciplinaryCase).filter(DisciplinaryCase.id == case_id).first()
    if case is None:
        raise HTTPException(status_code=404, detail="Case not found.")
    result = {
        "id": str(case.id),
        "employee_id": str(case.employee_id),
        "case_number": case.case_number,
        "case_type": case.case_type,
        "category": case.category,
        "severity": case.severity,
        "incident_date": case.incident_date.isoformat() if case.incident_date else None,
        "description": case.description,
        "action_taken": case.action_taken,
        "policy_breached": case.policy_breached,
        "status": case.status,
        "confidential": case.confidential,
        "warning_level": case.warning_level,
        "expires_at": case.expires_at.isoformat() if case.expires_at else None,
        "resolution_note": case.resolution_note,
        "resolved_at": case.resolved_at.isoformat() if case.resolved_at else None,
        "evidence": [evidence_payload(e) for e in case.evidence],
        "outcome": outcome_payload(case.outcome) if case.outcome else None,
    }
    return result


@router.post("/{case_id}/evidence", status_code=201)
def add_evidence(
    case_id: UUID,
    request: EvidenceCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    require_hr(user)
    case = db.query(DisciplinaryCase).filter(DisciplinaryCase.id == case_id).first()
    if case is None:
        raise HTTPException(status_code=404, detail="Case not found.")
    evidence = DisciplinaryEvidence(
        case_id=case_id,
        file_name=request.file_name.strip(),
        file_path=request.file_path.strip(),
        file_type=request.file_type,
        file_size=request.file_size,
        description=request.description,
        uploaded_by_user_id=user.id,
    )
    db.add(evidence)
    db.commit()
    db.refresh(evidence)
    return evidence_payload(evidence)


@router.get("/{case_id}/evidence")
def list_evidence(
    case_id: UUID,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    require_hr(user)
    evidence = db.query(DisciplinaryEvidence).filter(DisciplinaryEvidence.case_id == case_id).order_by(DisciplinaryEvidence.uploaded_at.desc()).all()
    return [evidence_payload(e) for e in evidence]


@router.delete("/evidence/{evidence_id}")
def delete_evidence(
    evidence_id: UUID,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    require_hr(user)
    evidence = db.query(DisciplinaryEvidence).filter(DisciplinaryEvidence.id == evidence_id).first()
    if evidence is None:
        raise HTTPException(status_code=404, detail="Evidence not found.")
    db.delete(evidence)
    db.commit()
    return {"message": "Evidence deleted."}


@router.post("/{case_id}/outcome", status_code=201)
def record_outcome(
    case_id: UUID,
    request: OutcomeCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    require_hr(user)
    case = db.query(DisciplinaryCase).filter(DisciplinaryCase.id == case_id).first()
    if case is None:
        raise HTTPException(status_code=404, detail="Case not found.")
    if case.outcome:
        raise HTTPException(status_code=409, detail="This case already has an outcome. Use appeal to update.")
    outcome = DisciplinaryOutcome(
        case_id=case_id,
        outcome_type=request.outcome_type,
        warning_level=request.warning_level,
        effective_date=request.effective_date,
        expiry_date=request.expiry_date,
        suspension_days=request.suspension_days,
        payroll_deduction=request.payroll_deduction,
        deduction_amount=request.deduction_amount,
        decision_by_user_id=user.id,
        decision_notes=request.decision_notes,
    )
    db.add(outcome)
    case.status = "RESOLVED"
    case.resolved_by = user.id
    case.resolved_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(outcome)
    return outcome_payload(outcome)


@router.put("/{case_id}/appeal")
def update_appeal(
    case_id: UUID,
    request: AppealUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    require_hr(user)
    case = db.query(DisciplinaryCase).filter(DisciplinaryCase.id == case_id).first()
    if case is None:
        raise HTTPException(status_code=404, detail="Case not found.")
    if not case.outcome:
        raise HTTPException(status_code=409, detail="Cannot record appeal without an outcome.")
    outcome = case.outcome
    outcome.appeal_lodged = request.appeal_lodged
    if request.appeal_date:
        outcome.appeal_date = request.appeal_date
    if request.appeal_grounds:
        outcome.appeal_grounds = request.appeal_grounds
    if request.appeal_outcome:
        outcome.appeal_outcome = request.appeal_outcome
    if request.appeal_notes:
        outcome.appeal_notes = request.appeal_notes
    if request.appeal_lodged:
        case.status = "APPEALED"
    db.commit()
    db.refresh(outcome)
    return outcome_payload(outcome)
