import { useState } from 'react'
import axios from 'axios'
import { useNavigate } from 'react-router-dom'

const API_BASE = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api'

export default function ChangePassword() {
  const navigate = useNavigate()
  const [form, setForm] = useState({ current_password: '', new_password: '', confirm_password: '' })
  const [error, setError] = useState('')
  const [saving, setSaving] = useState(false)

  const submit = async (event) => {
    event.preventDefault(); setSaving(true); setError('')
    try {
      await axios.post(`${API_BASE}/auth/change-password`, form, { headers: { Authorization: `Bearer ${localStorage.getItem('token') || ''}` } })
      localStorage.setItem('must_change_password', 'false')
      const role = (localStorage.getItem('role') || '').toUpperCase()
      navigate(['HOD', 'DEVELOPER'].includes(role) ? '/ess?section=performance' : '/ess', { replace: true })
    } catch (requestError) {
      setError(requestError.response?.data?.detail || 'Password could not be updated. Check your entries and try again.')
    } finally { setSaving(false) }
  }

  return <section className="module-page"><header className="module-heading"><div><p className="eyebrow">ACCOUNT SECURITY</p><h1>Set your password</h1><p>Your HRMS account was issued with a temporary password. Choose a private password to continue.</p></div></header><div className="module-panel" style={{maxWidth:560}}>{error && <p className="module-alert error" role="alert">{error}</p>}<form className="module-form" onSubmit={submit}><label>Temporary password<input type="password" autoComplete="current-password" required value={form.current_password} onChange={e=>setForm({...form,current_password:e.target.value})}/></label><label>New password<input type="password" autoComplete="new-password" minLength="10" required value={form.new_password} onChange={e=>setForm({...form,new_password:e.target.value})}/><small>Use at least 10 characters.</small></label><label>Confirm new password<input type="password" autoComplete="new-password" minLength="10" required value={form.confirm_password} onChange={e=>setForm({...form,confirm_password:e.target.value})}/></label><button className="btn-primary" type="submit" disabled={saving}>{saving ? 'Updating…' : 'Update password and continue'}</button></form></div></section>
}
