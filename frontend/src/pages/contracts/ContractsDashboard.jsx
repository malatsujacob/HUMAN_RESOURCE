import { useCallback, useEffect, useState } from 'react'
import axios from 'axios'
import FlexibleSelect from '../../components/FlexibleSelect'

const API_BASE = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api'
const authConfig = () => ({headers:{Authorization:`******'token')||localStorage.getItem('access_token')||''}`}})
const DEFAULT_TERMS = `1. The Employee will carry out the duties of the appointed role with care and follow reasonable workplace policies.\n\n2. Salary and benefits are as recorded in this agreement and will be paid subject to applicable statutory deductions.\n\n3. Leave, working hours, health and safety, confidentiality, notice, and termination are subject to applicable law and the Employer's policies as provided to the Employee.\n\n4. Any amendment to this agreement must be made in writing and signed by both parties.`
const emptyForm = {
  employee_id:'',contract_type:'FIXED_TERM',start_date:'',end_date:'',base_salary:'',
  job_title:'',work_location:'',employment_type:'Full-time',probation_period:'',notice_period:'',
  payment_frequency:'Monthly',expiry_reminder_days:'',responsibilities:'',benefits:'',
  terms_and_conditions:DEFAULT_TERMS,
}

export default function ContractsDashboard() {
  const [contracts,setContracts] = useState([])
  const [employees,setEmployees] = useState([])
  const [form,setForm] = useState(emptyForm)
  const [showForm,setShowForm] = useState(false)
  const [employerSignatures,setEmployerSignatures] = useState({})
  const [uploading,setUploading] = useState('')
  const [saving,setSaving] = useState(false)
  const [loading,setLoading] = useState(true)
  const [error,setError] = useState('')
  const [notice,setNotice] = useState('')

  const loadData = useCallback(async () => {
    setLoading(true)
    try {
      const [contractResult,employeeResult] = await Promise.all([
        axios.get(`${API_BASE}/contracts/`,authConfig()),
        axios.get(`${API_BASE}/employees/`,authConfig()),
      ])
      setContracts(contractResult.data)
      setEmployees(employeeResult.data.filter(employee=>!['EXITED','INACTIVE'].includes(employee.status)))
    } catch (requestError) {
      setError(requestError.response?.data?.detail||'Contract records could not be loaded.')
    } finally { setLoading(false) }
  },[])

  useEffect(()=>{loadData()},[loadData])

  const createContract = async event => {
    event.preventDefault(); setSaving(true); setError(''); setNotice('')
    const payload={...form,end_date:form.end_date||null,base_salary:Number(form.base_salary),expiry_reminder_days:form.end_date&&form.expiry_reminder_days!==''?Number(form.expiry_reminder_days):null}
    if (!form.end_date) payload.expiry_reminder_days=null
    try {
      const {data}=await axios.post(`${API_BASE}/contracts/`,payload,authConfig())
      setNotice(data.message); setForm(emptyForm); setShowForm(false); await loadData()
    } catch (requestError) { setError(requestError.response?.data?.detail||'Contract draft could not be generated.') }
    finally { setSaving(false) }
  }

  const issueContract = async contract => {
    const name=(employerSignatures[contract.id]||'').trim()
    if (name.length<2) {setError(`Enter the employer signatory name for ${contract.employee_name}.`);return}
    setSaving(true);setError('');setNotice('')
    try {const {data}=await axios.put(`${API_BASE}/contracts/${contract.id}/issue`,{employer_signature_name:name},authConfig());setNotice(data.message);await loadData()}
    catch(requestError){setError(requestError.response?.data?.detail||'Contract could not be issued.')}
    finally{setSaving(false)}
  }

  const uploadSignedCopy = async (contract,file) => {
    if (!file) return
    setUploading(contract.id);setError('');setNotice('')
    const body=new FormData();body.append('file',file)
    try {const {data}=await axios.post(`${API_BASE}/contracts/${contract.id}/signed-copy`,body,{...authConfig(),headers:{...authConfig().headers,'Content-Type':'multipart/form-data'}});setNotice(data.message);await loadData()}
    catch(requestError){setError(requestError.response?.data?.detail||'Signed contract could not be uploaded.')}
    finally{setUploading('')}
  }

  const downloadContract = async (contract,copy='generated') => {
    setError('')
    try {
      const {data}=await axios.get(`${API_BASE}/contracts/${contract.id}/download?copy=${copy}`,{...authConfig(),responseType:'blob'})
      const url=URL.createObjectURL(data);const link=document.createElement('a');link.href=url;link.download=`employment-contract-${contract.employee_number}-${copy}${copy==='signed'?(contract.signed_file_extension||'.html'):'.html'}`;link.click();window.setTimeout(()=>URL.revokeObjectURL(url),1000)
    } catch(requestError){setError(requestError.response?.data?.detail||'Contract document could not be downloaded.')}
  }

  const previewContract = async contract => {
    setError('')
    const preview=window.open('about:blank','_blank')
    if(!preview){setError('Allow pop-ups to preview and print the contract.');return}
    try {
      const {data}=await axios.get(`${API_BASE}/contracts/${contract.id}/document`,{...authConfig(),responseType:'text'})
      const url=URL.createObjectURL(new Blob([data],{type:'text/html'}));preview.location.href=url;window.setTimeout(()=>URL.revokeObjectURL(url),60000)
    } catch(requestError){preview.close();setError(requestError.response?.data?.detail||'Contract preview could not be opened.')}
  }

  const activateContract = async contract => {
    setSaving(true);setError('');setNotice('')
    try{const {data}=await axios.put(`${API_BASE}/contracts/${contract.id}/activate`,{},authConfig());setNotice(data.message);await loadData()}
    catch(requestError){setError(requestError.response?.data?.detail||'Contract could not be activated.')}
    finally{setSaving(false)}
  }

  return <section className="module-page">
    <header className="module-heading" style={{display:'flex',justifyContent:'space-between',alignItems:'center',gap:12,flexWrap:'wrap'}}>
      <div><p className="eyebrow">PEOPLE OPERATIONS</p><h1>Contracts</h1><p>Prepare, issue, sign, print, and securely store employee agreements.</p></div>
      <button className="btn-primary" type="button" onClick={()=>{setForm(emptyForm);setShowForm(value=>!value);setError('')}}>{showForm?'Close form':'+ Prepare contract'}</button>
    </header>
    {error&&<p className="module-alert error" role="alert">{error}</p>}{notice&&<p className="module-alert success" role="status">{notice}</p>}
    {showForm&&<section className="card" style={{marginBottom:16}}>
      <h2>Prepare employment agreement</h2><p className="ess-muted">This creates a printable HTML contract in the employee directory. The standard clauses are an editable draft and require HR/legal review before use.</p>
      <form className="ess-performance-form" onSubmit={createContract}>
        <label className="ess-wide">Employee<select required value={form.employee_id} onChange={event=>{const employee=employees.find(item=>item.id===event.target.value);setForm(current=>({...current,employee_id:event.target.value,job_title:current.job_title||employee?.job_title||'',work_location:current.work_location||employee?.work_location||''}))}}><option value="">Select employee</option>{employees.map(employee=><option key={employee.id} value={employee.id}>{employee.full_name||`${employee.first_name} ${employee.last_name}`} · {employee.employee_number}</option>)}</select></label>
        <label>Contract type<FlexibleSelect name="contract_type" required value={form.contract_type} onChange={event=>setForm({...form,contract_type:event.target.value})} options={ [['FIXED_TERM','Fixed term'],['PERMANENT','Permanent'],['PROBATION','Probation'],['INTERNSHIP','Internship'],['OTHER','Other']] } placeholder="Select contract type"/></label>
        <label>Job title<input required maxLength="100" value={form.job_title} onChange={event=>setForm({...form,job_title:event.target.value})}/></label>
        <label>Start date<input type="date" required value={form.start_date} onChange={event=>setForm({...form,start_date:event.target.value})}/></label>
        <label>End date (leave blank for open-ended)<input type="date" min={form.start_date||undefined} value={form.end_date} onChange={event=>setForm({...form,end_date:event.target.value})}/></label>
        <label>Monthly salary (UGX)<input type="number" min="0" step="1000" required value={form.base_salary} onChange={event=>setForm({...form,base_salary:event.target.value})}/></label>
        <label>Work location<input maxLength="200" value={form.work_location} onChange={event=>setForm({...form,work_location:event.target.value})}/></label>
        <label>Employment type<input maxLength="30" value={form.employment_type} onChange={event=>setForm({...form,employment_type:event.target.value})}/></label>
        <label>Probation period<input maxLength="50" placeholder="e.g. 3 months" value={form.probation_period} onChange={event=>setForm({...form,probation_period:event.target.value})}/></label>
        <label>Notice period<input maxLength="50" placeholder="e.g. 1 month" value={form.notice_period} onChange={event=>setForm({...form,notice_period:event.target.value})}/></label>
        <label>Pay frequency<input maxLength="50" value={form.payment_frequency} onChange={event=>setForm({...form,payment_frequency:event.target.value})}/></label>
        <label>Expiry reminder lead time (days)<input type="number" min="0" max="365" disabled={!form.end_date} value={form.end_date?form.expiry_reminder_days:''} placeholder="Enter days before expiry" onChange={event=>setForm({...form,expiry_reminder_days:event.target.value})}/><small>Choose the alert period for this agreement; leave blank to disable its expiry reminder.</small></label>
        <label className="ess-wide">Responsibilities<textarea rows="3" maxLength="5000" value={form.responsibilities} onChange={event=>setForm({...form,responsibilities:event.target.value})}/></label>
        <label className="ess-wide">Benefits<textarea rows="2" maxLength="5000" value={form.benefits} onChange={event=>setForm({...form,benefits:event.target.value})}/></label>
        <label className="ess-wide">Terms and conditions<textarea rows="8" required maxLength="12000" value={form.terms_and_conditions} onChange={event=>setForm({...form,terms_and_conditions:event.target.value})}/><small>Review and adapt these clauses to approved company policy and applicable law.</small></label>
        <div className="ess-form-actions ess-wide"><button className="btn-primary" disabled={saving}>{saving?'Generating…':'Generate draft contract'}</button></div>
      </form>
    </section>}
    <section className="card" style={{overflowX:'auto'}}>
      <div className="ess-section-heading"><div><h2>Employee contracts</h2><p>Signed agreements with a lead-time reminder are monitored when this dashboard is opened.</p></div><button className="module-secondary-button" type="button" disabled={loading} onClick={loadData}>Refresh</button></div>
      <table className="ess-table" style={{minWidth:1050}}><thead><tr><th>Employee / department</th><th>Agreement</th><th>Term</th><th>Expiry alert</th><th>Status</th><th>Documents and actions</th></tr></thead><tbody>
        {contracts.map(contract=><tr key={contract.id}>
          <td><strong>{contract.employee_name}</strong><small style={{display:'block'}}>{contract.employee_number} · {contract.department_name||'Unassigned'}</small></td>
          <td>{contract.contract_type.replaceAll('_',' ')}<small style={{display:'block'}}>{contract.job_title} · UGX {Number(contract.base_salary||0).toLocaleString()}</small></td>
          <td>{contract.start_date} – {contract.end_date||'Open-ended'}</td>
          <td>{contract.status==='TERMINATED'?`Terminated effective ${contract.end_date}`:contract.end_date?contract.days_to_expiry<0?`Expired ${Math.abs(contract.days_to_expiry)} days ago`:contract.days_to_expiry===0?'Expires today':`${contract.days_to_expiry} days left`:'Open-ended'}{contract.status!=='TERMINATED'&&contract.expiry_reminder_days!==null&&contract.expiry_reminder_days!==undefined&&<small style={{display:'block'}}>Alert at {contract.expiry_reminder_days} days</small>}</td>
          <td>{contract.status.replaceAll('_',' ')}<small style={{display:'block'}}>{contract.signing_method==='MANUAL'?'Manual signed copy':'Digital consent'}</small></td>
          <td><div style={{display:'grid',gap:7,minWidth:230}}>
            <div style={{display:'flex',gap:6,flexWrap:'wrap'}}><button className="module-secondary-button" type="button" onClick={()=>previewContract(contract)}>Preview / print</button><button className="module-secondary-button" type="button" onClick={()=>downloadContract(contract)}>Download</button>{contract.has_signed_document&&<button className="module-secondary-button" type="button" onClick={()=>downloadContract(contract,'signed')}>Signed copy</button>}</div>
            {contract.status==='DRAFT'&&<><input aria-label={`Employer signatory for ${contract.employee_name}`} placeholder="Employer signatory full name" value={employerSignatures[contract.id]||''} onChange={event=>setEmployerSignatures({...employerSignatures,[contract.id]:event.target.value})}/><button className="btn-primary" type="button" disabled={saving} onClick={()=>issueContract(contract)}>Issue for employee signature</button></>}
            {['DRAFT','PENDING_EMPLOYEE_SIGNATURE','SIGNED','ACTIVE'].includes(contract.status)&&<label style={{fontSize:12}}>Upload manually signed copy<input type="file" accept=".pdf,.doc,.docx,.png,.jpg,.jpeg" disabled={uploading===contract.id} onChange={event=>uploadSignedCopy(contract,event.target.files?.[0])}/><small>PDF, DOC, DOCX, PNG, JPG or JPEG · up to 20 MB</small></label>}
            {contract.status==='SIGNED'&&<button className="module-secondary-button" type="button" disabled={saving} onClick={()=>activateContract(contract)}>Activate agreement</button>}
          </div></td>
        </tr>)}
        {!loading&&contracts.length===0&&<tr><td colSpan="6">No contracts yet. Prepare a contract to get started.</td></tr>}
        {loading&&<tr><td colSpan="6">Loading contracts…</td></tr>}
      </tbody></table>
    </section>
  </section>
}
