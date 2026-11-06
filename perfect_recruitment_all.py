import os

# 1. Update Backend Recruitment API with Notifications and Emails
backend_code = '''from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from uuid import UUID
from app.database import SessionLocal
from app.models.recruitment import JobRequisition, Candidate
from app.models.department import Department
from app.models.notification import Notification
import uuid

router = APIRouter()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

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

class StatusUpdate(BaseModel):
    status: str
    reason: str = None

class GradeUpdate(BaseModel):
    grade: str
    reason: str = None
    interview_date: str = None
    interviewer: str = None
    location: str = None

class OfferUpdate(BaseModel):
    status: str # OFFERED, DECLINED
    requirements: str = None
    salary: str = None
    reason: str = None

# --- PORTAL CONTROL ---
@router.post("/toggle-portal")
def toggle_portal():
    global PORTAL_IS_OPEN
    PORTAL_IS_OPEN = not PORTAL_IS_OPEN
    return {"portal_is_open": PORTAL_IS_OPEN}

@router.get("/portal-status")
def portal_status():
    return {"portal_is_open": PORTAL_IS_OPEN}

# --- REQUISITIONS ---
@router.post("/requisitions")
def create_requisition(req: RequisitionCreate, db: Session = Depends(get_db)):
    dept = db.query(Department).filter(Department.code == req.department_code).first()
    if not dept:
        raise HTTPException(status_code=400, detail="Department not found")
    new_req = JobRequisition(department_id=dept.id, job_title=req.job_title, min_education=req.min_education, min_experience=req.min_experience, status="PENDING_HR")
    db.add(new_req)
    db.commit()
    return {"message": "Requisition created and sent to HR", "id": new_req.id}

@router.get("/requisitions")
def get_requisitions(db: Session = Depends(get_db)):
    return db.query(JobRequisition).all()

@router.put("/requisitions/{id}/approve")
def approve_requisition(id: str, db: Session = Depends(get_db)):
    req = db.query(JobRequisition).filter(JobRequisition.id == id).first()
    if req:
        req.status = "APPROVED"
        db.commit()
    return {"message": "Requisition approved and published to website"}

# --- PUBLIC APPLY ---
@router.post("/apply")
def apply_for_job(req: PublicApplyCreate, db: Session = Depends(get_db)):
    if not PORTAL_IS_OPEN:
        raise HTTPException(status_code=403, detail="The application portal is currently closed.")
    job = db.query(JobRequisition).filter(JobRequisition.id == req.requisition_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    status = "IN_PIPELINE"
    rejection_reason = None
    
    # Auto-Filter
    if req.experience_years < job.min_experience:
        status = "REJECTED"
        rejection_reason = f"Auto-Rejected: Requires {job.min_experience} years of experience."
    
    new_candidate = Candidate(
        requisition_id=job.id, first_name=req.first_name, last_name=req.last_name,
        email=req.email, phone_number=req.phone_number, cover_letter=req.cover_letter,
        status=status, rejection_reason=rejection_reason
    )
    db.add(new_candidate)
    db.commit()
    return {"message": "Application processed", "status": status}

# --- PIPELINE MANAGEMENT ---
@router.get("/candidates")
def get_candidates(db: Session = Depends(get_db)):
    return db.query(Candidate).all()

@router.put("/candidates/{id}/status")
def update_candidate_status(id: str, update: StatusUpdate, db: Session = Depends(get_db)):
    candidate = db.query(Candidate).filter(Candidate.id == id).first()
    if candidate:
        candidate.status = update.status
        if update.status == "REJECTED":
            candidate.rejection_reason = update.reason
        db.commit()
    return {"message": "Status updated"}

# --- INTERVIEWS & GRADING ---
@router.put("/candidates/{id}/interview")
def schedule_interview(id: str, update: GradeUpdate, db: Session = Depends(get_db)):
    candidate = db.query(Candidate).filter(Candidate.id == id).first()
    if candidate:
        candidate.status = "INTERVIEW_SCHEDULED"
        # Mock Email Trigger
        print(f"[EMAIL MOCK] Sent to {candidate.email}: Interview scheduled on {update.interview_date} with {update.interviewer} at {update.location}")
        db.commit()
    return {"message": "Interview scheduled and email sent"}

@router.put("/candidates/{id}/grade")
def grade_candidate(id: str, update: GradeUpdate, db: Session = Depends(get_db)):
    candidate = db.query(Candidate).filter(Candidate.id == id).first()
    if candidate:
        if update.grade in ["FAILED", "REJECTED"]:
            candidate.status = "REJECTED"
            candidate.rejection_reason = f"Interview Result: Failed. {update.reason or ''}"
            print(f"[EMAIL MOCK] Sent to {candidate.email}: We regret to inform you...")
        else:
            candidate.status = "PASSED"
            candidate.interview_grade = update.grade
            print(f"[EMAIL MOCK] Sent to {candidate.email}: Congratulations, you passed the interview!")
        db.commit()
    return {"message": "Grade submitted"}

# --- OFFERS ---
@router.put("/candidates/{id}/offer")
def handle_offer(id: str, update: OfferUpdate, db: Session = Depends(get_db)):
    candidate = db.query(Candidate).filter(Candidate.id == id).first()
    if candidate:
        if update.status == "OFFERED":
            candidate.status = "OFFERED"
            candidate.onboarding_requirements = update.requirements
            print(f"[EMAIL MOCK] Sent to {candidate.email}: Offer of {update.salary}. Requirements: {update.requirements}")
        elif update.status == "DECLINED":
            candidate.status = "REJECTED"
            candidate.rejection_reason = f"Offer Declined: {update.reason}"
        db.commit()
    return {"message": "Offer handled"}
'''

