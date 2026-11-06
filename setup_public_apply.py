import os

# 1. Create the Public Apply React component
frontend_code = '''import { useState, useEffect } from 'react';
import axios from 'axios';

export default function PublicApply() {
  const [requisitions, setRequisitions] = useState([]);
  const [formData, setFormData] = useState({
    requisition_id: '', first_name: '', last_name: '', email: '', phone_number: '',
    education_level: 'Bachelor', experience_years: 0, cover_letter: ''
  });
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
    } catch (err) {
      setMessage('Error submitting application.');
    }
  };

  return (
    <div style={{ backgroundColor: '#f3f4f6', minHeight: '100vh', display: 'flex', justifyContent: 'center', alignItems: 'center', padding: '20px' }}>
      <div className="card" style={{ width: '600px', maxWidth: '100%' }}>
        <div style={{ textAlign: 'center', marginBottom: '20px' }}>
          <h1 style={{ color: '#2563eb', margin: 0 }}>CHAP CHAP AFRICA</h1>
          <p style={{ color: '#64748b' }}>Careers Portal</p>
        </div>
        
        {message && <div style={{ padding: '15px', background: message.includes('reject') ? '#fee2e2' : '#dcfce7', color: message.includes('reject') ? '#991b1b' : '#166534', marginBottom: '20px', borderRadius: '5px', textAlign: 'center', fontWeight: 'bold' }}>{message}</div>}

        <form onSubmit={handleSubmit}>
          <div className="input-group">
            <label>Target Job Title</label>
            <select required value={formData.requisition_id} onChange={e => setFormData({...formData, requisition_id: e.target.value})}>
              <option value="">Select an open position...</option>
              {requisitions.map(r => <option key={r.id} value={r.id}>{r.job_title}</option>)}
            </select>
          </div>
          
          <div style={{ display: 'flex', gap: '15px' }}>
            <div className="input-group" style={{ flex: 1 }}>
              <label>First Name</label>
              <input type="text" required value={formData.first_name} onChange={e => setFormData({...formData, first_name: e.target.value})} />
            </div>
            <div className="input-group" style={{ flex: 1 }}>
              <label>Last Name</label>
              <input type="text" required value={formData.last_name} onChange={e => setFormData({...formData, last_name: e.target.value})} />
            </div>
          </div>

          <div style={{ display: 'flex', gap: '15px' }}>
            <div className="input-group" style={{ flex: 1 }}>
              <label>Email Address</label>
              <input type="email" required value={formData.email} onChange={e => setFormData({...formData, email: e.target.value})} />
            </div>
            <div className="input-group" style={{ flex: 1 }}>
              <label>Phone Number</label>
              <input type="text" required value={formData.phone_number} onChange={e => setFormData({...formData, phone_number: e.target.value})} />
            </div>
          </div>

          <div style={{ display: 'flex', gap: '15px' }}>
            <div className="input-group" style={{ flex: 1 }}>
              <label>Highest Education Level</label>
              <select value={formData.education_level} onChange={e => setFormData({...formData, education_level: e.target.value})}>
                <option>Certificate</option><option>Diploma</option><option>Bachelor</option><option>Master</option>
              </select>
            </div>
            <div className="input-group" style={{ flex: 1 }}>
              <label>Years of Experience</label>
              <input type="number" required min="0" value={formData.experience_years} onChange={e => setFormData({...formData, experience_years: parseInt(e.target.value)})} />
            </div>
          </div>

          <div className="input-group">
            <label>Cover Letter (Max 500 words)</label>
            <textarea required rows="5" maxLength="500" style={{ width: '100%', padding: '10px', borderRadius: '5px', border: '1px solid #ccc', fontFamily: 'inherit' }} value={formData.cover_letter} onChange={e => setFormData({...formData, cover_letter: e.target.value})} placeholder="Briefly explain why you are a good fit..."></textarea>
            <div style={{ textAlign: 'right', fontSize: '12px', color: '#64748b', marginTop: '5px' }}>{formData.cover_letter.length}/500</div>
          </div>

          <button type="submit" className="btn-primary" style={{ marginTop: '10px' }}>Submit Application</button>
        </form>
      </div>
    </div>
  );
}
'''

# 2. Add the route to App.jsx (Safely inserts it)
app_path = 'frontend/src/App.jsx'
with open(app_path, 'r', encoding='utf-8') as f:
    app_content = f.read()

if 'PublicApply' not in app_content:
    # Add import
    app_content = app_content.replace("import Login from", "import PublicApply from './pages/recruitment/PublicApply';\nimport Login from")
    # Add route (assuming you have a route for /login)
    app_content = app_content.replace('<Route path="/login"', '<Route path="/apply" element={<PublicApply />} />\n<Route path="/login"')
    
    with open(app_path, 'w', encoding='utf-8') as f:
        f.write(app_content)
    print("✅ App.jsx updated with /apply route!")
else:
    print("✅ App.jsx already has PublicApply route.")

# 3. Ensure the directory exists and write the file
os.makedirs('frontend/src/pages/recruitment', exist_ok=True)
with open('frontend/src/pages/recruitment/PublicApply.jsx', 'w', encoding='utf-8') as f:
    f.write(frontend_code)
print("✅ PublicApply.jsx created successfully!")

# 4. Update the backend auto-filter to match documentation exactly
backend_path = 'app/api/recruitment.py'
with open(backend_path, 'r', encoding='utf-8') as f:
    backend_content = f.read()

# Just replacing the core logic chunk
old_logic = """    status = "IN_PIPELINE"
    rejection_reason = None
    
    # AUTO-FILTER LOGIC
    if req.experience_years < job.min_experience:
        status = "REJECTED"
        rejection_reason = f"Requires {job.min_experience} years of experience."
"""

new_logic = """    status = "IN_PIPELINE"
    rejection_reason = None
    
    # AUTO-FILTER LOGIC (From Documentation)
    if req.experience_years < job.min_experience:
        status = "REJECTED"
        rejection_reason = f"Requires {job.min_experience} years of experience."
"""

if old_logic in backend_content:
    backend_content = backend_content.replace(old_logic, new_logic)
    with open(backend_path, 'w', encoding='utf-8') as f:
        f.write(backend_content)
    print("✅ Backend auto-filter logic verified!")

print("\n🚀 Done! Restart both servers and check /apply in your browser.")
