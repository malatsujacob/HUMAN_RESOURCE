import { useEffect, useState } from 'react'
import { useParams, useNavigate, useSearchParams } from 'react-router-dom'
import {
  getDisciplinaryCaseDetail,
  addDisciplinaryEvidence,
  listDisciplinaryEvidence,
  deleteDisciplinaryEvidence,
  recordDisciplinaryOutcome,
  resolveDisciplinaryCase,
  updateDisciplinaryAppeal,
  getModuleError,
} from '../../api/peopleModules'

function CaseDetail() {
  const { id } = useParams()
  const navigate = useNavigate()
  const [searchParams] = useSearchParams()
  const requestedTab = searchParams.get('tab')
  const [tab, setTab] = useState(
    ['overview', 'resolution', 'evidence', 'outcome', 'appeal'].includes(requestedTab)
      ? requestedTab
      : 'overview',
  )
  const [loading, setLoading] = useState(true)
  const [caseData, setCaseData] = useState(null)
  const [evidence, setEvidence] = useState([])
  const [error, setError] = useState('')
  const [notice, setNotice] = useState('')
  const [busy, setBusy] = useState(false)
  const [resolutionNote, setResolutionNote] = useState('')
  const [evidenceForm, setEvidenceForm] = useState({ file_name: '', file_path: '', file_type: '', description: '' })
  const [outcomeForm, setOutcomeForm] = useState({
    outcome_type: '', warning_level: '', effective_date: '', expiry_date: '',
    suspension_days: '', payroll_deduction: false, deduction_amount: '', decision_notes: '',
  })
  const [appealForm, setAppealForm] = useState({
    appeal_lodged: true, appeal_date: '', appeal_grounds: '', appeal_outcome: '', appeal_notes: '',
  })

  const load = async () => {
    setError('')
    try {
      const [detail, evs] = await Promise.all([
        getDisciplinaryCaseDetail(id),
        listDisciplinaryEvidence(id).catch(() => []),
      ])
      setCaseData(detail)
      setEvidence(evs)
    } catch (e) {
      setError(getModuleError(e))
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => { load() }, [id])

  const submitEvidence = async (e) => {
    e.preventDefault(); setBusy(true); setError(''); setNotice('')
    try {
      await addDisciplinaryEvidence(id, evidenceForm)
      setEvidenceForm({ file_name: '', file_path: '', file_type: '', description: '' })
      setNotice('Evidence added.'); await load()
    } catch (e) { setError(getModuleError(e)) }
    finally { setBusy(false) }
  }

  const removeEvidence = async (eid) => {
    if (!confirm('Delete this evidence?')) return
    setBusy(true); setError(''); setNotice('')
    try {
      await deleteDisciplinaryEvidence(eid)
      setNotice('Evidence deleted.'); await load()
    } catch (e) { setError(getModuleError(e)) }
    finally { setBusy(false) }
  }

  const submitOutcome = async (e) => {
    e.preventDefault(); setBusy(true); setError(''); setNotice('')
    try {
      const payload = { ...outcomeForm }
      if (!payload.effective_date) delete payload.effective_date
      if (!payload.expiry_date) delete payload.expiry_date
      if (payload.suspension_days === '') delete payload.suspension_days
      else payload.suspension_days = Number(payload.suspension_days)
      if (payload.deduction_amount === '') delete payload.deduction_amount
      else payload.deduction_amount = Number(payload.deduction_amount)
      if (!payload.warning_level) delete payload.warning_level
      if (!payload.decision_notes) delete payload.decision_notes
      await recordDisciplinaryOutcome(id, payload)
      setNotice('Outcome recorded.'); await load()
    } catch (e) { setError(getModuleError(e)) }
    finally { setBusy(false) }
  }

  const submitResolution = async (e) => {
    e.preventDefault(); setBusy(true); setError(''); setNotice('')
    try {
      await resolveDisciplinaryCase(id, { resolution_note: resolutionNote.trim() })
      setNotice('Case resolved. The resolution report has been saved.')
      await load()
    } catch (e) { setError(getModuleError(e)) }
    finally { setBusy(false) }
  }

  const submitAppeal = async (e) => {
    e.preventDefault(); setBusy(true); setError(''); setNotice('')
    try {
      const payload = { ...appealForm }
      if (!payload.appeal_date) delete payload.appeal_date
      if (!payload.appeal_grounds) delete payload.appeal_grounds
      if (!payload.appeal_outcome) delete payload.appeal_outcome
      if (!payload.appeal_notes) delete payload.appeal_notes
      await updateDisciplinaryAppeal(id, payload)
      setNotice('Appeal updated.'); await load()
    } catch (e) { setError(getModuleError(e)) }
    finally { setBusy(false) }
  }

  if (!caseData) {
    return (
      <div className="module-page">
        {loading ? <p>Loading case details…</p> : (
          <>
            <div className="module-error" role="alert">{error || 'Case details could not be loaded.'}</div>
            <button className="module-secondary-button" type="button" onClick={() => navigate('/disciplinary')}>
              Back to disciplinary cases
            </button>
          </>
        )}
      </div>
    )
  }

  return (
    <div className="module-page">
      <header className="module-header">
        <div>
          <p className="module-kicker">{caseData.case_number || 'CASE'} · {caseData.status}</p>
          <h1>Case detail</h1>
          <p>{caseData.category || 'Uncategorised'} · {caseData.severity || '—'} · {caseData.incident_date}</p>
        </div>
        <button className="module-secondary-button" onClick={() => navigate('/disciplinary')}>← Back</button>
      </header>

      {notice && <div className="module-notice">{notice}</div>}
      {error && <div className="module-error">{error}</div>}

      <div style={{ display: 'flex', gap: 8, marginBottom: 16, flexWrap: 'wrap' }}>
        {[
          ['overview', 'Overview'],
          ['resolution', 'Resolution report'],
          ['evidence', 'Evidence'],
          ['outcome', 'Outcome'],
          ['appeal', 'Appeal'],
        ].map(([id, label]) => (
          <button key={id} type="button" className={tab === id ? 'btn-primary' : 'module-secondary-button'}
            onClick={() => setTab(id)}>
            {label}
          </button>
        ))}
      </div>

      {tab === 'overview' && (
        <section className="module-card">
          <h2>Overview</h2>
          <dl style={{ display: 'grid', gridTemplateColumns: '160px 1fr', gap: 8 }}>
            <dt>Case type</dt><dd>{caseData.case_type || '—'}</dd>
            <dt>Category</dt><dd>{caseData.category || '—'}</dd>
            <dt>Severity</dt><dd>{caseData.severity || '—'}</dd>
            <dt>Policy breached</dt><dd>{caseData.policy_breached || '—'}</dd>
            <dt>Confidential</dt><dd>{caseData.confidential ? 'Yes' : 'No'}</dd>
            <dt>Incident date</dt><dd>{caseData.incident_date}</dd>
            <dt>Description</dt><dd style={{ whiteSpace: 'pre-wrap' }}>{caseData.description}</dd>
            <dt>Action taken</dt><dd>{caseData.action_taken || '—'}</dd>
            <dt>Resolution note</dt><dd>{caseData.resolution_note || '—'}</dd>
          </dl>
        </section>
      )}

      {tab === 'resolution' && (
        <section className="module-card">
          <h2>Resolution report</h2>
          {caseData.status === 'OPEN' ? (
            <>
              <p>Record the decision and resolution summary to close this case.</p>
              <form className="module-form" onSubmit={submitResolution}>
                <label style={{ gridColumn: '1 / -1' }}>Resolution note
                  <textarea
                    required
                    minLength={5}
                    maxLength={1000}
                    rows={4}
                    value={resolutionNote}
                    onChange={(e) => setResolutionNote(e.target.value)}
                    placeholder="Describe the resolution and any actions agreed."
                  />
                </label>
                <button className="btn-primary" type="submit" disabled={busy} style={{ gridColumn: '1 / -1' }}>
                  {busy ? 'Saving…' : 'Resolve case'}
                </button>
              </form>
            </>
          ) : (
            <div>
              <p><strong>Status:</strong> {caseData.status}</p>
              <p style={{ whiteSpace: 'pre-wrap' }}>
                {caseData.resolution_note
                  || caseData.outcome?.decision_notes
                  || 'No separate resolution note was recorded.'}
              </p>
              {caseData.resolved_at && (
                <p className="module-empty">
                  Resolved {new Date(caseData.resolved_at).toLocaleString()}
                </p>
              )}
            </div>
          )}
        </section>
      )}

      {tab === 'evidence' && (
        <>
          <section className="module-card">
            <h2>Add evidence</h2>
            <form className="module-form" onSubmit={submitEvidence}>
              <label>File name
                <input required value={evidenceForm.file_name}
                  onChange={(e) => setEvidenceForm({ ...evidenceForm, file_name: e.target.value })} />
              </label>
              <label>File path
                <input required value={evidenceForm.file_path}
                  onChange={(e) => setEvidenceForm({ ...evidenceForm, file_path: e.target.value })}
                  placeholder="/uploads/cases/…" />
              </label>
              <label>File type
                <input value={evidenceForm.file_type}
                  onChange={(e) => setEvidenceForm({ ...evidenceForm, file_type: e.target.value })}
                  placeholder="pdf, image, doc" />
              </label>
              <label style={{ gridColumn: '1 / -1' }}>Description
                <textarea rows={2} value={evidenceForm.description}
                  onChange={(e) => setEvidenceForm({ ...evidenceForm, description: e.target.value })} />
              </label>
              <button className="btn-primary" type="submit" disabled={busy} style={{ gridColumn: '1 / -1' }}>
                {busy ? 'Adding…' : 'Add evidence'}
              </button>
            </form>
          </section>
          <section className="module-card">
            <h2>Evidence ({evidence.length})</h2>
            {evidence.length === 0 ? <p className="module-empty">No evidence added.</p> : (
              <ul>
                {evidence.map((ev) => (
                  <li key={ev.id} style={{ marginBottom: 8 }}>
                    <strong>{ev.file_name}</strong> — {ev.file_type || 'file'} — {ev.description || ''}
                    <button className="module-secondary-button" style={{ marginLeft: 8 }}
                      onClick={() => removeEvidence(ev.id)}>Delete</button>
                  </li>
                ))}
              </ul>
            )}
          </section>
        </>
      )}

      {tab === 'outcome' && (
        <section className="module-card">
          <h2>Outcome</h2>
          {caseData.outcome ? (
            <dl style={{ display: 'grid', gridTemplateColumns: '160px 1fr', gap: 8 }}>
              <dt>Outcome type</dt><dd>{caseData.outcome.outcome_type}</dd>
              <dt>Warning level</dt><dd>{caseData.outcome.warning_level || '—'}</dd>
              <dt>Effective</dt><dd>{caseData.outcome.effective_date || '—'}</dd>
              <dt>Expiry</dt><dd>{caseData.outcome.expiry_date || '—'}</dd>
              <dt>Suspension days</dt><dd>{caseData.outcome.suspension_days ?? '—'}</dd>
              <dt>Payroll deduction</dt><dd>{caseData.outcome.payroll_deduction ? `Yes (${caseData.outcome.deduction_amount ?? 0})` : 'No'}</dd>
              <dt>Decision notes</dt><dd style={{ whiteSpace: 'pre-wrap' }}>{caseData.outcome.decision_notes || '—'}</dd>
            </dl>
          ) : (
            <form className="module-form" onSubmit={submitOutcome}>
              <label>Outcome type
                <select required value={outcomeForm.outcome_type}
                  onChange={(e) => setOutcomeForm({ ...outcomeForm, outcome_type: e.target.value })}>
                  <option value="">— Select —</option>
                  <option value="NO_ACTION">No action</option>
                  <option value="VERBAL_WARNING">Verbal warning</option>
                  <option value="WRITTEN_WARNING">Written warning</option>
                  <option value="FINAL_WARNING">Final warning</option>
                  <option value="SUSPENSION">Suspension</option>
                  <option value="DISMISSAL">Dismissal</option>
                  <option value="TRAINING">Training required</option>
                </select>
              </label>
              <label>Warning level
                <select value={outcomeForm.warning_level}
                  onChange={(e) => setOutcomeForm({ ...outcomeForm, warning_level: e.target.value })}>
                  <option value="">—</option>
                  <option value="FIRST">First</option>
                  <option value="SECOND">Second</option>
                  <option value="FINAL">Final</option>
                </select>
              </label>
              <label>Effective date
                <input type="date" required={outcomeForm.payroll_deduction} value={outcomeForm.effective_date}
                  onChange={(e) => setOutcomeForm({ ...outcomeForm, effective_date: e.target.value })} />
                {outcomeForm.payroll_deduction && (
                  <small>This date determines the payroll month for the deduction.</small>
                )}
              </label>
              <label>Expiry date
                <input type="date" value={outcomeForm.expiry_date}
                  onChange={(e) => setOutcomeForm({ ...outcomeForm, expiry_date: e.target.value })} />
              </label>
              <label>Suspension days
                <input type="number" min="0" value={outcomeForm.suspension_days}
                  onChange={(e) => setOutcomeForm({ ...outcomeForm, suspension_days: e.target.value })} />
              </label>
              <label style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                <input type="checkbox" checked={outcomeForm.payroll_deduction}
                  onChange={(e) => setOutcomeForm({ ...outcomeForm, payroll_deduction: e.target.checked })} />
                Payroll deduction
              </label>
              {outcomeForm.payroll_deduction && (
                <label>Deduction amount
                  <input type="number" min="0.01" step="0.01" required value={outcomeForm.deduction_amount}
                    onChange={(e) => setOutcomeForm({ ...outcomeForm, deduction_amount: e.target.value })} />
                </label>
              )}
              <label style={{ gridColumn: '1 / -1' }}>Decision notes
                <textarea rows={3} value={outcomeForm.decision_notes}
                  onChange={(e) => setOutcomeForm({ ...outcomeForm, decision_notes: e.target.value })} />
              </label>
              <button className="btn-primary" type="submit" disabled={busy} style={{ gridColumn: '1 / -1' }}>
                {busy ? 'Recording…' : 'Record outcome'}
              </button>
            </form>
          )}
        </section>
      )}

      {tab === 'appeal' && (
        <section className="module-card">
          <h2>Appeal</h2>
          {!caseData.outcome ? (
            <div className="module-empty">
              <p>Record an outcome before tracking an appeal.</p>
              <button className="module-secondary-button" type="button" onClick={() => setTab('outcome')}>
                Go to outcome
              </button>
            </div>
          ) : (
            <>
              <dl style={{ display: 'grid', gridTemplateColumns: '160px 1fr', gap: 8 }}>
                <dt>Lodged</dt><dd>{caseData.outcome.appeal_lodged ? 'Yes' : 'No'}</dd>
                <dt>Date</dt><dd>{caseData.outcome.appeal_date || '—'}</dd>
                <dt>Grounds</dt><dd>{caseData.outcome.appeal_grounds || '—'}</dd>
                <dt>Outcome</dt><dd>{caseData.outcome.appeal_outcome || '—'}</dd>
                <dt>Notes</dt><dd>{caseData.outcome.appeal_notes || '—'}</dd>
              </dl>
              <h3 style={{ marginTop: 16 }}>Update appeal</h3>
              <form className="module-form" onSubmit={submitAppeal}>
                <label style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                  <input type="checkbox" checked={appealForm.appeal_lodged}
                    onChange={(e) => setAppealForm({ ...appealForm, appeal_lodged: e.target.checked })} />
                  Appeal lodged
                </label>
                <label>Appeal date
                  <input type="date" value={appealForm.appeal_date}
                    onChange={(e) => setAppealForm({ ...appealForm, appeal_date: e.target.value })} />
                </label>
                <label style={{ gridColumn: '1 / -1' }}>Grounds
                  <textarea rows={2} value={appealForm.appeal_grounds}
                    onChange={(e) => setAppealForm({ ...appealForm, appeal_grounds: e.target.value })} />
                </label>
                <label>Appeal outcome
                  <select value={appealForm.appeal_outcome}
                    onChange={(e) => setAppealForm({ ...appealForm, appeal_outcome: e.target.value })}>
                    <option value="">—</option>
                    <option value="UPHELD">Upheld</option>
                    <option value="OVERTURNED">Overturned</option>
                    <option value="MODIFIED">Modified</option>
                    <option value="REJECTED">Rejected</option>
                  </select>
                </label>
                <label style={{ gridColumn: '1 / -1' }}>Notes
                  <textarea rows={2} value={appealForm.appeal_notes}
                    onChange={(e) => setAppealForm({ ...appealForm, appeal_notes: e.target.value })} />
                </label>
                <button className="btn-primary" type="submit" disabled={busy} style={{ gridColumn: '1 / -1' }}>
                  {busy ? 'Saving…' : 'Save appeal'}
                </button>
              </form>
            </>
          )}
        </section>
      )}
    </div>
  )
}

export default CaseDetail
