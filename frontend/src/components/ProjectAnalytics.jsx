import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { getAnalytics, getModuleError } from '../api/peopleModules.js'
import './ProjectAnalytics.css'

const HR_ROLES = ['HR', 'HR_ADMIN', 'ADMIN', 'MANAGEMENT', 'DEVELOPER']
const MODULE_ROUTES = {
  employees: '/employees',
  attendance: '/attendance',
  leave: '/leave',
  performance: '/performance',
  recruitment: '/recruitment',
  onboarding: '/onboarding',
  contracts: '/contracts',
  payroll: '/payroll',
  disciplinary: '/disciplinary',
  exit: '/exit',
  training: '/training',
}
let analyticsCache = null
let analyticsCacheTime = 0
let analyticsRequest = null
const SUMMARY_LABELS = [
  ['active_employees', 'Active employees'],
  ['gross_payroll_recorded', 'Gross payroll recorded'],
  ['open_requisitions', 'Open requisitions'],
  ['candidates_in_pipeline', 'Candidates in pipeline'],
  ['employees_onboarding', 'Employees onboarding'],
  ['pending_leave', 'Leave awaiting review'],
  ['pending_performance_reviews', 'Performance awaiting HOD'],
  ['contracts_expiring_30d', 'Contracts expiring in 30 days'],
  ['open_disciplinary_cases', 'Open disciplinary cases'],
  ['pending_exit_clearances', 'Exit clearances pending'],
  ['pending_payroll_cycles', 'Payroll cycles not posted'],
  ['upcoming_training_sessions', 'Upcoming training sessions'],
]

function formatValue(value, format = 'number') {
  if (format === 'currency') {
    return new Intl.NumberFormat(undefined, {
      style: 'currency',
      currency: 'UGX',
      maximumFractionDigits: 0,
    }).format(Number(value || 0))
  }
  if (format === 'rating') return `${Number(value || 0).toFixed(1)} / 5`
  if (format === 'hours') return `${Number(value || 0).toLocaleString()} hrs`
  return Number(value || 0).toLocaleString()
}

function BarChart({ items, title, currency = false, compact = false }) {
  if (!items?.length) {
    return <p className="project-analytics-empty">No records available for this report yet.</p>
  }
  const maximum = Math.max(...items.map(item => Number(item.value) || 0), 1)
  return (
    <div className={`project-analytics-bars${compact ? ' compact' : ''}`} role="img" aria-label={title}>
      {items.map((item, index) => {
        const value = Number(item.value) || 0
        const width = value > 0 ? Math.max((value / maximum) * 100, 1) : 0
        return (
          <div className="project-analytics-bar-row" key={`${item.label}-${index}`} aria-label={`${item.label}: ${formatValue(value, currency ? 'currency' : 'number')}`}>
            <span className="project-analytics-bar-label" title={item.label}>{item.label}</span>
            <span className="project-analytics-bar-track">
              <span className="project-analytics-bar-fill" style={{ width: `${width}%` }} />
            </span>
            <strong className="project-analytics-bar-value">{formatValue(value, currency ? 'currency' : 'number')}</strong>
          </div>
        )
      })}
    </div>
  )
}

function ModuleReport({ moduleKey, report, central = false }) {
  return (
    <article className={`project-analytics-module${central ? ' central' : ''}`}>
      <header className="project-analytics-module-header">
        <div>
          <h2>{report.title}</h2>
          <p>{report.description}</p>
        </div>
        {MODULE_ROUTES[moduleKey] && <Link to={MODULE_ROUTES[moduleKey]}>Open module</Link>}
      </header>
      <div className="project-analytics-metrics">
        {report.metrics.map(metric => (
          <div className="project-analytics-metric" key={metric.label}>
            <span>{metric.label}</span>
            <strong>{formatValue(metric.value, metric.format)}</strong>
          </div>
        ))}
      </div>
      <h3 className="project-analytics-chart-title">{report.chart_title}</h3>
      <BarChart
        items={report.distribution}
        title={report.chart_title}
        currency={moduleKey === 'payroll'}
        compact={!central}
      />
      {central && report.trend?.length > 0 && moduleKey !== 'payroll' && (
        <>
          <h3 className="project-analytics-chart-title">{report.title} activity by period</h3>
          <BarChart items={report.trend} title={`${report.title} activity by period`} compact />
        </>
      )}
    </article>
  )
}

function fetchProjectAnalytics(force = false) {
  if (!force && analyticsCache && Date.now() - analyticsCacheTime < 60000) {
    return Promise.resolve(analyticsCache)
  }
  if (!force && analyticsRequest) return analyticsRequest
  analyticsRequest = getAnalytics()
    .then(data => {
      analyticsCache = data
      analyticsCacheTime = Date.now()
      return data
    })
    .finally(() => { analyticsRequest = null })
  return analyticsRequest
}

function loadAnalytics(setData, setError, setLoading) {
  setLoading(true)
  setError('')
  fetchProjectAnalytics(true)
    .then(setData)
    .catch(error => setError(getModuleError(error)))
    .finally(() => setLoading(false))
}

