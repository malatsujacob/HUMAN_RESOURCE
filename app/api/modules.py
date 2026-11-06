from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database import SessionLocal
from app.models.contract import Contract
from app.models.performance import PerformanceReview
from app.models.disciplinary import DisciplinaryCase
from app.models.payroll import Payslip

router = APIRouter()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.get("/contracts")
def get_contracts(db: Session = Depends(get_db)):
    return db.query(Contract).all()

@router.get("/performance")
def get_performance(db: Session = Depends(get_db)):
    return db.query(PerformanceReview).all()

@router.get("/disciplinary")
def get_disciplinary(db: Session = Depends(get_db)):
    return db.query(DisciplinaryCase).all()

@router.get("/payslips")
def get_payslips(db: Session = Depends(get_db)):
    return db.query(Payslip).all()

@router.get("/analytics")
def get_analytics():
    # A sample analytics endpoint for the dashboard
    return {
        "total_employees": 45,
        "total_payroll_cost": 125000000,
        "open_positions": 3,
        "absent_today": 2
    }
