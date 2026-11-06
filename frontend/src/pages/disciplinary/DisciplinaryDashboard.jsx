import { useCallback, useEffect, useState } from 'react'
import {
  createDisciplinaryCase,
  getDisciplinaryCases,
  getModuleError,
} from '../../api/peopleModules.js'
import '../ModuleDashboards.css'

const HR_ROLES = new Set(['HR', 'HR_ADMIN'])

function DisciplinaryDashboard() {
  const role = (window.localStorage.getItem('role') || '').toUpperCase()
  const canManageCases = HR_ROLES.has(role)
  const [cases, setCases] = useState([])
  const [loading, setLoading] = useState(true)
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState('')
  const [notice, setNotice] = useState('')

  const loadCases = useCallback(async () => {
    setError('')
    try {
      setCases(await getDisciplinaryCases())
    } catch (requestError) {
      setError(getModuleError(requestError))
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    if (canManageCases) loadCases()
    else setLoading(false)
  }, [canManageCases, loadCases])

  async function handleSubmit(event) {
    event.preventDefault()
    setSubmitting(true)
    setError('')
    setNotice('')
    const form = event.currentTarget
    const formData = new FormData(form)
    const incidentDate = formData.get('incident_date')
    const payload = {
      employee_id: formData.get('employee_id').trim(),
      incident_date: incidentDate,
      description: formData.get('description').trim(),
      action_taken: formData.get('action_taken').trim() || null,
    }

    try {
      await createDisciplinaryCase(payload)
      form.reset()
      setNotice('Disciplinary case logged.')
      await loadCases()
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
          <p className="eyebrow">EMPLOYEE RELATIONS</p>
          <h1>Disciplinary</h1>
          <p>Record and review employee relations cases.</p>
        </div>
      </header>

      {error && <p className="module-feedback error" role="alert">{error}</p>}
      {notice && <p className="module-feedback success" role="status">{notice}</p>}

      {!canManageCases ? (
        <section className="module-card"><p className="module-empty">Only HR can access disciplinary cases.</p></section>
      ) : (
        <>
          <section className="module-card">
            <h2>Log a case</h2>
            <form className="module-form" onSubmit={handleSubmit}>
              <label>
                Employee ID
                <input name="employee_id" required />
              </label>
              <label>
                Incident date
                <input name="incident_date" type="date" required />
              </label>
              <label className="module-form-wide">
                Description
                <textarea name="description" maxLength="500" rows="3" required />
              </label>
              <label className="module-form-wide">
                Action taken
                <textarea name="action_taken" maxLength="255" rows="2" />
              </label>
              <button className="btn-primary" type="submit" disabled={submitting}>
                {submitting ? 'Saving…' : 'Log case'}
              </button>
            </form>
          </section>

          <section className="module-card">
            <div className="module-card-heading">
              <div><h2>All cases</h2><p>Disciplinary records across the company.</p></div>
              <button className="module-secondary-button" type="button" onClick={loadCases} disabled={loading}>Refresh</button>
            </div>
            {loading ? (
              <p className="module-empty" role="status">Loading cases…</p>
            ) : cases.length === 0 ? (
              <p className="module-empty">No disciplinary cases have been logged.</p>
            ) : (
              <div className="module-table-scroll">
                <table className="module-table">
                  <thead><tr><th>Employee ID</th><th>Incident date</th><th>Description</th><th>Action taken</th><th>Status</th></tr></thead>
                  <tbody>
                    {cases.map((item) => (
                      <tr key={item.id}>
                        <td>{item.employee_id}</td>
                        <td>{item.incident_date}</td>
                        <td>{item.description}</td>
                        <td>{item.action_taken || '—'}</td>
                        <td><span className="module-status">{item.status}</span></td>
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

export default DisciplinaryDashboard
