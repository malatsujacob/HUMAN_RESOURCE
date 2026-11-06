backend = '''from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
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

class RequisitionCreate(BaseModel):
    department_code: str
    job_title: str
    min_education: str
    min_experience: int
    description: str

@router.post('/requisitions')
def create_requisition(req: RequisitionCreate, db: Session = Depends(get_db)):
    dept = db.query(Department).filter(Department.code == req.department_code).first()
    if not dept:
        raise HTTPException(status_code=400, detail='Department not found')
    new_req = JobRequisition(department_id=dept.id, job_title=req.job_title, min_education=req.min_education, min_experience=req.min_experience, status='APPROVED')
    db.add(new_req)
    db.commit()
    return {'message': 'Requisition created successfully', 'id': new_req.id}

@router.get('/requisitions')
def get_requisitions(db: Session = Depends(get_db)):
    return db.query(JobRequisition).all()

@router.get('/candidates')
def get_candidates(db: Session = Depends(get_db)):
    return db.query(Candidate).filter(Candidate.status == 'IN_PIPELINE').all()

@router.put('/candidates/{id}/status')
def update_candidate_status(id: str, status: str, db: Session = Depends(get_db)):
    candidate = db.query(Candidate).filter(Candidate.id == id).first()
    if candidate:
        candidate.status = status
        db.commit()
    return {'message': 'Status updated'}
'''

frontend = '''import { useState, useEffect } from 'react';
import axios from 'axios';

export default function RecruitmentDashboard() {
  const [activeTab, setActiveTab] = useState('requisitions');
  const [requisitions, setRequisitions] = useState([]);
  const [candidates, setCandidates] = useState([]);
  const [showModal, setShowModal] = useState(false);
  const [formData, setFormData] = useState({ department_code: 'TECH', job_title: '', min_education: 'Bachelor', min_experience: 2, description: '' });

  useEffect(() => { fetchRequisitions(); fetchCandidates(); }, []);

  const fetchRequisitions = async () => {
    const res = await axios.get('http://localhost:8000/api/recruitment/requisitions');
    setRequisitions(res.data);
  };

  const fetchCandidates = async () => {
    const res = await axios.get('http://localhost:8000/api/recruitment/candidates');
    setCandidates(res.data);
  };

  const handleCreateReq = async (e) => {
    e.preventDefault();
    await axios.post('http://localhost:8000/api/recruitment/requisitions', formData);
    setShowModal(false);
    fetchRequisitions();
  };

  const handleCandidateAction = async (id, newStatus) => {
    await axios.put('http://localhost:8000/api/recruitment/candidates/' + id + '/status?status=' + newStatus);
    fetchCandidates();
  };

  return (
    <div>
      <h1>Recruitment Management</h1>
      <div style={{ display: 'flex', gap: '10px', marginBottom: '20px' }}>
        {['requisitions', 'candidates', 'interviews', 'offers', 'emails'].map(tab => (
          <button key={tab} onClick={() => setActiveTab(tab)} className={'btn-primary ' + (activeTab === tab ? 'active' : '')} style={{ textTransform: 'capitalize' }}>{tab}</button>
        ))}
      </div>
      {activeTab === 'requisitions' && (
        <div className='card'>
          <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '15px' }}>
            <h2>Job Requisitions</h2>
            <button className='btn-primary' onClick={() => setShowModal(true)}>+ Create Requisition</button>
          </div>
          <table>
            <thead><tr><th>Job Title</th><th>Min Education</th><th>Min Exp</th><th>Status</th></tr></thead>
            <tbody>
              {requisitions.map(r => (<tr key={r.id}><td>{r.job_title}</td><td>{r.min_education}</td><td>{r.min_experience} yrs</td><td>{r.status}</td></tr>))}
            </tbody>
          </table>
        </div>
      )}
      {activeTab === 'candidates' && (
        <div className='card'>
          <h2>Candidate Pipeline</h2>
          <table>
            <thead><tr><th>Name</th><th>Email</th><th>Action</th></tr></thead>
            <tbody>
              {candidates.map(c => (
                <tr key={c.id}>
                  <td>{c.first_name} {c.last_name}</td><td>{c.email}</td>
                  <td><button className='btn-primary' onClick={() => handleCandidateAction(c.id, 'INTERVIEW_SCHEDULED')}>Schedule Interview</button></td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
      {showModal && (
        <div style={{ position: 'fixed', top: 0, left: 0, right: 0, bottom: 0, background: 'rgba(0,0,0,0.5)', display: 'flex', justifyContent: 'center', alignItems: 'center' }}>
          <div className='card' style={{ width: '400px' }}>
            <h2>Create Job Requisition</h2>
            <form onSubmit={handleCreateReq}>
              <div className='input-group'><label>Job Title</label><input type='text' required value={formData.job_title} onChange={e => setFormData({...formData, job_title: e.target.value})} /></div>
              <div className='input-group'><label>Min Education</label><select value={formData.min_education} onChange={e => setFormData({...formData, min_education: e.target.value})}><option>Certificate</option><option>Diploma</option><option>Bachelor</option><option>Master</option></select></div>
              <div className='input-group'><label>Min Experience</label><input type='number' required value={formData.min_experience} onChange={e => setFormData({...formData, min_experience: parseInt(e.target.value)})} /></div>
              <button type='submit' className='btn-primary'>Save Requisition</button>
              <button type='button' onClick={() => setShowModal(false)} style={{ marginTop: '10px', width: '100%', background: 'transparent', border: 'none', color: 'red' }}>Cancel</button>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
'''

with open('app/api/recruitment.py', 'w', encoding='utf-8') as f: f.write(backend)
with open('frontend/src/pages/recruitment/RecruitmentDashboard.jsx', 'w', encoding='utf-8') as f: f.write(frontend)
print('✅ SUCCESS: Both files updated perfectly!')
