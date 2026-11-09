import { useCallback, useEffect, useState } from 'react'
import { Navigate } from 'react-router-dom'
import { getModuleError, getPerformanceReviews, getQuarterlyPerformanceRanking } from '../../api/peopleModules.js'
import '../ModuleDashboards.css'

const quarterNow = () => {
  const now = new Date()
  return `${now.getFullYear()}-Q${Math.ceil((now.getMonth() + 1) / 3)}`
}

function PerformanceDashboard() {
  const role = (window.localStorage.getItem('role') || '').toUpperCase()
  const [reviews, setReviews] = useState([])
  const [ranking, setRanking] = useState([])
  const [quarter, setQuarter] = useState(quarterNow())
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  const loadData = useCallback(async () => {
    setError('')
    setLoading(true)
    try {
      const [reviewRows, rankingData] = await Promise.all([
        getPerformanceReviews(), getQuarterlyPerformanceRanking(quarter),
      ])
      setReviews(reviewRows)
      setRanking(rankingData.ranking || [])
    } catch (requestError) {
      setError(getModuleError(requestError))
    } finally { setLoading(false) }
  }, [quarter])

  useEffect(() => { loadData() }, [loadData])

  // HODs complete their reviews within ESS so the team workflow stays in one place.
  if (role === 'HOD' || role === 'DEVELOPER') return <Navigate to="/ess?section=performance" replace />

  return (
    <section className="module-dashboard">
      <header className="module-dashboard-heading"><div><p className="eyebrow">PEOPLE DEVELOPMENT</p><h1>Performance</h1><p>Monthly self assessments, completed HOD ratings, and quarterly results.</p></div></header>
      {error && <p className="module-feedback error" role="alert">{error}</p>}
      <section className="module-card">
        <div className="module-card-heading"><div><h2>Quarterly ranking</h2><p>Average of completed monthly HOD ratings; ties favor employees with more months reviewed.</p></div><label>Quarter<select value={quarter} onChange={event => setQuarter(event.target.value)}>{[0,1,2,3].map(offset => {const current=new Date();const startMonth=Math.floor(current.getMonth()/3)*3;const start=new Date(current.getFullYear(),startMonth-offset*3,1);const q=Math.ceil((start.getMonth()+1)/3);const value=`${start.getFullYear()}-Q${q}`;return <option key={value} value={value}>{value}</option>})}</select></label></div>
        {loading ? <p className="module-empty">Loading quarterly ratings…</p> : ranking.length === 0 ? <p className="module-empty">No completed monthly ratings for {quarter}.</p> : <div className="module-table-scroll"><table className="module-table"><thead><tr><th>Rank</th><th>Employee</th><th>Department</th><th>Quarter score</th><th>Months rated</th></tr></thead><tbody>{ranking.map(row => <tr key={row.employee_id}><td>{row.rank}</td><td>{row.employee_name}</td><td>{row.department_name || '—'}</td><td>{row.quarter_rating}/5</td><td>{row.months_completed}</td></tr>)}</tbody></table></div>}
      </section>
      <section className="module-card"><div className="module-card-heading"><div><h2>{role === 'EMPLOYEE' ? 'My monthly assessments' : 'Monthly performance records'}</h2><p>Employees submit a self rating in ESS. HOD behavior indicators and final monthly rating are stored with the review.</p></div><button className="module-secondary-button" type="button" onClick={loadData} disabled={loading}>Refresh</button></div>
        {loading ? <p className="module-empty">Loading reviews…</p> : reviews.length === 0 ? <p className="module-empty">No monthly assessments recorded yet.</p> : <div className="module-table-scroll"><table className="module-table"><thead><tr>{role !== 'EMPLOYEE' && <th>Employee</th>}<th>Month</th><th>Self rating</th><th>Behavior score</th><th>HOD rating</th><th>HOD comments</th></tr></thead><tbody>{reviews.map(review => <tr key={review.id}>{role !== 'EMPLOYEE' && <td>{review.employee_name}</td>}<td>{review.review_period}</td><td>{review.self_rating ?? '—'}</td><td>{review.behavior_rating ?? 'Pending'}</td><td>{review.hod_rating ?? 'Pending'}</td><td>{review.hod_comments || review.self_comment || '—'}</td></tr>)}</tbody></table></div>}
      </section>
    </section>
  )
}

export default PerformanceDashboard
