import os

# 1. Ensure the directory exists
os.makedirs('frontend/src/pages/employees', exist_ok=True)

# 2. Create the Employee Dashboard file
frontend_code = '''import { useState, useEffect } from 'react';
import axios from 'axios';

export default function EmployeeDashboard() {
  const [employees, setEmployees] = useState([]);
  const [showModal, setShowModal] = useState(false);
  const [formData, setFormData] = useState({ first_name: '', last_name: '', personal_email: '', job_title: '', department_code: 'TECH', role: 'EMPLOYEE' });

  useEffect(() => {
    fetchEmployees();
  }, []);

  const fetchEmployees = async () => {
    try {
      const res = await axios.get('http://localhost:8000/api/employees/');
      setEmployees(res.data);
    } catch (err) { console.error(err); }
  };

  const handleCreate = async (e) => {
    e.preventDefault();
    try {
      await axios.post('http://localhost:8000/api/employees/', formData);
      setShowModal(false);
      fetchEmployees();
      setFormData({ first_name: '', last_name: '', personal_email: '', job_title: '', department_code: 'TECH', role: 'EMPLOYEE' });
    } catch (err) { alert("Error creating employee. Check the terminal."); }
  };

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px' }}>
        <h1>Employee Directory</h1>
        <button className="btn-primary" onClick={() => setShowModal(true)}>+ Onboard New Employee</button>
      </div>

      <div className="card">
        <table>
          <thead>
            <tr>
              <th>Emp No.</th>
              <th>Full Name</th>
              <th>Email</th>
              <th>Job Title</th>
              <th>Status</th>
            </tr>
          </thead>
          <tbody>
            {employees.map(emp => (
              <tr key={emp.id}>
                <td>{emp.employee_number}</td>
                <td><strong>{emp.first_name} {emp.last_name}</strong></td>
                <td>{emp.personal_email}</td>
                <td>{emp.job_title}</td>
                <td>
                  <span style={{ padding: '4px 8px', borderRadius: '12px', fontSize: '12px', background: emp.status === 'ACTIVE' ? '#dcfce7' : '#fef9c3', color: emp.status === 'ACTIVE' ? '#166534' : '#854d0e' }}>
                    {emp.status}
                  </span>
                </td>
              </tr>
            ))}
            {employees.length === 0 && <tr><td colSpan="5" style={{ textAlign: 'center', padding: '20px' }}>No employees found.</td></tr>}
          </tbody>
        </table>
      </div>

      {showModal && (
        <div style={{ position: 'fixed', top: 0, left: 0, right: 0, bottom: 0, background: 'rgba(0,0,0,0.5)', display: 'flex', justifyContent: 'center', alignItems: 'center' }}>
          <div className="card" style={{ width: '500px' }}>
            <h2>Onboard New Employee</h2>
            <form onSubmit={handleCreate}>
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
              <div className="input-group">
                <label>Work Email</label>
                <input type="email" required value={formData.personal_email} onChange={e => setFormData({...formData, personal_email: e.target.value})} />
              </div>
              <div className="input-group">
                <label>Job Title</label>
                <input type="text" required value={formData.job_title} onChange={e => setFormData({...formData, job_title: e.target.value})} />
              </div>
              <div style={{ display: 'flex', gap: '15px' }}>
                <div className="input-group" style={{ flex: 1 }}>
                  <label>Department</label>
                  <select value={formData.department_code} onChange={e => setFormData({...formData, department_code: e.target.value})}>
                    <option value="TECH">Tech</option>
                    <option value="FINANCE">Finance</option>
                    <option value="SALES">Sales</option>
                    <option value="ADMINISTRATION">Administration</option>
                  </select>
                </div>
                <div className="input-group" style={{ flex: 1 }}>
                  <label>System Role</label>
                  <select value={formData.role} onChange={e => setFormData({...formData, role: e.target.value})}>
                    <option value="EMPLOYEE">Employee</option>
                    <option value="HOD">HOD</option>
                    <option value="HR">HR</option>
                  </select>
                </div>
              </div>
              <button type="submit" className="btn-primary" style={{ marginTop: '10px' }}>Save Employee</button>
              <button type="button" onClick={() => setShowModal(false)} style={{ marginTop: '10px', width: '100%', background: 'transparent', border: 'none', color: 'red' }}>Cancel</button>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
'''

# Write the file
with open('frontend/src/pages/employees/EmployeeDashboard.jsx', 'w', encoding='utf-8') as f:
    f.write(frontend_code)
print("✅ EmployeeDashboard.jsx created!")

# 3. Verify and fix App.jsx
app_path = 'frontend/src/App.jsx'
with open(app_path, 'r', encoding='utf-8') as f:
    app = f.read()

if 'import EmployeeDashboard' not in app:
    app = app.replace("import Login from", "import EmployeeDashboard from './pages/employees/EmployeeDashboard';\nimport Login from")
    with open(app_path, 'w', encoding='utf-8') as f:
        f.write(app)
    print("✅ App.jsx updated with EmployeeDashboard import!")
else:
    print("✅ App.jsx already had the import.")

print("\n🚀 DONE! Vite should auto-reload. Refresh your browser.")
