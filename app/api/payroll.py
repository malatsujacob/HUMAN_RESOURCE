from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List
from uuid import UUID
from app.database import SessionLocal
from app.models.payroll import PayrollRun, Payslip
from app.models.employee import Employee
from app.models.contract import Contract

router = APIRouter()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

class RunCreate(BaseModel):
    pay_period: str
    target_audience: str

@router.get("/runs")
def get_runs(db: Session = Depends(get_db)):
    return db.query(PayrollRun).all()

@router.post("/runs")
def create_run(req: RunCreate, db: Session = Depends(get_db)):
    # Step 1 & 2: Pull data based on filter
    query = db.query(Employee).filter(Employee.status == 'ACTIVE')
    if req.target_audience == "One Department":
        # In a real app, this would filter by department ID
        pass 
    
    employees = query.all()
    if not employees:
        raise HTTPException(status_code=400, detail="No active employees found for this filter.")

    new_run = PayrollRun(pay_period=req.pay_period, target_audience=req.target_audience, status="PENDING_APPROVAL")
    db.add(new_run)
    db.commit()
    db.refresh(new_run)

    total_gross = 0.0
    total_net = 0.0

    # Step 4, 5, 6: Compute
    for emp in employees:
        # Fetch basic salary from contract
        contract = db.query(Contract).filter(Contract.employee_id == emp.id).order_by(Contract.start_date.desc()).first()
        basic = float(contract.base_salary) if contract and contract.base_salary else 2000000.0
        
        # Mock attendance/leave data for now
        allowances = 200000.0
        overtime = 0.0
        gross = basic + allowances + overtime
        
        # Statutory Deductions (Mock Uganda rates: NSSF 5%, PAYE roughly 20%)
        nssf = gross * 0.05
        paye = gross * 0.20
        net = gross - nssf - paye

        total_gross += gross
        total_net += net

        slip = Payslip(
            run_id=new_run.id, employee_id=emp.id,
            basic_salary=basic, allowances=allowances, overtime=overtime, gross_pay=gross,
            paye_tax=paye, nssf_deduction=nssf, net_pay=net
        )
        db.add(slip)
    
    new_run.total_gross = total_gross
    new_run.total_net = total_net
    db.commit()
    return {"message": f"Payroll Run generated for {len(employees)} employees", "run_id": new_run.id}

@router.put("/runs/{run_id}/approve")
def approve_run(run_id: str, db: Session = Depends(get_db)):
    # Step 7: Approval
    run = db.query(PayrollRun).filter(PayrollRun.id == run_id).first()
    if run:
        run.status = "APPROVED"
        db.commit()
    return {"message": "Payroll approved"}

@router.get("/runs/{run_id}/payslips")
def get_payslips(run_id: str, db: Session = Depends(get_db)):
    # Step 8: Payslips
    slips = db.query(Payslip, Employee).join(Employee, Payslip.employee_id == Employee.id).filter(Payslip.run_id == run_id).all()
    return [{
        "id": s.Payslip.id, "employee_name": f"{s.Employee.first_name} {s.Employee.last_name}",
        "gross": s.Payslip.gross_pay, "net": s.Payslip.net_pay
    } for s in slips]
