import { useEffect, useState } from 'react'
import { createPortal } from 'react-dom'
import axios from 'axios'
import FlexibleSelect from '../../components/FlexibleSelect'
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
const getTrainingResourceUrl = value => {
  const resource = value?.trim()
  if (!resource) return null
  const isHttpUrl = /^https?:\/\//i.test(resource)
  const isRelativePath = (resource.startsWith('/') && !resource.startsWith('//'))
    || resource.startsWith('./')
  if (!isHttpUrl && !isRelativePath) return null
  try {
    const url = new URL(resource, window.location.origin)
    return ['http:', 'https:'].includes(url.protocol) ? url.href : null
  } catch {
    return null
  }
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
  const isHOD = role === 'HOD' || role === 'DEVELOPER'
  const isHR = ['HR', 'HR_ADMIN', 'ADMIN', 'MANAGEMENT', 'DEVELOPER'].includes(role)
  const canReview = isHOD || isHR
  const defaultTab = ['performance', 'training', 'leave'].includes(requestedTab)
    ? requestedTab
    : requestedTab === 'team' && isHOD
      ? 'team'
      : role === 'HOD' ? 'team' : role === 'DEVELOPER' ? 'performance' : 'profile'
  const [activeTab, setActiveTab] = useState(defaultTab)
  const [employeeProfile, setEmployeeProfile] = useState(null)
  const [profileError, setProfileError] = useState('')
  const [employeeContracts, setEmployeeContracts] = useState([])
  const [contractSignatures, setContractSignatures] = useState({})
  const [signingContract, setSigningContract] = useState('')
  const [leaves, setLeaves] = useState([])
  const [pendingLeaves, setPendingLeaves] = useState([])
  const [trainingRows, setTrainingRows] = useState([])
  const [trainingError, setTrainingError] = useState('')
  const [trainingBusy, setTrainingBusy] = useState('')
  const [selectedTrainingResourceIndex, setSelectedTrainingResourceIndex] = useState(null)
  const [leaveForm, setLeaveForm] = useState({ leave_type: 'ANNUAL', start_date: '', end_date: '', reason: '' })
  const [leaveDecisionNotes, setLeaveDecisionNotes] = useState({})
  const [leaveBusy, setLeaveBusy] = useState(false)
  const [reviews, setReviews] = useState([])
  const [teamReviews, setTeamReviews] = useState([])
  const [pendingReviews, setPendingReviews] = useState([])
  const [notifications, setNotifications] = useState([])
  const [quarterRanking, setQuarterRanking] = useState([])
  const [passwordForm, setPasswordForm] = useState({ current_password: '', new_password: '', confirm_password: '' })
  const [passwordBusy, setPasswordBusy] = useState(false)
  const [passwordError, setPasswordError] = useState('')
  const [passwordNotice, setPasswordNotice] = useState('')
  const [selectedReview, setSelectedReview] = useState(null)
  const [selfRating, setSelfRating] = useState('')
  const [selfComment, setSelfComment] = useState('')
  const [behavior, setBehavior] = useState(emptyBehavior)
  const [performanceBusy, setPerformanceBusy] = useState(false)
  const [performanceMessage, setPerformanceMessage] = useState('')
  const [reqData, setReqData] = useState({ job_title: '', min_education: 'Bachelor', min_experience: 2, description: '', department_code: 'TECH', max_applicants: 10 })
  const [message, setMessage] = useState('')
  const [reqSubmitting, setReqSubmitting] = useState(false)
  const apiConfig = getApiConfig()
  const alreadySubmitted = reviews.some(item => item.review_period === currentPeriod() && item.self_rating !== null)
  const trainingResources = trainingRows.flatMap(session => {
    const url = getTrainingResourceUrl(session.venue_link)
    return url ? [{ session, url }] : []
  })
  const selectedTrainingResource = selectedTrainingResourceIndex === null
    ? null
    : trainingResources[selectedTrainingResourceIndex]
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
    if (['performance', 'training', 'leave'].includes(requestedTab) || (requestedTab === 'team' && isHOD)) {
      setActiveTab(requestedTab)
    }
  }, [requestedTab, role])

  useEffect(() => {
    if (selectedTrainingResourceIndex === null) return undefined
    const closeOnEscape = event => {
      if (event.key === 'Escape') setSelectedTrainingResourceIndex(null)
    }
    window.addEventListener('keydown', closeOnEscape)
    return () => window.removeEventListener('keydown', closeOnEscape)
  }, [selectedTrainingResourceIndex])

  useEffect(() => {
    if (isHOD) {
      axios.get(`${API_BASE}/leave/pending`, getApiConfig()).then(res => setPendingLeaves(res.data)).catch(() => setPendingLeaves([]))
    }
    axios.get(`${API_BASE}/leave/my-history`, getApiConfig()).then(res => setLeaves(res.data)).catch(() => setLeaves([]))
    axios.get(`${API_BASE}/employees/me`, getApiConfig()).then(res => setEmployeeProfile(res.data)).catch(error => setProfileError(error.response?.data?.detail || 'Employee profile could not be loaded.'))
    axios.get(`${API_BASE}/contracts/mine`, getApiConfig()).then(res => setEmployeeContracts(res.data)).catch(() => setEmployeeContracts([]))
    axios.get(`${API_BASE}/training/mine`, getApiConfig())
      .then(res => { setTrainingRows(res.data); setTrainingError('') })
      .catch(error => setTrainingError(error.response?.data?.detail || 'Assigned training could not be loaded.'))
    loadPerformance()
    // Load the ESS panels once for the signed-in role.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [isHOD, isHR])

  useEffect(() => {
    if (!isHOD) return undefined
    const timer = window.setInterval(async () => {
      try {
        const [pending, notices, leaves] = await Promise.all([
          axios.get(`${API_BASE}/performance/pending`, getApiConfig()),
          axios.get(`${API_BASE}/performance/notifications`, getApiConfig()),
          axios.get(`${API_BASE}/leave/pending`, getApiConfig()),
        ])
        setPendingReviews(pending.data)
        setNotifications(notices.data)
        setPendingLeaves(leaves.data)
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

  const refreshLeave = async () => {
    try {
      const requests = [axios.get(`${API_BASE}/leave/my-history`, getApiConfig())]
      if (isHOD) requests.push(axios.get(`${API_BASE}/leave/pending`, getApiConfig()))
      const responses = await Promise.all(requests)
      setLeaves(responses[0].data)
      if (isHOD) setPendingLeaves(responses[1].data)
    } catch (error) {
      setMessage(error.response?.data?.detail || 'Leave information could not be refreshed.')
    }
  }

  const submitEssLeave = async (event) => {
    event.preventDefault(); setLeaveBusy(true); setMessage('')
    try {
      await axios.post(`${API_BASE}/leave/request`, leaveForm, getApiConfig())
      setLeaveForm({ leave_type: 'ANNUAL', start_date: '', end_date: '', reason: '' })
      setMessage('Leave request sent to your HOD and HR.'); await refreshLeave()
    } catch (error) { setMessage(error.response?.data?.detail || 'Leave request could not be submitted.') }
    finally { setLeaveBusy(false) }
  }

  const decideEssLeave = async (item, decision) => {
    const note = (leaveDecisionNotes[item.id] || '').trim()
    if (note.length < 5) { setMessage('Please add a decision note of at least 5 characters.'); return }
    setLeaveBusy(true); setMessage('')
    try {
      await axios.put(`${API_BASE}/leave/${item.id}/${decision.toLowerCase()}`, { note }, getApiConfig())
      setLeaveDecisionNotes(notes => ({ ...notes, [item.id]: '' }))
      setMessage(`Leave request ${decision.toLowerCase()}. HR has been notified.`); await refreshLeave()
    } catch (error) { setMessage(error.response?.data?.detail || 'Leave decision could not be saved.') }
    finally { setLeaveBusy(false) }
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

  const handlePasswordChange = async (event) => {
    event.preventDefault()
    setPasswordBusy(true); setPasswordError(''); setPasswordNotice('')
    try {
      const { data } = await axios.post(`${API_BASE}/auth/change-password`, passwordForm, apiConfig)
      localStorage.setItem('must_change_password', 'false')
      setPasswordForm({ current_password: '', new_password: '', confirm_password: '' })
      setPasswordNotice(data.message || 'Password changed successfully.')
    } catch (error) {
      setPasswordError(error.response?.data?.detail || 'Password could not be updated. Check your entries and try again.')
    } finally { setPasswordBusy(false) }
  }

  const downloadMyContract = async (contract, copy = 'signed') => {
    try {
      const { data } = await axios.get(`${API_BASE}/contracts/${contract.id}/download?copy=${copy}`, { ...apiConfig, responseType: 'blob' })
      const url = URL.createObjectURL(data)
      const link = document.createElement('a')
      link.href = url
      link.download = `employment-contract-${contract.employee_number}-${copy}${copy === 'signed' ? contract.signed_file_extension || '.html' : '.html'}`
      link.click()
      window.setTimeout(() => URL.revokeObjectURL(url), 1000)
    } catch (error) {
      setProfileError(error.response?.data?.detail || 'Your contract could not be downloaded.')
    }
  }

  const previewMyContract = async (contract) => {
    const preview = window.open('about:blank', '_blank')
    if (!preview) { setProfileError('Allow pop-ups to review and print your contract.'); return }
    try {
      const { data } = await axios.get(`${API_BASE}/contracts/${contract.id}/document`, { ...apiConfig, responseType: 'text' })
      const url = URL.createObjectURL(new Blob([data], { type: 'text/html' }))
      preview.location.href = url
      window.setTimeout(() => URL.revokeObjectURL(url), 60000)
    } catch (error) {
      preview.close()
      setProfileError(error.response?.data?.detail || 'Your contract could not be opened.')
    }
  }

  const refreshMyContracts = async () => {
    setProfileError('')
    try {
      const { data } = await axios.get(`${API_BASE}/contracts/mine`, apiConfig)
      setEmployeeContracts(data)
    } catch (error) {
      setProfileError(error.response?.data?.detail || 'Your contracts could not be refreshed.')
    }
  }

  const signMyContract = async (event, contract) => {
    event.preventDefault()
    setSigningContract(contract.id); setProfileError('')
    try {
      const { data } = await axios.post(`${API_BASE}/contracts/${contract.id}/sign`, {
        employee_signature_name: contractSignatures[contract.id] || '',
        accepted: true,
      }, apiConfig)
      setEmployeeContracts(items => items.map(item => item.id === contract.id ? data.contract : item))
    } catch (error) {
      setProfileError(error.response?.data?.detail || 'The contract could not be signed.')
    } finally { setSigningContract('') }
  }

  const completeTraining = async (session) => {
    setTrainingBusy(session.id)
    setTrainingError('')
    try {
      const { data } = await axios.post(`${API_BASE}/training/sessions/${session.id}/complete`, {}, apiConfig)
      setTrainingRows(rows => rows.map(item => item.id === session.id
        ? { ...item, status: data.status, completed_at: data.completed_at }
        : item))
    } catch (error) {
      setTrainingError(error.response?.data?.detail || 'Training completion could not be recorded.')
    } finally {
      setTrainingBusy('')
    }
  }

  return (
    <div className="ess-portal">
      <div className="ess-welcome"><div><p className="ess-kicker">EMPLOYEE SELF SERVICE</p><h1>Welcome, {employeeProfile?.full_name || email || 'Employee'}</h1><p>Role: {role} · Your employee workspace</p></div></div>
      {message && <div className="ess-alert">{message}</div>}
      <div className="tabs ess-tabs">
        <button onClick={() => setActiveTab('profile')} className={`tab ${activeTab === 'profile' ? 'active' : ''}`}>My Profile</button>
        <button onClick={() => { setActiveTab('password'); setPasswordError(''); setPasswordNotice('') }} className={`tab ${activeTab === 'password' ? 'active' : ''}`}>Change Password</button>
        <button onClick={() => setActiveTab('leave')} className={`tab ${activeTab === 'leave' ? 'active' : ''}`}>My Leave</button>
        <button onClick={() => setActiveTab('performance')} className={`tab ${activeTab === 'performance' ? 'active' : ''}`}>Performance{isHOD && notifications.some(item => !item.is_read) && <span className="ess-notification-count">{notifications.filter(item => !item.is_read).length}</span>}</button>
        <button onClick={() => setActiveTab('training')} className={`tab ${activeTab === 'training' ? 'active' : ''}`}>My Training</button>
        {isHOD && <button onClick={() => setActiveTab('team')} className={`tab ${activeTab === 'team' ? 'active' : ''}`}>Team Approvals{pendingLeaves.length > 0 && <span className="ess-notification-count">{pendingLeaves.length}</span>}</button>}
        {isHOD && <button onClick={() => setActiveTab('requisition')} className={`tab ${activeTab === 'requisition' ? 'active' : ''}`}>Request New Hire</button>}
      </div>

      {activeTab === 'profile' && <section className="card ess-profile-card"><div className="ess-section-heading"><div><h2>My Profile</h2><p>Current information held in the employee directory.</p></div><span className="ess-profile-tag">HR managed</span></div>{profileError && <div className="ess-alert">{profileError}</div>}{employeeProfile && <><div className="ess-profile-grid">{[['Full name', employeeProfile.full_name], ['System role', employeeProfile.account_role], ['Employee number', employeeProfile.employee_number], ['Date of birth', employeeProfile.date_of_birth], ['Gender', employeeProfile.gender], ['Nationality', employeeProfile.nationality], ['Marital status', employeeProfile.marital_status], ['Personal email', employeeProfile.personal_email], ['Work email', employeeProfile.work_email], ['Phone number', employeeProfile.phone_number], ['Home / physical address', employeeProfile.home_address], ['Father name', employeeProfile.father_name], ['Mother name', employeeProfile.mother_name], ['Next of kin', employeeProfile.next_of_kin_name], ['Next of kin relationship', employeeProfile.next_of_kin_relationship], ['Next of kin phone', employeeProfile.next_of_kin_phone], ['Next of kin address', employeeProfile.next_of_kin_address], ['Department', employeeProfile.department_name || employeeProfile.legacy_department], ['Job title', employeeProfile.job_title], ['Reporting manager', employeeProfile.reporting_manager], ['Work location', employeeProfile.work_location], ['Hire date', employeeProfile.hire_date], ['Employment type', employeeProfile.employment_type], ['Probation period', employeeProfile.probation_period], ['Notice period', employeeProfile.notice_period], ['Contract end date', employeeProfile.contract_end_date], ['Employment status', employeeProfile.status], ['National ID', employeeProfile.national_id], ['TIN number', employeeProfile.tin_number], ['NSSF number', employeeProfile.nssf_number], ['Bank name', employeeProfile.bank_name], ['Bank account number', employeeProfile.account_number]].map(([label, value]) => <div className="ess-profile-field" key={label}><span>{label}</span><strong>{value || 'Not recorded'}</strong></div>)}</div><p className="ess-muted">To correct profile information, contact HR. HR updates employee records in the Employee Directory.</p></>}
        <div style={{marginTop:20}}><div className="ess-section-heading"><div><h2>My employment contracts</h2><p>Review and download contracts issued by HR.</p></div><button className="module-secondary-button" type="button" onClick={refreshMyContracts}>Refresh</button></div>{employeeContracts.length===0?<p className="ess-muted">No contracts are available.</p>:<div className="ess-review-list">{employeeContracts.map(contract=><article className="ess-review-card" key={contract.id}><div><strong>{contract.contract_type.replaceAll('_',' ')} · {contract.job_title||'Employment agreement'}</strong><span>{contract.start_date} – {contract.end_date||'Open-ended'} · {contract.status.replaceAll('_',' ')}</span><span>Salary: UGX {Number(contract.base_salary||0).toLocaleString()}</span></div><div style={{display:'grid',gap:9,width:'100%'}}>{contract.has_generated_document&&<div style={{display:'flex',gap:8,flexWrap:'wrap'}}><button type="button" className="module-secondary-button" onClick={()=>previewMyContract(contract)}>Review / print</button><button type="button" className="module-secondary-button" onClick={()=>downloadMyContract(contract,'generated')}>Download contract</button></div>}{contract.has_signed_document&&<button type="button" className="module-secondary-button" onClick={()=>downloadMyContract(contract)}>Download signed copy</button>}{contract.status==='PENDING_EMPLOYEE_SIGNATURE'&&<form className="ess-performance-form" onSubmit={event=>signMyContract(event,contract)}><label>Your full name<input required value={contractSignatures[contract.id]??employeeProfile?.full_name??''} onChange={event=>setContractSignatures({...contractSignatures,[contract.id]:event.target.value})}/></label><label className="ess-check-field"><input type="checkbox" required/>I have read and agree to the contract terms.</label><div className="ess-form-actions ess-wide"><button className="btn-primary" type="submit" disabled={signingContract===contract.id}>{signingContract===contract.id?'Signing…':'Sign contract'}</button></div><small className="ess-muted">Your typed name records in-app consent; it is not independently identity-verified.</small></form>}</div></article>)}</div>}</div>
      </section>}

      {activeTab === 'password' && <section className="card"><h2>Change your password</h2><p className="ess-muted">Use your current password to set a new password for your account.</p>{passwordError && <div className="ess-alert" role="alert">{passwordError}</div>}{passwordNotice && <div className="ess-alert" role="status">{passwordNotice}</div>}<form className="ess-performance-form" onSubmit={handlePasswordChange}><label>Current password<input type="password" autoComplete="current-password" required value={passwordForm.current_password} onChange={event=>setPasswordForm({...passwordForm,current_password:event.target.value})}/></label><label>New password<input type="password" autoComplete="new-password" minLength="10" maxLength="128" required value={passwordForm.new_password} onChange={event=>setPasswordForm({...passwordForm,new_password:event.target.value})}/><small>Use at least 10 characters.</small></label><label>Confirm new password<input type="password" autoComplete="new-password" minLength="10" maxLength="128" required value={passwordForm.confirm_password} onChange={event=>setPasswordForm({...passwordForm,confirm_password:event.target.value})}/></label><div className="ess-form-actions ess-wide"><button className="btn-primary" type="submit" disabled={passwordBusy}>{passwordBusy?'Updating…':'Update password'}</button></div></form></section>}

      {activeTab === 'leave' && <div className="ess-stack"><section className="card"><h2>Request leave</h2><p className="ess-muted">Add the reason for your request. Your HOD and HR will be notified.</p><form className="ess-performance-form" onSubmit={submitEssLeave}><label>Leave type<FlexibleSelect name="leave_type" value={leaveForm.leave_type} onChange={event=>setLeaveForm({...leaveForm,leave_type:event.target.value})} options={ [['ANNUAL','Annual'],['SICK','Sick'],['MATERNITY','Maternity'],['PATERNITY','Paternity'],['COMPASSIONATE','Compassionate'],['OTHER','Other']] } placeholder="Select leave type" required/></label><label>Start date<input type="date" required value={leaveForm.start_date} onChange={event=>setLeaveForm({...leaveForm,start_date:event.target.value})}/></label><label>End date<input type="date" required value={leaveForm.end_date} onChange={event=>setLeaveForm({...leaveForm,end_date:event.target.value})}/></label><label className="ess-wide">Reason{leaveForm.leave_type === 'OTHER' ? ' (describe the leave type and reason)' : ''}<textarea placeholder={leaveForm.leave_type === 'OTHER' ? 'Describe the type of leave you need and why you are requesting it.' : 'Explain why you are requesting this leave.'} required minLength="5" maxLength="255" rows="3" value={leaveForm.reason} onChange={event=>setLeaveForm({...leaveForm,reason:event.target.value})}/></label><button className="btn-primary" disabled={leaveBusy}>{leaveBusy?'Submitting - ':'Submit leave request'}</button></form></section><section className="card"><h2>My Leave Requests</h2><div className="ess-record-table-wrap"><table className="ess-table"><thead><tr><th>Type</th><th>Dates</th><th>My reason</th><th>Decision</th><th>HOD note</th></tr></thead><tbody>{leaves.map(item => <tr key={item.id}><td>{item.leave_type}</td><td>{item.start_date} to {item.end_date}</td><td>{item.reason}</td><td>{item.status}{item.approved_by_name && <small>{item.approved_by_name}  -  {item.decided_at ? new Date(item.decided_at).toLocaleString() : ''}</small>}</td><td>{item.decision_note || ' - '}</td></tr>)}</tbody></table></div>{leaves.length===0 && <p className="ess-muted">No leave requests yet.</p>}</section></div>}

      {activeTab === 'training' && <section className="card">
        <div className="ess-section-heading"><div><h2>My training</h2><p>Courses and sessions assigned to you. You can mark a session complete after you finish it.</p></div></div>
        {trainingError && <div className="ess-alert" role="alert">{trainingError}</div>}
        {trainingRows.length === 0
          ? <p className="ess-muted">No training sessions have been assigned to you.</p>
          : <div className="ess-review-list">{trainingRows.map(session => {
            const resourceIndex = trainingResources.findIndex(resource => resource.session.id === session.id)
            return <article className="ess-review-card" key={session.id}>
            <div><strong>{session.course_title}</strong><span>{session.date} · {session.trainer} · {session.audience}</span>{resourceIndex >= 0 ? <button className="module-secondary-button" type="button" onClick={() => setSelectedTrainingResourceIndex(resourceIndex)}>Open training resource</button> : <span>{session.venue_link}</span>}<span>Status: {session.status === 'COMPLETED' ? `Completed${session.completed_at ? ` on ${new Date(session.completed_at).toLocaleDateString()}` : ''}` : 'Assigned'}</span></div>
            {session.status !== 'COMPLETED' && <button className="btn-primary" type="button" disabled={trainingBusy === session.id} onClick={() => completeTraining(session)}>{trainingBusy === session.id ? 'Saving…' : 'Mark complete'}</button>}
          </article>
          })}</div>}
      </section>}

      {selectedTrainingResource && createPortal(<div className="ess-review-backdrop" style={{zIndex:1100}} onMouseDown={event => { if (event.target === event.currentTarget) setSelectedTrainingResourceIndex(null) }}>
        <section className="card" role="dialog" aria-modal="true" aria-labelledby="training-resource-title" style={{width:'min(1000px, 100%)',height:'min(85vh, 760px)',maxHeight:'calc(100vh - 40px)',display:'flex',flexDirection:'column',padding:16,margin:0,overflow:'hidden'}}>
          <div className="ess-section-heading">
            <div><p className="eyebrow">TRAINING RESOURCE {selectedTrainingResourceIndex + 1} OF {trainingResources.length}</p><h2 id="training-resource-title">{selectedTrainingResource.session.course_title}</h2></div>
            <div style={{display:'flex',gap:8,flexWrap:'wrap',justifyContent:'flex-end'}}>
              <button className="module-secondary-button" type="button" disabled={selectedTrainingResourceIndex === 0} onClick={() => setSelectedTrainingResourceIndex(index => index - 1)}>Previous file</button>
              <button className="module-secondary-button" type="button" disabled={selectedTrainingResourceIndex === trainingResources.length - 1} onClick={() => setSelectedTrainingResourceIndex(index => index + 1)}>Next file</button>
              <button className="module-secondary-button" type="button" onClick={() => setSelectedTrainingResourceIndex(null)}>Close file</button>
            </div>
          </div>
          <iframe title={`${selectedTrainingResource.session.course_title} training resource`} src={selectedTrainingResource.url} referrerPolicy="no-referrer" style={{width:'100%',minHeight:0,flex:1,border:0,borderRadius:8}} />
        </section>
      </div>, document.body)}

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
          {pendingReviews.length > 0 && <label className="ess-review-select">Select an employee to rate
            <select value="" onChange={event => { const review = pendingReviews.find(item => item.id === event.target.value); if (review) openReview(review) }}>
              <option value="">Choose employee and month…</option>
              {pendingReviews.map(review => <option value={review.id} key={review.id}>{review.employee_name} · {review.review_period} · self rating {review.self_rating}/5</option>)}
            </select>
            <small>{role === 'HOD' ? 'Only employees in your department who submitted a self assessment appear here.' : 'Only employees with a submitted self assessment appear here.'}</small>
          </label>}
          {pendingReviews.length === 0 ? <p className="ess-muted">No employee self assessments are waiting for a HOD rating.</p> : <div className="ess-review-list">{pendingReviews.map(review => <article className="ess-review-card" key={review.id}><div><strong>{review.employee_name}</strong><span>{review.department_name || 'Department'} · {review.review_period}</span><span>Self rating: {review.self_rating}/5</span>{review.self_comment && <p>Employee reflection: {review.self_comment}</p>}</div><button className="btn-primary" type="button" onClick={() => openReview(review)}>Review and rate</button></article>)}</div>}
        </section>}
        {canReview && <section className="card"><div className="ess-section-heading"><div><h2>{role === 'HOD' ? 'Department monthly records' : 'All monthly performance records'}</h2><p>{role === 'HOD' ? 'Your department’s self assessments and completed HOD reviews.' : 'Company-wide employee, HOD, and HR review records.'}</p></div><span className="ess-pending-count">{teamReviews.length} records</span></div>{teamReviews.length === 0 ? <p className="ess-muted">No monthly records have been submitted.</p> : <div className="ess-record-table-wrap"><table className="ess-table ess-record-table"><thead><tr><th>Employee</th><th>Month</th><th>Self</th><th>Punctuality</th><th>Overtime</th><th>Tasks</th><th>Efficiency</th><th>Quality</th><th>Teamwork</th><th>Behavior</th><th>Final</th><th>HOD comment</th></tr></thead><tbody>{teamReviews.map(row => <tr key={row.id}><td>{row.employee_name}</td><td>{row.review_period}</td><td>{row.self_rating ?? '—'}{row.self_comment ? <small>{row.self_comment}</small> : null}</td><td>{row.punctuality?.replaceAll('_',' ') || '—'}</td><td>{row.overtime_worked ? 'Yes' : row.overtime_worked === false ? 'No' : '—'}</td><td>{row.task_completion?.replaceAll('_',' ') || '—'}</td><td>{row.efficiency?.replaceAll('_',' ') || '—'}</td><td>{row.quality_of_work?.replaceAll('_',' ') || '—'}</td><td>{row.teamwork?.replaceAll('_',' ') || '—'}</td><td>{row.behavior_rating ?? 'Pending'}</td><td>{row.hod_rating ?? 'Pending'}</td><td>{row.hod_comments || '—'}</td></tr>)}</tbody></table></div>}</section>}
        {canReview && <section className="card"><h2>Quarterly performance</h2><p className="ess-muted">Completed monthly HOD ratings contribute to {currentQuarter()} rankings.</p>{quarterRanking.length === 0 ? <p className="ess-muted">No completed monthly ratings for this quarter yet.</p> : <table className="ess-table"><thead><tr><th>Rank</th><th>Employee</th><th>Department</th><th>Quarter score</th><th>Months rated</th></tr></thead><tbody>{quarterRanking.map(row => <tr key={row.employee_id}><td>{row.rank}</td><td>{row.employee_name}</td><td>{row.department_name || '—'}</td><td>{row.quarter_rating}/5</td><td>{row.months_completed}</td></tr>)}</tbody></table>}</section>}
        <section className="card"><h2>My monthly records</h2>{reviews.length === 0 ? <p className="ess-muted">Your submitted and completed monthly ratings will appear here.</p> : <div className="ess-review-list">{reviews.map(review => <article className="ess-review-card" key={review.id}><div><strong>{review.review_period} · Self {review.self_rating ?? '—'}/5{review.hod_rating !== null ? ` · HOD ${review.hod_rating}/5` : ''}</strong><span>{review.hod_rating !== null ? `Behavior score ${review.behavior_rating}/5 · ${review.hod_comments || 'No HOD comment'}` : review.self_rating !== null ? 'Waiting for HOD review' : 'Self assessment not submitted'}</span></div></article>)}</div>}</section>
      </div>}

      {activeTab === 'team' && isHOD && <section className="card">
        <div className="ess-section-heading"><div><h2>Team responsibilities</h2><p>Review department leave requests and monthly employee self-ratings.</p></div><span className="ess-pending-count">{pendingLeaves.length} leave requests</span></div>
        {message && <div className="ess-alert" role="status">{message}</div>}
        {pendingLeaves.length === 0 ? <p className="ess-muted">No leave requests are waiting for your decision.</p> : <div className="ess-review-list">
          {pendingLeaves.map(item => <article className="ess-review-card ess-team-leave" key={item.id}>
            <div><strong>{item.employee_name} · {item.leave_type}</strong><span>{item.employee_number} · {item.start_date} to {item.end_date}</span><p>{item.reason}</p></div>
            <div className="ess-team-leave-actions"><label>Decision note<input value={leaveDecisionNotes[item.id] || ''} maxLength="255" onChange={event => setLeaveDecisionNotes(notes => ({ ...notes, [item.id]: event.target.value }))} placeholder="At least 5 characters" /></label><div><button className="btn-primary" type="button" disabled={leaveBusy} onClick={() => decideEssLeave(item, 'APPROVE')}>Approve</button><button className="ess-cancel" type="button" disabled={leaveBusy} onClick={() => decideEssLeave(item, 'REJECT')}>Reject</button></div></div>
          </article>)}
        </div>}
      </section>}

      {activeTab === 'requisition' && isHOD && <div className="card"><h2>Request New Hire</h2><form onSubmit={handleRequestHire}>
        <div className="input-group"><label>Job Title</label><input type="text" maxLength="100" required value={reqData.job_title} onChange={event => setReqData({...reqData, job_title: event.target.value})} /></div>
        <div className="input-group"><label>Minimum Education<FlexibleSelect name="min_education" required value={reqData.min_education} onChange={event => setReqData({...reqData, min_education: event.target.value})} options={['Certificate', 'Diploma', 'Bachelor', 'Master', 'PhD']} placeholder="Select minimum education"/></label></div>
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
