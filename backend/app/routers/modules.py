from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database import SessionLocal
from app.models.user import User
from app.models.contract import Contract
from app.models.performance import PerformanceReview
from app.models.disciplinary import DisciplinaryCase
from app.models.payroll import Payslip
from app.routers.attendance import get_current_user
from app.services.project_analytics import build_project_analytics

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
def get_analytics(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    return build_project_analytics(db, user)
