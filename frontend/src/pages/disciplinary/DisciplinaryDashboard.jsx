import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import {
  createDisciplinaryCase,
  getEmployees,
  getDisciplinaryCases,
  getDisciplinaryAnalytics,
  getModuleError,
} from '../../api/peopleModules'
import '../ModuleDashboards.css'

const employeeName = (employee) => employee.full_name
  || [employee.first_name, employee.middle_name, employee.last_name].filter(Boolean).join(' ')
  || `Employee ${employee.employee_number || ''}`.trim()

function DisciplinaryDashboard() {
  const navigate = useNavigate()
  const [employees, setEmployees] = useState([])
  const [employeeSearch, setEmployeeSearch] = useState('')
  const [employeeListOpen, setEmployeeListOpen] = useState(false)
  const [employeesLoading, setEmployeesLoading] = useState(true)
  const [cases, setCases] = useState([])
  const [caseView, setCaseView] = useState('ALL')
  const [analytics, setAnalytics] = useState(null)
  const [notice, setNotice] = useState('')
  const [error, setError] = useState('')
  const [submitting, setSubmitting] = useState(false)
  const [form, setForm] = useState({
    employee_id: '',
    incident_date: '',
    description: '',
    action_taken: '',
    case_type: 'DISCIPLINARY',
    category: '',
    severity: '',
    policy_breached: '',
    confidential: false,
  })

  const loadCases = async () => {
    try {
      const [caseList, stats] = await Promise.all([
        getDisciplinaryCases(),
        getDisciplinaryAnalytics().catch(() => null),
      ])
      setCases(caseList)
      setAnalytics(stats)
    } catch (e) {
      setError(getModuleError(e))
    }
  }

  const loadEmployees = async () => {
    try {
      setEmployees(await getEmployees())
    } catch (e) {
      setError(getModuleError(e))
    } finally {
      setEmployeesLoading(false)
    }
  }

  useEffect(() => {
    loadCases()
    loadEmployees()
  }, [])

  const employeeOptions = employees
    .slice()
    .sort((a, b) => employeeName(a).localeCompare(employeeName(b)))
  const filteredEmployees = employeeOptions.filter((employee) => {
    const search = employeeSearch.trim().toLocaleLowerCase()
    return !search || [
      employeeName(employee),
      employee.employee_number,
      employee.department_name,
      employee.legacy_department,
    ].some((value) => String(value || '').toLocaleLowerCase().includes(search))
  })
  const visibleCases = cases.filter((item) => {
    if (caseView === 'RESOLVED') return item.status === 'RESOLVED'
    if (caseView === 'APPEALED') return item.status === 'APPEALED'
    if (caseView === 'OPEN') return item.status === 'OPEN'
    return true
  })
  const caseViewTitles = {
    ALL: 'All cases',
    OPEN: 'Open cases',
    RESOLVED: 'Resolution reports',
    APPEALED: 'Appeals',
  }

  const selectEmployee = (employee) => {
    setForm({ ...form, employee_id: employee.id })
    setEmployeeSearch(employeeName(employee))
    setEmployeeListOpen(false)
  }

  const handleSubmit = async (event) => {
    event.preventDefault()
    setError(''); setNotice(''); setSubmitting(true)
    try {
      const payload = { ...form }
      if (!payload.action_taken) delete payload.action_taken
      if (!payload.category) delete payload.category
      if (!payload.severity) delete payload.severity
      if (!payload.policy_breached) delete payload.policy_breached
      await createDisciplinaryCase(payload)
      setForm({
        employee_id: '', incident_date: '', description: '', action_taken: '',
        case_type: 'DISCIPLINARY', category: '', severity: '', policy_breached: '', confidential: false,
      })
      setEmployeeSearch('')
      setNotice('Disciplinary case logged.')
      await loadCases()
    } catch (e) {
      setError(getModuleError(e))
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <div className="module-page">
      <header className="module-header">
        <div>
          <p className="module-kicker">EMPLOYEE RELATIONS</p>
          <h1>Disciplinary</h1>
          <p>Record and review employee relations cases.</p>
        </div>
      </header>

      {notice && <div className="module-notice">{notice}</div>}
      {error && <div className="module-error">{error}</div>}

      {analytics && (
        <section style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: 16, marginBottom: 24 }}>
          <div className="module-card">
            <p className="module-kicker">TOTAL CASES</p>
            <h2>{analytics.total_cases || 0}</h2>
          </div>
          <div className="module-card">
            <p className="module-kicker">OPEN</p>
            <h2>{analytics.by_status?.OPEN || 0}</h2>
          </div>
          <div className="module-card">
            <p className="module-kicker">RESOLVED</p>
            <h2>{analytics.by_status?.RESOLVED || 0}</h2>
          </div>
          <div className="module-card">
            <p className="module-kicker">APPEALED</p>
            <h2>{analytics.by_status?.APPEALED || 0}</h2>
          </div>
        </section>
      )}

      <section className="module-card">
        <h2>Log a case</h2>
        <form className="module-form" onSubmit={handleSubmit}>
          <label className="disciplinary-employee-field">Employee
            <input
              required
              role="combobox"
              aria-autocomplete="list"
              aria-expanded={employeeListOpen}
              aria-controls="disciplinary-employee-options"
              autoComplete="off"
              value={employeeSearch}
              onFocus={() => setEmployeeListOpen(true)}
              onBlur={() => setTimeout(() => setEmployeeListOpen(false), 150)}
              onChange={(e) => {
                setEmployeeSearch(e.target.value)
                setForm({ ...form, employee_id: '' })
                setEmployeeListOpen(true)
              }}
              onKeyDown={(e) => {
                if (e.key === 'Escape') setEmployeeListOpen(false)
              }}
              placeholder="Search by employee or department"
            />
            {employeeListOpen && (
              <ul id="disciplinary-employee-options" className="disciplinary-employee-options">
                {employeesLoading ? (
                  <li className="disciplinary-employee-empty">Loading employees…</li>
                ) : filteredEmployees.length > 0 ? filteredEmployees.map((employee) => (
                  <li key={employee.id}>
                    <button type="button" onMouseDown={(e) => e.preventDefault()} onClick={() => selectEmployee(employee)}>
                      <strong>{employeeName(employee)}</strong>
                      <span>
                        {employee.department_name || employee.legacy_department || 'Department not recorded'}
                        {employee.employee_number ? ` · ${employee.employee_number}` : ''}
                      </span>
                    </button>
                  </li>
                )) : (
                  <li className="disciplinary-employee-empty">
                    {employeeOptions.length ? 'No employees match your search.' : 'No employees available.'}
                  </li>
                )}
              </ul>
            )}
          </label>
          <label>Incident date
            <input type="date" required value={form.incident_date}
              onChange={(e) => setForm({ ...form, incident_date: e.target.value })} />
          </label>
          <label>Case type
            <select value={form.case_type}
              onChange={(e) => setForm({ ...form, case_type: e.target.value })}>
              <option value="DISCIPLINARY">Disciplinary</option>
              <option value="GRIEVANCE">Grievance</option>
              <option value="INVESTIGATION">Investigation</option>
              <option value="APPEAL">Appeal</option>
            </select>
          </label>
          <label>Category
            <select value={form.category}
              onChange={(e) => setForm({ ...form, category: e.target.value })}>
              <option value="">— Select —</option>
              <option value="MISCONDUCT">Misconduct</option>
              <option value="ABSENCE">Absence</option>
              <option value="PERFORMANCE">Performance</option>
              <option value="HARASSMENT">Harassment</option>
              <option value="THEFT">Theft</option>
              <option value="POLICY_BREACH">Policy breach</option>
              <option value="SAFETY">Safety</option>
              <option value="OTHER">Other</option>
            </select>
          </label>
          <label>Severity
            <select value={form.severity}
              onChange={(e) => setForm({ ...form, severity: e.target.value })}>
              <option value="">— Select —</option>
              <option value="MINOR">Minor</option>
              <option value="MODERATE">Moderate</option>
              <option value="SERIOUS">Serious</option>
              <option value="GROSS">Gross misconduct</option>
            </select>
          </label>
          <label>Policy breached
            <input value={form.policy_breached}
              onChange={(e) => setForm({ ...form, policy_breached: e.target.value })}
              placeholder="e.g., Code of Conduct §4.2" />
          </label>
          <label style={{ display: 'flex', alignItems: 'center', gap: 8, gridColumn: '1 / -1' }}>
            <input type="checkbox" checked={form.confidential}
              onChange={(e) => setForm({ ...form, confidential: e.target.checked })} />
            Confidential case
          </label>
          <label style={{ gridColumn: '1 / -1' }}>Description
            <textarea required rows={3} value={form.description}
              onChange={(e) => setForm({ ...form, description: e.target.value })}
              placeholder="What happened?" />
          </label>
          <label style={{ gridColumn: '1 / -1' }}>Action taken
            <textarea rows={2} value={form.action_taken}
              onChange={(e) => setForm({ ...form, action_taken: e.target.value })}
              placeholder="Immediate action taken, if any" />
          </label>
          <button className="btn-primary" type="submit" disabled={submitting || !form.employee_id} style={{ gridColumn: '1 / -1' }}>
            {submitting ? 'Logging…' : 'Log case'}
          </button>
        </form>
      </section>

      <section className="module-card">
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
          <div>
            <h2>{caseViewTitles[caseView]}</h2>
            <p>Review cases, resolution reports, and appeals.</p>
          </div>
          <button className="module-secondary-button" type="button" onClick={loadCases}>Refresh</button>
        </div>
        <div role="tablist" aria-label="Disciplinary case views" style={{ display: 'flex', gap: 8, flexWrap: 'wrap', marginBottom: 16 }}>
          {[
            ['ALL', 'All cases'],
            ['OPEN', 'Open cases'],
            ['RESOLVED', 'Resolution reports'],
            ['APPEALED', 'Appeals'],
          ].map(([view, label]) => (
            <button
              key={view}
              type="button"
              role="tab"
              aria-selected={caseView === view}
              className={caseView === view ? 'btn-primary' : 'module-secondary-button'}
              onClick={() => setCaseView(view)}
            >
              {label}
            </button>
          ))}
        </div>
        {visibleCases.length === 0 ? (
          <p className="module-empty">
            {caseView === 'ALL' ? 'No disciplinary cases have been logged.' : `No ${caseViewTitles[caseView].toLowerCase()} to display.`}
          </p>
        ) : (
          <div style={{ overflowX: 'auto' }}>
            <table className="module-table" style={{ width: '100%' }}>
              <thead>
                <tr>
                  <th>Case #</th>
                  <th>Employee</th>
                  <th>Date</th>
                  <th>Type</th>
                  <th>Category</th>
                  <th>Severity</th>
                  <th>Status</th>
                  {caseView === 'RESOLVED' && <th>Resolution report</th>}
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                {visibleCases.map((c) => (
                  <tr key={c.id}>
                    <td>{c.case_number || '—'}</td>
                    <td>{c.employee_id?.slice(0, 8)}</td>
                    <td>{c.incident_date}</td>
                    <td>{c.case_type || '—'}</td>
                    <td>{c.category || '—'}</td>
                    <td>{c.severity || '—'}</td>
                    <td>{c.status}</td>
                    {caseView === 'RESOLVED' && (
                      <td style={{ whiteSpace: 'pre-wrap' }}>{c.resolution_note || 'See the case for its recorded outcome.'}</td>
                    )}
                    <td>
                      <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap' }}>
                        <button className="module-secondary-button" type="button"
                          onClick={() => navigate(`/disciplinary/${c.id}?tab=overview`)}>
                          View
                        </button>
                        {c.status === 'OPEN' && (
                          <button className="module-secondary-button" type="button"
                            onClick={() => navigate(`/disciplinary/${c.id}?tab=resolution`)}>
                            Resolve
                          </button>
                        )}
                        {(c.status === 'RESOLVED' || c.status === 'APPEALED') && (
                          <>
                            <button className="module-secondary-button" type="button"
                              onClick={() => navigate(`/disciplinary/${c.id}?tab=resolution`)}>
                              Resolution report
                            </button>
                          </>
                        )}
                        {c.status === 'RESOLVED' && (
                          <button className="module-secondary-button" type="button"
                            onClick={() => navigate(`/disciplinary/${c.id}?tab=appeal`)}>
                            Appeal
                          </button>
                        )}
                        {c.status === 'APPEALED' && (
                          <button className="module-secondary-button" type="button"
                            onClick={() => navigate(`/disciplinary/${c.id}?tab=appeal`)}>
                            Review appeal
                          </button>
                        )}
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </section>
    </div>
  )
}

export default DisciplinaryDashboard
