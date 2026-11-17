import { useCallback, useEffect, useState } from 'react'
import axios from 'axios'
import { ArrowRight, BadgeCheck, RefreshCw, Users } from 'lucide-react'
import './OnboardingDashboard.css'

const API_BASE = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api'
const auth = () => ({ Authorization: `Bearer ${localStorage.getItem('access_token') || localStorage.getItem('token') || ''}` })

export default function OnboardingDashboard() {
  const [items, setItems] = useState([])
  const [selected, setSelected] = useState(null)
  const [notes, setNotes] = useState({})
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState('')
  const [notice, setNotice] = useState('')
  const [credentials, setCredentials] = useState(null)

  const refresh = useCallback(async () => {
    setLoading(true); setError('')
    try {
      const { data } = await axios.get(`${API_BASE}/onboarding/pending`, { headers: auth() })
      setItems(data)
      if (selected) setSelected(data.find((item) => item.candidate_id === selected.candidate_id) || null)
    } catch (e) { setError(e.response?.data?.detail || 'Could not load onboarding records.') }
    finally { setLoading(false) }
  }, [selected?.candidate_id])

  useEffect(() => { refresh() }, [refresh])

  const action = async (fn, message) => {
    setSaving(true); setError(''); setNotice('')
    try { await fn(); setNotice(message); await refresh() }
    catch (e) { setError(e.response?.data?.detail || 'The onboarding update could not be saved.') }
    finally { setSaving(false) }
  }

  const review = (doc, status) => {
    const note = notes[doc.id] || ''
    if (status === 'REJECTED' && !note.trim()) { setError('Add a reason before rejecting a document.'); return }
    action(() => axios.put(`${API_BASE}/onboarding/${selected.candidate_id}/documents/${doc.id}`, { status, note }, { headers: auth() }), `Document ${status.toLowerCase()}.`)
  }

  const finalize = async () => {
    setSaving(true); setError(''); setNotice('')
    try {
      const { data } = await axios.post(`${API_BASE}/onboarding/${selected.candidate_id}/finalize`, {}, { headers: auth() })
      setCredentials(data.temporary_password ? { name: `${selected.first_name} ${selected.last_name}`, email: data.login_email, password: data.temporary_password } : null)
      setSelected(null); setNotice(data.temporary_password ? 'Employee activated. Share the temporary login securely.' : 'Employee record finalized.'); await refresh()
    } catch (e) { setError(e.response?.data?.detail || 'The employee record could not be finalized.') }
    finally { setSaving(false) }
  }

  const allVerified = selected?.documents?.length > 0 && selected.documents.every((doc) => doc.status === 'VERIFIED')
  const details = selected?.personal_details || {}

  return <section className="onboarding-page">
    <header className="onboarding-heading"><div><p className="onboarding-eyebrow">PEOPLE OPERATIONS <span>/</span> HIRING</p><h1>Onboarding</h1><p>Review candidate details and submitted documents before activating the employee record.</p></div><button className="onboarding-refresh" type="button" onClick={refresh} disabled={loading}><RefreshCw size={15}/> Refresh</button></header>
    <div className="onboarding-flow"><div className="onboarding-flow-step complete"><span><BadgeCheck size={16}/></span><div><strong>Offer accepted</strong><small>Recruitment</small></div></div><ArrowRight className="onboarding-flow-arrow" size={17}/><div className="onboarding-flow-step current"><span><Users size={16}/></span><div><strong>Review submission</strong><small>Documents & details</small></div></div><ArrowRight className="onboarding-flow-arrow" size={17}/><div className="onboarding-flow-step"><span><BadgeCheck size={16}/></span><div><strong>Employee directory</strong><small>After HR verification</small></div></div></div>
    {(error || notice) && <div className={`onboarding-message ${error ? 'error' : 'success'}`} role={error ? 'alert' : 'status'}><span>{error || notice}</span><button type="button" onClick={() => {setError('');setNotice('')}} aria-label="Dismiss">×</button></div>}
    {credentials && <div className="onboarding-message success" role="status"><span><strong>Temporary login for {credentials.name}:</strong> {credentials.email} · Password: <code>{credentials.password}</code>. The employee must change it when first signing in.</span><button type="button" onClick={() => setCredentials(null)} aria-label="Dismiss">×</button></div>}
    <div className="onboarding-section-heading"><div><h2>Awaiting HR review</h2><p>Document decisions and completion checks are recorded on each candidate.</p></div><span className="onboarding-count"><Users size={15}/> {items.length} awaiting</span></div>
    <div className="onboarding-table-card">{loading ? <div className="onboarding-state">Loading onboarding records…</div> : items.length === 0 ? <div className="onboarding-empty"><span><BadgeCheck size={22}/></span><strong>No onboarding submissions</strong><p>Accepted offers appear here once candidates respond.</p></div> : <div className="onboarding-table-scroll"><table className="onboarding-table"><thead><tr><th>New employee</th><th>Position</th><th>Documents</th><th>Action</th></tr></thead><tbody>{items.map((item) => <tr key={item.candidate_id}><td><strong>{item.first_name} {item.last_name}</strong><span>{item.email}</span><span>{item.employee_number}</span></td><td>{item.job_title || '—'}<span>{item.department_name || '—'}</span></td><td>{item.documents.filter((doc) => doc.status === 'VERIFIED').length} / {item.documents.length} verified</td><td><button className="onboarding-primary" type="button" onClick={() => {setSelected(item);setError('')}}>Review submission <ArrowRight size={14}/></button></td></tr>)}</tbody></table></div>}</div>
    {selected && <div className="onboarding-modal-backdrop" onMouseDown={(e) => {if (e.target === e.currentTarget && !saving) setSelected(null)}}><section className="onboarding-modal" role="dialog" aria-modal="true"><div className="onboarding-modal-heading"><div><p className="onboarding-eyebrow">{selected.employee_number}</p><h2>{selected.first_name} {selected.last_name}</h2><p>{selected.job_title} · {selected.email}</p></div><button type="button" onClick={() => setSelected(null)} aria-label="Close">×</button></div>
      <h3>Personal and statutory details</h3><div className="onboarding-form-grid">{Object.entries({ 'Personal email': details.personal_email, 'Work email': details.work_email, Phone: selected.phone_number, 'Home address': details.home_address, 'National ID (NIN)': details.national_id, TIN: details.tin_number, NSSF: details.nssf_number, Bank: details.bank_name, 'Account number': details.account_number, 'Father name': details.father_name, 'Mother name': details.mother_name, 'Next of kin': details.next_of_kin_name, Relationship: details.next_of_kin_relationship, 'Next of kin phone': details.next_of_kin_phone, 'Next of kin address': details.next_of_kin_address }).map(([label, value]) => <label key={label}>{label}<input readOnly value={value || 'Not provided'}/></label>)}</div>
      <h3>Required documents</h3><div className="onboarding-doc-list">{selected.documents.map((doc) => <article key={doc.id}><div><strong>{doc.document_type}</strong><small>{doc.file_name || 'Not submitted'} · {doc.status.replaceAll('_',' ').toLowerCase()}</small>{doc.review_note && <small>Note: {doc.review_note}</small>}</div>{doc.file_name && <a href={`${API_BASE}/onboarding/documents/${doc.id}/download`} target="_blank" rel="noreferrer" onClick={(e) => {e.preventDefault();axios.get(e.currentTarget.href,{headers:auth(),responseType:'blob'}).then(({data})=>{const url=URL.createObjectURL(data);window.open(url,'_blank','noopener');setTimeout(()=>URL.revokeObjectURL(url),30000)})}}>View file</a>}{doc.status !== 'VERIFIED' && <div className="onboarding-doc-actions"><input aria-label={`Reason for ${doc.document_type}`} placeholder="Reason if rejecting" value={notes[doc.id] || ''} onChange={(e)=>setNotes({...notes,[doc.id]:e.target.value})}/><button type="button" disabled={saving || !doc.file_name} onClick={()=>review(doc,'VERIFIED')}>Verify</button><button type="button" disabled={saving || !doc.file_name} onClick={()=>review(doc,'REJECTED')}>Reject</button></div>}</article>)}</div>
      <div className="onboarding-modal-actions"><button className="onboarding-cancel" type="button" onClick={()=>setSelected(null)}>Close</button><button className="onboarding-primary" type="button" disabled={saving || !allVerified} onClick={finalize}>{saving?'Saving…':'Finalize employee record'} <ArrowRight size={14}/></button></div>
    </section></div>}
  </section>
}
