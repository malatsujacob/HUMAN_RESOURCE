import os

# 1. Overwrite index.css with a beautiful Enterprise Design System
css_code = '''@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

:root {
  --primary: #2563eb;
  --primary-hover: #1d4ed8;
  --bg: #f1f5f9;
  --surface: #ffffff;
  --text-main: #0f172a;
  --text-muted: #64748b;
  --border: #e2e8f0;
}

* { box-sizing: border-box; margin: 0; padding: 0; }

body {
  font-family: 'Inter', sans-serif;
  background-color: var(--bg);
  color: var(--text-main);
  -webkit-font-smoothing: antialiased;
}

/* Layout */
.dashboard-layout { display: flex; height: 100vh; overflow: hidden; }
.sidebar { width: 260px; background: #0f172a; color: white; display: flex; flex-direction: column; }
.sidebar-header { padding: 24px; font-size: 20px; font-weight: 700; color: #38bdf8; border-bottom: 1px solid #1e293b; letter-spacing: 1px; }
.sidebar nav { padding: 20px 10px; flex: 1; overflow-y: auto; }
.sidebar a { display: flex; align-items: center; gap: 12px; color: #94a3b8; text-decoration: none; padding: 12px 16px; border-radius: 8px; margin-bottom: 4px; transition: all 0.2s; font-weight: 500; font-size: 14px; }
.sidebar a:hover, .sidebar a.active { background: #1e293b; color: white; }
.main-content { flex: 1; display: flex; flex-direction: column; overflow: hidden; }
.header { background: var(--surface); padding: 16px 32px; border-bottom: 1px solid var(--border); display: flex; justify-content: space-between; align-items: center; height: 70px; }
.header h3 { font-size: 18px; color: var(--text-main); }
.content-area { padding: 32px; overflow-y: auto; flex: 1; }

/* Typography */
h1 { font-size: 24px; font-weight: 700; margin-bottom: 8px; }
h2 { font-size: 18px; font-weight: 600; margin-bottom: 16px; }
p { color: var(--text-muted); font-size: 14px; }

/* Components */
.card { background: var(--surface); border-radius: 12px; padding: 24px; box-shadow: 0 1px 3px rgba(0,0,0,0.05); border: 1px solid var(--border); margin-bottom: 24px; }

table { width: 100%; border-collapse: collapse; text-align: left; font-size: 14px; }
th { background: #f8fafc; padding: 12px 16px; font-weight: 600; color: var(--text-muted); border-bottom: 1px solid var(--border); text-transform: uppercase; font-size: 12px; letter-spacing: 0.5px; }
td { padding: 16px; border-bottom: 1px solid var(--border); color: var(--text-main); }
tr:hover { background: #f8fafc; }

.btn-primary { background: var(--primary); color: white; border: none; padding: 10px 20px; border-radius: 8px; font-weight: 500; cursor: pointer; transition: background 0.2s; font-size: 14px; }
.btn-primary:hover { background: var(--primary-hover); }

.input-group { margin-bottom: 16px; }
.input-group label { display: block; font-size: 14px; font-weight: 500; margin-bottom: 6px; color: var(--text-main); }
.input-group input, .input-group select, .input-group textarea { width: 100%; padding: 10px 14px; border: 1px solid var(--border); border-radius: 8px; font-size: 14px; font-family: inherit; outline: none; transition: border 0.2s; }
.input-group input:focus, .input-group select:focus, .input-group textarea:focus { border-color: var(--primary); box-shadow: 0 0 0 3px rgba(37,99,235,0.1); }

.tabs { display: flex; gap: 8px; margin-bottom: 24px; border-bottom: 1px solid var(--border); padding-bottom: 8px; }
.tab { padding: 8px 16px; cursor: pointer; font-weight: 500; color: var(--text-muted); border-radius: 6px; transition: all 0.2s; text-transform: capitalize; }
.tab:hover { background: #f1f5f9; }
.tab.active { background: #e0e7ff; color: var(--primary); }

/* Login / Public Container */
.auth-container { min-height: 100vh; display: flex; align-items: center; justify-content: center; background: #f1f5f9; padding: 20px; }
.auth-card { background: white; padding: 40px; border-radius: 16px; box-shadow: 0 10px 25px rgba(0,0,0,0.05); width: 100%; max-width: 500px; }
.auth-card h2 { text-align: center; font-size: 24px; margin-bottom: 8px; color: var(--primary); }
'''

with open('frontend/src/index.css', 'w', encoding='utf-8') as f:
    f.write(css_code)
print("✅ index.css completely rewritten with Enterprise Styles!")

# 2. Update App.jsx to ensure all routes exist
app_path = 'frontend/src/App.jsx'
with open(app_path, 'r', encoding='utf-8') as f:
    app = f.read()

# Ensure PublicApply is imported
if 'PublicApply' not in app:
    app = app.replace("import Login from", "import PublicApply from './pages/recruitment/PublicApply';\nimport Login from")

# Ensure /apply route is public (outside Layout)
if '/apply' not in app:
    app = app.replace('</Routes>', '  <Route path="/apply" element={<PublicApply />} />\n      </Routes>')

