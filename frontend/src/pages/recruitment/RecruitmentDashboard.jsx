import { useCallback, useEffect, useMemo, useState } from 'react'
import axios from 'axios'
import { BriefcaseBusiness, Check, ClipboardList, RefreshCw, Users } from 'lucide-react'
import { Link, useSearchParams } from 'react-router-dom'
import './Recruitment.css'

const API_BASE = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api'
const apiConfig = () => ({ headers: { Authorization: `Bearer ${localStorage.getItem('token') || localStorage.getItem('access_token') || ''}` } })
const EMAIL_TEMPLATES = {
  INTERVIEW: {
    subject: 'Interview invitation',
    body: 'Dear {{first_name}},\n\nWe would like to invite you to interview for {{job_title}}. Our HR team will share the interview details with you shortly.\n\nRegards,\nHuman Resources',
  },
  OFFER: {
    subject: 'Offer of employment',
    body: 'Dear {{first_name}},\n\nWe are pleased to offer you the role of {{job_title}}. Please review the offer details and onboarding requirements below.\n\nRegards,\nHuman Resources',
  },
  REJECTION: {
    subject: 'Update on your application',
    body: 'Dear {{first_name}},\n\nThank you for your interest in {{job_title}}. We regret to inform you that your application will not proceed further.\n\nRegards,\nHuman Resources',
  },
  CUSTOM: { subject: '', body: '' },
}
const REJECTION_TYPES = [
  ['ALL', 'All reasons'],
  ['NOT_QUALIFIED', 'Did not meet job requirements'],
  ['PIPELINE_REJECTED', 'Rejected by HR'],
  ['INTERVIEW_FAILED', 'Failed interview'],
  ['OFFER_FAILED', 'Offer not accepted'],
]

