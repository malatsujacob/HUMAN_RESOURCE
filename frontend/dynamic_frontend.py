import os

# ---------------------------------------------------------
# 1. Update HOD Portal (The Requisition Form)
# ---------------------------------------------------------
hod_path = 'src/pages/ess/ESSPortal.jsx'
with open(hod_path, 'r', encoding='utf-8') as f:
    hod = f.read()

# Update state
hod = hod.replace(
    "const [reqData, setReqData] = useState({ job_title: '', min_education: 'Bachelor', min_experience: 2, department_code: 'TECH', max_applicants: 10 });",
    "const [reqData, setReqData] = useState({ job_title: '', min_education: 'Bachelor', min_experience: 2, description: '', department_code: 'TECH', max_applicants: 10 });"
)

# Update form inputs
old_form = """
<div className="input-group"><label>Job Title</label><input type="text" required value={reqData.job_title} onChange={e => setReqData({...reqData, job_title: e.target.value})} /></div>
            <div className="input-group"><label>Min Exp (Years)</label><input type="number" required value={reqData.min_experience} onChange={e => setReqData({...reqData, min_experience: parseInt(e.target.value)})} /></div>
            <div className="input-group"><label>Max Applicants (Cap)</label><input type="number" required value={reqData.max_applicants} onChange={e => setReqData({...reqData, max_applicants: parseInt(e.target.value)})} /></div>
"""
new_form = """
<div className="input-group"><label>Job Title</label><input type="text" required value={reqData.job_title} onChange={e => setReqData({...reqData, job_title: e.target.value})} placeholder="e.g. Software Engineer" /></div>
            <div className="input-group"><label>Min Education Level</label>
              <select value={reqData.min_education} onChange={e => setReqData({...reqData, min_education: e.target.value})}>
                <option>Certificate</option><option>Diploma</option><option>Bachelor</option><option>Master</option>
              </select>
            </div>
            <div className="input-group"><label>Min Exp (Years)</label><input type="number" required value={reqData.min_experience} onChange={e => setReqData({...reqData, min_experience: parseInt(e.target.value)})} /></div>
            <div className="input-group"><label>Nature of the Person (Description)</label><textarea rows="3" required value={reqData.description} onChange={e => setReqData({...reqData, description: e.target.value})} placeholder="Describe the exact type of person you need..."></textarea></div>
            <div className="input-group"><label>Max Applicants (Cap)</label><input type="number" required value={reqData.max_applicants} onChange={e => setReqData({...reqData, max_applicants: parseInt(e.target.value)})} /></div>
"""
hod = hod.replace(old_form, new_form)
with open(hod_path, 'w', encoding='utf-8') as f:
    f.write(hod)
print("✅ HOD Requisition Form upgraded with Description!")

# ---------------------------------------------------------
# 2. Update Recruitment Dashboard (The Dynamic Email System)
# ---------------------------------------------------------
rec_path = 'src/pages/recruitment/RecruitmentDashboard.jsx'
with open(rec_path, 'r', encoding='utf-8') as f:
    rec = f.read()

# Add states for bulk email
rec = rec.replace(
    "const [emails] = useState([",
    "const [emailType, setEmailType] = useState('INTERVIEW');\n  const [emailSubject, setEmailSubject] = useState('');\n  const [emailBody, setEmailBody] = useState('');\n  const [selectedEmails, setSelectedEmails] = useState([]);\n\n  const [emails] = useState(["
)

# Add the bulk email function
rec = rec.replace(
    "const pipelineCands = candidates.filter(c => c.status === 'IN_PIPELINE');",
    """const handleBulkEmail = async () => {
    if (selectedEmails.length === 0) return alert('Select at least one candidate');
    await axios.post('http://localhost:8000/api/recruitment/send-email', {
      candidate_ids: selectedEmails,
      email_type: emailType,
      subject: emailSubject,
      message: emailBody
    });
    alert(`Emails sent to ${selectedEmails.length} candidates!`);
    setSelectedEmails([]);
    fetchData();
  };

  const toggleSelection = (id) => {
    if (selectedEmails.includes(id)) setSelectedEmails(selectedEmails.filter(x => x !== id));
    else setSelectedEmails([...selectedEmails, id]);
  };

  const pipelineCands = candidates.filter(c => c.status === 'IN_PIPELINE');"""
)

# Replace the EMPTY emails tab with the real dynamic UI
old_email_tab = """
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
"""

new_email_tab = """
      {/* EMAILS TAB */}
      {activeTab === 'emails' && (
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '20px' }}>
          {/* Email Composer */}
          <div className="card">
            <h2>📧 Dynamic Email Campaign</h2>
            <div className="input-group">
              <label>Email Type</label>
              <select value={emailType} onChange={e => setEmailType(e.target.value)}>
                <option value="INTERVIEW">Interview Invitation</option>
                <option value="OFFER">Offer Letter</option>
                <option value="REJECTION">Rejection Notice</option>
                <option value="CUSTOM">Custom Message</option>
              </select>
            </div>
            <div className="input-group">
              <label>Subject</label>
              <input type="text" value={emailSubject} onChange={e => setEmailSubject(e.target.value)} placeholder="Email Subject..." />
            </div>
            <div className="input-group">
              <label>Message Body</label>
              <textarea rows="6" value={emailBody} onChange={e => setEmailBody(e.target.value)} placeholder="Type your message here..."></textarea>
            </div>
            <button className="btn-primary" style={{ width: '100%' }} onClick={handleBulkEmail}>
              Send Email to {selectedEmails.length} Selected Candidates
            </button>
          </div>

          {/* Candidate Selector */}
          <div className="card">
            <h2>Select Recipients</h2>
            <table>
              <thead><tr><th>Select</th><th>Name</th><th>Email</th><th>Status</th></tr></thead>
              <tbody>
                {candidates.map(c => (
                  <tr key={c.id}>
                    <td>
                      <input type="checkbox" checked={selectedEmails.includes(c.id)} onChange={() => toggleSelection(c.id)} style={{ width: '20px', height: '20px' }} />
                    </td>
                    <td><strong>{c.first_name} {c.last_name}</strong></td>
                    <td>{c.email}</td>
                    <td><span style={{ fontSize: '12px', fontWeight: 'bold', color: '#2563eb' }}>{c.status}</span></td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
"""
rec = rec.replace(old_email_tab, new_email_tab)

with open(rec_path, 'w', encoding='utf-8') as f:
    f.write(rec)
print("✅ Recruitment Dashboard upgraded with Dynamic Email Composer & Checkboxes!")
