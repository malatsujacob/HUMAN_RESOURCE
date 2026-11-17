import { useCallback, useEffect, useMemo, useRef, useState } from 'react'
import axios from 'axios'
import FlexibleSelect from '../../components/FlexibleSelect'

const API_BASE = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api'
const authHeaders = () => ({ Authorization: `Bearer ${localStorage.getItem('token') || localStorage.getItem('access_token') || ''}` })
const EMPTY_FORM = {
  first_name: '', middle_name: '', last_name: '', date_of_birth: '', gender: '', nationality: '', marital_status: '',
  personal_email: '', work_email: '', phone_number: '', home_address: '',
  father_name: '', mother_name: '', next_of_kin_name: '', next_of_kin_relationship: '', next_of_kin_phone: '', next_of_kin_address: '',
  department_code: '', job_title: '', reporting_manager: '', work_location: '', hire_date: '', employment_type: '',
  probation_period: '', notice_period: '', contract_end_date: '', status: 'ACTIVE',
  national_id: '', tin_number: '', nssf_number: '', bank_name: '', account_number: '', base_salary: '', role: 'EMPLOYEE',
}
const ROLE_OPTIONS = [['EMPLOYEE','Employee'],['HOD','Head of Department'],['HR','HR'],['HR_ADMIN','HR Admin'],['MANAGEMENT','Management'],['ADMIN','Administrator'],['DEVELOPER','Developer']]
const EMPLOYEE_DOCUMENT_TYPES = ['National ID','Academic certificate','TIN certificate','NSSF record','Bank confirmation','Employment contract','Other']
const FIELD_SECTIONS = [
  { title:'Personal information', fields:[['first_name','First name','text',true],['middle_name','Middle name'],['last_name','Last name','text',true],['date_of_birth','Date of birth','date'],['gender','Gender','select'],['nationality','Nationality'],['marital_status','Marital status','select']] },
  { title:'Contact and next of kin', fields:[['personal_email','Personal email','email'],['work_email','Work email','email'],['phone_number','Phone number'],['home_address','Home / physical address','text',false,true],['father_name','Father name'],['mother_name','Mother name'],['next_of_kin_name','Next-of-kin full name'],['next_of_kin_relationship','Next-of-kin relationship'],['next_of_kin_phone','Next-of-kin phone'],['next_of_kin_address','Next-of-kin address','text',false,true]] },
  { title:'Position and employment', fields:[['department_code','Department','department',true],['job_title','Job title','text',true],['role','System role','role',true],['reporting_manager','Reporting manager'],['work_location','Work location'],['hire_date','Hire date','date'],['employment_type','Employment type','select'],['status','Employment status','status'],['probation_period','Probation period'],['notice_period','Notice period'],['contract_end_date','Contract end date','date']] },
  { title:'Statutory and bank information', fields:[['national_id','National ID'],['tin_number','TIN number'],['nssf_number','NSSF number'],['bank_name','Bank name'],['account_number','Bank account number'],['base_salary','Basic monthly salary (UGX)','number'],['employee_documents','Employee documents','documents']] },
]
const FIELD_PLACEHOLDERS = {
  first_name:'Enter the employee’s first name', middle_name:'Enter the middle name, if any', last_name:'Enter the employee’s last name',
  date_of_birth:'Select date of birth', gender:'Select gender', nationality:'Enter nationality', marital_status:'Select marital status',
  personal_email:'name@example.com', work_email:'name@chapchapafrica.com', phone_number:'+256 7XX XXX XXX',
  home_address:'Enter residential address, district, and country', father_name:'Enter father’s full name, if provided',
  mother_name:'Enter mother’s full name, if provided', next_of_kin_name:'Enter next of kin’s full name',
  next_of_kin_relationship:'e.g. Spouse, parent, sibling', next_of_kin_phone:'+256 7XX XXX XXX',
  next_of_kin_address:'Enter next of kin’s address', department_code:'Select the employee’s department',
  job_title:'Enter the employee’s job title', role:'Select the employee’s system role',
  reporting_manager:'Enter the manager’s full name', work_location:'e.g. Kampala office or remote',
  hire_date:'Select employment start date', employment_type:'Select employment type', status:'Select employment status',
  probation_period:'e.g. 3 months', notice_period:'e.g. 1 month', contract_end_date:'Select contract end date, if applicable',
  national_id:'Enter national identification number', tin_number:'Enter tax identification number',
  nssf_number:'Enter NSSF membership number', bank_name:'Enter account-holding bank name',
  account_number:'Enter employee bank account number', base_salary:'Enter monthly amount in UGX',
}
const PROFILE_FIELDS = [
  ['Employee number','employee_number'],['System role','account_role'],['Employment status','status'],['First name','first_name'],['Middle name','middle_name'],['Last name','last_name'],['Date of birth','date_of_birth'],['Gender','gender'],['Nationality','nationality'],['Marital status','marital_status'],
  ['Personal email','personal_email'],['Work email','work_email'],['Login email','account_email'],['Phone number','phone_number'],['Home / physical address','home_address'],
  ['Father name','father_name'],['Mother name','mother_name'],['Next-of-kin full name','next_of_kin_name'],['Next-of-kin relationship','next_of_kin_relationship'],['Next-of-kin phone','next_of_kin_phone'],['Next-of-kin address','next_of_kin_address'],
  ['Department','department_name'],['Job title','job_title'],['Reporting manager','reporting_manager'],['Work location','work_location'],['Hire date','hire_date'],['Employment type','employment_type'],['Probation period','probation_period'],['Notice period','notice_period'],['Contract end date','contract_end_date'],
  ['National ID','national_id'],['TIN number','tin_number'],['NSSF number','nssf_number'],['Bank name','bank_name'],['Bank account number','account_number'],['Basic monthly salary (UGX)','base_salary'],
]
const displayValue = value => value === null || value === undefined || value === '' ? 'Not recorded' : String(value)
const employeeName = employee => employee.full_name || [employee.first_name,employee.middle_name,employee.last_name].filter(Boolean).join(' ') || employee.name || employee.employee_name || `Employee ${employee.employee_number || ''}`.trim()
const displayRole = employee => employee.account_role || employee.role || employee.user?.role || employee.user_account?.role || employee.legacy_role || 'No role recorded'
const formRole = value => { const role=String(value||'EMPLOYEE').trim().toUpperCase().replaceAll('-','_'); const aliases={'ASSISTANT HR':'HR_ADMIN','ASSISTANT_HR':'HR_ADMIN','CEO':'MANAGEMENT','MD':'MANAGEMENT','SYSTEM ADMINISTRATOR':'ADMIN','SYSTEM_ADMINISTRATOR':'ADMIN','HEAD OF DEPARTMENT':'HOD'}; const mapped=aliases[role]||role; return ROLE_OPTIONS.some(([key])=>key===mapped)?mapped:'EMPLOYEE' }
const employeeDepartmentName = employee => employee.department_name || employee.department?.name || employee.department || employee.legacy_department || ''

