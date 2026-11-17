import { useEffect, useState } from 'react'
import axios from 'axios'
import { BriefcaseBusiness } from 'lucide-react'
import FlexibleSelect from '../../components/FlexibleSelect'
import './PublicApply.css'

const API_BASE = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api'
const EMPTY_FORM = {
  requisition_id: '',
  first_name: '',
  last_name: '',
  email: '',
  phone_number: '',
  education_level: 'Bachelor',
  experience_years: 0,
  cover_letter: '',
}

function PublicApply() {
  const [requisitions, setRequisitions] = useState([])
  const [formData, setFormData] = useState(EMPTY_FORM)
  const [cv, setCv] = useState(null)
  const [message, setMessage] = useState('')
  const [messageType, setMessageType] = useState('')
  const [submitting, setSubmitting] = useState(false)
  const [loading, setLoading] = useState(true)
  const [portalClosed, setPortalClosed] = useState(false)

  useEffect(() => {
    Promise.all([
      axios.get(`${API_BASE}/recruitment/portal-status`),
      axios.get(`${API_BASE}/recruitment/requisitions/active`),
    ]).then(([portalResponse, requisitionResponse]) => {
      setPortalClosed(!portalResponse.data.portal_is_open)
      setRequisitions(requisitionResponse.data)
    }).catch((requestError) => {
      setMessage(requestError.response?.data?.detail || 'The careers portal could not be loaded. Please try again later.')
      setMessageType('error')
    }).finally(() => setLoading(false))
  }, [])

  const selectedJob = requisitions.find((item) => item.id === formData.requisition_id)
  const coverLetterWords = formData.cover_letter.trim().split(/\s+/).filter(Boolean).length

  const handleSubmit = async (event) => {
    event.preventDefault()
    if (coverLetterWords > 500) {
      setMessage('Please keep your cover letter to 500 words or fewer.')
      setMessageType('error')
      return
    }
    if (cv && cv.size > 5 * 1024 * 1024) {
      setMessage('Your CV must be smaller than 5 MB.')
      setMessageType('error')
      return
    }

    setSubmitting(true)
    setMessage('')
    try {
      const request = cv
        ? (() => {
          const payload = new FormData()
          payload.append('application', JSON.stringify(formData))
          payload.append('cv', cv)
          return axios.post(`${API_BASE}/recruitment/apply-with-cv`, payload)
        })()
        : axios.post(`${API_BASE}/recruitment/apply`, formData)
      const response = await request
      const emailNote = response.data.email_sent === false ? ' A notification email could not be sent at this time.' : ''
      setMessage(`${response.data.message}${emailNote}`)
      setMessageType(response.data.status === 'REJECTED' ? 'error' : 'success')
      if (response.data.status === 'IN_PIPELINE') {
        setFormData(EMPTY_FORM)
        setCv(null)
        event.target.reset()
      }
    } catch (requestError) {
      setMessage(requestError.response?.data?.detail || 'There was a problem submitting your application.')
      setMessageType('error')
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <main className="public-apply-page">
      <div className="apply-brand">
        <span className="brand-mark">CC</span>
        <span className="brand-copy"><strong>Chap Chap Africa</strong><span>CAREERS</span></span>
      </div>
      <section className="apply-card">
        <header className="apply-card-heading">
          <span className="apply-heading-icon"><BriefcaseBusiness size={19} aria-hidden="true" /></span>
          <p className="eyebrow">JOIN OUR TEAM</p>
          <h1>Job application</h1>
          <p>Tell us about yourself and the role you are interested in.</p>
        </header>

        {loading ? <p className="apply-loading" role="status">Loading open positions…</p> : portalClosed ? (
          <div className="apply-error" role="status">{message || 'The application portal is currently closed. Please check back later.'}</div>
        ) : requisitions.length === 0 ? (
          <div className="apply-error" role="status">{message || 'There are no open positions at the moment. Please check back later.'}</div>
        ) : (
          <form className="apply-form" onSubmit={handleSubmit}>
            {message && <p className={messageType === 'error' ? 'apply-error' : 'apply-success-message'} role={messageType === 'error' ? 'alert' : 'status'}>{message}</p>}

            <label className="form-field">Position <b>*</b>
              <select required value={formData.requisition_id} onChange={(event) => setFormData({ ...formData, requisition_id: event.target.value })}>
                <option value="">Select an open position</option>
                {requisitions.map((item) => <option key={item.id} value={item.id}>{item.job_title}</option>)}
              </select>
              {selectedJob && <small>{selectedJob.min_education} minimum · {selectedJob.min_experience} years’ experience. {selectedJob.description}</small>}
            </label>

            <div className="apply-field-grid">
              <label className="form-field">First name <b>*</b><input required maxLength="100" value={formData.first_name} onChange={(event) => setFormData({ ...formData, first_name: event.target.value })} /></label>
              <label className="form-field">Last name <b>*</b><input required maxLength="100" value={formData.last_name} onChange={(event) => setFormData({ ...formData, last_name: event.target.value })} /></label>
            </div>

            <div className="apply-field-grid">
              <label className="form-field">Email <b>*</b><input type="email" required maxLength="100" value={formData.email} onChange={(event) => setFormData({ ...formData, email: event.target.value })} /></label>
              <label className="form-field">Phone <b>*</b><input type="tel" required maxLength="30" value={formData.phone_number} onChange={(event) => setFormData({ ...formData, phone_number: event.target.value })} /></label>
            </div>

            <div className="apply-field-grid">
              <label className="form-field">Highest education <b>*</b>
                <FlexibleSelect name="education_level" required value={formData.education_level} onChange={(event) => setFormData({ ...formData, education_level: event.target.value })} options={['Certificate', 'Diploma', 'Bachelor', 'Master', 'PhD']} placeholder="Select highest education"/>
              </label>
              <label className="form-field">Years of experience <b>*</b><input type="number" min="0" required value={formData.experience_years} onChange={(event) => setFormData({ ...formData, experience_years: Number(event.target.value) })} /></label>
            </div>

            <label className="form-field">Cover letter <b>*</b>
              <textarea required rows="5" value={formData.cover_letter} onChange={(event) => setFormData({ ...formData, cover_letter: event.target.value })} placeholder="Briefly explain why you are a good fit." />
              <small className={`word-count ${coverLetterWords > 500 ? 'over-limit' : ''}`}>{coverLetterWords} / 500 words</small>
            </label>

            <label className="form-field">CV / resume <small>Optional · PDF, DOC, or DOCX · 5 MB maximum</small>
              <span className="cv-file-input">
                <BriefcaseBusiness size={15} aria-hidden="true" />
                <span>{cv?.name || 'Choose a file'}</span>
                <input type="file" accept=".pdf,.doc,.docx" onChange={(event) => setCv(event.target.files?.[0] || null)} />
              </span>
            </label>

            <button className="apply-submit" type="submit" disabled={submitting || coverLetterWords > 500}>
              {submitting ? 'Submitting application…' : 'Submit application'}
            </button>
            <p className="apply-privacy">Your application details and documents are used only for recruitment.</p>
          </form>
        )}

      </section>
    </main>
  )
}

export default PublicApply
