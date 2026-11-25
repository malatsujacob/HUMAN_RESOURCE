import { useCallback, useEffect, useMemo, useState } from 'react'
import {
  getEmployeeExits,
  getEmployees,
  getModuleError,
  initiateEmployeeExit,
} from '../../api/peopleModules.js'
import '../ModuleDashboards.css'

const HR_ROLES = new Set(['HR', 'HR_ADMIN', 'ADMIN', 'MANAGEMENT', 'DEVELOPER'])
const CLEARANCE_ITEMS = ['Department handover', 'Finance clearance', 'Equipment return', 'HR exit interview']

function ExitDashboard() {
  const role = (window.localStorage.getItem('role') || '').toUpperCase()
  const canManageExits = HR_ROLES.has(role)
  const [exits, setExits] = useState([])
  const [employees, setEmployees] = useState([])
  const [employeeId, setEmployeeId] = useState('')
  const [employeeSearch, setEmployeeSearch] = useState('')
  const [employeeListOpen, setEmployeeListOpen] = useState(false)
  const [employeesLoading, setEmployeesLoading] = useState(true)
  const [loading, setLoading] = useState(true)
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState('')
  const [notice, setNotice] = useState('')

  const loadExits = useCallback(async () => {
    setError('')
    try {
      setExits(await getEmployeeExits())
    } catch (requestError) {
      setError(getModuleError(requestError))
    } finally {
      setLoading(false)
    }
  }, [])

  const loadEmployees = useCallback(async () => {
    try {
      setEmployees(await getEmployees())
    } catch (requestError) {
      setError(getModuleError(requestError))
    } finally {
      setEmployeesLoading(false)
    }
  }, [])

  useEffect(() => {
    if (canManageExits) {
      loadExits()
      loadEmployees()
    }
    else setLoading(false)
  }, [canManageExits, loadExits, loadEmployees])

  const employeeOptions = useMemo(() => employees
    .filter((employee) => !['EXITED', 'INACTIVE'].includes(String(employee.status || '').toUpperCase())
      && !exits.some((item) => item.employee_id === employee.id && item.clearance_status !== 'CLEARED'))
    .slice()
    .sort((a, b) => employeeName(a).localeCompare(employeeName(b))), [employees, exits])
  const filteredEmployees = employeeOptions.filter((employee) => {
    const search = employeeSearch.trim().toLocaleLowerCase()
    return !search || [
      employeeName(employee),
      employee.employee_number,
      employee.department_name,
      employee.legacy_department,
      employee.job_title,
    ].some((value) => String(value || '').toLocaleLowerCase().includes(search))
  })

  function employeeName(employee) {
    return employee.full_name
      || [employee.first_name, employee.middle_name, employee.last_name].filter(Boolean).join(' ')
      || `Employee ${employee.employee_number || ''}`.trim()
  }

  function selectEmployee(employee) {
    setEmployeeId(employee.id)
    setEmployeeSearch(employeeName(employee))
    setEmployeeListOpen(false)
  }

  async function handleSubmit(event) {
    event.preventDefault()
    setSubmitting(true)
    setError('')
    setNotice('')
    const form = event.currentTarget
    const formData = new FormData(form)
    try {
      await initiateEmployeeExit({
        employee_id: employeeId,
        last_working_day: formData.get('last_working_day'),
        reason: formData.get('reason').trim(),
      })
      form.reset()
      setEmployeeId('')
      setEmployeeSearch('')
      setNotice('Employee exit initiated. Clearance is pending; any active contract ends on the last working day.')
      await loadExits()
    } catch (requestError) {
      setError(getModuleError(requestError))
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <section className="module-dashboard">
      <header className="module-dashboard-heading">
        <div>
          <p className="eyebrow">EMPLOYEE LIFECYCLE</p>
          <h1>Exit &amp; Clearance</h1>
          <p>Initiate employee exits and track clearance progress.</p>
        </div>
      </header>

      {error && <p className="module-feedback error" role="alert">{error}</p>}
      {notice && <p className="module-feedback success" role="status">{notice}</p>}

      {!canManageExits ? (
        <section className="module-card"><p className="module-empty">Only HR can manage employee exits.</p></section>
      ) : (
        <>
          <section className="module-card">
            <h2>Initiate exit</h2>
            <form className="module-form" onSubmit={handleSubmit}>
              <label className="employee-picker-field">
                Employee
                <input
                  required
                  role="combobox"
                  aria-autocomplete="list"
                  aria-expanded={employeeListOpen}
                  aria-controls="exit-employee-options"
                  autoComplete="off"
                  value={employeeSearch}
                  onFocus={() => setEmployeeListOpen(true)}
                  onBlur={() => setTimeout(() => setEmployeeListOpen(false), 150)}
                  onChange={(event) => {
                    setEmployeeSearch(event.target.value)
                    setEmployeeId('')
                    setEmployeeListOpen(true)
                  }}
                  onKeyDown={(event) => {
                    if (event.key === 'Escape') setEmployeeListOpen(false)
                  }}
                  placeholder="Search by name, department, or employee number"
                />
                {employeeListOpen && (
                  <ul id="exit-employee-options" className="employee-picker-options">
                    {employeesLoading ? (
                      <li className="disciplinary-employee-empty">Loading employees…</li>
                    ) : filteredEmployees.length > 0 ? filteredEmployees.map((employee) => (
                      <li key={employee.id}>
                        <button type="button" onMouseDown={(event) => event.preventDefault()} onClick={() => selectEmployee(employee)}>
                          <strong>{employeeName(employee)}</strong>
                          <span>
                            {employee.department_name || employee.legacy_department || 'Department not recorded'}
                            {employee.employee_number ? ` · ${employee.employee_number}` : ''}
                          </span>
                        </button>
                      </li>
                    )) : (
                      <li className="disciplinary-employee-empty">
                        {employeeOptions.length ? 'No employees match your search.' : 'No eligible employees available.'}
                      </li>
                    )}
                  </ul>
                )}
              </label>
              <label>
                Last working day
                <input name="last_working_day" type="date" required />
              </label>
              <label className="module-form-wide">
                Reason
                <textarea name="reason" maxLength="500" rows="3" required />
              </label>
              <button className="btn-primary" type="submit" disabled={submitting || !employeeId}>
                {submitting ? 'Saving…' : 'Initiate exit'}
              </button>
            </form>
          </section>

          <section className="module-card">
            <div className="module-card-heading">
              <div><h2>Clearance checklist</h2><p>Monitor each exiting employee’s overall clearance status.</p></div>
              <button className="module-secondary-button" type="button" onClick={loadExits} disabled={loading}>Refresh</button>
            </div>
            {loading ? (
              <p className="module-empty" role="status">Loading exit records…</p>
            ) : exits.length === 0 ? (
              <p className="module-empty">No exit records have been initiated.</p>
            ) : (
              <div className="module-table-scroll">
                <table className="module-table">
                  <thead><tr><th>Employee ID</th><th>Last working day</th><th>Reason</th><th>Checklist items</th><th>Clearance status</th></tr></thead>
                  <tbody>
                    {exits.map((item) => (
                      <tr key={item.id}>
                        <td>
                          {(() => {
                            const employee = employees.find((record) => record.id === item.employee_id)
                            return (
                              <>
                                <strong>{employee ? employeeName(employee) : item.employee_id}</strong>
                                {employee && <small style={{ display: 'block' }}>{employee.employee_number} · {employee.department_name || employee.legacy_department || 'Department not recorded'}</small>}
                              </>
                            )
                          })()}
                        </td>
                        <td>{item.last_working_day}</td>
                        <td>{item.reason}</td>
                        <td>
                          <ul className="clearance-list">
                            {CLEARANCE_ITEMS.map((label) => (
                              <li key={label}>
                                <span aria-hidden="true">{item.clearance_status === 'CLEARED' ? '✓' : '○'}</span>
                                {label}
                              </li>
                            ))}
                          </ul>
                        </td>
                        <td><span className={`module-status ${item.clearance_status.toLowerCase()}`}>{item.clearance_status}</span></td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </section>
        </>
      )}
    </section>
  )
}

export default ExitDashboard