# Ensure EmployeeDashboard is imported and routed
if 'EmployeeDashboard' not in app:
    app = app.replace("import Login from", "import EmployeeDashboard from './pages/employees/EmployeeDashboard';\nimport Login from")
    app = app.replace('<Route path="/employees" element={<div>Employees</div>} />', '<Route path="/employees" element={<EmployeeDashboard />} />')
    # If employees route didn't exist, force insert it
    if '/employees' not in app:
        app = app.replace('<Route path="/"', '<Route path="/employees" element={<EmployeeDashboard />} />\n<Route path="/"')

with open(app_path, 'w', encoding='utf-8') as f:
    f.write(app)
print("✅ App.jsx routes fixed!")

# 3. Create the missing PublicApply.jsx (Again, ensuring it exists)
public_apply_code = '''import { useState, useEffect } from 'react';
import axios from 'axios';

export default function PublicApply() {
  const [requisitions, setRequisitions] = useState([]);
  const [formData, setFormData] = useState({ requisition_id: '', first_name: '', last_name: '', email: '', phone_number: '', education_level: 'Bachelor', experience_years: 0, cover_letter: '' });
  const [message, setMessage] = useState('');

  useEffect(() => {
    axios.get('http://localhost:8000/api/recruitment/requisitions')
      .then(res => setRequisitions(res.data.filter(r => r.status === 'APPROVED')))
      .catch(err => console.error(err));
  }, []);

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      const res = await axios.post('http://localhost:8000/api/recruitment/apply', formData);
      setMessage(res.data.message);
      if (res.data.status === 'IN_PIPELINE') {
        setFormData({ requisition_id: '', first_name: '', last_name: '', email: '', phone_number: '', education_level: 'Bachelor', experience_years: 0, cover_letter: '' });
      }
    } catch (err) { setMessage('Error submitting application.'); }
  };

  return (
    <div className="auth-container">
      <div className="auth-card" style={{ maxWidth: '600px' }}>
        <h2>CHAP CHAP AFRICA</h2>
        <p style={{ textAlign: 'center', marginBottom: '24px' }}>Careers Portal</p>
        
        {message && <div style={{ padding: '12px', background: message.includes('reject') ? '#fee2e2' : '#dcfce7', color: message.includes('reject') ? '#991b1b' : '#166534', marginBottom: '20px', borderRadius: '8px', textAlign: 'center', fontWeight: '500' }}>{message}</div>}

        <form onSubmit={handleSubmit}>
          <div className="input-group">
            <label>Target Job Title</label>
            <select required value={formData.requisition_id} onChange={e => setFormData({...formData, requisition_id: e.target.value})}>
              <option value="">Select an open position...</option>
              {requisitions.map(r => <option key={r.id} value={r.id}>{r.job_title}</option>)}
            </select>
          </div>
          
          <div style={{ display: 'flex', gap: '16px' }}>
            <div className="input-group" style={{ flex: 1 }}><label>First Name</label><input type="text" required onChange={e => setFormData({...formData, first_name: e.target.value})} value={formData.first_name} /></div>
            <div className="input-group" style={{ flex: 1 }}><label>Last Name</label><input type="text" required onChange={e => setFormData({...formData, last_name: e.target.value})} value={formData.last_name} /></div>
          </div>

          <div style={{ display: 'flex', gap: '16px' }}>
            <div className="input-group" style={{ flex: 1 }}><label>Email</label><input type="email" required onChange={e => setFormData({...formData, email: e.target.value})} value={formData.email} /></div>
            <div className="input-group" style={{ flex: 1 }}><label>Phone</label><input type="text" required onChange={e => setFormData({...formData, phone_number: e.target.value})} value={formData.phone_number} /></div>
          </div>

          <div style={{ display: 'flex', gap: '16px' }}>
            <div className="input-group" style={{ flex: 1 }}>
              <label>Education</label>
              <select value={formData.education_level} onChange={e => setFormData({...formData, education_level: e.target.value})}>
                <option>Certificate</option><option>Diploma</option><option>Bachelor</option><option>Master</option>
              </select>
            </div>
            <div className="input-group" style={{ flex: 1 }}><label>Years Exp</label><input type="number" required min="0" onChange={e => setFormData({...formData, experience_years: parseInt(e.target.value)})} value={formData.experience_years} /></div>
          </div>

          <div className="input-group">
            <label>Cover Letter (Max 500 words)</label>
            <textarea required rows="4" maxLength="500" value={formData.cover_letter} onChange={e => setFormData({...formData, cover_letter: e.target.value})} placeholder="Briefly explain why you are a good fit..."></textarea>
          </div>

          <button type="submit" className="btn-primary" style={{ width: '100%' }}>Submit Application</button>
        </form>
      </div>
    </div>
  );
}
'''

os.makedirs('frontend/src/pages/recruitment', exist_ok=True)
with open('frontend/src/pages/recruitment/PublicApply.jsx', 'w', encoding='utf-8') as f:
    f.write(public_apply_code)
print("✅ PublicApply.jsx created!")

print("\n🚀 DONE! Restart your frontend (npm run dev) and refresh the browser.")
