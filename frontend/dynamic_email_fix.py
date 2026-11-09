import os

rec_path = 'src/pages/recruitment/RecruitmentDashboard.jsx'
with open(rec_path, 'r', encoding='utf-8') as f:
    rec = f.read()

# We will rewrite the dynamic email logic to filter the recipient list based on the dropdown
old_email_tab = rec[rec.find("{/* EMAILS TAB */}"):rec.find("{/* --- MODALS --- */}")]

new_email_tab = """
      {/* EMAILS TAB */}
      {activeTab === 'emails' && (
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '20px' }}>
          {/* Email Composer */}
          <div className="card">
            <h2>📧 Dynamic Email Campaign</h2>
            <div className="input-group">
              <label>Email Type</label>
              <select value={emailType} onChange={e => { setEmailType(e.target.value); setSelectedEmails([]); }}>
                <option value="INTERVIEW">Interview Invitation (Shows Pipeline Candidates)</option>
                <option value="OFFER">Offer Letter (Shows Passed Candidates)</option>
                <option value="REJECTION">Rejection Notice (Shows Pipeline Candidates)</option>
                <option value="CUSTOM">Custom Message (Shows Everyone)</option>
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
            <p style={{ fontSize: '12px', color: '#64748b', marginBottom: '10px' }}>
              {emailType === 'OFFER' ? "Showing candidates who passed the interview." : 
               emailType === 'CUSTOM' ? "Showing all candidates." : 
               "Showing candidates currently in the pipeline."}
            </p>
            <table>
              <thead><tr><th>Select</th><th>Name</th><th>Email</th><th>Status</th></tr></thead>
              <tbody>
                {candidates
                  .filter(c => {
                    if (emailType === 'OFFER') return c.status === 'PASSED';
                    if (emailType === 'INTERVIEW' || emailType === 'REJECTION') return c.status === 'IN_PIPELINE';
                    return true; // Custom shows all
                  })
                  .map(c => (
                  <tr key={c.id}>
                    <td>
                      <input type="checkbox" checked={selectedEmails.includes(c.id)} onChange={() => toggleSelection(c.id)} style={{ width: '20px', height: '20px' }} />
                    </td>
                    <td><strong>{c.first_name} {c.last_name}</strong></td>
                    <td>{c.email}</td>
                    <td><span style={{ fontSize: '12px', fontWeight: 'bold', color: '#2563eb' }}>{c.status}</span></td>
                  </tr>
                ))}
                {candidates.filter(c => emailType === 'OFFER' ? c.status === 'PASSED' : c.status === 'IN_PIPELINE').length === 0 && (
                  <tr><td colSpan="4" style={{ textAlign: 'center', padding: '20px' }}>No candidates match this category.</td></tr>
                )}
              </tbody>
            </table>
          </div>
        </div>
      )}
"""

rec = rec.replace(old_email_tab, new_email_tab)

# Also update the Bulk Email function to attach the exact data
rec = rec.replace("const handleBulkEmail = async () => {", 
"""const handleBulkEmail = async () => {
    if (!emailSubject || !emailBody) return alert('Subject and Body are required');""")

with open(rec_path, 'w', encoding='utf-8') as f:
    f.write(rec)
print("✅ Email Tab logic fixed: Recipients now dynamically filter based on Email Type!")
