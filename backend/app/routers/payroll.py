from datetime import date, datetime, timezone
from decimal import Decimal, ROUND_HALF_UP
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session, joinedload

from app.routers.attendance import get_current_user, get_db
from app.models.attendance import Attendance
from app.models.employee import Employee
from app.models.payroll import PayrollAuditEvent, PayrollCycle, PayrollReconciliation, Payslip
from app.models.user import User

router = APIRouter()
PAYROLL_ROLES = {"HR", "HR_ADMIN", "ADMIN", "FINANCE", "MANAGEMENT", "DEVELOPER"}
PAY_CODE_CATEGORIES = {
    "BASE_WAGES": "Wages",
    "REGULAR": "Wages",
    "BONUS": "Bonus",
    "OVERTIME": "Overtime",
    "RETRO": "Retroactive pay",
}
CENT = Decimal("0.01")


class GeneratePayrollRequest(BaseModel):
    pay_period: str = Field(pattern=r"^\d{4}-(0[1-9]|1[0-2])$")


class PayslipResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    employee_id: UUID
    pay_period: str
    gross_salary: Decimal
    paye_tax: Decimal
    nssf_deduction: Decimal
    net_salary: Decimal
    employer_contribution: Decimal = Decimal("0")
    employer_pension: Decimal = Decimal("0")
    employer_social_contribution: Decimal = Decimal("0")
    bonus_amount: Decimal = Decimal("0")
    overtime_amount: Decimal = Decimal("0")
    retro_amount: Decimal = Decimal("0")
    retro_reason: Optional[str] = None
    retro_source: Optional[str] = None
    retro_verified: str = "PENDING"
    pay_code: str = "BASE_WAGES"
    reporting_category: Optional[str] = None
    employee_name: Optional[str] = None
    employee_number: Optional[str] = None
    department_id: Optional[UUID] = None
    department_name: Optional[str] = None
    cost_center: Optional[str] = None
    work_location: Optional[str] = None
    employee_valid: bool = True
    department_valid: bool = False


class ReconciliationRequest(BaseModel):
    register_total: Decimal = Field(ge=0)
    source_total: Decimal = Field(ge=0)
    discrepancies: list[dict] = Field(default_factory=list, max_length=1000)
    source_filename: Optional[str] = Field(default=None, max_length=255)


class CycleStageRequest(BaseModel):
    stage: str = Field(pattern=r"^(DATA_ENTRY|APPROVAL|POSTING|POSTED)$")


class CycleDeadlinesRequest(BaseModel):
    approval_deadline: Optional[date] = None
    posting_deadline: Optional[date] = None


class PaymentElectionRequest(BaseModel):
    bank_name: str = Field(min_length=1, max_length=100)
    account_number: str = Field(min_length=6, max_length=50)


class PayrollGenerationResponse(BaseModel):
    pay_period: str
    generated_count: int
    skipped_count: int
    payslips: list[PayslipResponse]


def require_payroll_role(user: User) -> None:
    if user.role.upper() not in PAYROLL_ROLES:
        raise HTTPException(status_code=403, detail="Role is not allowed to access company payroll")


def round_money(amount: Decimal) -> Decimal:
    return amount.quantize(CENT, rounding=ROUND_HALF_UP)


def validate_pay_period(pay_period: str) -> None:
    if len(pay_period) != 7:
        raise HTTPException(status_code=422, detail="pay_period must be formatted as YYYY-MM")
    try:
        date.fromisoformat(f"{pay_period}-01")
    except ValueError:
        raise HTTPException(status_code=422, detail="pay_period must be formatted as YYYY-MM")


def add_audit_event(
    db: Session,
    user: User,
    pay_period: str,
    action_type: str,
    target: str,
    before_value: Optional[str] = None,
    after_value: Optional[str] = None,
) -> None:
    db.add(PayrollAuditEvent(
        pay_period=pay_period,
        actor_id=user.id,
        actor_email=user.email,
        action_type=action_type,
        target=target,
        before_value=before_value,
        after_value=after_value,
    ))


