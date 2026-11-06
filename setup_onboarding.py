import os

# 1. Backend Onboarding API
backend_code = '''from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from uuid import UUID
from app.database import SessionLocal
from app.models.recruitment import Candidate
from app.models.employee import Employee
from app.models.department import Department
import uuid
import datetime

router = APIRouter()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

class OnboardCreate(BaseModel):
    national_id: str
    tin_number: str
    nssf_number: str
    bank_name: str
    account_number: str

@router.get("/pending")
def get_pending_candidates(db: Session = Depends(get_db)):
    # Candidates who have OFFERED status need onboarding
    candidates = db.query(Candidate).filter(Candidate.status == "OFFERED").all()
    return candidates

@router.post("/{candidate_id}/convert")
def convert_to_employee(candidate_id: str, req: OnboardCreate, db: Session = Depends(get_db)):
    candidate = db.query(Candidate).filter(Candidate.id == candidate_id).first()
    if not candidate:
        raise HTTPException(status_code=404, detail="Candidate not found")

    # 1. Create the Employee record
    new_emp = Employee(
        id=uuid.uuid4(),
        employee_number=f"EMP-{int(datetime.datetime.now().timestamp())}",
        first_name=candidate.first_name,
        last_name=candidate.last_name,
        personal_email=candidate.email,
        phone_number=candidate.phone_number,
        national_id=req.national_id,
        tin_number=req.tin_number,
        nssf_number=req.nssf_number,
        bank_name=req.bank_name,
        account_number=req.account_number,
        job_title="New Hire", # Will be updated when contract is made
        department_id=candidate.requisition.department_id if candidate.requisition else None,
        hire_date=datetime.date.today(),
        status="PROBATION"
    )
    db.add(new_emp)
    
    # 2. Mark candidate as HIRED and link them
    candidate.status = "HIRED"
    candidate.employee_id = new_emp.id
    db.commit()
    
    return {"message": "Candidate successfully converted to Employee"}
'''

with open('app/api/onboarding.py', 'w', encoding='utf-8') as f:
    f.write(backend_code)
print("✅ Backend Onboarding API created!")

# 2. Register router in main.py
main_path = 'main.py'
with open(main_path, 'r', encoding='utf-8') as f:
    main_code = f.read()

if 'onboarding' not in main_code:
    main_code = main_code.replace("from app.api import", "from app.api import onboarding,")
    main_code = main_code.replace("app.include_router(contracts.router", "app.include_router(onboarding.router, prefix='/api/onboarding', tags=['Onboarding'])\napp.include_router(contracts.router")
    with open(main_path, 'w', encoding='utf-8') as f:
        f.write(main_code)
    print("✅ main.py updated to register Onboarding router!")

