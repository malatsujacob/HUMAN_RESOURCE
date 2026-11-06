import os

# 1. Update Backend (app/api/recruitment.py) to handle the exact logic
backend_path = '../app/api/recruitment.py'
with open(backend_path, 'r', encoding='utf-8') as f:
    api = f.read()

# We need to make sure the Status and Grade endpoints handle the rejection reasons properly
if 'class OfferUpdate' not in api:
    api += '''

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
'''
    with open(backend_path, 'w', encoding='utf-8') as f:
        f.write(api)
    print("✅ Backend Recruitment API updated!")

# 2. Rewrite the Frontend Dashboard
frontend_code = '''import { useState, useEffect } from 'react';
import axios from 'axios';

export default function RecruitmentDashboard() {
  const [activeTab, setActiveTab] = useState('candidates');
  const [candidates, setCandidates] = useState([]);
  const [requisitions, setRequisitions] = useState([]);
  const [showReqModal, setShowReqModal] = useState(false);
  const [reqData, setReqData] = useState({ job_title: '', min_education: 'Bachelor', min_experience: 2, department_code: 'TECH' });

  // Modals state
  const [selectedCand, setSelectedCand] = useState(null);
  const [actionType, setActionType] = useState('');
  const [reason, setReason] = useState('');
  const [requirements, setRequirements] = useState('');
  const [candidateView, setCandidateView] = useState('pipeline');
  const [searchTerm, setSearchTerm] = useState('');

  useEffect(() => { fetchData(); }, []);

  const fetchData = async () => {
    const resC = await axios.get('http://localhost:8000/api/recruitment/candidates');
    const resR = await axios.get('http://localhost:8000/api/recruitment/requisitions');
    setCandidates(resC.data);
    setRequisitions(resR.data);
  };

  const handleCreateReq = async (e) => {
    e.preventDefault();
    await axios.post('http://localhost:8000/api/recruitment/requisitions', reqData);
    setShowReqModal(false);
    fetchData();
    alert("Requisition sent to HR for approval.");
  };

  const updateStatus = async (id, status, reasonText = null) => {
    await axios.put(`http://localhost:8000/api/recruitment/candidates/${id}/status`, { status, reason: reasonText });
    fetchData();
    setSelectedCand(null);
  };

  const gradeCandidate = async (id, grade, reasonText = null) => {
    await axios.put(`http://localhost:8000/api/recruitment/candidates/${id}/grade`, { grade, reason: reasonText });
    fetchData();
    setSelectedCand(null);
  };

  const sendOffer = async (id) => {
    await axios.put(`http://localhost:8000/api/recruitment/candidates/${id}/offer`, { status: 'OFFERED', requirements });
    fetchData();
    setSelectedCand(null);
  };

  const handleDeclineOffer = async (id, reasonText) => {
    await axios.put(`http://localhost:8000/api/recruitment/candidates/${id}/offer`, { status: 'DECLINED', reason: reasonText });
    fetchData();
    setSelectedCand(null);
  };

  // Filter lists
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
        <button className="btn-primary" onClick={() => setShowReqModal(true)}>+ Create Requisition</button>
      </div>
      
      {/* TABS */}
      <div className="tabs">
        {['candidates', 'interviews', 'offers'].map(tab => (
          <button key={tab} onClick={() => setActiveTab(tab)} className={`tab ${activeTab === tab ? 'active' : ''}`}>
            {tab === 'candidates' ? 'Candidate Pipeline' : tab}
          </button>
        ))}
      </div>

      {/* 1. CANDIDATE PIPELINE TAB */}
      {activeTab === 'candidates' && (
        <div>
          <div style={{ display: 'flex', gap: '10px', marginBottom: '15px' }}>
            <button className={`btn-primary ${candidateView === 'pipeline' ? '' : 'btn-secondary'}`} style={{ background: candidateView === 'pipeline' ? '#2563eb' : '#e2e8f0', color: candidateView === 'pipeline' ? 'white' : '#0f172a' }} onClick={() => setCandidateView('pipeline')}>Active Pipeline</button>
            <button className={`btn-primary ${candidateView === 'rejected' ? '' : 'btn-secondary'}`} style={{ background: candidateView === 'rejected' ? '#dc2626' : '#e2e8f0', color: candidateView === 'rejected' ? 'white' : '#0f172a' }} onClick={() => setCandidateView('rejected')}>Rejected Archive</button>
          </div>

          {candidateView === 'pipeline' && (
            <div className="card">
              <h2>Review Candidates</h2>
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
                          if (val === 'INTERVIEW_SCHEDULED') updateStatus(c.id, val);
                          else if (val === 'REJECTED') { setSelectedCand(c); setActionType('REJECT_PIPELINE'); }
                        }}>
                          <option value="">-- Select Action --</option>
                          <option value="INTERVIEW_SCHEDULED">Approve for Interview</option>
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
                <input type="text" placeholder="Search name or reason..." value={searchTerm} onChange={e => setSearchTerm(e.target.value)} style={{ padding: '8px', borderRadius: '5px', border: '1px solid #ccc', width: '300px' }} />
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

      {/* 2. INTERVIEW TAB */}
      {activeTab === 'interviews' && (
        <div className="card">
          <h2>Grade Candidates</h2>
          <table>
            <thead><tr><th>Name</th><th>Action</th></tr></thead>
            <tbody>
              {interviewCands.map(c => (
                <tr key={c.id}>
                  <td><strong>{c.first_name} {c.last_name}</strong></td>
                  <td>
                    <select className="input-group" style={{ padding: '5px', borderRadius: '5px' }} onChange={(e) => {
                      const val = e.target.value;
                      if (val === 'OUTSTANDING' || val === 'PASSED') gradeCandidate(c.id, val);
                      else if (val === 'FAILED') { setSelectedCand(c); setActionType('FAIL_INTERVIEW'); }
                    }}>
                      <option value="">-- Select Grade --</option>
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

      {/* 3. OFFERS TAB */}
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

      {/* MODALS */}
      {selectedCand && (actionType === 'REJECT_PIPELINE' || actionType === 'FAIL_INTERVIEW' || actionType === 'DECLINE_OFFER') && (
        <div className="modal-overlay">
          <div className="card" style={{ width: '400px' }}>
            <h2 style={{ color: '#dc2626' }}>Reason Required</h2>
            <textarea rows="3" className="input-group" value={reason} onChange={e => setReason(e.target.value)} placeholder="Type the reason for rejection here..." />
            <button className="btn-primary" style={{ background: '#dc2626', width: '100%' }} onClick={() => {
              if (!reason) return alert("Reason required");
              if (actionType === 'REJECT_PIPELINE') updateStatus(selectedCand.id, 'REJECTED', reason);
              if (actionType === 'FAIL_INTERVIEW') gradeCandidate(selectedCand.id, 'FAILED', reason);
              if (actionType === 'DECLINE_OFFER') handleDeclineOffer(selectedCand.id, reason);
            }}>Confirm</button>
          </div>
        </div>
      )}

      {selectedCand && actionType === 'SEND_OFFER' && (
        <div className="modal-overlay">
          <div className="card" style={{ width: '500px' }}>
            <h2 style={{ color: '#16a34a' }}>Generate Offer</h2>
            <label>Onboarding Requirements (What must they submit?)</label>
            <textarea rows="4" className="input-group" value={requirements} onChange={e => setRequirements(e.target.value)} placeholder="e.g. NIN, TIN, NSSF, Bank Details..." />
            <button className="btn-primary" style={{ background: '#16a34a', width: '100%' }} onClick={() => sendOffer(selectedCand.id)}>Send Offer Email</button>
          </div>
        </div>
      )}
    </div>
  );
}
'''

with open('src/pages/recruitment/RecruitmentDashboard.jsx', 'w', encoding='utf-8') as f:
    f.write(frontend_code)
print("✅ Frontend Recruitment Dashboard rewritten perfectly!")

print("🚀 DONE! Restart frontend.")
