import { useEffect, useState } from 'react'
import axios from 'axios'
import { BriefcaseBusiness } from 'lucide-react'
import '../recruitment/OfferResponse.css'
import './OnboardingDashboard.css'

const API_BASE = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api'
const DETAIL_FIELDS = [
  ['middle_name','Middle name'],['gender','Gender'],['marital_status','Marital status'],
  ['personal_email','Personal email'],['work_email','Work email'],['phone_number','Phone number'],
  ['home_address','Home address'],['national_id','National ID (NIN)'],['tin_number','TIN number'],
  ['nssf_number','NSSF number'],['bank_name','Bank name'],['account_number','Bank account number'],
  ['father_name','Father name'],['mother_name','Mother name'],['next_of_kin_name','Next of kin name'],
  ['next_of_kin_relationship','Next of kin relationship'],['next_of_kin_phone','Next of kin phone'],
  ['next_of_kin_address','Next of kin address'],
]

export default function OnboardingResponse() {
  const token = new URLSearchParams(window.location.search).get('token') || ''
  const [record, setRecord] = useState(null)
  const [details, setDetails] = useState({})
  const [uploads, setUploads] = useState({})
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState('')
  const [done, setDone] = useState(null)

  useEffect(() => {
    if (!token) { setError('This onboarding link is incomplete. Open the secure link from your email.'); return }
    axios.get(`${API_BASE}/onboarding/candidate/${encodeURIComponent(token)}`)
      .then(({data}) => { setRecord(data); setDetails({...data.personal_details, phone_number: data.phone_number}) })
      .catch((e) => setError(e.response?.data?.detail || 'Could not load your onboarding form.'))
  }, [token])

  const submit = async (event) => {
    event.preventDefault(); setSaving(true); setError('')
    const body = new FormData()
    const { phone_number, ...employeeDetails } = details
    body.append('application', JSON.stringify(employeeDetails))
    const selectedDocs = record.documents.filter((doc) => uploads[doc.document_type])
    selectedDocs.forEach((doc) => { body.append('document_types', doc.document_type); body.append('documents', uploads[doc.document_type]) })
    try {
      const {data} = await axios.post(`${API_BASE}/onboarding/candidate/${encodeURIComponent(token)}/submit`, body)
      setDone(data)
    } catch (e) { setError(e.response?.data?.detail || 'Your submission could not be saved. Please try again.') }
    finally { setSaving(false) }
  }

  return <main className="offer-response-page"><div className="offer-response-brand"><span className="brand-mark">CC</span><span><strong>Chap Chap Africa</strong><small>CAREERS</small></span></div><section className="offer-response-card onboarding-response-card"><span className="offer-response-icon"><BriefcaseBusiness size={20}/></span><p className="eyebrow">NEW EMPLOYEE SETUP</p><h1>Complete onboarding</h1>{error && <p className="offer-response-error" role="alert">{error}</p>}{done ? <div className="offer-response-success" role="status">{done.message}{done.missing_documents?.length > 0 && <p>Still required: {done.missing_documents.join(', ')}. We sent a secure link to your email to continue.</p>}{done.email_sent === false && <p>Your submission was received, but the email reminder could not be sent. Contact Human Resources if needed.</p>}</div> : record && <form onSubmit={submit}><p className="offer-response-description">Welcome, {record.first_name}. Please complete your employee details and upload the requested documents. You can return to this form if HR requests a replacement.</p><div className="onboarding-response-fields">{DETAIL_FIELDS.map(([key,label]) => <label key={key}>{label}<input type={key.includes('email') ? 'email' : 'text'} required={!['father_name','mother_name','next_of_kin_address'].includes(key)} value={details[key] || ''} onChange={(e)=>setDetails({...details,[key]:e.target.value})}/></label>)}</div><h2>Required documents</h2><p className="offer-response-description">Accepted file types: PDF, DOC, DOCX, CSV, PNG, JPG. Maximum 10 MB per file.</p><div className="onboarding-response-docs">{record.documents.map((doc)=><label key={doc.id}>{doc.document_type}<small>Current status: {doc.status.replaceAll('_',' ').toLowerCase()}{doc.review_note ? ` · ${doc.review_note}` : ''}</small><input type="file" accept=".pdf,.doc,.docx,.csv,.png,.jpg,.jpeg" onChange={(e)=>setUploads({...uploads,[doc.document_type]:e.target.files?.[0]})}/></label>)}</div><button className="onboarding-response-submit" type="submit" disabled={saving}>{saving?'Submitting…':'Submit onboarding details'}</button></form>}</section></main>
}
