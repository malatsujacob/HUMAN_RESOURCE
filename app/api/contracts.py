from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from datetime import date
from uuid import UUID
from app.database import SessionLocal
from app.models.contract import Contract
from app.models.employee import Employee

router = APIRouter()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

class ContractCreate(BaseModel):
    employee_id: UUID
    contract_type: str
    start_date: date
    end_date: date
    base_salary: float

@router.post("/")
def create_contract(req: ContractCreate, db: Session = Depends(get_db)):
    # Check if employee exists
    emp = db.query(Employee).filter(Employee.id == req.employee_id).first()
    if not emp:
        raise HTTPException(status_code=404, detail="Employee not found")
    
    new_contract = Contract(
        employee_id=req.employee_id,
        contract_type=req.contract_type,
        start_date=req.start_date,
        end_date=req.end_date,
        base_salary=req.base_salary,
        status="ACTIVE"
    )
    db.add(new_contract)
    db.commit()
    return {"message": "Contract generated successfully", "id": new_contract.id}

@router.get("/")
def get_all_contracts(db: Session = Depends(get_db)):
    # Join Contract and Employee to get names for the frontend
    results = db.query(Contract, Employee).join(Employee, Contract.employee_id == Employee.id).all()
    contracts = []
    for contract, emp in results:
        contracts.append({
            "id": contract.id,
            "employee_name": f"{emp.first_name} {emp.last_name}",
            "contract_type": contract.contract_type,
            "start_date": contract.start_date,
            "end_date": contract.end_date,
            "base_salary": contract.base_salary,
            "status": contract.status,
            "days_to_expiry": (contract.end_date - date.today()).days if contract.end_date else None
        })
    return contracts

@router.put("/{id}/activate")
def activate_contract(id: str, db: Session = Depends(get_db)):
    contract = db.query(Contract).filter(Contract.id == id).first()
    if contract:
        contract.status = "ACTIVE"
        db.commit()
    return {"message": "Contract activated"}
