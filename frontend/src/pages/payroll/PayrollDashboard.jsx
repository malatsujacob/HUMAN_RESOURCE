import { useState, useEffect } from 'react';
import axios from 'axios';

export default function PayrollDashboard() {
  const [runs, setRuns] = useState([]);
  const [payslips, setPayslips] = useState([]);
  const [selectedRun, setSelectedRun] = useState(null);
  const [showRunModal, setShowRunModal] = useState(false);
  
  // Step 3: Audience Filter
  const [runData, setRunData] = useState({ pay_period: '', target_audience: 'Entire Company' });
  const role = localStorage.getItem('role');
  const isHR = ['HR', 'MANAGEMENT', 'FINANCE'].includes(role);

  useEffect(() => { fetchRuns(); }, []);

  const fetchRuns = async () => {
    const res = await axios.get('http://localhost:8000/api/payroll/runs');
    setRuns(res.data);
  };

  const handleCreateRun = async (e) => {
    e.preventDefault();
    await axios.post('http://localhost:8000/api/payroll/runs', runData);
    setShowRunModal(false);
    fetchRuns();
    alert("Payroll run generated and is pending approval.");
  };

  const handleApprove = async (id) => {
    await axios.put(`http://localhost:8000/api/payroll/runs/${id}/approve`);
    fetchRuns();
    alert("Payroll Approved! Payslips generated.");
  };

  const viewPayslips = async (run) => {
    const res = await axios.get(`http://localhost:8000/api/payroll/runs/${run.id}/payslips`);
    setPayslips(res.data);
    setSelectedRun(run);
  };

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px' }}>
        <h1>Payroll Management</h1>
        {isHR && <button className="btn-primary" onClick={() => setShowRunModal(true)}>+ Initiate Payroll Run</button>}
      </div>
      
      <div className="card">
        <h2>Payroll Runs</h2>
        <table>
          <thead><tr><th>Period</th><th>Audience</th><th>Total Gross</th><th>Total Net</th><th>Status</th><th>Action</th></tr></thead>
          <tbody>
            {runs.map(r => (
              <tr key={r.id}>
                <td><strong>{r.pay_period}</strong></td>
                <td>{r.target_audience}</td>
                <td>UGX {r.total_gross?.toLocaleString()}</td>
                <td>UGX {r.total_net?.toLocaleString()}</td>
                <td>
                  <span style={{ padding: '4px 8px', borderRadius: '12px', fontSize: '12px', fontWeight: 'bold', 
                    background: r.status === 'APPROVED' ? '#dcfce7' : '#fef9c3', 
                    color: r.status === 'APPROVED' ? '#166534' : '#854d0e' }}>
                    {r.status}
                  </span>
                </td>
                <td>
                  {r.status === 'PENDING_APPROVAL' && isHR && (
                    <button className="btn-primary" style={{ background: '#16a34a', padding: '6px 12px', fontSize: '12px', marginRight: '10px' }} onClick={() => handleApprove(r.id)}>Approve</button>
                  )}
                  <button className="btn-primary" style={{ padding: '6px 12px', fontSize: '12px' }} onClick={() => viewPayslips(r)}>View Payslips</button>
                </td>
              </tr>
            ))}
            {runs.length === 0 && <tr><td colSpan="6" style={{ textAlign: 'center' }}>No payroll runs initiated yet.</td></tr>}
          </tbody>
        </table>
      </div>

      {selectedRun && (
        <div className="card" style={{ marginTop: '20px', borderTop: '4px solid #2563eb' }}>
          <h2>Payslips for {selectedRun.pay_period}</h2>
          <table>
            <thead><tr><th>Employee</th><th>Gross Pay</th><th>Net Pay</th><th>Action</th></tr></thead>
            <tbody>
              {payslips.map(p => (
                <tr key={p.id}>
                  <td>{p.employee_name}</td>
                  <td>UGX {p.gross.toLocaleString()}</td>
                  <td style={{ fontWeight: 'bold' }}>UGX {p.net.toLocaleString()}</td>
                  <td><button className="btn-primary" style={{ padding: '5px 10px', fontSize: '12px', background: '#64748b' }}>Download PDF</button></td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {showRunModal && (
        <div style={{ position: 'fixed', top: 0, left: 0, right: 0, bottom: 0, background: 'rgba(0,0,0,0.5)', display: 'flex', justifyContent: 'center', alignItems: 'center' }}>
          <div className="card" style={{ width: '400px' }}>
            <h2>Initiate Payroll Run</h2>
            <form onSubmit={handleCreateRun}>
              <div className="input-group"><label>Pay Period</label><input type="text" placeholder="e.g. October 2026" required value={runData.pay_period} onChange={e => setRunData({...runData, pay_period: e.target.value})} /></div>
              <div className="input-group">
                <label>Target Audience Filter</label>
                <select value={runData.target_audience} onChange={e => setRunData({...runData, target_audience: e.target.value})}>
                  <option>Entire Company</option>
                  <option>One Department</option>
                  <option>HODs Only</option>
                  <option>Specific Individuals</option>
                </select>
              </div>
              <button type="submit" className="btn-primary" style={{ width: '100%' }}>Calculate & Generate</button>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
