import { useState, useEffect } from 'react';
import axios from 'axios';

export default function PublicApply() {
  const [requisitions, setRequisitions] = useState([]);
  const [formData, setFormData] = useState({ requisition_id: '', first_name: '', last_name: '', email: '', phone_number: '', education_level: 'Bachelor', experience_years: 0, cover_letter: '' });
  const [message, setMessage] = useState('');
  const [portalClosed, setPortalClosed] = useState(false);

  useEffect(() => {
    axios.get('http://localhost:8000/api/recruitment/portal-status').then(res => {
      if (!res.data.portal_is_open) setPortalClosed(true);
    });
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
        
        {portalClosed ? (
          <div style={{ textAlign: 'center', padding: '40px 0' }}>
            <h2 style={{ color: '#dc2626', marginBottom: '10px' }}>Portal Closed</h2>
            <p style={{ color: '#64748b' }}>HR is currently not accepting new job applications. Please check back later.</p>
          </div>
        ) : (
          <>
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
        </>
        )}
      </div>
    </div>
  );
}
