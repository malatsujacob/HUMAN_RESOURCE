import os

# 1. Add the Portal Setting to the Database (app/api/recruitment.py)
backend_code = '''from fastapi import APIRouter, Depends, HTTPException
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
'''

with open('app/api/recruitment.py', 'w', encoding='utf-8') as f:
    f.write(backend_code)
print("✅ Backend updated with Portal Toggle logic!")

# 2. Add the Toggle Button to the HR Dashboard
dashboard_path = 'frontend/src/pages/recruitment/RecruitmentDashboard.jsx'
with open(dashboard_path, 'r', encoding='utf-8') as f:
    dash = f.read()

# We will do a simple find and replace to add the toggle button next to the title
if 'togglePortal' not in dash:
    dash = dash.replace(
        "const [showModal, setShowModal] = useState(false);",
        "const [showModal, setShowModal] = useState(false);\n  const [portalOpen, setPortalOpen] = useState(true);"
    )
    dash = dash.replace(
        "  useEffect(() => {\n    fetchRequisitions();",
        "  useEffect(() => {\n    axios.get('http://localhost:8000/api/recruitment/portal-status').then(res => setPortalOpen(res.data.portal_is_open));\n    fetchRequisitions();"
    )
    
    # Add the toggle function
    dash = dash.replace(
        "  const handleCreateReq = async (e) => {",
        "  const togglePortal = async () => {\n    const res = await axios.post('http://localhost:8000/api/recruitment/toggle-portal');\n    setPortalOpen(res.data.portal_is_open);\n  };\n\n  const handleCreateReq = async (e) => {"
    )

    # Add the UI button
    dash = dash.replace(
        "<h1>Recruitment Management</h1>",
        "<div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>\n        <h1>Recruitment Management</h1>\n        <button onClick={togglePortal} className='btn-primary' style={{ background: portalOpen ? '#16a34a' : '#dc2626' }}>\n          {portalOpen ? '🟢 Portal is OPEN (Click to Close)' : '🔴 Portal is CLOSED (Click to Open)'}\n        </button>\n      </div>"
    )
    
    with open(dashboard_path, 'w', encoding='utf-8') as f:
        f.write(dash)
    print("✅ HR Dashboard updated with Portal Toggle button!")
else:
    print("✅ Dashboard already had the toggle.")

# 3. Update Public Form to show "Closed" message
public_path = 'frontend/src/pages/recruitment/PublicApply.jsx'
with open(public_path, 'r', encoding='utf-8') as f:
    public = f.read()

if 'portalClosed' not in public:
    public = public.replace(
        "const [message, setMessage] = useState('');",
        "const [message, setMessage] = useState('');\n  const [portalClosed, setPortalClosed] = useState(false);"
    )
    public = public.replace(
        "  useEffect(() => {\n    axios.get('http://localhost:8000/api/recruitment/requisitions')",
        "  useEffect(() => {\n    axios.get('http://localhost:8000/api/recruitment/portal-status').then(res => {\n      if (!res.data.portal_is_open) setPortalClosed(true);\n    });\n    axios.get('http://localhost:8000/api/recruitment/requisitions')"
    )
    
    # Add the conditional render before the form
    public = public.replace(
        "{message && <div",
        "{portalClosed ? (\n          <div style={{ textAlign: 'center', padding: '40px 0' }}>\n            <h2 style={{ color: '#dc2626', marginBottom: '10px' }}>Portal Closed</h2>\n            <p style={{ color: '#64748b' }}>HR is currently not accepting new job applications. Please check back later.</p>\n          </div>\n        ) : (\n          <>\n          {message && <div"
    )
    
    # Close the fragment at the end of the form
    public = public.replace(
        "        </form>\n      </div>\n    </div>",
        "        </form>\n        </>\n        )}\n      </div>\n    </div>"
    )

    with open(public_path, 'w', encoding='utf-8') as f:
        f.write(public)
    print("✅ Public Form updated to show 'Closed' message!")
else:
    print("✅ Public Form already updated.")

print("\n🚀 DONE! Restart backend & frontend. Check the HR dashboard for the Portal Toggle!")
