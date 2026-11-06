import os

# 1. Create the Employee/HOD Self-Service Portal (ESS)
ess_code = '''import { useState, useEffect } from 'react';
import axios from 'axios';

export default function ESSPortal() {
  const [activeTab, setActiveTab] = useState('profile');
  const [leaves, setLeaves] = useState([]);
  const [pendingLeaves, setPendingLeaves] = useState([]);
  const [reqData, setReqData] = useState({ job_title: '', min_education: 'Bachelor', min_experience: 2, department_code: 'TECH' });
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
            <button type="submit" className="btn-primary">Send to HR</button>
          </form>
        </div>
      )}
    </div>
  );
}
'''

os.makedirs('src/pages/ess', exist_ok=True)
with open('src/pages/ess/ESSPortal.jsx', 'w', encoding='utf-8') as f:
    f.write(ess_code)
print("✅ Employee/HOD ESS Portal created!")

# 2. Update App.jsx Routing: Everyone lands on ESS by default, except HR/MANAGEMENT
with open('src/App.jsx', 'r', encoding='utf-8') as f:
    app = f.read()

if 'ESSPortal' not in app:
    app = app.replace("import HRInbox from", "import ESSPortal from './pages/ess/ESSPortal';\nimport HRInbox from")
    
    # We will route "/" based on role
    app = app.replace('<Route path="/" element={<ProtectedRoute>{localStorage.getItem(\'role\') === \'HOD\' ? <HODDashboard /> : <HRInbox />}</ProtectedRoute>} />', 
    '''<Route path="/" element={
        <ProtectedRoute>
          {['HR', 'MANAGEMENT'].includes(localStorage.getItem('role')) ? <HRInbox /> : <ESSPortal />}
        </ProtectedRoute>
      } />''')
    
    with open('src/App.jsx', 'w', encoding='utf-8') as f:
        f.write(app)
    print("✅ Routing updated: Employees & HODs land on ESS, HR lands on Master Dashboard!")

# 3. Update Sidebar Layout: Hide HR modules from Employees & HODs
with open('src/components/Layout.jsx', 'r', encoding='utf-8') as f:
    layout = f.read()

if 'isHR' not in layout:
    layout = layout.replace("const isHOD = role === 'HOD';", "const isHOD = role === 'HOD';\n  const isHR = ['HR', 'MANAGEMENT'].includes(role);")
    
    # Hide Employees, Recruitment, Contracts, Payroll, Performance, Training, Disciplinary, Exit from non-HR
    for path in ['/employees', '/recruitment', '/contracts', '/payroll', '/performance', '/training', '/disciplinary', '/exit']:
        # If the line exists, add hideForStaff: true
        if f"path: '{path}'" in layout:
            layout = layout.replace(f"path: '{path}',", f"path: '{path}', hideForStaff: true,")
    
    # Filter based on role
    layout = layout.replace("{navItems.filter(item => !item.hideForHOD || !isHOD).map(item => (", "{navItems.filter(item => (!item.hideForStaff || isHR)).map(item => (")
    
    with open('src/components/Layout.jsx', 'w', encoding='utf-8') as f:
        f.write(layout)
    print("✅ Sidebar updated: Non-HR users only see ESS modules!")
