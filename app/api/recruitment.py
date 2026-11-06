from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from uuid import UUID
from app.database import SessionLocal
from app.models.recruitment import JobRequisition, Candidate
from app.models.department import Department

router = APIRouter()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# In-memory toggle for the Portal (in production, this goes in a SystemSettings database table)
PORTAL_IS_OPEN = True

class RequisitionCreate(BaseModel):
    department_code: str
    job_title: str
    min_education: str
    min_experience: int
    description: str
    max_applicants: int = 50

class PublicApplyCreate(BaseModel):
    requisition_id: UUID
    first_name: str
    last_name: str
    email: str
    phone_number: str
    education_level: str
    experience_years: int
    cover_letter: str

@router.post("/toggle-portal")
def toggle_portal():
    global PORTAL_IS_OPEN
    PORTAL_IS_OPEN = not PORTAL_IS_OPEN
    return {"portal_is_open": PORTAL_IS_OPEN}

@router.get("/portal-status")
def portal_status():
    return {"portal_is_open": PORTAL_IS_OPEN}

@router.post("/requisitions")
def create_requisition(req: RequisitionCreate, db: Session = Depends(get_db)):
    dept = db.query(Department).filter(Department.code == req.department_code).first()
    if not dept:
        raise HTTPException(status_code=400, detail="Department not found")
    new_req = JobRequisition(department_id=dept.id, job_title=req.job_title, min_education=req.min_education, min_experience=req.min_experience, status="APPROVED")
    db.add(new_req)
    db.commit()
    return {"message": "Requisition created successfully", "id": new_req.id}

@router.get("/requisitions")
def get_requisitions(db: Session = Depends(get_db)):
    return db.query(JobRequisition).all()

@router.post("/apply")
def apply_for_job(req: PublicApplyCreate, db: Session = Depends(get_db)):
    if not PORTAL_IS_OPEN:
        raise HTTPException(status_code=403, detail="The application portal is currently closed.")
        
    job = db.query(JobRequisition).filter(JobRequisition.id == req.requisition_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    current_applicants = db.query(Candidate).filter(Candidate.requisition_id == job.id).count()
    if current_applicants >= getattr(job, 'max_applicants', 50):
        raise HTTPException(status_code=403, detail='Application portal closed: Maximum number of applicants reached.')
        
    status = "IN_PIPELINE"
    rejection_reason = None
    
    if req.experience_years < job.min_experience:
        status = "REJECTED"
        rejection_reason = f"Requires {job.min_experience} years of experience."
    
    new_candidate = Candidate(
        requisition_id=job.id,
        first_name=req.first_name,
        last_name=req.last_name,
        email=req.email,
        phone_number=req.phone_number,
        cover_letter=req.cover_letter,
        status=status,
        rejection_reason=rejection_reason
    )
    db.add(new_candidate)
    db.commit()
    
    if status == "REJECTED":
        return {"message": "Application received, but you do not meet the minimum experience requirements.", "status": "REJECTED"}
    return {"message": "Application submitted successfully! You are now in the HR pipeline.", "status": "IN_PIPELINE"}

@router.get("/candidates")
def get_candidates(db: Session = Depends(get_db)):
    return db.query(Candidate).filter(Candidate.status == "IN_PIPELINE").all()

@router.put("/candidates/{id}/status")
def update_candidate_status(id: str, status: str, db: Session = Depends(get_db)):
    candidate = db.query(Candidate).filter(Candidate.id == id).first()
    if candidate:
        candidate.status = status
        db.commit()
    return {"message": "Status updated"}


class InterviewUpdate(BaseModel):
    interview_date: str
    interviewer_name: str

@router.put("/candidates/{id}/interview")
def schedule_interview(id: str, req: InterviewUpdate, db: Session = Depends(get_db)):
    candidate = db.query(Candidate).filter(Candidate.id == id).first()
    if candidate:
        candidate.status = "INTERVIEW_SCHEDULED"
        # In a real app, we would save the interview details and send an email here
        db.commit()
    return {"message": "Interview scheduled"}

@router.put("/candidates/{id}/grade")
def grade_interview(id: str, db: Session = Depends(get_db)):
    candidate = db.query(Candidate).filter(Candidate.id == id).first()
    if candidate:
        candidate.status = "GRADED"
        db.commit()
    return {"message": "Candidate graded"}

@router.put("/candidates/{id}/offer")
def generate_offer(id: str, db: Session = Depends(get_db)):
    candidate = db.query(Candidate).filter(Candidate.id == id).first()
    if candidate:
        candidate.status = "OFFERED"
        # In a real app, this would trigger the offer email
        db.commit()
    return {"message": "Offer generated and sent"}

@router.get("/candidates/all")
def get_all_candidates(db: Session = Depends(get_db)):
    # Returns ALL candidates regardless of status so HR can see the whole pipeline
    return db.query(Candidate).all()


class StatusUpdate(BaseModel):
    status: str
    reason: str = None

@router.put("/candidates/{id}/status")
def update_candidate_status(id: str, update: StatusUpdate, db: Session = Depends(get_db)):
    candidate = db.query(Candidate).filter(Candidate.id == id).first()
    if candidate:
        candidate.status = update.status
        candidate.rejection_reason = update.reason
        db.commit()
    return {"message": "Status updated"}

class GradeUpdate(BaseModel):
    grade: str
    reason: str = None

@router.put("/candidates/{id}/grade")
def grade_candidate(id: str, update: GradeUpdate, db: Session = Depends(get_db)):
    candidate = db.query(Candidate).filter(Candidate.id == id).first()
    if candidate:
        if update.grade == "FAILED":
            candidate.status = "REJECTED"
            candidate.rejection_reason = f"Interview Result: Failed. {update.reason or ''}"
        else:
            candidate.status = "PASSED"
            candidate.interview_grade = update.grade
        db.commit()
    return {"message": "Grade submitted"}

class OfferUpdate(BaseModel):
    status: str
    requirements: str = None
    reason: str = None

@router.put("/candidates/{id}/offer")
def handle_offer(id: str, update: OfferUpdate, db: Session = Depends(get_db)):
    candidate = db.query(Candidate).filter(Candidate.id == id).first()
    if candidate:
        if update.status == "OFFERED":
            candidate.status = "OFFERED"
            candidate.onboarding_requirements = update.requirements
        elif update.status == "DECLINED":
            candidate.status = "REJECTED"
            candidate.rejection_reason = f"Offer Declined: {update.reason}"
        db.commit()
    return {"message": "Offer handled"}
