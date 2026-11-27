import { useEffect, useState } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import {
  getExitDetail,
  updateExitClearanceItem,
  upsertExitInterview,
  upsertExitFinalPay,
  revokeExitAccess,
  checkExitComplete,
  getModuleError,
} from '../../api/peopleModules'

function ExitDetail() {
  const { id } = useParams()
  const navigate = useNavigate()
  const [tab, setTab] = useState('overview')
  const [data, setData] = useState(null)
  const [completion, setCompletion] = useState(null)
  const [error, setError] = useState('')
  const [notice, setNotice] = useState('')
  const [busy, setBusy] = useState(false)

  const load = async () => {
    try {
      const [detail, comp] = await Promise.all([
        getExitDetail(id),
        checkExitComplete(id).catch(() => null),
      ])
      setData(detail)
      setCompletion(comp)
    } catch (e) {
      setError(getModuleError(e))
    }
  }

  useEffect(() => { load() }, [id])

  const markItem = async (itemId, status) => {
    setBusy(true); setError(''); setNotice('')
    try {
      await updateExitClearanceItem(itemId, { status })
      setNotice(`Item marked ${status}`)
      await load()
    } catch (e) { setError(getModuleError(e)) }
    finally { setBusy(false) }
  }

  const revokeAccess = async () => {
    if (!confirm('Revoke system access for this employee?')) return
    setBusy(true); setError(''); setNotice('')
    try {
      await revokeExitAccess(id)
      setNotice('Access revoked.')
      await load()
    } catch (e) { setError(getModuleError(e)) }
    finally { setBusy(false) }
  }

  if (!data) return <div className="module-page"><p>Loading…</p></div>

  return (
    <div className="module-page">
      <header className="module-header">
        <div>
          <p className="module-kicker">EXIT · {data.clearance_status}</p>
          <h1>Exit detail</h1>
          <p>{data.exit_type} · Last day: {data.last_working_day}</p>
        </div>
        <button className="module-secondary-button" onClick={() => navigate('/exit')}>← Back</button>
      </header>

      {notice && <div className="module-notice">{notice}</div>}
      {error && <div className="module-error">{error}</div>}

      {completion && (
        <section className="module-card" style={{ background: completion.fully_complete ? '#e8f5e9' : '#fff3e0' }}>
          <h3>{completion.fully_complete ? '✓ Fully complete' : '⚠ Incomplete'}</h3>
          <ul style={{ margin: 0 }}>
            <li>Clearance: {completion.clearance_items_done ? '✓' : '✗'}</li>
            <li>Interview: {completion.interview_done ? '✓' : '✗'}</li>
            <li>Final pay: {completion.final_pay_done ? '✓' : '✗'}</li>
            <li>Access revoked: {completion.access_revoked ? '✓' : '✗'}</li>
          </ul>
        </section>
      )}

      <div style={{ display: 'flex', gap: 8, marginBottom: 16, flexWrap: 'wrap' }}>
        {['overview', 'clearance', 'interview', 'final-pay'].map((t) => (
          <button key={t} className={tab === t ? 'btn-primary' : 'module-secondary-button'}
            onClick={() => setTab(t)}>
            {t === 'final-pay' ? 'Final Pay' : t.charAt(0).toUpperCase() + t.slice(1)}
          </button>
        ))}
      </div>

      {tab === 'overview' && (
        <section className="module-card">
          <h2>Overview</h2>
          <dl style={{ display: 'grid', gridTemplateColumns: '200px 1fr', gap: 8 }}>
            <dt>Exit type</dt><dd>{data.exit_type || '—'}</dd>
            <dt>Resignation date</dt><dd>{data.resignation_date || '—'}</dd>
            <dt>Notice period</dt><dd>{data.notice_period_days ?? '—'} days</dd>
            <dt>Notice served</dt><dd>{data.notice_served ? 'Yes' : 'No'}</dd>
            <dt>Rehire eligible</dt><dd>{data.rehire_eligible === null ? '—' : (data.rehire_eligible ? 'Yes' : 'No')}</dd>
            <dt>Access revoked</dt><dd>{data.access_revoked ? `Yes (${data.access_revoked_at})` : 'No'}</dd>
            <dt>Reason</dt><dd style={{ whiteSpace: 'pre-wrap' }}>{data.reason}</dd>
          </dl>
          {!data.access_revoked && (
            <button className="btn-primary" onClick={revokeAccess} disabled={busy} style={{ marginTop: 12 }}>
              {busy ? 'Revoking…' : 'Revoke system access now'}
            </button>
          )}
        </section>
      )}

      {tab === 'clearance' && (
        <section className="module-card">
          <h2>Clearance items</h2>
          <table className="module-table" style={{ width: '100%' }}>
            <thead>
              <tr><th>Item</th><th>Status</th><th>Cleared by</th><th>Actions</th></tr>
            </thead>
            <tbody>
              {data.clearance_items.map((i) => (
                <tr key={i.id}>
                  <td>{i.item_name}</td>
                  <td><span className={`module-status ${i.status.toLowerCase()}`}>{i.status}</span></td>
                  <td>{i.cleared_at ? new Date(i.cleared_at).toLocaleString() : '—'}</td>
                  <td>
                    {i.status !== 'CLEARED' && (
                      <button className="module-secondary-button" onClick={() => markItem(i.id, 'CLEARED')} disabled={busy}>
                        Mark cleared
                      </button>
                    )}
                    {i.status === 'PENDING' && (
                      <button className="module-secondary-button" onClick={() => markItem(i.id, 'BLOCKED')} disabled={busy} style={{ marginLeft: 8 }}>
                        Mark blocked
                      </button>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </section>
      )}

      {tab === 'interview' && (
        <section className="module-card">
          <h2>Exit interview</h2>
          {data.interview ? (
            <dl style={{ display: 'grid', gridTemplateColumns: '200px 1fr', gap: 8 }}>
              <dt>Interview date</dt><dd>{data.interview.interview_date || '—'}</dd>
              <dt>Reason category</dt><dd>{data.interview.reason_category || '—'}</dd>
              <dt>Would recommend</dt><dd>{data.interview.would_recommend === null ? '—' : (data.interview.would_recommend ? 'Yes' : 'No')}</dd>
              <dt>Rehire eligible</dt><dd>{data.interview.rehire_eligible === null ? '—' : (data.interview.rehire_eligible ? 'Yes' : 'No')}</dd>
              <dt>Feedback</dt><dd style={{ whiteSpace: 'pre-wrap' }}>{data.interview.feedback_notes || '—'}</dd>
            </dl>
          ) : (
            <InterviewForm exitId={id} onSaved={load} />
          )}
        </section>
      )}

      {tab === 'final-pay' && (
        <section className="module-card">
          <h2>Final pay</h2>
          {data.final_pay ? (
            <dl style={{ display: 'grid', gridTemplateColumns: '200px 1fr', gap: 8 }}>
              <dt>Basic salary</dt><dd>{Number(data.final_pay.basic_salary).toLocaleString()}</dd>
              <dt>Leave payout</dt><dd>{Number(data.final_pay.leave_payout).toLocaleString()}</dd>
              <dt>Gratuity</dt><dd>{Number(data.final_pay.gratuity).toLocaleString()}</dd>
              <dt>Notice pay</dt><dd>{Number(data.final_pay.notice_pay).toLocaleString()}</dd>
              <dt>Other earnings</dt><dd>{Number(data.final_pay.other_earnings).toLocaleString()}</dd>
              <dt>Loan deduction</dt><dd>-{Number(data.final_pay.loan_deduction).toLocaleString()}</dd>
              <dt>Advance deduction</dt><dd>-{Number(data.final_pay.advance_deduction).toLocaleString()}</dd>
              <dt>Asset deduction</dt><dd>-{Number(data.final_pay.asset_deduction).toLocaleString()}</dd>
              <dt>Other deductions</dt><dd>-{Number(data.final_pay.other_deductions).toLocaleString()}</dd>
              <dt><strong>Net pay</strong></dt><dd><strong>{Number(data.final_pay.net_pay).toLocaleString()}</strong></dd>
              <dt>Payment date</dt><dd>{data.final_pay.payment_date || '—'}</dd>
              <dt>Paid</dt><dd>{data.final_pay.paid ? 'Yes' : 'No'}</dd>
            </dl>
          ) : (
            <FinalPayForm exitId={id} onSaved={load} />
          )}
        </section>
      )}
    </div>
  )
}

function InterviewForm({ exitId, onSaved }) {
  const [form, setForm] = useState({ interview_date: '', reason_category: '', feedback_notes: '', would_recommend: null, rehire_eligible: null })
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')

  const submit = async (e) => {
    e.preventDefault(); setBusy(true); setError('')
    try {
      const payload = { ...form }
      if (!payload.interview_date) delete payload.interview_date
      await upsertExitInterview(exitId, payload)
      onSaved()
    } catch (e) { setError(getModuleError(e)) }
    finally { setBusy(false) }
  }

  return (
    <form className="module-form" onSubmit={submit}>
      {error && <div className="module-error">{error}</div>}
      <label>Interview date
        <input type="date" value={form.interview_date} onChange={(e) => setForm({ ...form, interview_date: e.target.value })} />
      </label>
      <label>Reason category
        <select value={form.reason_category} onChange={(e) => setForm({ ...form, reason_category: e.target.value })}>
          <option value="">— Select —</option>
          <option value="BETTER_PAY">Better pay</option>
          <option value="CAREER_GROWTH">Career growth</option>
          <option value="WORK_ENVIRONMENT">Work environment</option>
          <option value="PERSONAL">Personal reasons</option>
          <option value="RELOCATION">Relocation</option>
          <option value="OTHER">Other</option>
        </select>
      </label>
      <label style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
        <input type="checkbox" checked={form.would_recommend === true} onChange={(e) => setForm({ ...form, would_recommend: e.target.checked ? true : null })} />
        Would recommend company
      </label>
      <label style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
        <input type="checkbox" checked={form.rehire_eligible === true} onChange={(e) => setForm({ ...form, rehire_eligible: e.target.checked ? true : null })} />
        Rehire eligible
      </label>
      <label style={{ gridColumn: '1 / -1' }}>Feedback notes
        <textarea rows={4} value={form.feedback_notes} onChange={(e) => setForm({ ...form, feedback_notes: e.target.value })} />
      </label>
      <button className="btn-primary" type="submit" disabled={busy} style={{ gridColumn: '1 / -1' }}>
        {busy ? 'Saving…' : 'Save interview'}
      </button>
    </form>
  )
}

function FinalPayForm({ exitId, onSaved }) {
  const [form, setForm] = useState({
    basic_salary: 0, leave_payout: 0, gratuity: 0, notice_pay: 0, other_earnings: 0,
    loan_deduction: 0, advance_deduction: 0, asset_deduction: 0, other_deductions: 0,
    payment_date: '', paid: false, notes: '',
  })
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')

  const submit = async (e) => {
    e.preventDefault(); setBusy(true); setError('')
    try {
      const payload = { ...form }
      if (!payload.payment_date) delete payload.payment_date
      for (const k of ['basic_salary', 'leave_payout', 'gratuity', 'notice_pay', 'other_earnings', 'loan_deduction', 'advance_deduction', 'asset_deduction', 'other_deductions']) {
        payload[k] = Number(payload[k] || 0)
      }
      await upsertExitFinalPay(exitId, payload)
      onSaved()
    } catch (e) { setError(getModuleError(e)) }
    finally { setBusy(false) }
  }

  return (
    <form className="module-form" onSubmit={submit}>
      {error && <div className="module-error">{error}</div>}
      <label>Basic salary<input type="number" step="0.01" value={form.basic_salary} onChange={(e) => setForm({ ...form, basic_salary: e.target.value })} /></label>
      <label>Leave payout<input type="number" step="0.01" value={form.leave_payout} onChange={(e) => setForm({ ...form, leave_payout: e.target.value })} /></label>
      <label>Gratuity<input type="number" step="0.01" value={form.gratuity} onChange={(e) => setForm({ ...form, gratuity: e.target.value })} /></label>
      <label>Notice pay<input type="number" step="0.01" value={form.notice_pay} onChange={(e) => setForm({ ...form, notice_pay: e.target.value })} /></label>
      <label>Other earnings<input type="number" step="0.01" value={form.other_earnings} onChange={(e) => setForm({ ...form, other_earnings: e.target.value })} /></label>
      <label>Loan deduction<input type="number" step="0.01" value={form.loan_deduction} onChange={(e) => setForm({ ...form, loan_deduction: e.target.value })} /></label>
      <label>Advance deduction<input type="number" step="0.01" value={form.advance_deduction} onChange={(e) => setForm({ ...form, advance_deduction: e.target.value })} /></label>
      <label>Asset deduction<input type="number" step="0.01" value={form.asset_deduction} onChange={(e) => setForm({ ...form, asset_deduction: e.target.value })} /></label>
      <label>Other deductions<input type="number" step="0.01" value={form.other_deductions} onChange={(e) => setForm({ ...form, other_deductions: e.target.value })} /></label>
      <label>Payment date<input type="date" value={form.payment_date} onChange={(e) => setForm({ ...form, payment_date: e.target.value })} /></label>
      <label style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
        <input type="checkbox" checked={form.paid} onChange={(e) => setForm({ ...form, paid: e.target.checked })} /> Paid
      </label>
      <label style={{ gridColumn: '1 / -1' }}>Notes<textarea rows={2} value={form.notes} onChange={(e) => setForm({ ...form, notes: e.target.value })} /></label>
      <button className="btn-primary" type="submit" disabled={busy} style={{ gridColumn: '1 / -1' }}>
        {busy ? 'Saving…' : 'Save final pay'}
      </button>
    </form>
  )
}

export default ExitDetail