function RecruitmentDashboard() {
  const [searchParams, setSearchParams] = useSearchParams()
  const tabIds = ['candidates', 'interviews', 'offers', 'requisitions', 'rejections', 'emails']
  const requestedTab = searchParams.get('section')
  const activeTab = tabIds.includes(requestedTab) ? requestedTab : 'candidates'
  const [candidates, setCandidates] = useState([])
  const [requisitions, setRequisitions] = useState([])
  const [approvalCaps, setApprovalCaps] = useState({})
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState('')
  const [feedback, setFeedback] = useState('')
  const [searchTerm, setSearchTerm] = useState('')
  const [rejectionType, setRejectionType] = useState('ALL')
  const [selectedCandidate, setSelectedCandidate] = useState(null)
  const [actionType, setActionType] = useState('')
  const [showReqModal, setShowReqModal] = useState(false)
  const [reqData, setReqData] = useState({
    job_title: '',
    min_education: 'Bachelor',
    min_experience: 2,
    description: '',
    department_code: 'TECH',
    max_applicants: 50,
  })
  const [interview, setInterview] = useState({
    interview_date: '',
    interviewer_name: '',
    location: '',
  })
  const [grade, setGrade] = useState('')
  const [reason, setReason] = useState('')
  const [requirements, setRequirements] = useState('')
  const [requiredDocuments, setRequiredDocuments] = useState('')
  const [salary, setSalary] = useState('')
  const [emailType, setEmailType] = useState('INTERVIEW')
  const [emailSubject, setEmailSubject] = useState(EMAIL_TEMPLATES.INTERVIEW.subject)
  const [emailBody, setEmailBody] = useState(EMAIL_TEMPLATES.INTERVIEW.body)
  const [selectedEmails, setSelectedEmails] = useState([])

  const fetchData = useCallback(async (showLoading = false) => {
    if (showLoading) setLoading(true)
    setError('')
    try {
      const [candidateResponse, requisitionResponse] = await Promise.all([
        axios.get(`${API_BASE}/recruitment/candidates/all`, apiConfig()),
        axios.get(`${API_BASE}/recruitment/requisitions`, apiConfig()),
      ])
      setCandidates(candidateResponse.data)
      setRequisitions(requisitionResponse.data)
    } catch (requestError) {
      setError(requestError.response?.data?.detail || requestError.message || 'Could not load recruitment data.')
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    fetchData(true)
  }, [fetchData])

  const pipelineCandidates = useMemo(
    () => candidates.filter((candidate) => candidate.status === 'IN_PIPELINE'),
    [candidates],
  )
  const interviewCandidates = useMemo(
    () => candidates.filter((candidate) => candidate.status === 'INTERVIEW_SCHEDULED'),
    [candidates],
  )
  const offerCandidates = useMemo(
    () => candidates.filter((candidate) => ['PASSED', 'OFFERED', 'OFFER_ACCEPTED', 'HIRED'].includes(candidate.status)),
    [candidates],
  )
  const rejectedCandidates = useMemo(
    () => candidates.filter((candidate) => candidate.status === 'REJECTED')
      .filter((candidate) => rejectionType === 'ALL' || candidate.rejection_type === rejectionType)
      .filter((candidate) => {
        const query = searchTerm.trim().toLowerCase()
        return !query || [
          candidate.first_name,
          candidate.last_name,
          candidate.email,
          candidate.job_title,
          candidate.rejection_reason,
        ].some((value) => value?.toLowerCase().includes(query))
      }),
    [candidates, rejectionType, searchTerm],
  )
  const emailCandidates = useMemo(() => candidates.filter((candidate) => {
    if (emailType === 'OFFER') return candidate.status === 'PASSED'
    if (emailType === 'INTERVIEW' || emailType === 'REJECTION') return candidate.status === 'IN_PIPELINE'
    return true
  }), [candidates, emailType])

  const performAction = async (action, successMessage) => {
    setSaving(true)
    setError('')
    setFeedback('')
    try {
      const response = await action()
      const emailNote = response.data.email_sent === false
        ? ' The record was saved, but email was not sent. Configure SMTP_HOST and SMTP_FROM on the server.'
        : ''
      setFeedback(`${successMessage}${emailNote}`)
      setSelectedCandidate(null)
      setActionType('')
      setReason('')
      setGrade('')
      setRequirements('')
      setSalary('')
      await fetchData()
      return response
    } catch (requestError) {
      setError(requestError.response?.data?.detail || requestError.message || 'The action could not be completed.')
    } finally {
      setSaving(false)
    }
  }

  const createRequisition = async (event) => {
    event.preventDefault()
    const response = await performAction(
      () => axios.post(`${API_BASE}/recruitment/requisitions`, reqData, apiConfig()),
      'Requisition sent to the HR dashboard for review.',
    )
    if (response) {
      setShowReqModal(false)
      setReqData({
        job_title: '',
        min_education: 'Bachelor',
        min_experience: 2,
        description: '',
        department_code: 'TECH',
        max_applicants: 50,
      })
    }
  }

  const reviewRequisition = (id, status, maxApplicants) => performAction(
    () => axios.patch(`${API_BASE}/recruitment/requisitions/${id}/status`, { status, max_applicants: maxApplicants }, apiConfig()),
    `Requisition ${status.toLowerCase()}.`,
  )

  const scheduleInterview = (event) => {
    event.preventDefault()
    if (!selectedCandidate) return
    performAction(
      () => axios.put(`${API_BASE}/recruitment/candidates/${selectedCandidate.id}/interview`, interview, apiConfig()),
      'Interview scheduled.',
    )
  }

  const submitGrade = (event) => {
    event.preventDefault()
    if (!selectedCandidate) return
    performAction(
      () => axios.put(`${API_BASE}/recruitment/candidates/${selectedCandidate.id}/grade`, { grade, reason }, apiConfig()),
      'Interview result recorded.',
    )
  }

  const submitOffer = (event) => {
    event.preventDefault()
    if (!selectedCandidate) return
    performAction(
      () => axios.put(`${API_BASE}/recruitment/candidates/${selectedCandidate.id}/offer`, {
        status: 'OFFERED',
        requirements,
        salary: salary || null,
        required_documents: requiredDocuments,
      }, apiConfig()),
      'Offer recorded.',
    )
  }

  const rejectCandidate = (event) => {
    event.preventDefault()
    if (!selectedCandidate) return
    performAction(
      () => axios.put(`${API_BASE}/recruitment/candidates/${selectedCandidate.id}/status`, {
        status: 'REJECTED',
        reason,
      }, apiConfig()),
      'Candidate rejected.',
    )
  }

  const declineOffer = (event) => {
    event.preventDefault()
    if (!selectedCandidate) return
    performAction(
      () => axios.put(`${API_BASE}/recruitment/candidates/${selectedCandidate.id}/offer`, {
        status: 'DECLINED',
        reason,
      }, apiConfig()),
      'Offer decline recorded in the rejected archive.',
    )
  }

  const changeEmailType = (type) => {
    setEmailType(type)
    setSelectedEmails([])
    setEmailSubject(EMAIL_TEMPLATES[type].subject)
    setEmailBody(EMAIL_TEMPLATES[type].body)
  }

  const toggleSelection = (id) => {
    setSelectedEmails((selection) => selection.includes(id)
      ? selection.filter((item) => item !== id)
      : [...selection, id])
  }

  const sendBulkEmail = () => performAction(
    () => axios.post(`${API_BASE}/recruitment/send-email`, {
      candidate_ids: selectedEmails,
      email_type: emailType,
      subject: emailSubject,
      message: emailBody,
    }, apiConfig()),
    'Email campaign completed.',
  ).then((result) => {
    if (result?.data) {
      setFeedback(result.data.message)
      setSelectedEmails([])
    }
  })

  const openAction = (candidate, type) => {
    setSelectedCandidate(candidate)
    setActionType(type)
    setReason('')
    setGrade('')
    setRequirements(candidate.onboarding_requirements || '')
    setRequiredDocuments((candidate.onboarding_documents_required || []).join('\n'))
    setSalary(candidate.offer_salary || '')
    setInterview({ interview_date: '', interviewer_name: '', location: '' })
  }

  const tabs = [
    ['candidates', 'Candidate pipeline', pipelineCandidates.length],
    ['interviews', 'Interviews', interviewCandidates.length],
    ['offers', 'Offers', offerCandidates.length],
    ['requisitions', 'Requisitions', requisitions.length],
    ['rejections', 'Rejected archive', candidates.filter((item) => item.status === 'REJECTED').length],
    ['emails', 'Email letters', null],
  ]

  return (
    <section className="recruitment-page">
      <header className="recruitment-heading">
        <div>
          <p className="eyebrow">PEOPLE OPERATIONS</p>
          <h1>Recruitment</h1>
          <p>Review hiring requests, manage applicants, and move candidates through each stage.</p>
        </div>
        <div className="recruitment-heading-actions">
          <button className="refresh-button" type="button" onClick={() => fetchData(true)} disabled={loading}>
            <RefreshCw size={14} aria-hidden="true" /> Refresh
          </button>
          <button className="recruitment-primary-button" type="button" onClick={() => setShowReqModal(true)}>
            + Create requisition
          </button>
        </div>
      </header>

      <div className="recruitment-summary" aria-label="Recruitment summary">
        <article><span className="recruitment-summary-icon"><BriefcaseBusiness size={17} /></span><span>Open requisitions</span><strong>{requisitions.filter((item) => item.status === 'APPROVED').length}</strong></article>
        <article><span className="recruitment-summary-icon blue"><Users size={17} /></span><span>Active applicants</span><strong>{pipelineCandidates.length}</strong></article>
        <article><span className="recruitment-summary-icon green"><ClipboardList size={17} /></span><span>Awaiting interview</span><strong>{interviewCandidates.length}</strong></article>
      </div>

      {(error || feedback) && (
        <div className={`recruitment-alert ${error ? 'error' : 'success'}`} role={error ? 'alert' : 'status'}>
          <span>{error || feedback}</span>
          <button type="button" onClick={() => { setError(''); setFeedback('') }} aria-label="Dismiss message">×</button>
        </div>
      )}

      <nav className="recruitment-tabs" aria-label="Recruitment sections">
        {tabs.map(([id, label, count]) => (
          <button
            type="button"
            key={id}
            className={`recruitment-tab ${activeTab === id ? 'active' : ''}`}
            aria-current={activeTab === id ? 'page' : undefined}
            onClick={() => setSearchParams((current) => {
              const next = new URLSearchParams(current)
              next.set('section', id)
              return next
            })}
          >
            {label}{count !== null && <span className="tab-count">{count}</span>}
          </button>
        ))}
      </nav>

      <div className="recruitment-panel">
        {loading ? <p className="recruitment-loading" role="status">Loading recruitment records…</p> : (
          <>
            {activeTab === 'candidates' && (
              <>
                <SectionHeading title="Candidate pipeline" description="Applicants who meet the minimum experience and education requirements." />
                <DataTable
                  headings={['Candidate', 'Job', 'Education / experience', 'Application', 'Action']}
                  empty="No eligible applicants are waiting in the pipeline."
                >
                  {pipelineCandidates.map((candidate) => (
                    <tr key={candidate.id}>
                      <td><strong className="table-primary">{candidate.first_name} {candidate.last_name}</strong><br /><a className="candidate-email" href={`mailto:${candidate.email}`}>{candidate.email}</a></td>
                      <td>{candidate.job_title || '—'}</td>
                      <td>{candidate.education_level || '—'}<br />{candidate.experience_years ?? '—'} years</td>
                      <td>{candidate.has_cv ? <CvLink candidate={candidate} /> : 'No CV uploaded'}</td>
                      <td className="candidate-actions">
                        <button className="approve-button" type="button" onClick={() => openAction(candidate, 'interview')}>Schedule interview</button>
                        <button className="reject-button" type="button" onClick={() => openAction(candidate, 'reject')}>Reject</button>
                      </td>
                    </tr>
                  ))}
                </DataTable>
              </>
            )}

            {activeTab === 'interviews' && (
              <>
                <SectionHeading title="Interview schedule & grading" description="Interview details are saved on each candidate record. Grade candidates as outstanding, pass, or fail." />
                <DataTable headings={['Candidate', 'Job', 'Interview', 'Interviewer / place', 'Action']} empty="No interviews have been scheduled.">
                  {interviewCandidates.map((candidate) => (
                    <tr key={candidate.id}>
                      <td><strong className="table-primary">{candidate.first_name} {candidate.last_name}</strong><br />{candidate.email}</td>
                      <td>{candidate.job_title || '—'}</td>
                      <td>{candidate.interview_date ? new Date(candidate.interview_date).toLocaleString() : '—'}</td>
                      <td>{candidate.interviewer_name || '—'}<br />{candidate.interview_location || '—'}</td>
                      <td><button className="approve-button" type="button" onClick={() => openAction(candidate, 'grade')}>Grade interview</button></td>
                    </tr>
                  ))}
                </DataTable>
              </>
            )}

            {activeTab === 'offers' && (
              <>
                <SectionHeading title="Offers & onboarding" description="Issue offers to candidates who passed. Accepted offers move into the onboarding queue." />
                <DataTable headings={['Candidate', 'Job', 'Interview grade', 'Offer details', 'Action']} empty="No candidates are ready for an offer.">
                  {offerCandidates.map((candidate) => (
                    <tr key={candidate.id}>
                      <td><strong className="table-primary">{candidate.first_name} {candidate.last_name}</strong><br />{candidate.email}</td>
                      <td>{candidate.job_title || '—'}</td>
                      <td><StatusPill value={candidate.status === 'OFFER_ACCEPTED' ? 'OFFER_ACCEPTED' : candidate.interview_grade || 'PASSED'} /></td>
                      <td>{['OFFERED', 'OFFER_ACCEPTED', 'HIRED'].includes(candidate.status)
                        ? <>{candidate.offer_salary ? `UGX ${Number(candidate.offer_salary).toLocaleString()}` : 'Salary not set'}<br />{candidate.onboarding_requirements}</>
                        : 'Not issued'}</td>
                      <td className="candidate-actions">
                        {candidate.status === 'PASSED'
                          ? <button className="approve-button" type="button" onClick={() => openAction(candidate, 'offer')}>Prepare offer</button>
                          : candidate.status === 'OFFERED'
                            ? <button className="approve-button" type="button" onClick={() => openAction(candidate, 'offer')}>Resend offer</button>
                            : <Link className="approve-button" to="/onboarding">Open onboarding</Link>}
                      </td>
                    </tr>
                  ))}
                </DataTable>
              </>
            )}

            {activeTab === 'requisitions' && (
              <>
                <SectionHeading title="Master dashboard · job requisitions" description="HOD submissions appear here for HR review. Only approved roles are listed on the public application page." />
                <DataTable headings={['Job title / department', 'Minimum requirements', 'HOD note', 'Applicants', 'Status / action']} empty="No job requisitions have been submitted.">
                  {requisitions.map((item) => {
                    const applicantCount = candidates.filter((candidate) => candidate.requisition_id === item.id).length
                    return (
                      <tr key={item.id}>
                        <td><strong className="table-primary">{item.job_title}</strong><br />{item.department_code || '—'}</td>
                        <td>{item.min_education} · {item.min_experience} years</td>
                        <td>{item.description || '—'}</td>
                        <td>{applicantCount} / {item.max_applicants}</td>
                        <td>
                          {item.status === 'PENDING_HR' ? (
                            <div className="candidate-actions">
                              <label className="recruitment-cap-field">Applicant limit
                                <input type="number" min="1" max="10000" value={approvalCaps[item.id] ?? item.max_applicants ?? 20} onChange={(event) => setApprovalCaps({ ...approvalCaps, [item.id]: Number(event.target.value) })} />
                              </label>
                              <button className="approve-button" type="button" disabled={saving || !(approvalCaps[item.id] ?? item.max_applicants)} onClick={() => reviewRequisition(item.id, 'APPROVED', approvalCaps[item.id] ?? item.max_applicants)}>Approve & publish</button>
                              <button className="reject-button" type="button" disabled={saving} onClick={() => reviewRequisition(item.id, 'REJECTED')}>Reject request</button>
                            </div>
                          ) : <StatusPill value={item.status} />}
                        </td>
                      </tr>
                    )
                  })}
                </DataTable>
              </>
            )}

            {activeTab === 'rejections' && (
              <>
                <SectionHeading title="Rejected candidate archive" description="Retained applications include the rejection reason, interview grade, contact details, and submitted CV." />
                <div className="rejection-filters">
                  <input aria-label="Search rejected applicants" type="search" placeholder="Search name, email, job, or reason…" value={searchTerm} onChange={(event) => setSearchTerm(event.target.value)} />
                  <select aria-label="Filter rejection reason" value={rejectionType} onChange={(event) => setRejectionType(event.target.value)}>
                    {REJECTION_TYPES.map(([value, label]) => <option key={value} value={value}>{label}</option>)}
                  </select>
                </div>
                <DataTable headings={['Candidate', 'Job', 'Category / reason', 'Interview grade', 'Documents']} empty="No rejected candidates match these filters.">
                  {rejectedCandidates.map((candidate) => (
                    <tr key={candidate.id}>
                      <td><strong className="table-primary">{candidate.first_name} {candidate.last_name}</strong><br /><a className="candidate-email" href={`mailto:${candidate.email}`}>{candidate.email}</a><br />{candidate.phone_number}</td>
                      <td>{candidate.job_title || '—'}<br />{candidate.education_level} · {candidate.experience_years ?? 0} years</td>
                      <td><StatusPill value={candidate.rejection_type || 'REJECTED'} /><p className="rejection-reason">{candidate.rejection_reason || 'No reason recorded.'}</p></td>
                      <td>{candidate.interview_grade || 'Not interviewed'}</td>
                      <td>{candidate.has_cv ? <CvLink candidate={candidate} /> : 'No CV uploaded'}{candidate.cover_letter && <details className="cover-letter-details"><summary>View cover letter</summary><p>{candidate.cover_letter}</p></details>}</td>
                    </tr>
                  ))}
                </DataTable>
              </>
            )}

            {activeTab === 'emails' && (
              <div className="email-workspace">
                <div>
                  <SectionHeading title="Email letters" description="Editable templates are provided for interview invitations, offers, and rejections." />
                  <label className="recruitment-field">Letter type
                    <select value={emailType} onChange={(event) => changeEmailType(event.target.value)}>
                      <option value="INTERVIEW">Interview invitation</option>
                      <option value="OFFER">Offer letter</option>
                      <option value="REJECTION">Rejection notice</option>
                      <option value="CUSTOM">Custom message</option>
                    </select>
                  </label>
                  <label className="recruitment-field">Subject
                    <input value={emailSubject} onChange={(event) => setEmailSubject(event.target.value)} required />
                  </label>
                  <label className="recruitment-field">Message
                    <textarea rows="9" value={emailBody} onChange={(event) => setEmailBody(event.target.value)} required />
                  </label>
                  <p className="email-template-hint">Available placeholders: {'{{first_name}}'}, {'{{job_title}}'}.</p>
                  <button className="recruitment-primary-button" type="button" disabled={saving || !selectedEmails.length || !emailSubject.trim() || !emailBody.trim()} onClick={sendBulkEmail}>
                    Send to {selectedEmails.length} selected
                  </button>
                  <p className="email-template-hint">Email delivery requires SMTP_HOST and SMTP_FROM on the backend. Undelivered messages are reported; candidate records are retained.</p>
                </div>
                <div>
                  <h2 className="recruitment-subheading">Recipients</h2>
                  <DataTable headings={['Select', 'Candidate', 'Status']} empty="No candidates match this letter type.">
                    {emailCandidates.map((candidate) => (
                      <tr key={candidate.id}>
                        <td><input aria-label={`Select ${candidate.first_name}`} type="checkbox" checked={selectedEmails.includes(candidate.id)} onChange={() => toggleSelection(candidate.id)} /></td>
                        <td><strong className="table-primary">{candidate.first_name} {candidate.last_name}</strong><br />{candidate.email}</td>
                        <td><StatusPill value={candidate.status} /></td>
                      </tr>
                    ))}
                  </DataTable>
                </div>
              </div>
            )}
          </>
        )}
      </div>

      {showReqModal && (
        <Modal title="Create job requisition" onClose={() => setShowReqModal(false)}>
          <form onSubmit={createRequisition}>
            <label className="recruitment-field">Job title<input required maxLength="100" value={reqData.job_title} onChange={(event) => setReqData({ ...reqData, job_title: event.target.value })} /></label>
            <label className="recruitment-field">Minimum education
              <select required value={reqData.min_education} onChange={(event) => setReqData({ ...reqData, min_education: event.target.value })}>
                {['Certificate', 'Diploma', 'Bachelor', 'Master', 'PhD'].map((level) => <option key={level}>{level}</option>)}
              </select>
            </label>
            <label className="recruitment-field">Minimum experience (years)<input type="number" min="0" required value={reqData.min_experience} onChange={(event) => setReqData({ ...reqData, min_experience: Number(event.target.value) })} /></label>
            <label className="recruitment-field">Department code<input required value={reqData.department_code} onChange={(event) => setReqData({ ...reqData, department_code: event.target.value })} /></label>
            <label className="recruitment-field">Maximum applicants<input type="number" min="1" required value={reqData.max_applicants} onChange={(event) => setReqData({ ...reqData, max_applicants: Number(event.target.value) })} /></label>
            <label className="recruitment-field">Note for HR<textarea rows="4" required value={reqData.description} onChange={(event) => setReqData({ ...reqData, description: event.target.value })} placeholder="Explain why the role is needed and any useful context." /></label>
            <button className="recruitment-primary-button" type="submit" disabled={saving}>{saving ? 'Submitting…' : 'Submit for HR approval'}</button>
          </form>
        </Modal>
      )}

      {selectedCandidate && actionType && (
        <Modal
          title={{
            interview: 'Schedule interview',
            grade: 'Grade interview',
            offer: 'Prepare offer',
            reject: 'Reject candidate',
            decline: 'Record offer decline',
          }[actionType]}
          onClose={() => { setSelectedCandidate(null); setActionType('') }}
        >
          <p className="modal-candidate-name">{selectedCandidate.first_name} {selectedCandidate.last_name} · {selectedCandidate.job_title || 'Applicant'}</p>
          {actionType === 'interview' && (
            <form onSubmit={scheduleInterview}>
              <label className="recruitment-field">Interview date and time<input type="datetime-local" required value={interview.interview_date} onChange={(event) => setInterview({ ...interview, interview_date: event.target.value })} /></label>
              <label className="recruitment-field">Interviewer<input required value={interview.interviewer_name} onChange={(event) => setInterview({ ...interview, interviewer_name: event.target.value })} /></label>
              <label className="recruitment-field">Interview location<input required value={interview.location} onChange={(event) => setInterview({ ...interview, location: event.target.value })} /></label>
              <ModalActions onCancel={() => { setSelectedCandidate(null); setActionType('') }} saving={saving} submitLabel="Schedule & send invitation" />
            </form>
          )}
          {actionType === 'grade' && (
            <form onSubmit={submitGrade}>
              <label className="recruitment-field">Interview result
                <select required value={grade} onChange={(event) => setGrade(event.target.value)}>
                  <option value="">Select a result</option><option value="OUTSTANDING">Outstanding</option><option value="PASSED">Pass</option><option value="FAILED">Fail</option>
                </select>
              </label>
              <label className="recruitment-field">Interview notes / feedback<textarea rows="4" value={reason} onChange={(event) => setReason(event.target.value)} /></label>
              <ModalActions onCancel={() => { setSelectedCandidate(null); setActionType('') }} saving={saving} submitLabel="Save interview result" />
            </form>
          )}
          {actionType === 'offer' && (
            <form onSubmit={submitOffer}>
              <label className="recruitment-field">Proposed salary (UGX)<input type="number" min="0" step="1" value={salary} onChange={(event) => setSalary(event.target.value)} /></label>
              <label className="recruitment-field">Onboarding instructions<textarea rows="3" required value={requirements} onChange={(event) => setRequirements(event.target.value)} placeholder="Welcome message and onboarding instructions for the new hire." /></label>
              <label className="recruitment-field">Required documents <span>One document per line</span><textarea rows="4" value={requiredDocuments} onChange={(event) => setRequiredDocuments(event.target.value)} placeholder="National ID (NIN)&#10;Education certificates&#10;TIN details&#10;Bank account proof&#10;NSSF details" /></label>
              <ModalActions onCancel={() => { setSelectedCandidate(null); setActionType('') }} saving={saving} submitLabel="Save offer & send letter" />
            </form>
          )}
          {(actionType === 'reject' || actionType === 'decline') && (
            <form onSubmit={actionType === 'reject' ? rejectCandidate : declineOffer}>
              <label className="recruitment-field">Reason<textarea rows="4" required value={reason} onChange={(event) => setReason(event.target.value)} /></label>
              <p className="email-template-hint">This candidate and their application documents will remain in the rejected archive.</p>
              <ModalActions onCancel={() => { setSelectedCandidate(null); setActionType('') }} saving={saving} submitLabel={actionType === 'reject' ? 'Reject & send notice' : 'Record decline'} />
            </form>
          )}
        </Modal>
      )}
    </section>
  )
}

function SectionHeading({ title, description }) {
  return <div className="recruitment-section-heading"><div><h2>{title}</h2><p>{description}</p></div></div>
}

function DataTable({ headings, empty, children }) {
  return (
    <div className="recruitment-table-wrap">
      <table className="recruitment-table">
        <thead><tr>{headings.map((heading) => <th key={heading}>{heading}</th>)}</tr></thead>
        <tbody>
          {children}
          {!children?.length && <tr><td className="recruitment-empty-cell" colSpan={headings.length}>{empty}</td></tr>}
        </tbody>
      </table>
    </div>
  )
}

function StatusPill({ value }) {
  const label = {
    NOT_QUALIFIED: 'Did not meet requirements',
    PIPELINE_REJECTED: 'Rejected by HR',
    INTERVIEW_FAILED: 'Failed interview',
    OFFER_DECLINED: 'Offer declined',
    OFFER_FAILED: 'Offer not accepted',
  }[value] || value?.replaceAll('_', ' ') || 'Unknown'
  return <span className={`status-pill status-${value?.toLowerCase()}`}>{label}</span>
}

function CvLink({ candidate }) {
  const download = async () => {
    try {
      const { data } = await axios.get(`${API_BASE}/recruitment/candidates/${candidate.id}/cv`, { ...apiConfig(), responseType: 'blob' })
      const url = URL.createObjectURL(data)
      const link = document.createElement('a')
      link.href = url
      link.download = `${candidate.first_name}-${candidate.last_name}-CV`
      link.click()
      setTimeout(() => URL.revokeObjectURL(url), 30000)
    } catch { window.alert('The CV could not be downloaded. Please check your access or try again.') }
  }
  return <button className="cv-download" type="button" onClick={download}>View CV</button>
}

function Modal({ title, onClose, children }) {
  return (
    <div className="recruitment-modal-backdrop" onMouseDown={(event) => { if (event.target === event.currentTarget) onClose() }}>
      <section className="recruitment-modal" role="dialog" aria-modal="true" aria-labelledby="recruitment-modal-title">
        <div className="recruitment-modal-heading"><h2 id="recruitment-modal-title">{title}</h2><button type="button" onClick={onClose} aria-label="Close dialog">×</button></div>
        {children}
      </section>
    </div>
  )
}

function ModalActions({ onCancel, saving, submitLabel }) {
  return (
    <div className="recruitment-modal-actions">
      <button className="recruitment-secondary-button" type="button" onClick={onCancel} disabled={saving}>Cancel</button>
      <button className="recruitment-primary-button" type="submit" disabled={saving}>{saving ? 'Saving…' : <><Check size={14} /> {submitLabel}</>}</button>
    </div>
  )
}

export default RecruitmentDashboard
