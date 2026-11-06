from datetime import date
from decimal import Decimal, ROUND_HALF_UP
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.api.attendance import get_current_user, get_db
from app.models.employee import Employee
from app.models.payroll import Payslip
from app.models.user import User

router = APIRouter()
PAYROLL_ROLES = {"HR", "HR_ADMIN", "FINANCE", "MANAGEMENT"}
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


@router.post("/generate", response_model=PayrollGenerationResponse)
def generate_payroll(
    request: GeneratePayrollRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    require_payroll_role(user)

    employees = (
        db.query(Employee)
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
    require_payroll_role(user)
    if pay_period is not None:
        try:
            date.fromisoformat(f"{pay_period}-01")
        except ValueError:
            raise HTTPException(status_code=422, detail="pay_period must be formatted as YYYY-MM")
        if len(pay_period) != 7:
            raise HTTPException(status_code=422, detail="pay_period must be formatted as YYYY-MM")

    query = db.query(Payslip)
    if pay_period is not None:
        query = query.filter(Payslip.pay_period == pay_period)
    return query.order_by(Payslip.pay_period.desc(), Payslip.employee_id).all()
