import { useEffect, useState } from 'react'
import axios from 'axios'
import './ESSPortal.css'

const API_BASE = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api'
const getApiConfig = () => ({ headers: { Authorization: `Bearer ${localStorage.getItem('token') || localStorage.getItem('access_token') || ''}` } })
const currentPeriod = () => {
  const now = new Date()
  return `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, '0')}`
}
const currentQuarter = () => {
  const now = new Date()
  return `${now.getFullYear()}-Q${Math.ceil((now.getMonth() + 1) / 3)}`
}
const emptyBehavior = {
  punctuality: 'ON_TIME', overtime_worked: false, task_completion: 'ON_TIME',
  efficiency: 'EFFICIENT', quality_of_work: 'MEETS_EXPECTATIONS', teamwork: 'GOOD',
  hod_rating: '', hod_comments: '',
}

export default function ESSPortal() {
  const role = (localStorage.getItem('role') || '').toUpperCase()
  const email = localStorage.getItem('email')
  const requestedTab = new URLSearchParams(window.location.search).get('section')
  const defaultTab = requestedTab === 'performance' || role === 'HOD' || role === 'DEVELOPER' ? 'performance' : 'profile'
  const [activeTab, setActiveTab] = useState(defaultTab)
  const [leaves, setLeaves] = useState([])
  const [pendingLeaves, setPendingLeaves] = useState([])
  const [reviews, setReviews] = useState([])
  const [teamReviews, setTeamReviews] = useState([])
  const [pendingReviews, setPendingReviews] = useState([])
  const [notifications, setNotifications] = useState([])
  const [quarterRanking, setQuarterRanking] = useState([])
  const [selectedReview, setSelectedReview] = useState(null)
  const [selfRating, setSelfRating] = useState('')
  const [selfComment, setSelfComment] = useState('')
  const [behavior, setBehavior] = useState(emptyBehavior)
  const [performanceBusy, setPerformanceBusy] = useState(false)
  const [performanceMessage, setPerformanceMessage] = useState('')
  const [reqData, setReqData] = useState({ job_title: '', min_education: 'Bachelor', min_experience: 2, description: '', department_code: 'TECH', max_applicants: 10 })
  const [message, setMessage] = useState('')
  const [reqSubmitting, setReqSubmitting] = useState(false)
  const isHOD = role === 'HOD' || role === 'DEVELOPER'
  const isHR = ['HR', 'HR_ADMIN', 'ADMIN', 'MANAGEMENT', 'DEVELOPER'].includes(role)
  const canReview = isHOD || isHR
  const apiConfig = getApiConfig()
  const alreadySubmitted = reviews.some(item => item.review_period === currentPeriod() && item.self_rating !== null)
  const behaviorScoreMap = { punctuality: { EARLY: 5, ON_TIME: 4, OCCASIONALLY_LATE: 3, FREQUENTLY_LATE: 1 }, task_completion: { AHEAD_OF_DEADLINE: 5, ON_TIME: 4, DELAYED: 2, INCOMPLETE: 1 }, efficiency: { HIGHLY_EFFICIENT: 5, EFFICIENT: 4, NEEDS_SUPPORT: 3, SLOW: 2 }, quality_of_work: { EXCEEDS_EXPECTATIONS: 5, MEETS_EXPECTATIONS: 4, NEEDS_IMPROVEMENT: 2, UNSATISFACTORY: 1 }, teamwork: { EXCELLENT: 5, GOOD: 4, DEVELOPING: 3, UNSATISFACTORY: 1 } }
  const liveBehaviorScore = Math.round(Object.entries(behaviorScoreMap).reduce((sum, [field, options]) => sum + options[behavior[field]], 0) / 5)

  const loadPerformance = async () => {
    try {
      const requests = [axios.get(`${API_BASE}/performance/mine`, apiConfig)]
      if (canReview) requests.push(axios.get(`${API_BASE}/performance/`, apiConfig))
      if (canReview) requests.push(axios.get(`${API_BASE}/performance/pending`, apiConfig))
      if (isHOD) requests.push(axios.get(`${API_BASE}/performance/notifications`, apiConfig))
      if (canReview) requests.push(axios.get(`${API_BASE}/performance/quarterly-ranking?quarter=${currentQuarter()}`, apiConfig))
      const responses = await Promise.all(requests)
      let index = 0
      setReviews(responses[index++].data)
      if (canReview) setTeamReviews(responses[index++].data)
      if (canReview) setPendingReviews(responses[index++].data)
      if (isHOD) setNotifications(responses[index++].data)
      if (canReview) setQuarterRanking(responses[index].data.ranking)
    } catch (error) {
      setPerformanceMessage(error.response?.data?.detail || 'Could not load performance information.')
    }
  }

  useEffect(() => {
    if (requestedTab === 'performance' || role === 'HOD' || role === 'DEVELOPER') setActiveTab('performance')
  }, [requestedTab, role])

  useEffect(() => {
    if (isHOD) {
      axios.get(`${API_BASE}/leave/pending`).then(res => setPendingLeaves(res.data)).catch(() => setPendingLeaves([]))
    }
    axios.get(`${API_BASE}/leave/my-history`).then(res => setLeaves(res.data)).catch(() => setLeaves([]))
    loadPerformance()
    // Load the ESS panels once for the signed-in role.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [isHOD, isHR])

  useEffect(() => {
    if (!isHOD) return undefined
    const timer = window.setInterval(async () => {
      try {
        const [pending, notices] = await Promise.all([
          axios.get(`${API_BASE}/performance/pending`, getApiConfig()),
          axios.get(`${API_BASE}/performance/notifications`, getApiConfig()),
        ])
        setPendingReviews(pending.data)
        setNotifications(notices.data)
      } catch { /* Existing inbox content remains visible during a temporary connection issue. */ }
    }, 30000)
    return () => window.clearInterval(timer)
  }, [isHOD])

  const handleSelfAssessment = async (event) => {
    event.preventDefault(); setPerformanceBusy(true); setPerformanceMessage('')
    try {
      await axios.post(`${API_BASE}/performance/self`, { review_period: currentPeriod(), self_rating: Number(selfRating), self_comment: selfComment }, apiConfig)
      setPerformanceMessage(`Your ${currentPeriod()} self assessment has been submitted to your HOD.`)
      setSelfRating(''); setSelfComment(''); await loadPerformance()
    } catch (error) {
      setPerformanceMessage(error.response?.data?.detail || 'Your self assessment could not be submitted.')
    } finally { setPerformanceBusy(false) }
  }

  const openReview = async (review) => {
    setSelectedReview(review); setBehavior(emptyBehavior); setPerformanceMessage('')
    const matching = notifications.find(item => !item.is_read && item.message.includes(review.employee_name) && item.message.includes(review.review_period))
    if (matching) {
      try {
        await axios.post(`${API_BASE}/performance/notifications/${matching.id}/read`, {}, apiConfig)
        setNotifications(list => list.map(item => item.id === matching.id ? { ...item, is_read: true } : item))
      } catch { /* The pending review remains available even if a notice could not be marked read. */ }
    }
  }

  const handleHodReview = async (event) => {
    event.preventDefault()
    if (!selectedReview) return
    setPerformanceBusy(true); setPerformanceMessage('')
    try {
      const payload = { ...behavior, overtime_worked: Boolean(behavior.overtime_worked), hod_rating: Number(behavior.hod_rating) }
      const { data } = await axios.post(`${API_BASE}/performance/${selectedReview.id}/hod-review`, payload, apiConfig)
      setPerformanceMessage(`Monthly review completed for ${data.employee_name}. Behavior score: ${data.behavior_rating}/5; final rating: ${data.hod_rating}/5.`)
      setSelectedReview(null); await loadPerformance()
    } catch (error) {
      setPerformanceMessage(error.response?.data?.detail || 'The monthly rating could not be saved.')
    } finally { setPerformanceBusy(false) }
  }

  const handleRequestHire = async (event) => {
    event.preventDefault(); setReqSubmitting(true); setMessage('')
    try {
      await axios.post(`${API_BASE}/recruitment/requisitions`, reqData, apiConfig)
      setMessage('Requisition submitted to HR for review. It will be published after approval.')
      setReqData({ job_title: '', min_education: 'Bachelor', min_experience: 2, description: '', department_code: 'TECH', max_applicants: 10 })
    } catch (requestError) {
      setMessage(requestError.response?.data?.detail || 'The requisition could not be submitted.')
    } finally { setReqSubmitting(false) }
  }

  return (
    <div className="ess-portal">
      <div className="ess-welcome"><div><p className="ess-kicker">EMPLOYEE SELF SERVICE</p><h1>Welcome, {email}</h1><p>Role: {role} · Your employee workspace</p></div></div>
      {message && <div className="ess-alert">{message}</div>}
      <div className="tabs ess-tabs">
        <button onClick={() => setActiveTab('profile')} className={`tab ${activeTab === 'profile' ? 'active' : ''}`}>My Profile</button>
        <button onClick={() => setActiveTab('leave')} className={`tab ${activeTab === 'leave' ? 'active' : ''}`}>My Leave</button>
        <button onClick={() => setActiveTab('performance')} className={`tab ${activeTab === 'performance' ? 'active' : ''}`}>Performance{isHOD && notifications.some(item => !item.is_read) && <span className="ess-notification-count">{notifications.filter(item => !item.is_read).length}</span>}</button>
        {isHOD && <button onClick={() => setActiveTab('team')} className={`tab ${activeTab === 'team' ? 'active' : ''}`}>Team Approvals</button>}
        {isHOD && <button onClick={() => setActiveTab('requisition')} className={`tab ${activeTab === 'requisition' ? 'active' : ''}`}>Request New Hire</button>}
      </div>

      {activeTab === 'profile' && <div className="card"><h2>My Profile</h2><p className="ess-muted">Your personal details, bank information, and documents are managed by HR.</p></div>}

      {activeTab === 'leave' && <div className="card"><h2>My Leave Requests</h2><table className="ess-table"><thead><tr><th>Type</th><th>Dates</th><th>Status</th></tr></thead><tbody>{leaves.map(item => <tr key={item.id}><td>{item.leave_type}</td><td>{item.start_date} to {item.end_date}</td><td>{item.status}</td></tr>)}</tbody></table></div>}

      {activeTab === 'performance' && <div className="ess-performance">
        {performanceMessage && <div className="ess-alert" role="status">{performanceMessage}</div>}
        <section className="card"><div className="ess-section-heading"><div><h2>Monthly self assessment</h2><p>Submit your assessment for {currentPeriod()}. Your HOD will be notified after submission.</p></div></div>
          {alreadySubmitted ? <p className="ess-muted">Your assessment for {currentPeriod()} is submitted. You can see the final monthly rating here after HOD review.</p> : <form className="ess-performance-form" onSubmit={handleSelfAssessment}>
            <label>Self rating<select value={selfRating} onChange={event => setSelfRating(event.target.value)} required><option value="">Select a rating</option><option value="5">5 · Outstanding</option><option value="4">4 · Exceeds expectations</option><option value="3">3 · Meets expectations</option><option value="2">2 · Needs improvement</option><option value="1">1 · Unsatisfactory</option></select></label>
            <label className="ess-wide">Reflection or achievements<textarea rows="3" maxLength="1000" value={selfComment} onChange={event => setSelfComment(event.target.value)} placeholder="Summarize your progress, achievements, or support needed this month." /></label>
            <button className="btn-primary" disabled={performanceBusy}>{performanceBusy ? 'Submitting…' : 'Submit monthly self assessment'}</button>
          </form>}
        </section>
        {canReview && <section className="card"><div className="ess-section-heading"><div><h2>HOD performance inbox</h2><p>Review employees after their monthly self assessment is submitted.</p></div><div className="ess-queue-actions"><span className="ess-pending-count">{pendingReviews.length} pending</span><button className="ess-cancel" type="button" onClick={loadPerformance}>Refresh</button></div></div>
          {isHOD && notifications.length > 0 && <div className="ess-notice-list"><strong>Notifications</strong>{notifications.slice(0,5).map(item => <p key={item.id} className={item.is_read ? 'read' : ''}>{item.title}: {item.message}</p>)}</div>}
          {pendingReviews.length === 0 ? <p className="ess-muted">No employee self assessments are waiting for a HOD rating.</p> : <div className="ess-review-list">{pendingReviews.map(review => <article className="ess-review-card" key={review.id}><div><strong>{review.employee_name}</strong><span>{review.department_name || 'Department'} · {review.review_period}</span><span>Self rating: {review.self_rating}/5</span>{review.self_comment && <p>Employee reflection: {review.self_comment}</p>}</div><button className="btn-primary" type="button" onClick={() => openReview(review)}>Review and rate</button></article>)}</div>}
        </section>}
        {canReview && <section className="card"><div className="ess-section-heading"><div><h2>{role === 'HOD' ? 'Department monthly records' : 'All monthly performance records'}</h2><p>{role === 'HOD' ? 'Your department’s self assessments and completed HOD reviews.' : 'Company-wide employee, HOD, and HR review records.'}</p></div><span className="ess-pending-count">{teamReviews.length} records</span></div>{teamReviews.length === 0 ? <p className="ess-muted">No monthly records have been submitted.</p> : <div className="ess-record-table-wrap"><table className="ess-table ess-record-table"><thead><tr><th>Employee</th><th>Month</th><th>Self</th><th>Punctuality</th><th>Overtime</th><th>Tasks</th><th>Efficiency</th><th>Quality</th><th>Teamwork</th><th>Behavior</th><th>Final</th><th>HOD comment</th></tr></thead><tbody>{teamReviews.map(row => <tr key={row.id}><td>{row.employee_name}</td><td>{row.review_period}</td><td>{row.self_rating ?? '—'}{row.self_comment ? <small>{row.self_comment}</small> : null}</td><td>{row.punctuality?.replaceAll('_',' ') || '—'}</td><td>{row.overtime_worked ? 'Yes' : row.overtime_worked === false ? 'No' : '—'}</td><td>{row.task_completion?.replaceAll('_',' ') || '—'}</td><td>{row.efficiency?.replaceAll('_',' ') || '—'}</td><td>{row.quality_of_work?.replaceAll('_',' ') || '—'}</td><td>{row.teamwork?.replaceAll('_',' ') || '—'}</td><td>{row.behavior_rating ?? 'Pending'}</td><td>{row.hod_rating ?? 'Pending'}</td><td>{row.hod_comments || '—'}</td></tr>)}</tbody></table></div>}</section>}
        {canReview && <section className="card"><h2>Quarterly performance</h2><p className="ess-muted">Completed monthly HOD ratings contribute to {currentQuarter()} rankings.</p>{quarterRanking.length === 0 ? <p className="ess-muted">No completed monthly ratings for this quarter yet.</p> : <table className="ess-table"><thead><tr><th>Rank</th><th>Employee</th><th>Department</th><th>Quarter score</th><th>Months rated</th></tr></thead><tbody>{quarterRanking.map(row => <tr key={row.employee_id}><td>{row.rank}</td><td>{row.employee_name}</td><td>{row.department_name || '—'}</td><td>{row.quarter_rating}/5</td><td>{row.months_completed}</td></tr>)}</tbody></table>}</section>}
        <section className="card"><h2>My monthly records</h2>{reviews.length === 0 ? <p className="ess-muted">Your submitted and completed monthly ratings will appear here.</p> : <div className="ess-review-list">{reviews.map(review => <article className="ess-review-card" key={review.id}><div><strong>{review.review_period} · Self {review.self_rating ?? '—'}/5{review.hod_rating !== null ? ` · HOD ${review.hod_rating}/5` : ''}</strong><span>{review.hod_rating !== null ? `Behavior score ${review.behavior_rating}/5 · ${review.hod_comments || 'No HOD comment'}` : review.self_rating !== null ? 'Waiting for HOD review' : 'Self assessment not submitted'}</span></div></article>)}</div>}</section>
      </div>}

      {activeTab === 'team' && isHOD && <div className="card"><h2>Team Leave Approvals</h2><table className="ess-table"><thead><tr><th>Employee</th><th>Dates</th><th>Status</th></tr></thead><tbody>{pendingLeaves.map(item => <tr key={item.id}><td>{String(item.employee_id).slice(0,8)}…</td><td>{item.start_date} to {item.end_date}</td><td>{item.status}</td></tr>)}</tbody></table></div>}

      {activeTab === 'requisition' && isHOD && <div className="card"><h2>Request New Hire</h2><form onSubmit={handleRequestHire}>
        <div className="input-group"><label>Job Title</label><input type="text" maxLength="100" required value={reqData.job_title} onChange={event => setReqData({...reqData, job_title: event.target.value})} /></div>
        <div className="input-group"><label>Minimum Education</label><select required value={reqData.min_education} onChange={event => setReqData({...reqData, min_education: event.target.value})}>{['Certificate', 'Diploma', 'Bachelor', 'Master', 'PhD'].map(level => <option key={level}>{level}</option>)}</select></div>
        <div className="input-group"><label>Minimum Experience (Years)</label><input type="number" min="0" required value={reqData.min_experience} onChange={event => setReqData({...reqData, min_experience: Number(event.target.value)})} /></div>
        <div className="input-group"><label>Maximum Applicants</label><input type="number" min="1" required value={reqData.max_applicants} onChange={event => setReqData({...reqData, max_applicants: Number(event.target.value)})} /></div>
        <div className="input-group"><label>Note for HR</label><textarea rows="4" required value={reqData.description} onChange={event => setReqData({...reqData, description: event.target.value})} placeholder="Explain why the role is needed and any useful context." /></div>
        <button type="submit" className="btn-primary" disabled={reqSubmitting}>{reqSubmitting ? 'Submitting…' : 'Submit for HR approval'}</button>
      </form></div>}

      {selectedReview && <div className="ess-review-backdrop"><section className="card ess-review-modal" role="dialog" aria-modal="true"><div className="ess-section-heading"><div><p className="ess-kicker">MONTHLY HOD REVIEW · {selectedReview.review_period}</p><h2>{selectedReview.employee_name}</h2><p>Employee self rating: {selectedReview.self_rating}/5</p>{selectedReview.self_comment && <p>Reflection: {selectedReview.self_comment}</p>}</div><button className="ess-close" type="button" onClick={() => setSelectedReview(null)} aria-label="Close">×</button></div>
        <form className="ess-performance-form" onSubmit={handleHodReview}>
          <label>Punctuality<select value={behavior.punctuality} onChange={event => setBehavior({...behavior,punctuality:event.target.value})}><option value="EARLY">Ahead of schedule</option><option value="ON_TIME">On time</option><option value="OCCASIONALLY_LATE">Occasionally late</option><option value="FREQUENTLY_LATE">Frequently late</option></select></label>
          <label className="ess-check-field"><input type="checkbox" checked={behavior.overtime_worked} onChange={event => setBehavior({...behavior,overtime_worked:event.target.checked})}/> Worked overtime this month</label>
          <label>Task completion<select value={behavior.task_completion} onChange={event => setBehavior({...behavior,task_completion:event.target.value})}><option value="AHEAD_OF_DEADLINE">Ahead of deadline</option><option value="ON_TIME">On time</option><option value="DELAYED">Delayed</option><option value="INCOMPLETE">Incomplete</option></select></label>
          <label>Efficiency<select value={behavior.efficiency} onChange={event => setBehavior({...behavior,efficiency:event.target.value})}><option value="HIGHLY_EFFICIENT">Highly efficient</option><option value="EFFICIENT">Efficient</option><option value="NEEDS_SUPPORT">Needs support</option><option value="SLOW">Slow</option></select></label>
          <label>Quality of work<select value={behavior.quality_of_work} onChange={event => setBehavior({...behavior,quality_of_work:event.target.value})}><option value="EXCEEDS_EXPECTATIONS">Exceeds expectations</option><option value="MEETS_EXPECTATIONS">Meets expectations</option><option value="NEEDS_IMPROVEMENT">Needs improvement</option><option value="UNSATISFACTORY">Unsatisfactory</option></select></label>
          <label>Teamwork<select value={behavior.teamwork} onChange={event => setBehavior({...behavior,teamwork:event.target.value})}><option value="EXCELLENT">Excellent</option><option value="GOOD">Good</option><option value="DEVELOPING">Developing</option><option value="UNSATISFACTORY">Unsatisfactory</option></select></label>
          <label>Final monthly rating<select value={behavior.hod_rating} onChange={event => setBehavior({...behavior,hod_rating:event.target.value})} required><option value="" disabled>Select final rating</option><option value="5">5 · Outstanding</option><option value="4">4 · Exceeds expectations</option><option value="3">3 · Meets expectations</option><option value="2">2 · Needs improvement</option><option value="1">1 · Unsatisfactory</option></select></label>
          <label className="ess-wide">HOD comments<textarea rows="3" maxLength="1000" required value={behavior.hod_comments} onChange={event => setBehavior({...behavior,hod_comments:event.target.value})} placeholder="Explain the rating and any agreed actions." /></label>
          <p className="ess-rating-note ess-wide">Current behavior score: <strong>{liveBehaviorScore}/5</strong>, calculated from punctuality, task completion, efficiency, work quality, and teamwork. Select the final rating based on this evidence and your review. Overtime is recorded as context and does not increase the score automatically.</p>
          <div className="ess-form-actions ess-wide"><button type="button" className="ess-cancel" onClick={() => setSelectedReview(null)}>Cancel</button><button type="submit" className="btn-primary" disabled={performanceBusy}>{performanceBusy ? 'Saving…' : 'Complete monthly review'}</button></div>
        </form>
      </section></div>}
    </div>
  )
}
