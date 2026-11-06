import { useState, useEffect } from 'react';
import axios from 'axios';

export default function OnboardingDashboard() {
  const [candidates, setCandidates] = useState([]);
  const [showModal, setShowModal] = useState(false);
  const [selectedCand, setSelectedCand] = useState(null);
  const [formData, setFormData] = useState({ national_id: '', tin_number: '', nssf_number: '', bank_name: '', account_number: '' });

  useEffect(() => {
    fetchCandidates();
  }, []);

  const fetchCandidates = async () => {
    try {
      const res = await axios.get('http://localhost:8000/api/onboarding/pending');
      setCandidates(res.data);
    } catch (err) { console.error(err); }
  };

  const handleConvert = async (e) => {
    e.preventDefault();
    try {
      await axios.post(`http://localhost:8000/api/onboarding/${selectedCand.id}/convert`, formData);
      setShowModal(false);
      fetchCandidates();
      alert("Candidate successfully converted to Employee!");
    } catch (err) { alert("Error converting candidate"); }
  };

  return (
    <div>
      <h1>Onboarding & Verification</h1>
      <p style={{ color: '#64748b', marginBottom: '20px' }}>Review candidates who accepted offers and collect their statutory details to create their Employee ID.</p>

      <div className="card">
        <table>
          <thead>
            <tr>
              <th>Name</th>
              <th>Email</th>
              <th>Phone</th>
              <th>Action</th>
            </tr>
          </thead>
          <tbody>
            {candidates.map(c => (
              <tr key={c.id}>
                <td><strong>{c.first_name} {c.last_name}</strong></td>
                <td>{c.email}</td>
                <td>{c.phone_number}</td>
                <td>
                  <button className="btn-primary" onClick={() => { setSelectedCand(c); setShowModal(true); }}>
                    Verify & Create Employee
                  </button>
                </td>
              </tr>
            ))}
            {candidates.length === 0 && <tr><td colSpan="4" style={{ textAlign: 'center' }}>No candidates pending onboarding.</td></tr>}
          </tbody>
        </table>
      </div>

      {showModal && (
        <div style={{ position: 'fixed', top: 0, left: 0, right: 0, bottom: 0, background: 'rgba(0,0,0,0.5)', display: 'flex', justifyContent: 'center', alignItems: 'center' }}>
          <div className="card" style={{ width: '600px' }}>
            <h2>Onboard: {selectedCand?.first_name} {selectedCand?.last_name}</h2>
            <form onSubmit={handleConvert}>
              <div style={{ display: 'flex', gap: '15px' }}>
                <div className="input-group" style={{ flex: 1 }}>
                  <label>National ID (NIN)</label>
                  <input type="text" required value={formData.national_id} onChange={e => setFormData({...formData, national_id: e.target.value})} />
                </div>
                <div className="input-group" style={{ flex: 1 }}>
                  <label>TIN Number</label>
                  <input type="text" required value={formData.tin_number} onChange={e => setFormData({...formData, tin_number: e.target.value})} />
                </div>
              </div>
              <div className="input-group">
                <label>NSSF Number</label>
                <input type="text" required value={formData.nssf_number} onChange={e => setFormData({...formData, nssf_number: e.target.value})} />
              </div>
              <div style={{ display: 'flex', gap: '15px' }}>
                <div className="input-group" style={{ flex: 1 }}>
                  <label>Bank Name</label>
                  <input type="text" required value={formData.bank_name} onChange={e => setFormData({...formData, bank_name: e.target.value})} />
                </div>
                <div className="input-group" style={{ flex: 1 }}>
                  <label>Account Number</label>
                  <input type="text" required value={formData.account_number} onChange={e => setFormData({...formData, account_number: e.target.value})} />
                </div>
              </div>
              <button type="submit" className="btn-primary" style={{ marginTop: '10px', width: '100%' }}>Create Employee Record</button>
              <button type="button" onClick={() => setShowModal(false)} style={{ marginTop: '10px', width: '100%', background: 'transparent', border: 'none', color: 'red' }}>Cancel</button>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
