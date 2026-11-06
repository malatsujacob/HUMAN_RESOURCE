import { useCallback, useEffect, useState } from 'react'
import { getLeaveError, getPendingLeave, reviewLeave } from '../../api/leave.js'

function HODApprovals() {
  const [requests, setRequests] = useState([])
  const [loading, setLoading] = useState(true)
  const [busyRequest, setBusyRequest] = useState('')
  const [error, setError] = useState('')
  const [notice, setNotice] = useState('')

  const loadRequests = useCallback(async () => {
    setError('')
    try {
      setRequests(await getPendingLeave())
    } catch (requestError) {
      setError(getLeaveError(requestError))
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    loadRequests()
  }, [loadRequests])

  async function handleReview(requestId, decision) {
    setBusyRequest(requestId)
    setError('')
    setNotice('')
    try {
      const action = decision === 'APPROVED' ? 'approve' : 'reject'
      await reviewLeave(requestId, action)
      setNotice(`Leave request ${decision.toLowerCase()}.`)
      await loadRequests()
    } catch (requestError) {
      setError(getLeaveError(requestError))
    } finally {
      setBusyRequest('')
    }
  }

  return (
    <section className="module-panel hod-approvals-panel">
      <div className="module-section-heading">
        <div>
          <h2>Pending HOD approvals</h2>
          <p>Review leave requests from employees in your department.</p>
        </div>
        <button className="btn-secondary" type="button" onClick={loadRequests} disabled={loading}>
          Refresh
        </button>
      </div>

      {error && <p className="module-alert error" role="alert">{error}</p>}
      {notice && <p className="module-alert success" role="status">{notice}</p>}
      {loading ? (
        <p className="module-message" role="status">Loading pending requests…</p>
      ) : requests.length === 0 ? (
        <p className="module-message">There are no pending leave requests.</p>
      ) : (
        <div className="module-table-wrap">
          <table className="module-table">
            <thead>
              <tr>
                <th>Employee</th>
                <th>Type</th>
                <th>Dates</th>
                <th>Reason</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {requests.map((request) => (
                <tr key={request.id}>
                  <td>{request.employee_id}</td>
                  <td>{request.leave_type}</td>
                  <td>{request.start_date} – {request.end_date}</td>
                  <td>{request.reason}</td>
                  <td>
                    <div className="leave-review-actions">
                      <button
                        className="leave-approve-button"
                        type="button"
                        disabled={busyRequest === request.id}
                        onClick={() => handleReview(request.id, 'APPROVED')}
                      >
                        Approve
                      </button>
                      <button
                        className="leave-reject-button"
                        type="button"
                        disabled={busyRequest === request.id}
                        onClick={() => handleReview(request.id, 'REJECTED')}
                      >
                        Reject
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </section>
  )
}

export default HODApprovals
