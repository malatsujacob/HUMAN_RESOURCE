import os

# 1. Backend Contracts API
backend_code = '''from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from datetime import date
from uuid import UUID
from app.database import SessionLocal
from app.models.contract import Contract
from app.models.employee import Employee

router = APIRouter()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

class ContractCreate(BaseModel):
    employee_id: UUID
    contract_type: str
    start_date: date
    end_date: date
    base_salary: float

@router.post("/")
def create_contract(req: ContractCreate, db: Session = Depends(get_db)):
    # Check if employee exists
    emp = db.query(Employee).filter(Employee.id == req.employee_id).first()
    if not emp:
        raise HTTPException(status_code=404, detail="Employee not found")
    
    new_contract = Contract(
        employee_id=req.employee_id,
        contract_type=req.contract_type,
        start_date=req.start_date,
        end_date=req.end_date,
        base_salary=req.base_salary,
        status="ACTIVE"
    )
    db.add(new_contract)
    db.commit()
    return {"message": "Contract generated successfully", "id": new_contract.id}

@router.get("/")
def get_all_contracts(db: Session = Depends(get_db)):
    # Join Contract and Employee to get names for the frontend
    results = db.query(Contract, Employee).join(Employee, Contract.employee_id == Employee.id).all()
    contracts = []
    for contract, emp in results:
        contracts.append({
            "id": contract.id,
            "employee_name": f"{emp.first_name} {emp.last_name}",
            "contract_type": contract.contract_type,
            "start_date": contract.start_date,
            "end_date": contract.end_date,
            "base_salary": contract.base_salary,
            "status": contract.status,
            "days_to_expiry": (contract.end_date - date.today()).days if contract.end_date else None
        })
    return contracts

@router.put("/{id}/activate")
def activate_contract(id: str, db: Session = Depends(get_db)):
    contract = db.query(Contract).filter(Contract.id == id).first()
    if contract:
        contract.status = "ACTIVE"
        db.commit()
    return {"message": "Contract activated"}
'''

with open('app/api/contracts.py', 'w', encoding='utf-8') as f:
    f.write(backend_code)
print("✅ Backend Contracts API created!")

# 2. Ensure main.py registers the contracts router
main_path = 'main.py'
with open(main_path, 'r', encoding='utf-8') as f:
    main_code = f.read()

if 'contracts' not in main_code:
    main_code = main_code.replace("from app.api import", "from app.api import contracts,")
    main_code = main_code.replace("app.include_router(leave_api.router", "app.include_router(contracts.router, prefix='/api/contracts', tags=['Contracts'])\napp.include_router(leave_api.router")
    with open(main_path, 'w', encoding='utf-8') as f:
        f.write(main_code)
    print("✅ main.py updated to register Contracts router!")

# 3. Frontend Contracts Dashboard
frontend_code = '''import { useState, useEffect } from 'react';
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
'''

os.makedirs('frontend/src/pages/contracts', exist_ok=True)
with open('frontend/src/pages/contracts/ContractsDashboard.jsx', 'w', encoding='utf-8') as f:
    f.write(frontend_code)
print("✅ Contracts Frontend created!")

# 4. Update App.jsx and Layout.jsx for routing
app_path = 'frontend/src/App.jsx'
with open(app_path, 'r', encoding='utf-8') as f:
    app = f.read()

if 'ContractsDashboard' not in app:
    app = app.replace("import EmployeeDashboard from", "import ContractsDashboard from './pages/contracts/ContractsDashboard';\nimport EmployeeDashboard from")
    app = app.replace('<Route path="/recruitment"', '<Route path="/contracts" element={<ProtectedRoute><ContractsDashboard /></ProtectedRoute>} />\n<Route path="/recruitment"')
    with open(app_path, 'w', encoding='utf-8') as f:
        f.write(app)
    print("✅ App.jsx updated with Contracts route!")

layout_path = 'frontend/src/components/Layout.jsx'
with open(layout_path, 'r', encoding='utf-8') as f:
    layout = f.read()

if '/contracts' not in layout:
    layout = layout.replace("{ path: '/recruitment', label: 'Recruitment' },", "{ path: '/recruitment', label: 'Recruitment' },\n    { path: '/contracts', label: 'Contracts' },")
    with open(layout_path, 'w', encoding='utf-8') as f:
        f.write(layout)
    print("✅ Sidebar updated with Contracts link!")

print("🚀 DONE! Restart backend & frontend.")
