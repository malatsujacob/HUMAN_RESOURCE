import { useState, useEffect } from 'react';
import axios from 'axios';

export default function ESSPortal() {
  const [activeTab, setActiveTab] = useState('profile');
  const [leaves, setLeaves] = useState([]);
  const [pendingLeaves, setPendingLeaves] = useState([]);
  const [reqData, setReqData] = useState({ job_title: '', min_education: 'Bachelor', min_experience: 2, department_code: 'TECH', max_applicants: 10 });
  const [message, setMessage] = useState('');
  const role = localStorage.getItem('role');
  const email = localStorage.getItem('email');
  const isHOD = role === 'HOD';

  useEffect(() => {
    if (isHOD) {
      axios.get('http://localhost:8000/api/leave/pending').then(res => setPendingLeaves(res.data));
    }
    axios.get('http://localhost:8000/api/leave/my-history').then(res => setLeaves(res.data));
  }, [isHOD]);

  const handleRequestHire = async (e) => {
    e.preventDefault();
    await axios.post('http://localhost:8000/api/recruitment/requisitions', reqData);
    setMessage('✅ Requisition sent to HR Master Dashboard!');
    setTimeout(() => setMessage(''), 4000);
  };

  return (
    <div>
      <div style={{ marginBottom: '30px' }}>
        <h1 style={{ fontSize: '28px' }}>Welcome, {email}</h1>
        <p style={{ color: '#64748b' }}>Role: {role} | Employee Self-Service Portal</p>
      </div>

      {message && <div style={{ padding: '15px', background: '#dcfce7', color: '#166534', marginBottom: '20px', borderRadius: '8px' }}>{message}</div>}

      {/* ESS TABS */}
      <div className="tabs">
        <button onClick={() => setActiveTab('profile')} className={`tab ${activeTab === 'profile' ? 'active' : ''}`}>My Profile</button>
        <button onClick={() => setActiveTab('leave')} className={`tab ${activeTab === 'leave' ? 'active' : ''}`}>My Leave</button>
        {isHOD && <button onClick={() => setActiveTab('team')} className={`tab ${activeTab === 'team' ? 'active' : ''}`}>Team Approvals</button>}
        {isHOD && <button onClick={() => setActiveTab('requisition')} className={`tab ${activeTab === 'requisition' ? 'active' : ''}`}>Request New Hire</button>}
      </div>

      {/* TABS CONTENT */}
      {activeTab === 'profile' && (
        <div className="card">
          <h2>My Profile</h2>
          <p style={{ color: '#64748b' }}>Your personal details, bank info, and documents are managed by HR.</p>
        </div>
      )}

      {activeTab === 'leave' && (
        <div className="card">
          <h2>My Leave Requests</h2>
          <table>
            <thead><tr><th>Type</th><th>Dates</th><th>Status</th></tr></thead>
            <tbody>
              {leaves.map(l => (
                <tr key={l.id}>
                  <td>{l.leave_type}</td>
                  <td>{l.start_date} to {l.end_date}</td>
                  <td><span style={{ padding: '4px 8px', borderRadius: '12px', fontSize: '12px', background: l.status === 'APPROVED' ? '#dcfce7' : '#fef9c3', color: l.status === 'APPROVED' ? '#166534' : '#854d0e' }}>{l.status}</span></td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* HOD ONLY: Team Approvals */}
      {isHOD && activeTab === 'team' && (
        <div className="card">
          <h2>Team Leave Approvals</h2>
          <table>
            <thead><tr><th>Employee</th><th>Dates</th><th>Action</th></tr></thead>
            <tbody>
              {pendingLeaves.map(l => (
                <tr key={l.id}>
                  <td>{l.employee_id.substring(0,8)}...</td>
                  <td>{l.start_date} to {l.end_date}</td>
                  <td><button className="btn-primary" style={{ padding: '6px 12px', fontSize: '12px' }}>Approve</button></td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* HOD ONLY: Request New Hire */}
      {isHOD && activeTab === 'requisition' && (
        <div className="card">
          <h2>Request New Hire</h2>
          <form onSubmit={handleRequestHire}>
            <div className="input-group"><label>Job Title</label><input type="text" required value={reqData.job_title} onChange={e => setReqData({...reqData, job_title: e.target.value})} /></div>
            <div className="input-group"><label>Min Exp (Years)</label><input type="number" required value={reqData.min_experience} onChange={e => setReqData({...reqData, min_experience: parseInt(e.target.value)})} /></div>
            <div className="input-group"><label>Max Applicants (Cap)</label><input type="number" required value={reqData.max_applicants} onChange={e => setReqData({...reqData, max_applicants: parseInt(e.target.value)})} /></div>
            <button type="submit" className="btn-primary">Send to HR</button>
          </form>
        </div>
      )}
    </div>
  );
}
