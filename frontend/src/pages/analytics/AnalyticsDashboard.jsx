import { useEffect, useState } from 'react'
import { getAnalytics, getModuleError } from '../../api/peopleModules.js'
import '../ModuleDashboards.css'

const analyticsCards = [
  { key: 'total_employees', title: 'Total Employees', format: (value) => Number(value || 0).toLocaleString() },
  { key: 'total_payroll_cost', title: 'Total Payroll', format: (value) => new Intl.NumberFormat(undefined, { style: 'currency', currency: 'UGX', maximumFractionDigits: 0 }).format(Number(value || 0)) },
  { key: 'open_positions', title: 'Open Positions', format: (value) => Number(value || 0).toLocaleString() },
]

function AnalyticsDashboard() {
  const [analytics, setAnalytics] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    let active = true
    getAnalytics()
      .then((data) => {
        if (active) setAnalytics(data)
      })
      .catch((requestError) => {
        if (active) setError(getModuleError(requestError))
      })
      .finally(() => {
        if (active) setLoading(false)
      })
    return () => {
      active = false
    }
  }, [])

  return (
    <section className="module-dashboard">
      <header className="module-dashboard-heading">
        <div>
          <p className="eyebrow">WORKFORCE INSIGHTS</p>
          <h1>Analytics</h1>
          <p>A high-level snapshot of key HR metrics.</p>
        </div>
      </header>

      {error && <p className="module-feedback error" role="alert">{error}</p>}
      {loading ? (
        <p className="module-empty" role="status">Loading analytics…</p>
      ) : analytics && (
        <div className="analytics-card-grid">
          {analyticsCards.map(({ key, title, format }) => (
            <article className="analytics-card" key={key}>
              <span>{title}</span>
              <strong>{format(analytics[key])}</strong>
            </article>
          ))}
        </div>
      )}
    </section>
  )
}

export default AnalyticsDashboard
