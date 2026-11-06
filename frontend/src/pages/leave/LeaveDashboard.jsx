import { useState } from 'react'
import { requestLeave, getLeaveError } from '../../api/leave.js'
import HODApprovals from './HODApprovals.jsx'
import './Leave.css'

function LeaveDashboard() {
  const role = (window.localStorage.getItem('role') || '').toUpperCase()
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState('')
  const [notice, setNotice] = useState('')

  async function handleSubmit(event) {
    event.preventDefault()
    setSubmitting(true)
    setError('')
    setNotice('')
    const formData = new FormData(event.currentTarget)

    try {
      await requestLeave({
        leave_type: formData.get('leave_type'),
        start_date: formData.get('start_date'),
        end_date: formData.get('end_date'),
        reason: formData.get('reason').trim(),
      })
      event.currentTarget.reset()
      setNotice('Your leave request has been submitted for approval.')
    } catch (requestError) {
      setError(getLeaveError(requestError))
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <section className="module-page">
      <header className="module-heading">
        <div>
          <p className="eyebrow">TIME AWAY</p>
          <h1>Leave</h1>
          <p>Submit a leave request and track the approval process.</p>
        </div>
      </header>

      {error && <p className="module-alert error" role="alert">{error}</p>}
      {notice && <p className="module-alert success" role="status">{notice}</p>}

      <section className="module-panel leave-request-panel">
        <div className="module-section-heading">
          <div>
            <h2>Request leave</h2>
            <p>Complete the details below to send a request to your HOD.</p>
          </div>
        </div>
        <form className="leave-form" onSubmit={handleSubmit}>
          <label>
            Leave type
            <select name="leave_type" defaultValue="ANNUAL" required>
              <option value="ANNUAL">Annual</option>
              <option value="SICK">Sick</option>
              <option value="MATERNITY">Maternity</option>
            </select>
          </label>
          <label>
            Start date
            <input name="start_date" type="date" required />
          </label>
          <label>
            End date
            <input name="end_date" type="date" required />
          </label>
          <label className="leave-reason-field">
            Reason
            <textarea name="reason" maxLength="255" rows="4" required />
          </label>
          <button className="btn-primary" type="submit" disabled={submitting}>
            {submitting ? 'Submitting…' : 'Submit request'}
          </button>
        </form>
      </section>

      {role === 'HOD' && <HODApprovals />}
    </section>
  )
}

export default LeaveDashboard