export default function EmployeeDashboard() {
  const [employees,setEmployees] = useState([])
  const [departments,setDepartments] = useState([])
  const [showModal,setShowModal] = useState(false)
  const [editing,setEditing] = useState(null)
  const [viewing,setViewing] = useState(null)
  const [documentEmployee,setDocumentEmployee] = useState(null)
  const [documentType,setDocumentType] = useState('National ID')
  const [documentFile,setDocumentFile] = useState(null)
  const [editDocumentType,setEditDocumentType] = useState('National ID')
  const [editDocumentFile,setEditDocumentFile] = useState(null)
  const [editDocumentError,setEditDocumentError] = useState('')
  const [editDocumentNotice,setEditDocumentNotice] = useState('')
  const editDocumentInput = useRef(null)
  const [formData,setFormData] = useState(EMPTY_FORM)
  const [credentials,setCredentials] = useState(null)
  const [legacyFile,setLegacyFile] = useState(null)
  const [query,setQuery] = useState('')
  const [departmentFilter,setDepartmentFilter] = useState('')
  const [error,setError] = useState('')
  const [notice,setNotice] = useState('')
  const [loading,setLoading] = useState(true)
  const [saving,setSaving] = useState(false)

  const fetchEmployees = useCallback(async () => {
    setLoading(true); setError('')
    try {
      const {data} = await axios.get(`${API_BASE}/employees/`,{headers:authHeaders()})
      setEmployees(Array.isArray(data) ? data : (data?.employees || data?.data || []))
    } catch (e) { setError(e.response?.data?.detail || 'Could not load employee records.') }
    finally { setLoading(false) }
  },[])
  const fetchDepartments = useCallback(async () => {
    try { const {data} = await axios.get(`${API_BASE}/employees/departments`,{headers:authHeaders()}); setDepartments(data) }
    catch { setDepartments([]) }
  },[])
  useEffect(() => { fetchEmployees(); fetchDepartments() },[fetchEmployees,fetchDepartments])

  const filteredEmployees = useMemo(() => employees.filter(employee => {
    const term = query.trim().toLowerCase()
    const matches = !term || [employeeName(employee),employee.employee_number,employee.work_email,employee.personal_email,employee.job_title,employeeDepartmentName(employee),displayRole(employee)].some(value => String(value || '').toLowerCase().includes(term))
    return matches && (!departmentFilter || employee.department_code === departmentFilter || employee.department_name === departmentFilter)
  }),[employees,query,departmentFilter])

  const openCreate = () => { setEditing(null); setFormData({...EMPTY_FORM,department_code:departments[0]?.code || ''}); setError(''); setShowModal(true) }
  const openEdit = employee => {
    setEditing(employee)
    setEditDocumentType('National ID'); setEditDocumentFile(null); setEditDocumentError(''); setEditDocumentNotice('')
    const next = {...EMPTY_FORM}
    for (const key of Object.keys(next)) {
      const value = key === 'role' ? formRole(employee.account_role || employee.legacy_role || 'EMPLOYEE') : employee[key]
      next[key] = value === null || value === undefined ? '' : String(value)
    }
    next.home_address = employee.home_address || employee.physical_address || ''
    next.department_code = employee.department_code || ''
    next.status = employee.status || 'ACTIVE'
    setFormData(next); setError(''); setShowModal(true)
  }
  const handleSave = async event => {
    event.preventDefault(); setSaving(true); setError(''); setNotice('')
    const payload = Object.fromEntries(Object.entries(formData).map(([key,value]) => [key,value === '' ? null : value]))
    if (!payload.work_email && !payload.personal_email) { setError('Enter a work or personal email to create their login.'); setSaving(false); return }
    try {
      if (editing) {
        const {data} = await axios.put(`${API_BASE}/employees/${editing.id}`,payload,{headers:authHeaders()}); setNotice(data.message)
      } else {
        const {data} = await axios.post(`${API_BASE}/employees/`,payload,{headers:authHeaders()})
        setCredentials({email:data.login_email,password:data.temporary_password,name:employeeName(formData)}); setNotice('Employee and login created. Share the temporary password securely.')
      }
      setShowModal(false); setEditing(null); setFormData(EMPTY_FORM); await fetchEmployees()
    } catch (e) { setError(e.response?.data?.detail || 'The employee record could not be saved.') }
    finally { setSaving(false) }
  }
  const handleArchive = async employee => {
    if (!window.confirm(`Archive ${employeeName(employee)} as exited? Their profile and history will remain in the system.`)) return
    setSaving(true); setError('')
    try { const {data}=await axios.delete(`${API_BASE}/employees/${employee.id}`,{headers:authHeaders()}); setNotice(data.message); await fetchEmployees() }
    catch (e) { setError(e.response?.data?.detail || 'The employee could not be archived.') }
    finally { setSaving(false) }
  }
  const generateLogin = async employee => {
    setSaving(true); setError(''); setNotice(''); setCredentials(null)
    try { const {data}=await axios.post(`${API_BASE}/employees/${employee.id}/generate-login`,{},{headers:authHeaders()}); setCredentials({email:data.login_email,password:data.temporary_password,name:employeeName(employee)}); setNotice(data.message); await fetchEmployees() }
    catch (e) { setError(e.response?.data?.detail || 'Could not generate login details.') }
    finally { setSaving(false) }
  }
  const importLegacyCsv = async event => {
    event.preventDefault()
    if (!legacyFile) { setError('Choose the employee CSV exported from the previous directory.'); return }
    setSaving(true); setError(''); setNotice('')
    const body=new FormData(); body.append('file',legacyFile)
    try {
      const {data}=await axios.post(`${API_BASE}/employees/import-legacy`,body,{headers:{...authHeaders(),'Content-Type':'multipart/form-data'}})
      setNotice(`${data.message} Created: ${data.created}; updated: ${data.updated}; skipped: ${data.skipped}.`)
      if (data.errors?.length) setError(data.errors.slice(0,5).map(row=>`Row ${row.row}: ${row.reason}`).join(' | '))
      setLegacyFile(null); await fetchEmployees(); await fetchDepartments()
    } catch (e) { setError(e.response?.data?.detail || 'The legacy employee file could not be imported.') }
    finally { setSaving(false) }
  }
  const exportCsv = async () => {
    setError('')
    try {
      const {data}=await axios.get(`${API_BASE}/employees/export`,{headers:authHeaders(),responseType:'blob'})
      const url=URL.createObjectURL(data); const link=document.createElement('a'); link.href=url; link.download='hrms_employee_directory.csv'; link.click(); URL.revokeObjectURL(url)
    } catch (e) { setError(e.response?.data?.detail || 'Employee export could not be downloaded.') }
  }
  const closeDocumentUpload = () => {
    if (saving) return
    setDocumentEmployee(null)
    setDocumentFile(null)
  }
  const uploadDocument = async event => {
    event.preventDefault()
    if (!documentEmployee || !documentFile) { setError('Choose a document type and file.'); return }
    setSaving(true); setError(''); setNotice('')
    const body=new FormData(); body.append('document_type',documentType); body.append('file',documentFile)
    try {
      const {data}=await axios.post(`${API_BASE}/employees/${documentEmployee.id}/documents`,body,{headers:{...authHeaders(),'Content-Type':'multipart/form-data'}})
      setNotice(data.message); setDocumentFile(null); setDocumentEmployee(null); await fetchEmployees()
    } catch (e) { setError(e.response?.data?.detail || 'Employee document could not be uploaded.') }
    finally { setSaving(false) }
  }
  const uploadEditedDocument = async () => {
    if (!editing || !editDocumentFile) { setEditDocumentError('Choose a document file to upload.'); return }
    const type = editDocumentType.trim()
    if (!type) { setEditDocumentError('Enter the document type.'); return }
    setSaving(true); setEditDocumentError(''); setEditDocumentNotice('')
    const body = new FormData()
    body.append('document_type',type); body.append('file',editDocumentFile)
    try {
      const {data} = await axios.post(`${API_BASE}/employees/${editing.id}/documents`,body,{headers:{...authHeaders(),'Content-Type':'multipart/form-data'}})
      const uploadedDocument = {...data.document,status:'VERIFIED'}
      setEditing(current => current ? {...current,documents:[...(current.documents||[]).filter(doc=>doc.document_type!==uploadedDocument.document_type),uploadedDocument]} : current)
      setEditDocumentFile(null)
      if (editDocumentInput.current) editDocumentInput.current.value = ''
      setEditDocumentNotice(data.message)
      await fetchEmployees()
    } catch (e) { setEditDocumentError(e.response?.data?.detail || 'Employee document could not be uploaded.') }
    finally { setSaving(false) }
  }
  const downloadDocument = async row => {
    try {
      const {data}=await axios.get(`${API_BASE}/employees/documents/${row.id}/download`,{headers:authHeaders(),responseType:'blob'})
      const url=URL.createObjectURL(data); const link=document.createElement('a'); link.href=url; link.download=row.file_name || 'employee-document'; link.click(); URL.revokeObjectURL(url)
    } catch { setError('The employee document could not be downloaded.') }
  }
  const copyCredentials = async () => {
    if (!credentials) return
    try { await navigator.clipboard.writeText(`Login: ${credentials.email}\nTemporary password: ${credentials.password}`); setNotice('Login details copied. Share them with the employee securely.') }
    catch { setNotice('Select and copy the displayed login details manually.') }
  }
  const renderField = ([name,label,type='text',required=false,wide=false]) => {
    if (type==='documents') {
      if (!editing) return null
      const documentTypes = [...new Set([...EMPLOYEE_DOCUMENT_TYPES,...(editing.documents||[]).map(doc=>doc.document_type)])]
      return <section className="ess-wide" aria-labelledby="edit-employee-documents-title" style={{display:'grid',gridTemplateColumns:'repeat(auto-fit,minmax(min(100%,230px),1fr))',gap:13,alignItems:'end',borderTop:'1px solid #e6edf2',paddingTop:14}}>
        <h3 id="edit-employee-documents-title" style={{gridColumn:'1 / -1',margin:'0 0 8px',color:'#31536a',fontSize:14}}>Employee documents</h3>
        <p className="ess-muted" style={{gridColumn:'1 / -1'}}>Upload missing documents or replace an existing file. Upload each document separately; the employee profile stays open.</p>
        {editing.documents?.length?<div style={{display:'grid',gap:8,marginBottom:14,gridColumn:'1 / -1'}}>{editing.documents.map(doc=><div key={doc.id||doc.document_type} style={{display:'flex',justifyContent:'space-between',gap:12,alignItems:'center',borderTop:'1px solid #e6edf2',padding:'9px 0'}}><span><strong>{doc.document_type}</strong><small style={{display:'block',color:'#718192'}}>{doc.file_name||'No file uploaded'}{doc.status?` · ${doc.status}`:''}</small></span>{doc.file_name&&<button type="button" className="module-secondary-button" onClick={()=>downloadDocument(doc)}>Download</button>}</div>)}</div>:<p className="ess-muted" style={{gridColumn:'1 / -1'}}>No documents have been added to this profile yet.</p>}
        <label htmlFor="edit-document-type">Document type<input id="edit-document-type" list="employee-document-type-options" value={editDocumentType} onChange={event=>setEditDocumentType(event.target.value)} maxLength={120}/><datalist id="employee-document-type-options">{documentTypes.map(documentType=><option key={documentType} value={documentType}/>)}</datalist></label>
        <label htmlFor="edit-document-file">File<input ref={editDocumentInput} id="edit-document-file" type="file" accept=".pdf,.doc,.docx,.csv,.png,.jpg,.jpeg" onChange={event=>{setEditDocumentFile(event.target.files?.[0]||null);setEditDocumentError('')}}/><small className="ess-muted">PDF, DOC, DOCX, CSV, PNG, JPG, or JPEG; up to 10 MB.</small></label>
        <div><button className="module-secondary-button" type="button" disabled={saving||!editDocumentFile} onClick={uploadEditedDocument}>{saving?'Uploading...':'Upload document'}</button></div>
        {editDocumentError&&<p className="module-alert error ess-wide" role="alert">{editDocumentError}</p>}
        {editDocumentNotice&&<p className="module-alert success ess-wide" role="status">{editDocumentNotice}</p>}
      </section>
    }
    const common={id:name,name,required,value:formData[name] ?? '',placeholder:FIELD_PLACEHOLDERS[name],onChange:event=>setFormData(current=>({...current,[name]:event.target.value}))}
    let control
    if (type==='select') {
      const options=name==='gender'?['Female','Male','Other','Prefer not to say']:name==='marital_status'?['Single','Married','Divorced','Separated','Widowed','Prefer not to say']:['Full-time','Part-time','Contract','Intern']
      control=<FlexibleSelect {...common} options={options} placeholder={FIELD_PLACEHOLDERS[name]}/>
    } else if (type==='department') control=<select {...common}><option value="">{FIELD_PLACEHOLDERS[name]}</option>{departments.map(dept=><option value={dept.code} key={dept.code}>{dept.name}</option>)}</select>
    else if (type==='role') control=<select {...common}>{ROLE_OPTIONS.map(([value,title])=><option value={value} key={value}>{title}</option>)}</select>
    else if (type==='status') control=<select {...common}>{[['ACTIVE','Active'],['ONBOARDING','Onboarding'],['PROBATION','Probation'],['ON_LEAVE','On leave'],['INACTIVE','Inactive'],['EXITED','Exited']].map(([value,title])=><option value={value} key={value}>{title}</option>)}</select>
    else control=<input {...common} type={type} min={type==='number'?'0':undefined} step={type==='number'?'1000':undefined}/>
    return <label className={wide?'ess-wide':''} htmlFor={name} key={name}>{label}{control}</label>
  }

  return <section className="module-page">
    <header className="module-heading" style={{display:'flex',justifyContent:'space-between',alignItems:'center',gap:16,flexWrap:'wrap'}}><div><p className="eyebrow">PEOPLE OPERATIONS</p><h1>Employee Directory</h1><p>Employee records, access roles, contact details, next of kin, and employment information.</p></div><div style={{display:'flex',gap:9,flexWrap:'wrap'}}><button className="module-secondary-button" type="button" onClick={exportCsv}>Export CSV</button><button className="btn-primary" type="button" onClick={openCreate}>+ Add employee</button></div></header>
    {error&&<p className="module-alert error" role="alert">{error}</p>}{notice&&<p className="module-alert success" role="status">{notice}</p>}
    {credentials&&<section className="card" style={{borderColor:'#9fcce0',background:'#f3fafe',marginBottom:16}}><div style={{display:'flex',justifyContent:'space-between',alignItems:'flex-start',gap:12}}><div><p className="eyebrow">TEMPORARY LOGIN - {credentials.name}</p><p><strong>Login email:</strong> {credentials.email}</p><p><strong>Temporary password:</strong> <code>{credentials.password}</code></p><p className="ess-muted">The employee must change this password the first time they sign in. This password is shown only now.</p></div><div style={{display:'flex',gap:8}}><button type="button" className="module-secondary-button" onClick={copyCredentials}>Copy details</button><button type="button" className="module-secondary-button" onClick={()=>setCredentials(null)}>Close</button></div></div></section>}
    <section className="card" style={{marginBottom:16}}><div className="ess-section-heading"><div><h2>Bring employee records into the new HRMS</h2><p>Choose the CSV exported from the old Employee Directory. Re-imports update matching legacy IDs, and old passwords are never imported.</p></div></div><form onSubmit={importLegacyCsv} style={{display:'flex',alignItems:'center',gap:10,flexWrap:'wrap'}}><input type="file" accept=".csv,text/csv" onChange={event=>setLegacyFile(event.target.files?.[0]||null)} aria-label="Legacy employee CSV"/><button className="module-secondary-button" type="submit" disabled={saving}>{saving?'Importing...':'Import legacy CSV'}</button></form></section>
    <section className="card" style={{overflowX:'auto'}}><div className="ess-section-heading"><div><h2>Employee records</h2><p>{filteredEmployees.length} of {employees.length} employee records</p></div><button className="module-secondary-button" type="button" onClick={fetchEmployees} disabled={loading}>Refresh</button></div><div style={{display:'flex',gap:10,marginBottom:14,flexWrap:'wrap'}}><input type="search" placeholder="Search employee, email, role, or job title" value={query} onChange={event=>setQuery(event.target.value)} style={{flex:'1 1 260px',minHeight:38,border:'1px solid #d5e0e8',borderRadius:7,padding:'8px 10px'}}/><select value={departmentFilter} onChange={event=>setDepartmentFilter(event.target.value)} style={{minWidth:210,minHeight:38,border:'1px solid #d5e0e8',borderRadius:7,padding:'8px 10px'}}><option value="">All departments</option>{departments.map(dept=><option value={dept.code} key={dept.code}>{dept.name}</option>)}</select></div>
      <table className="ess-table" style={{minWidth:1180}}><thead><tr><th>Employee</th><th>System role</th><th>Contact</th><th>Department and job</th><th>Employment</th><th>Actions</th></tr></thead><tbody>
        {filteredEmployees.map(employee=><tr key={employee.id||employee.employee_number}><td><strong>{employeeName(employee)}</strong><small style={{display:'block',color:'#718192'}}>{employee.employee_number||(employee.legacy_employee_id?`Legacy ID ${employee.legacy_employee_id}`:'Employee number not recorded')}</small></td><td>{displayRole(employee)}</td><td><span>{employee.work_email||'No work email'}</span><small style={{display:'block',color:'#718192'}}>{employee.personal_email||'No personal email'}</small><small style={{display:'block',color:'#718192'}}>{employee.phone_number||'No phone'}</small></td><td>{employee.department_name||employee.legacy_department||'Department not recorded'}<small style={{display:'block',color:'#718192'}}>{employee.job_title||'Job title not recorded'}</small></td><td>{employee.employment_type||employee.status||'Not recorded'}<small style={{display:'block',color:'#718192'}}>{employee.work_location||''}</small></td><td><div style={{display:'flex',gap:6,flexWrap:'wrap'}}><button className="module-secondary-button" type="button" onClick={()=>setViewing(employee)}>View</button><button className="module-secondary-button" type="button" onClick={()=>openEdit(employee)}>Edit</button><button className="module-secondary-button" type="button" onClick={()=>{setDocumentEmployee(employee);setError('')}}>Upload</button><button className="module-secondary-button" type="button" disabled={saving} onClick={()=>generateLogin(employee)}>{employee.has_account?'Reset login':'Generate login'}</button><button className="module-secondary-button" type="button" disabled={saving} onClick={()=>handleArchive(employee)}>Archive</button></div></td></tr>)}
        {!loading&&filteredEmployees.length===0&&<tr><td colSpan="6" style={{textAlign:'center',padding:22}}>{employees.length?'No employees match these filters.':'No employee records yet. Import the old directory CSV or add an employee.'}</td></tr>}{loading&&<tr><td colSpan="6" style={{textAlign:'center',padding:22}}>Loading employee records...</td></tr>}
      </tbody></table>
    </section>
    {viewing&&<div className="ess-review-backdrop" onMouseDown={event=>{if(event.target===event.currentTarget)setViewing(null)}}><section className="card ess-review-modal" role="dialog" aria-modal="true" aria-labelledby="employee-profile-title"><div className="ess-section-heading"><div><p className="eyebrow">EMPLOYEE PROFILE</p><h2 id="employee-profile-title">{employeeName(viewing)}</h2><p>Complete personal, contact, role, employment, statutory, and next-of-kin record.</p></div><button className="ess-close" type="button" onClick={()=>setViewing(null)}>Back</button></div><div style={{display:'grid',gridTemplateColumns:'repeat(auto-fit,minmax(210px,1fr))',gap:12}}>{PROFILE_FIELDS.map(([label,key])=><div className="ess-profile-field" key={key}><span>{label}</span><strong>{displayValue(key==='department_name'?(viewing.department_name||viewing.legacy_department):viewing[key])}</strong></div>)}</div><div style={{marginTop:20}}><h3>Employee documents</h3>{viewing.documents?.length?<div style={{display:'grid',gap:8}}>{viewing.documents.map(doc=><div key={doc.id} style={{display:'flex',justifyContent:'space-between',gap:12,alignItems:'center',borderTop:'1px solid #e6edf2',padding:'9px 0'}}><span>{doc.document_type}: {doc.file_name} ({doc.status})</span><button type="button" className="module-secondary-button" onClick={()=>downloadDocument(doc)}>Download</button></div>)}</div>:<p className="ess-muted">No documents have been attached to this profile.</p>}</div></section></div>}
    {showModal&&<div className="ess-review-backdrop" onMouseDown={event=>{if(event.target===event.currentTarget&&!saving)setShowModal(false)}}><section className="card ess-review-modal" role="dialog" aria-modal="true" aria-labelledby="employee-form-title"><div className="ess-section-heading"><div><p className="eyebrow">MASTER DASHBOARD</p><h2 id="employee-form-title">{editing?'Edit employee profile':'Add employee and login'}</h2><p>Complete the employee record. Enter a work or personal email to create their login.</p></div><button className="ess-close" type="button" onClick={()=>!saving&&setShowModal(false)}>Close</button></div><form className="ess-performance-form" onSubmit={handleSave}>{FIELD_SECTIONS.map(section=><div className="ess-wide" key={section.title} style={{display:'contents'}}><h3 className="ess-wide" style={{margin:'12px 0 0',color:'#31536a',fontSize:14}}>{section.title}</h3>{section.fields.map(renderField)}</div>)}<div className="ess-form-actions ess-wide"><button className="ess-cancel" type="button" disabled={saving} onClick={()=>setShowModal(false)}>Cancel</button><button className="btn-primary" type="submit" disabled={saving}>{saving?'Saving...':editing?'Save full profile':'Create employee and login'}</button></div></form></section></div>}
    {documentEmployee&&<div className="ess-review-backdrop" onMouseDown={event=>{if(event.target===event.currentTarget)closeDocumentUpload()}}><section className="card ess-review-modal" role="dialog" aria-modal="true" aria-labelledby="employee-document-title"><div className="ess-section-heading"><div><p className="eyebrow">EMPLOYEE FILES</p><h2 id="employee-document-title">Upload for {employeeName(documentEmployee)}</h2><p>PDF, DOC, DOCX, CSV, PNG, or JPG up to 10 MB.</p></div><button className="ess-close" type="button" disabled={saving} onClick={closeDocumentUpload}>Back</button></div><form className="ess-performance-form" onSubmit={uploadDocument}><label>Document type<select value={documentType} onChange={event=>setDocumentType(event.target.value)}>{['National ID','Academic certificate','TIN certificate','NSSF record','Bank confirmation','Employment contract','Other'].map(option=><option key={option}>{option}</option>)}</select></label><label>File<input type="file" accept=".pdf,.doc,.docx,.csv,.png,.jpg,.jpeg" required onChange={event=>setDocumentFile(event.target.files?.[0]||null)}/></label><div className="ess-form-actions ess-wide"><button className="ess-cancel" type="button" disabled={saving} onClick={closeDocumentUpload}>Back</button><button className="btn-primary" type="submit" disabled={saving}>{saving?'Uploading...':'Upload document'}</button></div></form></section></div>}
  </section>
}
