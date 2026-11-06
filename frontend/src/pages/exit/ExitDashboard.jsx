import { useCallback, useEffect, useState } from 'react'
import {
  getEmployeeExits,
  getModuleError,
  initiateEmployeeExit,
} from '../../api/peopleModules.js'
import '../ModuleDashboards.css'

const HR_ROLES = new Set(['HR', 'HR_ADMIN'])
const CLEARANCE_ITEMS = ['Department handover', 'Finance clearance', 'Equipment return', 'HR exit interview']

function ExitDashboard() {
  const role = (window.localStorage.getItem('role') || '').toUpperCase()
  const canManageExits = HR_ROLES.has(role)
  const [exits, setExits] = useState([])
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

  useEffect(() => {
    if (canManageExits) loadExits()
    else setLoading(false)
  }, [canManageExits, loadExits])

  async function handleSubmit(event) {
    event.preventDefault()
    setSubmitting(true)
    setError('')
    setNotice('')
    const form = event.currentTarget
    const formData = new FormData(form)
    try {
      await initiateEmployeeExit({
        employee_id: formData.get('employee_id').trim(),
        last_working_day: formData.get('last_working_day'),
        reason: formData.get('reason').trim(),
      })
      form.reset()
      setNotice('Employee exit initiated. Clearance is pending.')
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
              <label>
                Employee ID
                <input name="employee_id" required />
              </label>
              <label>
                Last working day
                <input name="last_working_day" type="date" required />
              </label>
              <label className="module-form-wide">
                Reason
                <textarea name="reason" maxLength="500" rows="3" required />
              </label>
              <button className="btn-primary" type="submit" disabled={submitting}>
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
                        <td>{item.employee_id}</td>
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
