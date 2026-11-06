import os

# Ensure we are in the right place
if not os.path.exists('src'):
    print("❌ ERROR: You must run this from the FRONTEND terminal!")
else:
    rec_path = 'src/pages/recruitment/RecruitmentDashboard.jsx'
    
    frontend_code = '''import { useState, useEffect } from 'react';
import axios from 'axios';

export default function RecruitmentDashboard() {
  const [activeTab, setActiveTab] = useState('candidates');
  const [candidates, setCandidates] = useState([]);
  const [requisitions, setRequisitions] = useState([]);
  
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
  const [grade, setGrade] = useState('');
  
  const [candidateView, setCandidateView] = useState('pipeline');
  const [searchTerm, setSearchTerm] = useState('');

  // Mock Emails for the tab
  const [emails] = useState([
    { id: 1, to: 'candidate@test.com', subject: 'Interview Invitation', body: 'You are invited for an interview on...' },
    { id: 2, to: 'failed@test.com', subject: 'Application Update', body: 'We regret to inform you...' }
  ]);

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
  };

  const submitGrade = async (id) => {
    await axios.put(`http://localhost:8000/api/recruitment/candidates/${id}/grade`, { grade, reason });
    fetchData();
    setSelectedCand(null);
  };

  const sendOffer = async (id) => {
    await axios.put(`http://localhost:8000/api/recruitment/candidates/${id}/offer`, { status: 'OFFERED', requirements, salary });
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
        <button className="btn-primary" onClick={() => setShowReqModal(true)}>+ Create Requisition</button>
      </div>
      
      <div className="tabs">
        {['candidates', 'interviews', 'offers', 'emails'].map(tab => (
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
                <thead><tr><th>Name</th><th>Email</th><th>Education</th><th>Documents</th><th>Action</th></tr></thead>
                <tbody>
                  {pipelineCands.map(c => (
                    <tr key={c.id}>
                      <td><strong>{c.first_name} {c.last_name}</strong></td>
                      <td>{c.email}</td>
                      <td>{c.education_level}</td>
                      <td>
                        <button className="btn-primary" style={{ padding: '5px 10px', fontSize: '12px', background: '#64748b' }} onClick={() => alert("Opening CV & Documents PDF...")}>View CV</button>
                      </td>
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
          <h2>Interview Grading</h2>
          <table>
            <thead><tr><th>Name</th><th>Email</th><th>Action</th></tr></thead>
            <tbody>
              {interviewCands.map(c => (
                <tr key={c.id}>
                  <td><strong>{c.first_name} {c.last_name}</strong></td>
                  <td>{c.email}</td>
                  <td>
                    <button className="btn-primary" onClick={() => { setSelectedCand(c); setActionType('GRADE_INTERVIEW'); }}>Grade Candidate</button>
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
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* EMAILS TAB */}
      {activeTab === 'emails' && (
        <div className="card">
          <h2>📧 Sent Email Logs</h2>
          <table>
            <thead><tr><th>To</th><th>Subject</th><th>Body Snippet</th><th>Status</th></tr></thead>
            <tbody>
              {emails.map(e => (
                <tr key={e.id}>
                  <td><strong>{e.to}</strong></td>
                  <td>{e.subject}</td>
                  <td style={{ fontSize: '12px', color: '#64748b' }}>{e.body}</td>
                  <td><span style={{ color: '#16a34a', fontWeight: 'bold' }}>SENT</span></td>
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

      {/* Grade Interview Modal */}
      {selectedCand && actionType === 'GRADE_INTERVIEW' && (
        <div style={{ position: 'fixed', top: 0, left: 0, right: 0, bottom: 0, background: 'rgba(0,0,0,0.5)', display: 'flex', justifyContent: 'center', alignItems: 'center' }}>
          <div className="card" style={{ width: '400px' }}>
            <h2>Grade Interview</h2>
            <div className="input-group">
              <label>Result</label>
              <select value={grade} onChange={e => setGrade(e.target.value)}>
                <option value="">-- Select Result --</option>
                <option value="OUTSTANDING">Outstanding</option>
                <option value="PASSED">Passed</option>
                <option value="FAILED">Failed</option>
              </select>
            </div>
            <div className="input-group">
              <label>Interviewer Notes / Reason</label>
              <textarea rows="3" value={reason} onChange={e => setReason(e.target.value)} placeholder="Notes..."></textarea>
            </div>
            <button className="btn-primary" style={{ width: '100%' }} onClick={() => {
              if (!grade) return alert("Select a grade");
              if (grade === 'FAILED') updateStatus(selectedCand.id, 'REJECTED', `Interview Failed: ${reason}`);
              else submitGrade(selectedCand.id);
            }}>Submit Grade</button>
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
              <textarea rows="3" required value={requirements} onChange={e => setRequirements(e.target.value)} placeholder="e.g. NIN, TIN, NSSF..."></textarea>
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
    </div>
  );
}
'''
    with open(rec_path, 'w', encoding='utf-8') as f:
        f.write(frontend_code)
    print("✅ Recruitment Dashboard rewritten successfully! You can now run: npm run dev")