# 3. Frontend Onboarding Dashboard
frontend_code = '''import { useState, useEffect } from 'react';
import axios from 'axios';

export default function OnboardingDashboard() {
  const [candidates, setCandidates] = useState([]);
  const [showModal, setShowModal] = useState(false);
  const [selectedCand, setSelectedCand] = useState(null);
  const [formData, setFormData] = useState({ national_id: '', tin_number: '', nssf_number: '', bank_name: '', account_number: '' });

  useEffect(() => {
    fetchCandidates();
  }, []);

  const fetchCandidates = async () => {
    try {
      const res = await axios.get('http://localhost:8000/api/onboarding/pending');
      setCandidates(res.data);
    } catch (err) { console.error(err); }
  };

  const handleConvert = async (e) => {
    e.preventDefault();
    try {
      await axios.post(`http://localhost:8000/api/onboarding/${selectedCand.id}/convert`, formData);
      setShowModal(false);
      fetchCandidates();
      alert("Candidate successfully converted to Employee!");
    } catch (err) { alert("Error converting candidate"); }
  };

  return (
    <div>
      <h1>Onboarding & Verification</h1>
      <p style={{ color: '#64748b', marginBottom: '20px' }}>Review candidates who accepted offers and collect their statutory details to create their Employee ID.</p>

      <div className="card">
        <table>
          <thead>
            <tr>
              <th>Name</th>
              <th>Email</th>
              <th>Phone</th>
              <th>Action</th>
            </tr>
          </thead>
          <tbody>
            {candidates.map(c => (
              <tr key={c.id}>
                <td><strong>{c.first_name} {c.last_name}</strong></td>
                <td>{c.email}</td>
                <td>{c.phone_number}</td>
                <td>
                  <button className="btn-primary" onClick={() => { setSelectedCand(c); setShowModal(true); }}>
                    Verify & Create Employee
                  </button>
                </td>
              </tr>
            ))}
            {candidates.length === 0 && <tr><td colSpan="4" style={{ textAlign: 'center' }}>No candidates pending onboarding.</td></tr>}
          </tbody>
        </table>
      </div>

      {showModal && (
        <div style={{ position: 'fixed', top: 0, left: 0, right: 0, bottom: 0, background: 'rgba(0,0,0,0.5)', display: 'flex', justifyContent: 'center', alignItems: 'center' }}>
          <div className="card" style={{ width: '600px' }}>
            <h2>Onboard: {selectedCand?.first_name} {selectedCand?.last_name}</h2>
            <form onSubmit={handleConvert}>
              <div style={{ display: 'flex', gap: '15px' }}>
                <div className="input-group" style={{ flex: 1 }}>
                  <label>National ID (NIN)</label>
                  <input type="text" required value={formData.national_id} onChange={e => setFormData({...formData, national_id: e.target.value})} />
                </div>
                <div className="input-group" style={{ flex: 1 }}>
                  <label>TIN Number</label>
                  <input type="text" required value={formData.tin_number} onChange={e => setFormData({...formData, tin_number: e.target.value})} />
                </div>
              </div>
              <div className="input-group">
                <label>NSSF Number</label>
                <input type="text" required value={formData.nssf_number} onChange={e => setFormData({...formData, nssf_number: e.target.value})} />
              </div>
              <div style={{ display: 'flex', gap: '15px' }}>
                <div className="input-group" style={{ flex: 1 }}>
                  <label>Bank Name</label>
                  <input type="text" required value={formData.bank_name} onChange={e => setFormData({...formData, bank_name: e.target.value})} />
                </div>
                <div className="input-group" style={{ flex: 1 }}>
                  <label>Account Number</label>
                  <input type="text" required value={formData.account_number} onChange={e => setFormData({...formData, account_number: e.target.value})} />
                </div>
              </div>
              <button type="submit" className="btn-primary" style={{ marginTop: '10px', width: '100%' }}>Create Employee Record</button>
              <button type="button" onClick={() => setShowModal(false)} style={{ marginTop: '10px', width: '100%', background: 'transparent', border: 'none', color: 'red' }}>Cancel</button>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
'''

os.makedirs('frontend/src/pages/onboarding', exist_ok=True)
with open('frontend/src/pages/onboarding/OnboardingDashboard.jsx', 'w', encoding='utf-8') as f:
    f.write(frontend_code)
print("✅ Onboarding Frontend created!")

# 4. Update App.jsx and Layout.jsx for routing
app_path = 'frontend/src/App.jsx'
with open(app_path, 'r', encoding='utf-8') as f:
    app = f.read()

if 'OnboardingDashboard' not in app:
    app = app.replace("import EmployeeDashboard from", "import OnboardingDashboard from './pages/onboarding/OnboardingDashboard';\nimport EmployeeDashboard from")
    app = app.replace('<Route path="/contracts"', '<Route path="/onboarding" element={<ProtectedRoute><OnboardingDashboard /></ProtectedRoute>} />\n<Route path="/contracts"')
    with open(app_path, 'w', encoding='utf-8') as f:
        f.write(app)
    print("✅ App.jsx updated with Onboarding route!")

layout_path = 'frontend/src/components/Layout.jsx'
with open(layout_path, 'r', encoding='utf-8') as f:
    layout = f.read()

if '/onboarding' not in layout:
    # Insert after Employees
    layout = layout.replace("label: 'Employees' }", "label: 'Employees' },\n    { path: '/onboarding', label: 'Onboarding' }")
    with open(layout_path, 'w', encoding='utf-8') as f:
        f.write(layout)
    print("✅ Sidebar updated with Onboarding link!")

print("🚀 DONE! Restart backend & frontend.")