# Ensure model has required columns
model_path = 'app/models/recruitment.py'
with open(model_path, 'r', encoding='utf-8') as f:
    model = f.read()
if 'onboarding_requirements' not in model:
    model = model.replace("status = Column(String(30), default=\"APPLIED\")", "status = Column(String(30), default=\"APPLIED\")\n    interview_grade = Column(String(30))\n    onboarding_requirements = Column(String(500))\n    phone_number = Column(String(30))")
    with open(model_path, 'w', encoding='utf-8') as f:
        f.write(model)

# Rebuild Database tables to include columns
from app.database import engine
from app.models.recruitment import Candidate, JobRequisition
JobRequisition.__table__.drop(bind=engine, checkfirst=True)
Candidate.__table__.drop(bind=engine, checkfirst=True)
JobRequisition.__table__.create(bind=engine, checkfirst=True)
Candidate.__table__.create(bind=engine, checkfirst=True)

with open('app/api/recruitment.py', 'w', encoding='utf-8') as f:
    f.write(backend_code)
print("✅ Full Backend Recruitment API created (with mock email triggers & auto-filters)!")

# 2. Build the complete Frontend Dashboard
frontend_code = '''import { useState, useEffect } from 'react';
import axios from 'axios';

export default function RecruitmentDashboard() {
  const [activeTab, setActiveTab] = useState('candidates');
  const [candidates, setCandidates] = useState([]);
  const [requisitions, setRequisitions] = useState([]);
  const [portalOpen, setPortalOpen] = useState(true);
  
  // Modals
  const [showReqModal, setShowReqModal] = useState(false);
  const [reqData, setReqData] = useState({ job_title: '', min_education: 'Bachelor', min_experience: 2, department_code: 'TECH' });
  
  const [selectedCand, setSelectedCand] = useState(null);
  const [actionType, setActionType] = useState('');
  const [reason, setReason] = useState('');
  const [requirements, setRequirements] = useState('');
  const [salary, setSalary] = useState('');
  const [interviewDate, setInterviewDate] = useState('');
  const [interviewer, setInterviewer] = useState('');
  
  const [candidateView, setCandidateView] = useState('pipeline');
  const [searchTerm, setSearchTerm] = useState('');

  useEffect(() => { fetchData(); }, []);

  const fetchData = async () => {
    const resC = await axios.get('http://localhost:8000/api/recruitment/candidates');
    const resR = await axios.get('http://localhost:8000/api/recruitment/requisitions');
    const resP = await axios.get('http://localhost:8000/api/recruitment/portal-status');
    setCandidates(resC.data);
    setRequisitions(resR.data);
    setPortalOpen(resP.data.portal_is_open);
  };

  const togglePortal = async () => {
    const res = await axios.post('http://localhost:8000/api/recruitment/toggle-portal');
    setPortalOpen(res.data.portal_is_open);
  };

  const handleCreateReq = async (e) => {
    e.preventDefault();
    await axios.post('http://localhost:8000/api/recruitment/requisitions', reqData);
    setShowReqModal(false);
    fetchData();
  };

  const handleApproveReq = async (id) => {
    await axios.put(`http://localhost:8000/api/recruitment/requisitions/${id}/approve`);
    fetchData();
  };

  const updateStatus = async (id, status, reasonText = null) => {
    await axios.put(`http://localhost:8000/api/recruitment/candidates/${id}/status`, { status, reason: reasonText });
    fetchData();
    setSelectedCand(null);
  };

  const scheduleInterview = async (id) => {
    await axios.put(`http://localhost:8000/api/recruitment/candidates/${id}/interview`, { 
      grade: "PENDING", interview_date: interviewDate, interviewer, location: "Head Office" 
    });
    fetchData();
    setSelectedCand(null);
    alert("Interview Scheduled! Email sent to candidate.");
  };

  const gradeCandidate = async (id, grade, reasonText = null) => {
    await axios.put(`http://localhost:8000/api/recruitment/candidates/${id}/grade`, { grade, reason: reasonText });
    fetchData();
    setSelectedCand(null);
  };

  const sendOffer = async (id) => {
    await axios.put(`http://localhost:8000/api/recruitment/candidates/${id}/offer`, { status: 'OFFERED', requirements, salary });
    fetchData();
    setSelectedCand(null);
    alert("Offer Generated! Email sent to candidate.");
  };

  const handleDeclineOffer = async (id, reasonText) => {
    await axios.put(`http://localhost:8000/api/recruitment/candidates/${id}/offer`, { status: 'DECLINED', reason: reasonText });
    fetchData();
    setSelectedCand(null);
  };

  // Filter Lists
  const pipelineCands = candidates.filter(c => c.status === 'IN_PIPELINE');
  const interviewCands = candidates.filter(c => c.status === 'INTERVIEW_SCHEDULED');
  const passedCands = candidates.filter(c => c.status === 'PASSED');
  const rejectedCands = candidates.filter(c => c.status === 'REJECTED' && 
    (c.first_name.toLowerCase().includes(searchTerm.toLowerCase()) || 
     c.last_name.toLowerCase().includes(searchTerm.toLowerCase()) ||
     (c.rejection_reason && c.rejection_reason.toLowerCase().includes(searchTerm.toLowerCase())))
  );

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px' }}>
        <h1>Recruitment Management</h1>
        <div style={{ display: 'flex', gap: '10px' }}>
          <button className="btn-primary" style={{ background: portalOpen ? '#16a34a' : '#dc2626' }} onClick={togglePortal}>
            {portalOpen ? '🟢 Portal OPEN (Click to Close)' : '🔴 Portal CLOSED (Click to Open)'}
          </button>
          <button className="btn-primary" onClick={() => setShowReqModal(true)}>+ Create Requisition</button>
        </div>
      </div>
      
      {/* TABS */}
      <div className="tabs">
        {['candidates', 'interviews', 'offers'].map(tab => (
          <button key={tab} onClick={() => setActiveTab(tab)} className={`tab ${activeTab === tab ? 'active' : ''}`}>
            {tab === 'candidates' ? 'Candidate Pipeline' : tab}
          </button>
        ))}
      </div>

      {/* CANDIDATE PIPELINE */}
      {activeTab === 'candidates' && (
        <div>
          <div style={{ display: 'flex', gap: '10px', marginBottom: '15px' }}>
            <button onClick={() => setCandidateView('pipeline')} style={{ background: candidateView === 'pipeline' ? '#2563eb' : '#e2e8f0', color: candidateView === 'pipeline' ? 'white' : '#0f172a', padding: '8px 16px', borderRadius: '8px', border: 'none', cursor: 'pointer' }}>Active Pipeline</button>
            <button onClick={() => setCandidateView('rejected')} style={{ background: candidateView === 'rejected' ? '#dc2626' : '#e2e8f0', color: candidateView === 'rejected' ? 'white' : '#0f172a', padding: '8px 16px', borderRadius: '8px', border: 'none', cursor: 'pointer' }}>Rejected Archive</button>
          </div>

          {candidateView === 'pipeline' && (
            <div className="card">
              <table>
                <thead><tr><th>Name</th><th>Email</th><th>Education</th><th>Status / Action</th></tr></thead>
                <tbody>
                  {pipelineCands.map(c => (
                    <tr key={c.id}>
                      <td><strong>{c.first_name} {c.last_name}</strong></td>
                      <td>{c.email}</td>
                      <td>{c.education_level}</td>
                      <td>
                        <select className="input-group" style={{ padding: '5px', borderRadius: '5px' }} onChange={(e) => {
                          const val = e.target.value;
                          if (val === 'APPROVE') { setSelectedCand(c); setActionType('SCHEDULE_INTERVIEW'); }
                          else if (val === 'REJECTED') { setSelectedCand(c); setActionType('REJECT_PIPELINE'); }
                        }}>
                          <option value="">-- Select Action --</option>
                          <option value="APPROVE">Approve for Interview</option>
                          <option value="REJECTED">Reject Candidate</option>
                        </select>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}

          {candidateView === 'rejected' && (
            <div className="card">
              <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '15px' }}>
                <h2>Rejected / Failed Archive</h2>
                <input type="text" placeholder="Search by name or reason..." value={searchTerm} onChange={e => setSearchTerm(e.target.value)} style={{ padding: '8px', borderRadius: '5px', border: '1px solid #ccc', width: '300px' }} />
              </div>
              <table>
                <thead><tr><th>Name</th><th>Email</th><th>Reason</th></tr></thead>
                <tbody>
                  {rejectedCands.map(c => (
                    <tr key={c.id}>
                      <td><strong>{c.first_name} {c.last_name}</strong></td>
                      <td>{c.email}</td>
                      <td><span style={{ color: '#dc2626' }}>{c.rejection_reason}</span></td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      )}

      {/* INTERVIEWS TAB */}
      {activeTab === 'interviews' && (
        <div className="card">
          <h2>Grade Candidates</h2>
          <table>
            <thead><tr><th>Name</th><th>Email</th><th>Action</th></tr></thead>
            <tbody>
              {interviewCands.map(c => (
                <tr key={c.id}>
                  <td><strong>{c.first_name} {c.last_name}</strong></td>
                  <td>{c.email}</td>
                  <td>
                    <select className="input-group" style={{ padding: '5px', borderRadius: '5px' }} onChange={(e) => {
                      const val = e.target.value;
                      if (val === 'OUTSTANDING' || val === 'PASSED') gradeCandidate(c.id, val);
                      else if (val === 'FAILED') { setSelectedCand(c); setActionType('FAIL_INTERVIEW'); }
                    }}>
                      <option value="">-- Grade --</option>
                      <option value="OUTSTANDING">Outstanding</option>
                      <option value="PASSED">Passed</option>
                      <option value="FAILED">Failed</option>
                    </select>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* OFFERS TAB */}
      {activeTab === 'offers' && (
        <div className="card">
          <h2>Send Offers</h2>
          <table>
            <thead><tr><th>Name</th><th>Grade</th><th>Action</th></tr></thead>
            <tbody>
              {passedCands.map(c => (
                <tr key={c.id}>
                  <td><strong>{c.first_name} {c.last_name}</strong></td>
                  <td><span style={{ color: 'green', fontWeight: 'bold' }}>{c.interview_grade}</span></td>
                  <td>
                    <button className="btn-primary" onClick={() => { setSelectedCand(c); setActionType('SEND_OFFER'); }}>Generate Offer</button>
                    <button className="btn-primary" style={{ background: '#dc2626', marginLeft: '10px' }} onClick={() => { setSelectedCand(c); setActionType('DECLINE_OFFER'); }}>Candidate Declined</button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* --- MODALS --- */}

      {/* Schedule Interview Modal */}
      {selectedCand && actionType === 'SCHEDULE_INTERVIEW' && (
        <div style={{ position: 'fixed', top: 0, left: 0, right: 0, bottom: 0, background: 'rgba(0,0,0,0.5)', display: 'flex', justifyContent: 'center', alignItems: 'center' }}>
          <div className="card" style={{ width: '400px' }}>
            <h2 style={{ color: '#2563eb' }}>Schedule Interview</h2>
            <p style={{ marginBottom: '15px', fontSize: '14px' }}>These details will be emailed to {selectedCand.first_name}.</p>
            <div className="input-group">
              <label>Interview Date & Time</label>
              <input type="datetime-local" required value={interviewDate} onChange={e => setInterviewDate(e.target.value)} />
            </div>
            <div className="input-group">
              <label>Interviewer Name</label>
              <input type="text" required value={interviewer} onChange={e => setInterviewer(e.target.value)} />
            </div>
            <button className="btn-primary" style={{ width: '100%' }} onClick={() => scheduleInterview(selectedCand.id)}>Send Email & Schedule</button>
            <button onClick={() => setSelectedCand(null)} style={{ marginTop: '10px', width: '100%', background: 'transparent', border: 'none', color: '#64748b' }}>Cancel</button>
          </div>
        </div>
      )}

      {/* Reject/Fail/Decline Modal */}
      {selectedCand && (actionType === 'REJECT_PIPELINE' || actionType === 'FAIL_INTERVIEW' || actionType === 'DECLINE_OFFER') && (
        <div style={{ position: 'fixed', top: 0, left: 0, right: 0, bottom: 0, background: 'rgba(0,0,0,0.5)', display: 'flex', justifyContent: 'center', alignItems: 'center' }}>
          <div className="card" style={{ width: '400px' }}>
            <h2 style={{ color: '#dc2626' }}>Reason Required</h2>
            <div className="input-group">
              <textarea rows="3" required value={reason} onChange={e => setReason(e.target.value)} placeholder="Enter the legal reason for this..."></textarea>
            </div>
            <button className="btn-primary" style={{ background: '#dc2626', width: '100%' }} onClick={() => {
              if (!reason) return alert("Reason is required");
              if (actionType === 'REJECT_PIPELINE') updateStatus(selectedCand.id, 'REJECTED', reason);
              if (actionType === 'FAIL_INTERVIEW') gradeCandidate(selectedCand.id, 'FAILED', reason);
              if (actionType === 'DECLINE_OFFER') handleDeclineOffer(selectedCand.id, reason);
            }}>Confirm</button>
            <button onClick={() => setSelectedCand(null)} style={{ marginTop: '10px', width: '100%', background: 'transparent', border: 'none', color: '#64748b' }}>Cancel</button>
          </div>
        </div>
      )}

      {/* Send Offer Modal */}
      {selectedCand && actionType === 'SEND_OFFER' && (
        <div style={{ position: 'fixed', top: 0, left: 0, right: 0, bottom: 0, background: 'rgba(0,0,0,0.5)', display: 'flex', justifyContent: 'center', alignItems: 'center' }}>
          <div className="card" style={{ width: '500px' }}>
            <h2 style={{ color: '#16a34a' }}>Generate Offer</h2>
            <div className="input-group">
              <label>Proposed Salary (UGX)</label>
              <input type="number" required value={salary} onChange={e => setSalary(e.target.value)} />
            </div>
            <div className="input-group">
              <label>Onboarding Requirements</label>
              <textarea rows="3" required value={requirements} onChange={e => setRequirements(e.target.value)} placeholder="e.g. NIN, TIN, NSSF, Bank Details..."></textarea>
            </div>
            <button className="btn-primary" style={{ background: '#16a34a', width: '100%' }} onClick={() => sendOffer(selectedCand.id)}>Send Offer Email</button>
            <button onClick={() => setSelectedCand(null)} style={{ marginTop: '10px', width: '100%', background: 'transparent', border: 'none', color: '#64748b' }}>Cancel</button>
          </div>
        </div>
      )}

      {/* Create Requisition Modal */}
      {showReqModal && (
        <div style={{ position: 'fixed', top: 0, left: 0, right: 0, bottom: 0, background: 'rgba(0,0,0,0.5)', display: 'flex', justifyContent: 'center', alignItems: 'center' }}>
          <div className="card" style={{ width: '400px' }}>
            <h2>Create Requisition</h2>
            <form onSubmit={handleCreateReq}>
              <div className="input-group"><label>Job Title</label><input type="text" required value={reqData.job_title} onChange={e => setReqData({...reqData, job_title: e.target.value})} /></div>
              <div className="input-group"><label>Min Exp (Years)</label><input type="number" required value={reqData.min_experience} onChange={e => setReqData({...reqData, min_experience: parseInt(e.target.value)})} /></div>
              <button type="submit" className="btn-primary">Send to HR</button>
            </form>
          </div>
        </div>
      )}

      {/* HR Requisitions Approval Section */}
      {requisitions.filter(r => r.status === 'PENDING_HR').length > 0 && (
        <div className="card" style={{ marginTop: '30px', borderLeft: '4px solid #eab308' }}>
          <h2>Pending Requisitions from HODs</h2>
          <table>
            <thead><tr><th>Job Title</th><th>Requirements</th><th>Action</th></tr></thead>
            <tbody>
              {requisitions.filter(r => r.status === 'PENDING_HR').map(r => (
                <tr key={r.id}>
                  <td><strong>{r.job_title}</strong></td>
                  <td>{r.min_education} | {r.min_experience} yrs</td>
                  <td><button onClick={() => handleApproveReq(r.id)} className="btn-primary" style={{ background: '#16a34a', padding: '6px 12px' }}>Approve & Publish</button></td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
'''

with open('frontend/src/pages/recruitment/RecruitmentDashboard.jsx', 'w', encoding='utf-8') as f:
    f.write(frontend_code)
print("✅ Full Frontend Recruitment Dashboard created!")
