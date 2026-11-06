import { useCallback, useEffect, useState } from 'react'
import {
  getModuleError,
  getPerformanceReviews,
  submitPerformanceReview,
} from '../../api/peopleModules.js'
import '../ModuleDashboards.css'

function PerformanceDashboard() {
  const role = (window.localStorage.getItem('role') || '').toUpperCase()
  const isHod = role === 'HOD'
  const [reviews, setReviews] = useState([])
  const [loading, setLoading] = useState(true)
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState('')
  const [notice, setNotice] = useState('')

  const loadReviews = useCallback(async () => {
    setError('')
    try {
      setReviews(await getPerformanceReviews())
    } catch (requestError) {
      setError(getModuleError(requestError))
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    loadReviews()
  }, [loadReviews])

  async function handleSubmit(event) {
    event.preventDefault()
    setSubmitting(true)
    setError('')
    setNotice('')
    const formData = new FormData(event.currentTarget)
    const payload = {
      review_period: formData.get('review_period').trim(),
      employee_id: formData.get('employee_id').trim(),
      hod_rating: Number(formData.get('hod_rating')),
      hod_comments: formData.get('hod_comments').trim(),
    }

    try {
      await submitPerformanceReview(payload)
      event.currentTarget.reset()
      setNotice('Performance rating submitted.')
      await loadReviews()
    } catch (requestError) {
      setError(getModuleError(requestError))
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <section className="module-dashboard">
      <header className="module-dashboard-heading">
        <div>
          <p className="eyebrow">PEOPLE DEVELOPMENT</p>
          <h1>Performance</h1>
          <p>{isHod ? 'Review employees in your department.' : 'Review your performance ratings and comments.'}</p>
        </div>
      </header>

      {error && <p className="module-feedback error" role="alert">{error}</p>}
      {notice && <p className="module-feedback success" role="status">{notice}</p>}

      {isHod && (
        <section className="module-card">
          <h2>Rate an employee</h2>
          <form className="module-form" onSubmit={handleSubmit}>
            <label>
              Employee ID
              <input name="employee_id" required />
            </label>
            <label>
              Review period
              <input name="review_period" placeholder="Q4 2026" maxLength="50" required />
            </label>
            <label>
              Rating (1–5)
              <select name="hod_rating" defaultValue="" required>
                <option value="" disabled>Select rating</option>
                {[1, 2, 3, 4, 5].map((rating) => (
                  <option value={rating} key={rating}>{rating}</option>
                ))}
              </select>
            </label>
            <label className="module-form-wide">
              Comments
              <textarea name="hod_comments" maxLength="500" rows="3" />
            </label>
            <button className="btn-primary" type="submit" disabled={submitting}>
              {submitting ? 'Submitting…' : 'Submit rating'}
            </button>
          </form>
        </section>
      )}

      <section className="module-card">
        <div className="module-card-heading">
          <div>
            <h2>{isHod ? 'Department reviews' : 'Past ratings'}</h2>
            <p>{isHod ? 'Ratings and self assessments for your team.' : 'Your past self and HOD ratings.'}</p>
          </div>
          <button className="module-secondary-button" type="button" onClick={loadReviews} disabled={loading}>
            Refresh
          </button>
        </div>
        {loading ? (
          <p className="module-empty" role="status">Loading reviews…</p>
        ) : reviews.length === 0 ? (
          <p className="module-empty">No performance reviews yet.</p>
        ) : (
          <div className="module-table-scroll">
            <table className="module-table">
              <thead>
                <tr>
                  {isHod && <th>Employee ID</th>}
                  <th>Period</th>
                  <th>Self rating</th>
                  <th>HOD rating</th>
                  <th>HOD comments</th>
                </tr>
              </thead>
              <tbody>
                {reviews.map((review) => (
                  <tr key={review.id}>
                    {isHod && <td>{review.employee_id}</td>}
                    <td>{review.review_period}</td>
                    <td>{review.self_rating ?? '—'}</td>
                    <td>{review.hod_rating ?? '—'}</td>
                    <td>{review.hod_comments || '—'}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </section>
    </section>
  )
}

export default PerformanceDashboard
