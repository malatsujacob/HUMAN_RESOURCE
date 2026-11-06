import { useState, useEffect } from 'react';
import axios from 'axios';

export default function ContractsDashboard() {
  const [contracts, setContracts] = useState([]);
  const [employees, setEmployees] = useState([]);
  const [showModal, setShowModal] = useState(false);
  const [formData, setFormData] = useState({ employee_id: '', contract_type: 'PERMANENT', start_date: '', end_date: '', base_salary: 0 });

  useEffect(() => {
    fetchContracts();
    fetchEmployees();
  }, []);

  const fetchContracts = async () => {
    try {
      const res = await axios.get('http://localhost:8000/api/contracts/');
      setContracts(res.data);
    } catch (err) { console.error(err); }
  };

  const fetchEmployees = async () => {
    try {
      const res = await axios.get('http://localhost:8000/api/employees/');
      setEmployees(res.data.filter(e => e.status === 'ACTIVE'));
    } catch (err) { console.error(err); }
  };

  const handleCreate = async (e) => {
    e.preventDefault();
    try {
      await axios.post('http://localhost:8000/api/contracts/', formData);
      setShowModal(false);
      fetchContracts();
    } catch (err) { alert("Error creating contract"); }
  };

  const getExpiryColor = (days) => {
    if (days === null) return '#64748b';
    if (days < 0) return '#991b1b'; // Expired
    if (days <= 30) return '#dc2626'; // Red alert
    if (days <= 60) return '#eab308'; // Yellow alert
    if (days <= 90) return '#f59e0b'; // Orange alert
    return '#16a34a'; // Good
  };

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px' }}>
        <h1>Contracts Management</h1>
        <button className="btn-primary" onClick={() => setShowModal(true)}>+ Generate New Contract</button>
      </div>

      <div className="card">
        <table>
          <thead>
            <tr>
              <th>Employee</th>
              <th>Contract Type</th>
              <th>Start Date</th>
              <th>End Date</th>
              <th>Salary (UGX)</th>
              <th>Expiry Alarm</th>
              <th>Status</th>
            </tr>
          </thead>
          <tbody>
            {contracts.map(c => (
              <tr key={c.id}>
                <td><strong>{c.employee_name}</strong></td>
                <td>{c.contract_type}</td>
                <td>{c.start_date}</td>
                <td>{c.end_date}</td>
                <td>{c.base_salary ? c.base_salary.toLocaleString() : '-'}</td>
                <td>
                  {c.days_to_expiry !== null ? (
                    <span style={{ padding: '4px 8px', borderRadius: '12px', fontSize: '12px', fontWeight: 'bold', color: 'white', background: getExpiryColor(c.days_to_expiry) }}>
                      {c.days_to_expiry < 0 ? 'EXPIRED' : `${c.days_to_expiry} Days left`}
                    </span>
                  ) : 'N/A'}
                </td>
                <td>
                  <span style={{ padding: '4px 8px', borderRadius: '12px', fontSize: '12px', background: c.status === 'ACTIVE' ? '#dcfce7' : '#fef9c3', color: c.status === 'ACTIVE' ? '#166534' : '#854d0e' }}>
                    {c.status}
                  </span>
                </td>
              </tr>
            ))}
            {contracts.length === 0 && <tr><td colSpan="7" style={{ textAlign: 'center' }}>No contracts generated yet.</td></tr>}
          </tbody>
        </table>
      </div>

      {showModal && (
        <div style={{ position: 'fixed', top: 0, left: 0, right: 0, bottom: 0, background: 'rgba(0,0,0,0.5)', display: 'flex', justifyContent: 'center', alignItems: 'center' }}>
          <div className="card" style={{ width: '500px' }}>
            <h2>Generate New Contract</h2>
            <form onSubmit={handleCreate}>
              <div className="input-group">
                <label>Select Employee</label>
                <select required value={formData.employee_id} onChange={e => setFormData({...formData, employee_id: e.target.value})}>
                  <option value="">Choose an employee...</option>
                  {employees.map(e => <option key={e.id} value={e.id}>{e.first_name} {e.last_name} ({e.job_title})</option>)}
                </select>
              </div>
              <div className="input-group">
                <label>Contract Type</label>
                <select value={formData.contract_type} onChange={e => setFormData({...formData, contract_type: e.target.value})}>
                  <option value="PERMANENT">Permanent</option>
                  <option value="FIXED_TERM">Fixed Term (Expires)</option>
                  <option value="PROBATION">Probation</option>
                </select>
              </div>
              <div style={{ display: 'flex', gap: '15px' }}>
                <div className="input-group" style={{ flex: 1 }}>
                  <label>Start Date</label>
                  <input type="date" required value={formData.start_date} onChange={e => setFormData({...formData, start_date: e.target.value})} />
                </div>
                <div className="input-group" style={{ flex: 1 }}>
                  <label>End Date</label>
                  <input type="date" required value={formData.end_date} onChange={e => setFormData({...formData, end_date: e.target.value})} />
                </div>
              </div>
              <div className="input-group">
                <label>Base Salary (UGX)</label>
                <input type="number" required value={formData.base_salary} onChange={e => setFormData({...formData, base_salary: parseFloat(e.target.value)})} />
              </div>
              <button type="submit" className="btn-primary" style={{ marginTop: '10px', width: '100%' }}>Generate Contract</button>
              <button type="button" onClick={() => setShowModal(false)} style={{ marginTop: '10px', width: '100%', background: 'transparent', border: 'none', color: 'red' }}>Cancel</button>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