def get_or_create_cycle(db: Session, pay_period: str) -> Optional[PayrollCycle]:
    cycle = db.query(PayrollCycle).filter(PayrollCycle.pay_period == pay_period).with_for_update().first()
    if cycle is None and db.query(Payslip.id).filter(Payslip.pay_period == pay_period).first():
        cycle = PayrollCycle(pay_period=pay_period, stage="DATA_ENTRY")
        db.add(cycle)
        db.flush()
    return cycle


@router.post("/generate", response_model=PayrollGenerationResponse)
def generate_payroll(
    request: GeneratePayrollRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    require_payroll_role(user)

    employees = (
        db.query(Employee)
        .options(joinedload(Employee.department))
        .filter(Employee.status == "ACTIVE")
        .order_by(Employee.id)
        .with_for_update()
        .all()
    )
    existing_employee_ids = {
        employee_id
        for (employee_id,) in db.query(Payslip.employee_id)
        .filter(Payslip.pay_period == request.pay_period)
        .all()
    }

    payslips = []
    skipped_count = 0
    for employee in employees:
        if employee.id in existing_employee_ids:
            skipped_count += 1
            continue
        if employee.department_id is None or employee.department is None:
            skipped_count += 1
            continue
        if employee.base_salary is None or employee.base_salary < 0:
            raise HTTPException(
                status_code=409,
                detail=f"Employee {employee.id} has no valid base salary",
            )

        gross_salary = round_money(Decimal(employee.base_salary))
        nssf_deduction = round_money(gross_salary * Decimal("0.05"))
        paye_tax = round_money(gross_salary * Decimal("0.10"))
        payslips.append(
            Payslip(
                employee_id=employee.id,
                pay_period=request.pay_period,
                gross_salary=gross_salary,
                nssf_deduction=nssf_deduction,
                paye_tax=paye_tax,
                net_salary=gross_salary - nssf_deduction - paye_tax,
            )
        )

    db.add_all(payslips)
    cycle = db.query(PayrollCycle).filter(PayrollCycle.pay_period == request.pay_period).first()
    if cycle is None:
        cycle = PayrollCycle(pay_period=request.pay_period, stage="DATA_ENTRY")
        db.add(cycle)
    add_audit_event(
        db, user, request.pay_period, "PAYROLL_GENERATED", request.pay_period,
        after_value=f"created={len(payslips)}; skipped={skipped_count}",
    )
    try:
        db.commit()
    except SQLAlchemyError:
        db.rollback()
        raise

    for payslip in payslips:
        db.refresh(payslip)

    return PayrollGenerationResponse(
        pay_period=request.pay_period,
        generated_count=len(payslips),
        skipped_count=skipped_count,
        payslips=payslips,
    )


@router.get("/my-payslips", response_model=list[PayslipResponse])
def get_my_payslips(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    if user.role.upper() not in PAYROLL_ROLES | {"HOD", "EMPLOYEE"}:
        raise HTTPException(status_code=403, detail="Role is not allowed to access payslips")
    if user.employee_id is None:
        raise HTTPException(status_code=403, detail="User is not linked to an employee record")

    return (
        db.query(Payslip)
        .filter(Payslip.employee_id == user.employee_id)
        .order_by(Payslip.pay_period.desc())
        .all()
    )


@router.get("/all", response_model=list[PayslipResponse])
def get_all_payslips(
    pay_period: Optional[str] = None,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    if pay_period is not None:
        validate_pay_period(pay_period)

    role = user.role.upper()
    query = db.query(Payslip).options(
        joinedload(Payslip.employee).joinedload(Employee.department)
    ).outerjoin(Employee, Payslip.employee_id == Employee.id)
    if role in PAYROLL_ROLES:
        pass
    elif role == "HOD":
        if user.employee is None or user.employee.department_id is None:
            raise HTTPException(status_code=403, detail="HOD is not assigned to a department")
        query = query.filter(Employee.department_id == user.employee.department_id)
    else:
        raise HTTPException(status_code=403, detail="Role is not allowed to access company payroll")
    if pay_period is not None:
        query = query.filter(Payslip.pay_period == pay_period)
    payslips = query.order_by(Payslip.pay_period.desc(), Payslip.employee_id).all()
    return [
        {
            "id": item.id,
            "employee_id": item.employee_id,
            "pay_period": item.pay_period,
            "gross_salary": item.gross_salary,
            "paye_tax": item.paye_tax,
            "nssf_deduction": item.nssf_deduction,
            "net_salary": item.net_salary,
            "employer_contribution": item.employer_contribution,
            "employer_pension": item.employer_pension,
            "employer_social_contribution": item.employer_social_contribution,
            "bonus_amount": item.bonus_amount,
            "overtime_amount": item.overtime_amount,
            "retro_amount": item.retro_amount,
            "retro_reason": item.retro_reason,
            "retro_source": item.retro_source,
            "retro_verified": item.retro_verified,
            "pay_code": item.pay_code,
            "reporting_category": PAY_CODE_CATEGORIES.get((item.pay_code or "").upper()),
            "employee_name": " ".join(
                part for part in [
                    item.employee.first_name if item.employee else "",
                    item.employee.middle_name if item.employee else "",
                    item.employee.last_name if item.employee else "",
                ] if part
            ) or None,
            "employee_number": item.employee.employee_number if item.employee else None,
            "department_id": item.employee.department_id if item.employee else None,
            "department_name": item.employee.department.name if item.employee and item.employee.department else None,
            "cost_center": item.employee.cost_center if item.employee else None,
            "work_location": item.employee.work_location if item.employee else None,
            "employee_valid": item.employee is not None,
            "department_valid": bool(item.employee and item.employee.department_id and item.employee.department),
        }
        for item in payslips
    ]


@router.put("/my-payment-election")
def update_my_payment_election(
    request: PaymentElectionRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    if user.role.upper() not in PAYROLL_ROLES | {"HOD", "EMPLOYEE"}:
        raise HTTPException(status_code=403, detail="Role is not allowed to update payment elections")
    if user.employee is None:
        raise HTTPException(status_code=403, detail="User is not linked to an employee record")
    employee = db.query(Employee).filter(Employee.id == user.employee.id).with_for_update().first()
    bank_name = request.bank_name.strip()
    account_number = request.account_number.strip()
    if not bank_name or len(account_number) < 6:
        raise HTTPException(status_code=422, detail="Enter a bank name and a valid account number")
    before_value = f"{employee.bank_name or ''}:****{(employee.account_number or '')[-4:]}"
    employee.bank_name = bank_name
    employee.account_number = account_number
    employee.payment_account_updated_at = datetime.now(timezone.utc)
    after_value = f"{employee.bank_name}:****{employee.account_number[-4:]}"
    today = date.today()
    pay_period = today.strftime("%Y-%m")
    effective_month = today.month + 1
    effective_year = today.year
    if effective_month == 13:
        effective_month = 1
        effective_year += 1
    add_audit_event(db, user, pay_period, "PAYMENT_ELECTION_UPDATED", str(employee.id), before_value, after_value)
    db.commit()
    return {
        "bank_name": employee.bank_name,
        "account_last_four": employee.account_number[-4:],
        "updated_at": employee.payment_account_updated_at,
        "effective_period": f"{effective_year}-{effective_month:02d}",
    }


@router.get("/cycles")
def list_payroll_cycles(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    role = user.role.upper()
    if role not in PAYROLL_ROLES | {"HOD"}:
        raise HTTPException(status_code=403, detail="Role is not allowed to access payroll cycles")
    cycles = {
        item.pay_period: item
        for item in db.query(PayrollCycle).order_by(PayrollCycle.pay_period.desc()).all()
    }
    periods = {period for (period,) in db.query(Payslip.pay_period).distinct().all()} | set(cycles)
    if role == "HOD":
        if user.employee is None or user.employee.department_id is None:
            raise HTTPException(status_code=403, detail="HOD is not assigned to a department")
        periods = {
            period for (period,) in db.query(Payslip.pay_period).join(Employee).filter(
                Employee.department_id == user.employee.department_id
            ).distinct().all()
        }
    return [
        {
            "pay_period": period,
            "stage": cycles[period].stage if period in cycles else "DATA_ENTRY",
            "approval_deadline": cycles[period].approval_deadline if period in cycles else None,
            "posting_deadline": cycles[period].posting_deadline if period in cycles else None,
            "updated_at": cycles[period].updated_at if period in cycles else None,
        }
        for period in sorted(periods, reverse=True)
    ]


@router.put("/cycles/{pay_period}/stage")
def update_cycle_stage(
    pay_period: str,
    request: CycleStageRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    require_payroll_role(user)
    validate_pay_period(pay_period)
    cycle = get_or_create_cycle(db, pay_period)
    if cycle is None:
        raise HTTPException(status_code=404, detail="Payroll cycle not found")
    transitions = {"DATA_ENTRY": "APPROVAL", "APPROVAL": "POSTING", "POSTING": "POSTED"}
    if transitions.get(cycle.stage) != request.stage:
        raise HTTPException(status_code=409, detail=f"Cannot move a {cycle.stage} cycle to {request.stage}")
    approver_roles = {"HR", "HR_ADMIN", "ADMIN", "MANAGEMENT", "DEVELOPER"}
    finance_roles = {"FINANCE", "ADMIN", "MANAGEMENT", "DEVELOPER"}
    if request.stage == "APPROVAL" and user.role.upper() not in approver_roles:
        raise HTTPException(status_code=403, detail="A payroll approver is required to send the cycle for approval")
    if request.stage in {"POSTING", "POSTED"} and user.role.upper() not in finance_roles:
        raise HTTPException(status_code=403, detail="Finance approval is required for posting")
    if request.stage == "POSTING":
        reconciliations = db.query(PayrollReconciliation).filter(
            PayrollReconciliation.pay_period == pay_period
        ).all()
        by_type = {item.reconciliation_type: item.status for item in reconciliations}
        if by_type.get("bank") != "MATCH" or by_type.get("tax") != "MATCH":
            raise HTTPException(status_code=409, detail="Bank and tax reconciliations must both match before approval")
    if request.stage == "POSTED":
        if cycle.stage != "POSTING":
            raise HTTPException(status_code=409, detail="Payroll must be in posting before it can be posted")
    old_stage = cycle.stage
    if request.stage == "APPROVAL":
        payslip_count = db.query(Payslip.id).filter(Payslip.pay_period == pay_period).count()
        if payslip_count == 0:
            raise HTTPException(status_code=409, detail="Generate payroll records before submitting the cycle for approval")
        unmapped_employee_count = db.query(Employee.id).filter(
            Employee.status == "ACTIVE",
            Employee.department_id.is_(None),
        ).count()
        if unmapped_employee_count:
            raise HTTPException(status_code=409, detail="Resolve active employees without department mappings before approval")
    cycle.stage = request.stage
    cycle.updated_by = user.id
    cycle.updated_at = datetime.now(timezone.utc)
    add_audit_event(db, user, pay_period, "CYCLE_STAGE_CHANGED", pay_period, old_stage, request.stage)
    db.commit()
    return {"pay_period": pay_period, "stage": cycle.stage}


@router.put("/cycles/{pay_period}/deadlines")
def update_cycle_deadlines(
    pay_period: str,
    request: CycleDeadlinesRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    require_payroll_role(user)
    validate_pay_period(pay_period)
    cycle = get_or_create_cycle(db, pay_period)
    if cycle is None:
        raise HTTPException(status_code=404, detail="Payroll cycle not found")
    before_value = f"approval={cycle.approval_deadline}; posting={cycle.posting_deadline}"
    cycle.approval_deadline = request.approval_deadline
    cycle.posting_deadline = request.posting_deadline
    cycle.updated_by = user.id
    cycle.updated_at = datetime.now(timezone.utc)
    after_value = f"approval={cycle.approval_deadline}; posting={cycle.posting_deadline}"
    add_audit_event(db, user, pay_period, "DEADLINES_UPDATED", pay_period, before_value, after_value)
    db.commit()
    return {
        "pay_period": pay_period,
        "approval_deadline": cycle.approval_deadline,
        "posting_deadline": cycle.posting_deadline,
    }


@router.put("/cycles/{pay_period}/reconciliations/{reconciliation_type}")
def save_reconciliation(
    pay_period: str,
    reconciliation_type: str,
    request: ReconciliationRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    require_payroll_role(user)
    validate_pay_period(pay_period)
    if reconciliation_type not in {"bank", "tax"}:
        raise HTTPException(status_code=422, detail="reconciliation_type must be bank or tax")
    cycle = get_or_create_cycle(db, pay_period)
    if cycle is None:
        raise HTTPException(status_code=404, detail="Payroll cycle not found")
    mismatches = request.discrepancies
    status = "MATCH" if request.register_total == request.source_total and not mismatches else "MISMATCH"
    details = {
        "register_total": str(request.register_total),
        "source_total": str(request.source_total),
        "source_filename": request.source_filename,
        "discrepancies": mismatches,
    }
    record = db.query(PayrollReconciliation).filter(
        PayrollReconciliation.pay_period == pay_period,
        PayrollReconciliation.reconciliation_type == reconciliation_type,
    ).first()
    before_value = f"{record.status}: {record.details}" if record else None
    if record is None:
        record = PayrollReconciliation(
            pay_period=pay_period,
            reconciliation_type=reconciliation_type,
            status=status,
            details=details,
            updated_by=user.id,
        )
        db.add(record)
    else:
        record.status = status
        record.details = details
        record.updated_by = user.id
        record.updated_at = datetime.now(timezone.utc)
    add_audit_event(db, user, pay_period, "RECONCILIATION_SAVED", reconciliation_type, before_value, f"{status}: {details}")
    db.commit()
    return {"pay_period": pay_period, "reconciliation_type": reconciliation_type, "status": status, "details": details}


@router.get("/cycles/{pay_period}/reconciliations")
def get_reconciliations(
    pay_period: str,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    role = user.role.upper()
    if role not in PAYROLL_ROLES | {"HOD"}:
        raise HTTPException(status_code=403, detail="Role is not allowed to access reconciliations")
    validate_pay_period(pay_period)
    query = db.query(PayrollReconciliation).filter(PayrollReconciliation.pay_period == pay_period)
    if role == "HOD":
        if user.employee is None or user.employee.department_id is None:
            raise HTTPException(status_code=403, detail="HOD is not assigned to a department")
        query = query.filter(False)
    return [
        {
            "reconciliation_type": item.reconciliation_type,
            "status": item.status,
            "details": item.details,
            "updated_at": item.updated_at,
        }
        for item in query.order_by(PayrollReconciliation.reconciliation_type).all()
    ]


@router.get("/cycles/{pay_period}/audit")
def get_payroll_audit(
    pay_period: str,
    search: Optional[str] = Query(default=None, max_length=200),
    action_type: Optional[str] = Query(default=None, max_length=50),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    role = user.role.upper()
    if role not in PAYROLL_ROLES | {"HOD"}:
        raise HTTPException(status_code=403, detail="Role is not allowed to access payroll audit events")
    validate_pay_period(pay_period)
    query = db.query(PayrollAuditEvent).filter(PayrollAuditEvent.pay_period == pay_period)
    if role == "HOD":
        if user.employee is None or user.employee.department_id is None:
            raise HTTPException(status_code=403, detail="HOD is not assigned to a department")
        query = query.filter(False)
    if action_type:
        query = query.filter(PayrollAuditEvent.action_type == action_type)
    if search:
        term = f"%{search.strip()}%"
        query = query.filter(
            (PayrollAuditEvent.actor_email.ilike(term))
            | (PayrollAuditEvent.action_type.ilike(term))
            | (PayrollAuditEvent.target.ilike(term))
            | (PayrollAuditEvent.before_value.ilike(term))
            | (PayrollAuditEvent.after_value.ilike(term))
        )
    return [
        {
            "id": str(item.id),
            "user": item.actor_email,
            "timestamp": item.created_at,
            "action_type": item.action_type,
            "target": item.target,
            "before_value": item.before_value,
            "after_value": item.after_value,
        }
        for item in query.order_by(PayrollAuditEvent.created_at.desc()).limit(500).all()
    ]


@router.get("/compliance")
def get_payroll_compliance(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    role = user.role.upper()
    if role not in PAYROLL_ROLES | {"HOD"}:
        raise HTTPException(status_code=403, detail="Role is not allowed to access payroll compliance data")
    query = db.query(Employee).options(
        joinedload(Employee.department), joinedload(Employee.documents)
    ).filter(Employee.status == "ACTIVE")
    if role == "HOD":
        if user.employee is None or user.employee.department_id is None:
            raise HTTPException(status_code=403, detail="HOD is not assigned to a department")
        query = query.filter(Employee.department_id == user.employee.department_id)
    return [
        {
            "employee_id": str(employee.id),
            "employee_name": " ".join(
                part for part in [employee.first_name, employee.middle_name, employee.last_name] if part
            ),
            "employee_number": employee.employee_number,
            "department_name": employee.department.name if employee.department else None,
            "department_valid": bool(employee.department_id and employee.department),
            "tax_id_present": bool(employee.tin_number),
            "tax_form_present": any(
                "tin" in (document.document_type or "").lower()
                and document.status.upper() not in {"MISSING", "REJECTED"}
                for document in employee.documents
            ) or employee.tax_form_updated_at is not None,
            "tax_form_updated_at": employee.tax_form_updated_at,
            "jurisdiction_address": employee.jurisdiction_address or employee.home_address,
            "jurisdiction_updated_at": employee.jurisdiction_updated_at,
        }
        for employee in query.order_by(Employee.last_name, Employee.first_name).all()
    ]


@router.get("/overtime")
def get_payroll_overtime(
    pay_period: str,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    role = user.role.upper()
    if role not in PAYROLL_ROLES | {"HOD"}:
        raise HTTPException(status_code=403, detail="Role is not allowed to access payroll overtime data")
    validate_pay_period(pay_period)
    period_start = date.fromisoformat(f"{pay_period}-01")
    period_end = date(period_start.year + (period_start.month == 12), period_start.month % 12 + 1, 1)
    query = db.query(Attendance).join(Employee).options(joinedload(Attendance.employee)).filter(
        Attendance.date >= period_start,
        Attendance.date < period_end,
        Attendance.overtime_hours > 0,
    )
    if role == "HOD":
        if user.employee is None or user.employee.department_id is None:
            raise HTTPException(status_code=403, detail="HOD is not assigned to a department")
        query = query.filter(Employee.department_id == user.employee.department_id)
    return [
        {
            "attendance_id": str(record.id),
            "employee_id": str(record.employee_id),
            "employee_name": " ".join(
                part for part in [
                    record.employee.first_name if record.employee else "",
                    record.employee.middle_name if record.employee else "",
                    record.employee.last_name if record.employee else "",
                ] if part
            ),
            "employee_number": record.employee.employee_number if record.employee else None,
            "date": record.date,
            "hours": record.overtime_hours,
        }
        for record in query.order_by(Attendance.date, Attendance.employee_id).all()
    ]
