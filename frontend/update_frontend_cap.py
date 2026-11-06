import os

# 1. Update HOD Requisition Form to include Max Applicants
hod_path = 'src/pages/ess/ESSPortal.jsx'
with open(hod_path, 'r', encoding='utf-8') as f:
    hod = f.read()

if 'max_applicants' not in hod:
    # Add to state
    hod = hod.replace(
        "const [reqData, setReqData] = useState({ job_title: '', min_education: 'Bachelor', min_experience: 2, department_code: 'TECH' });",
        "const [reqData, setReqData] = useState({ job_title: '', min_education: 'Bachelor', min_experience: 2, department_code: 'TECH', max_applicants: 10 });"
    )
    # Add to form
    hod = hod.replace(
        "<div className=\"input-group\"><label>Min Exp (Years)</label><input type=\"number\" required value={reqData.min_experience} onChange={e => setReqData({...reqData, min_experience: parseInt(e.target.value)})} /></div>",
        "<div className=\"input-group\"><label>Min Exp (Years)</label><input type=\"number\" required value={reqData.min_experience} onChange={e => setReqData({...reqData, min_experience: parseInt(e.target.value)})} /></div>\n            <div className=\"input-group\"><label>Max Applicants (Cap)</label><input type=\"number\" required value={reqData.max_applicants} onChange={e => setReqData({...reqData, max_applicants: parseInt(e.target.value)})} /></div>"
    )
    with open(hod_path, 'w', encoding='utf-8') as f:
        f.write(hod)
    print("✅ HOD Portal updated with Max Applicant Cap!")

# 2. Update HR Dashboard to show the Inbox/Notification banner
inbox_path = 'src/pages/dashboard/HRInbox.jsx'
with open(inbox_path, 'r', encoding='utf-8') as f:
    inbox = f.read()

if 'New notifications' not in inbox:
    inbox = inbox.replace(
        "<h1 style={{ fontSize: '28px' }}>HR Command Center</h1>",
        "<h1 style={{ fontSize: '28px' }}>HR Command Center</h1>\n        <div style={{ padding: '10px 20px', background: '#e0e7ff', color: '#2563eb', borderRadius: '8px', marginBottom: '20px', display: 'inline-block', fontWeight: 'bold' }}>\n          🔔 Notifications will appear here as candidates apply.\n        </div>"
    )
    with open(inbox_path, 'w', encoding='utf-8') as f:
        f.write(inbox)
    print("✅ HR Master Dashboard updated with Notification banner!")

# 3. Update PublicApply to show the "Portal Closed" error if cap is reached
apply_path = 'src/pages/recruitment/PublicApply.jsx'
with open(apply_path, 'r', encoding='utf-8') as f:
    apply_code = f.read()

if 'Maximum number of applicants' not in apply_code:
    apply_code = apply_code.replace(
        "setMessage(res.data.message);",
        "setMessage(res.data.message);"
    )
    apply_code = apply_code.replace(
        "catch (err) { setMessage('Error submitting application.'); }",
        "catch (err) { \n        if (err.response && err.response.status === 403) {\n          setMessage('❌ The application portal is closed: Maximum number of applicants reached.');\n        } else {\n          setMessage('Error submitting application.');\n        }\n      }"
    )
    with open(apply_path, 'w', encoding='utf-8') as f:
        f.write(apply_code)
    print("✅ Public Apply Form updated to handle 'Portal Closed' message!")
