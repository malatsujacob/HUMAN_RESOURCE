import { useState } from 'react'
import axios from 'axios'
import { BriefcaseBusiness } from 'lucide-react'
import './OfferResponse.css'

const API_BASE = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api'

function OfferResponse() {
  const token = new URLSearchParams(window.location.search).get('token') || ''
  const [reason, setReason] = useState('')
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState('')
  const [response, setResponse] = useState(null)

  const submitResponse = async (action) => {
    if (action === 'decline' && !reason.trim()) {
      setError('Please provide a reason when declining the offer.')
      return
    }
    setSubmitting(true)
    setError('')
    try {
      const { data } = await axios.post(
        `${API_BASE}/recruitment/offers/${encodeURIComponent(token)}/${action}`,
        { reason },
      )
      setResponse(data)
    } catch (requestError) {
      setError(requestError.response?.data?.detail || 'Your response could not be recorded. Please contact Human Resources.')
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <main className="offer-response-page">
      <div className="offer-response-brand">
        <span className="brand-mark">CC</span>
        <span><strong>Chap Chap Africa</strong><small>CAREERS</small></span>
      </div>
      <section className="offer-response-card">
        <span className="offer-response-icon"><BriefcaseBusiness size={20} aria-hidden="true" /></span>
        <p className="eyebrow">EMPLOYMENT OFFER</p>
        <h1>Respond to your offer</h1>
        {response ? (
          <div className="offer-response-success" role="status">
            {response.message}
            {response.email_sent === false && <p>A confirmation email could not be sent. Human Resources can still see your response.</p>}
          </div>
        ) : (
          <>
            <p className="offer-response-description">
              Accepting the offer creates your pending employee record and starts secure onboarding.
              This secure link can only be used once.
            </p>
            {!token && <p className="offer-response-error" role="alert">This offer link is incomplete. Please open the link from your offer email.</p>}
            {error && <p className="offer-response-error" role="alert">{error}</p>}
            <label className="offer-response-reason">
              If declining, provide a reason. This is required to record your response.
              <textarea rows="3" value={reason} onChange={(event) => setReason(event.target.value)} />
            </label>
            <div className="offer-response-actions">
              <button type="button" disabled={!token || submitting} onClick={() => submitResponse('accept')}>
                {submitting ? 'Submitting…' : 'Accept offer'}
              </button>
              <button type="button" className="offer-decline" disabled={!token || submitting} onClick={() => submitResponse('decline')}>
                Decline offer
              </button>
            </div>
            <p className="offer-response-footnote">If you have questions, reply to your offer email to contact Human Resources.</p>
          </>
        )}
      </section>
    </main>
  )
}

export default OfferResponse
