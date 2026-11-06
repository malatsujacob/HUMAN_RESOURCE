import { useState } from 'react'
import axios from 'axios'

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api'

function getErrorMessage(error) {
  const detail = error.response?.data?.detail
  if (Array.isArray(detail)) {
    const messages = detail.map((item) => item.msg).filter(Boolean).join('; ')
    if (messages) return messages
  }
  return detail || error.message || 'Unable to complete onboarding.'
}

function Onboarding() {
  const [candidateId, setCandidateId] = useState('')
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState('')
  const [success, setSuccess] = useState('')

  async function handleSubmit(event) {
    event.preventDefault()
    setError('')
    setSuccess('')
    setSubmitting(true)

    const form = event.currentTarget
    const formData = new FormData(event.currentTarget)
    const token = window.localStorage.getItem('access_token')
    const headers = token ? { Authorization: `Bearer ${token}` } : {}

    try {
      const { data } = await axios.post(
        `${API_BASE_URL}/onboarding/${candidateId.trim()}`,
        {
          national_id: formData.get('national_id').trim(),
          tin_number: formData.get('tin_number').trim(),
          nssf_number: formData.get('nssf_number').trim(),
          bank_name: formData.get('bank_name').trim(),
          account_number: formData.get('account_number').trim(),
        },
        { headers },
      )
      setSuccess(
        `${data.first_name} ${data.last_name} has been onboarded as ${data.employee_number}.`,
      )
      form.reset()
      setCandidateId('')
    } catch (requestError) {
      setError(getErrorMessage(requestError))
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <section>
      <div className="page-heading">
        <div>
          <p className="eyebrow">PEOPLE &amp; CULTURE</p>
          <h1>Onboarding</h1>
          <p className="heading-subtitle">
            Convert a selected candidate into an employee.
          </p>
        </div>
      </div>

      <section className="panel onboarding-panel">
        <h2>Employee statutory and banking details</h2>
        {error && <p className="form-message error" role="alert">{error}</p>}
        {success && <p className="form-message success" role="status">{success}</p>}

        <form className="onboarding-form" onSubmit={handleSubmit}>
          <div className="input-group">
            <label htmlFor="candidate-id">Candidate ID</label>
            <input
              id="candidate-id"
              name="candidate_id"
              value={candidateId}
              onChange={(event) => setCandidateId(event.target.value)}
              placeholder="Enter the candidate UUID"
              required
            />
            <small>Use a candidate ID with status OFFERED or INTERVIEW_SCHEDULED.</small>
          </div>

          <div className="onboarding-field-grid">
            <div className="input-group">
              <label htmlFor="national-id">National ID (NIN)</label>
              <input id="national-id" name="national_id" maxLength="30" required />
            </div>
            <div className="input-group">
              <label htmlFor="tin-number">TIN</label>
              <input id="tin-number" name="tin_number" maxLength="20" required />
            </div>
            <div className="input-group">
              <label htmlFor="nssf-number">NSSF Number</label>
              <input id="nssf-number" name="nssf_number" maxLength="20" required />
            </div>
            <div className="input-group">
              <label htmlFor="bank-name">Bank Name</label>
              <input id="bank-name" name="bank_name" maxLength="100" required />
            </div>
            <div className="input-group">
              <label htmlFor="account-number">Account Number</label>
              <input id="account-number" name="account_number" maxLength="50" required />
            </div>
          </div>

          <button className="btn-primary" type="submit" disabled={submitting}>
            {submitting ? 'Onboarding…' : 'Convert to Employee'}
          </button>
        </form>
      </section>
    </section>
  )
}

export default Onboarding