export function ModuleInsights({ moduleKey }) {
  const role = (window.localStorage.getItem('role') || '').toUpperCase()
  const canView = HR_ROLES.includes(role) || (role === 'FINANCE' && moduleKey === 'payroll')
  const [data, setData] = useState(null)
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    if (!canView) return undefined
    let active = true
    setLoading(true)
    setError('')
    fetchProjectAnalytics()
      .then(result => { if (active) setData(result) })
      .catch(requestError => { if (active) setError(getModuleError(requestError)) })
      .finally(() => { if (active) setLoading(false) })
    return () => { active = false }
  }, [canView, moduleKey])

  if (!canView) return null
  const report = data?.modules?.[moduleKey]
  return (
    <section className="project-analytics-inline" aria-label={`${report?.title || 'Module'} report`}>
      <div className="project-analytics-inline-heading">
        <div>
          <p className="eyebrow">MODULE REPORT</p>
          <h2>{report?.title || 'Module insights'}</h2>
        </div>
        {HR_ROLES.includes(role) && <Link to="/analytics">Project-wide analytics</Link>}
      </div>
      {loading ? <p className="project-analytics-empty" role="status">Loading module report…</p> : error ? (
        <div className="project-analytics-error" role="alert">
          <span>{error}</span>
          <button type="button" onClick={() => loadAnalytics(setData, setError, setLoading)}>Retry</button>
        </div>
      ) : report ? <ModuleReport moduleKey={moduleKey} report={report} /> : (
        <p className="project-analytics-empty">No report data is available for this module.</p>
      )}
    </section>
  )
}

function PayrollTrend({ rows }) {
  if (!rows?.length) return <p className="project-analytics-empty">No payroll cycles have been recorded yet.</p>
  const maximum = Math.max(...rows.flatMap(row => [row.gross, row.net, row.tax].map(Number)), 1)
  return (
    <div className="project-analytics-trend" role="img" aria-label="Gross, net pay, and tax totals by payroll cycle">
      <div className="project-analytics-legend">
        <span><i className="gross" />Gross pay</span>
        <span><i className="net" />Net pay</span>
        <span><i className="tax" />Tax</span>
      </div>
      {rows.map(row => (
        <div className="project-analytics-trend-row" key={row.label}>
          <strong>{row.label}</strong>
          <div className="project-analytics-trend-bars">
            {['gross', 'net', 'tax'].map(key => (
              <div className="project-analytics-trend-bar" key={key}>
                <span className={key} style={{ width: `${Math.max((Number(row[key]) / maximum) * 100, row[key] ? 1 : 0)}%` }} />
                <small>{key.toUpperCase()} {formatValue(row[key], 'currency')}</small>
              </div>
            ))}
          </div>
        </div>
      ))}
    </div>
  )
}

function exportReport(data) {
  const rows = [['Module', 'Report', 'Value']]
  Object.values(data.modules || {}).forEach(report => {
    report.metrics.forEach(metric => rows.push([report.title, metric.label, metric.value]))
    report.distribution.forEach(item => rows.push([report.title, item.label, item.value]))
  })
  const csv = rows.map(row => row.map(value => `"${String(value ?? '').replaceAll('"', '""')}"`).join(',')).join('\r\n')
  const url = URL.createObjectURL(new Blob([csv], { type: 'text/csv;charset=utf-8' }))
  const link = document.createElement('a')
  link.href = url
  link.download = 'hrms-project-analytics.csv'
  link.click()
  URL.revokeObjectURL(url)
}

export default function ProjectAnalyticsDashboard() {
  const [data, setData] = useState(null)
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    let active = true
    fetchProjectAnalytics()
      .then(result => { if (active) setData(result) })
      .catch(requestError => { if (active) setError(getModuleError(requestError)) })
      .finally(() => { if (active) setLoading(false) })
    return () => { active = false }
  }, [])

  return (
    <section className="project-analytics-page">
      <header className="project-analytics-page-heading">
        <div>
          <p className="eyebrow">WORKFORCE INSIGHTS</p>
          <h1>Project analytics and reports</h1>
          <p>One live view of workforce, attendance, leave, hiring, onboarding, payroll, compliance, and training.</p>
        </div>
        <div className="project-analytics-page-actions">
          {data && <button className="module-secondary-button" type="button" onClick={() => exportReport(data)}>Export report CSV</button>}
          <button className="module-secondary-button" type="button" onClick={() => loadAnalytics(setData, setError, setLoading)} disabled={loading}>Refresh reports</button>
        </div>
      </header>
      {error && <p className="project-analytics-error" role="alert">{error}</p>}
      {loading ? <p className="project-analytics-empty" role="status">Loading project reports…</p> : data && (
        <>
          <section className="project-analytics-summary" aria-label="Key organization metrics">
            {SUMMARY_LABELS.filter(([key]) => data.summary?.[key] !== undefined).map(([key, label]) => (
              <article className="project-analytics-summary-card" key={key}>
                <span>{label}</span>
                <strong>{formatValue(data.summary[key], key === 'gross_payroll_recorded' ? 'currency' : 'number')}</strong>
              </article>
            ))}
          </section>
          {data.workflow?.length > 0 && (
            <section className="project-analytics-section">
              <header>
                <h2>Employee lifecycle and project flow</h2>
                <p>Current records at each stage. These figures are snapshots, not additive totals.</p>
              </header>
              <BarChart items={data.workflow} title="Current employee lifecycle and project flow" />
            </section>
          )}
          {data.modules?.payroll?.trend?.length > 0 && (
            <section className="project-analytics-section">
              <header>
                <h2>Payroll across cycles</h2>
                <p>Recorded gross pay, net pay, and tax totals for each pay period.</p>
              </header>
              <PayrollTrend rows={data.modules.payroll.trend} />
            </section>
          )}
          <section className="project-analytics-section">
            <header>
              <h2>Reports by module</h2>
              <p>Each chart is calculated from current HRMS records; empty modules are clearly shown as having no data.</p>
            </header>
            <div className="project-analytics-module-grid">
              {Object.entries(data.modules || {}).map(([moduleKey, report]) => (
                <ModuleReport key={moduleKey} moduleKey={moduleKey} report={report} central />
              ))}
            </div>
          </section>
        </>
      )}
      {data?.generated_at && <p className="project-analytics-generated">Report data refreshed {new Date(data.generated_at).toLocaleString()}.</p>}
    </section>
  )
}
