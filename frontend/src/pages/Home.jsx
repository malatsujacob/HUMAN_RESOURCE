import { useCallback, useEffect, useMemo, useState } from 'react'
import axios from 'axios'
import { Link, useNavigate } from 'react-router-dom'
import { Activity, ArrowRight, Bell, BriefcaseBusiness, CalendarCheck2, Clock3, FileText, KeyRound, Users } from 'lucide-react'

const API_BASE = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api'
const formatDashboardDate = () => new Intl.DateTimeFormat(undefined, {
  weekday: 'long',
  year: 'numeric',
  month: 'long',
  day: 'numeric',
}).format(new Date()).toUpperCase()
const authConfig = () => ({
  headers: {
    Authorization: `Bearer ${localStorage.getItem('token') || localStorage.getItem('access_token') || ''}`,
  },
})
const HR_ROLES = ['HR','HR_ADMIN','ADMIN','MANAGEMENT','DEVELOPER']
const QUEUE_LINKS = [
  {label:'Employee records & password resets',path:'/employees',icon:Users},
  {label:'Onboarding checklist',path:'/onboarding',icon:Users},
  {label:'Recruitment decisions',path:'/recruitment',icon:BriefcaseBusiness},
  {label:'Leave requests',path:'/leave',icon:CalendarCheck2},
  {label:'Monthly performance',path:'/performance',icon:Activity},
  {label:'Contracts & expiry reminders',path:'/contracts',icon:FileText},
  {label:'Disciplinary cases',path:'/disciplinary',icon:FileText},
  {label:'Exit & clearance',path:'/exit',icon:ArrowRight},
  {label:'Payroll',path:'/payroll',icon:Clock3},
]

function Home() {
  const navigate = useNavigate()
  const role=(localStorage.getItem('role')||'').toUpperCase()
  const isHR=HR_ROLES.includes(role)
  const [employees,setEmployees]=useState([])
  const [leaves,setLeaves]=useState([])
  const [reviews,setReviews]=useState([])
  const [pendingReviews,setPendingReviews]=useState([])
  const [contracts,setContracts]=useState([])
  const [onboarding,setOnboarding]=useState([])
  const [requisitions,setRequisitions]=useState([])
  const [disciplinary,setDisciplinary]=useState([])
  const [exits,setExits]=useState([])
  const [notifications,setNotifications]=useState([])
  const [notificationError,setNotificationError]=useState('')
  const [loadError,setLoadError]=useState('')
  const [dashboardDate,setDashboardDate]=useState(formatDashboardDate)
  const [expandedNotification,setExpandedNotification]=useState('')
  const [selectedEmployee,setSelectedEmployee]=useState('')
  const [credentials,setCredentials]=useState(null)
  const [busy,setBusy]=useState(false)
  const [actionMessage,setActionMessage]=useState('')
  const [caseNotes,setCaseNotes]=useState({})
  const [exitNotes,setExitNotes]=useState({})
  const [exitStatuses,setExitStatuses]=useState({})
  const [queueBusy,setQueueBusy]=useState('')

  const loadDashboard=useCallback(async()=>{
    setLoadError('')
    const results=await Promise.allSettled([
      axios.get(`${API_BASE}/employees/`,authConfig()),
      axios.get(`${API_BASE}/leave/pending`,authConfig()),
      axios.get(`${API_BASE}/performance/`,authConfig()),
      axios.get(`${API_BASE}/performance/pending`,authConfig()),
      axios.get(`${API_BASE}/contracts/`,authConfig()),
      axios.get(`${API_BASE}/onboarding/pending`,authConfig()),
      axios.get(`${API_BASE}/recruitment/requisitions`,authConfig()),
      axios.get(`${API_BASE}/disciplinary/`,authConfig()),
      axios.get(`${API_BASE}/exit/`,authConfig()),
    ])
    const setters=[setEmployees,setLeaves,setReviews,setPendingReviews,setContracts,setOnboarding,setRequisitions,setDisciplinary,setExits]
    const labels=['employee records','leave requests','performance reviews','performance items awaiting HOD ratings','contract reminders','onboarding records','requisitions','disciplinary cases','exit records']
    if(results.some(result=>result.status==='rejected'&&result.reason?.response?.status===401)){
      localStorage.removeItem('token')
      localStorage.removeItem('access_token')
      localStorage.removeItem('role')
      localStorage.removeItem('email')
      navigate('/login',{replace:true})
      return
    }
    const failures=[]
    results.forEach((result,index)=>{
      if(result.status==='fulfilled') setters[index](result.value.data)
      else if(result.reason?.response?.status!==403){
        const status=result.reason?.response?.status
        failures.push(`${labels[index]} (${status?`HTTP ${status}`:result.reason?.code||'network error'})`)
      }
    })
    if(failures.length)setLoadError(`Could not load: ${failures.join(', ')}.`)
    if(isHR){
      try{
        const {data}=await axios.get(`${API_BASE}/notifications/hr`,authConfig())
        setNotifications(data);setNotificationError('')
      }catch(requestError){setNotificationError(requestError.response?.status===403?'':'HR notifications could not be loaded.')}
    }
  },[isHR,navigate])

  useEffect(()=>{if(isHR)loadDashboard()},[isHR,loadDashboard])
  useEffect(()=>{
    const timer=window.setInterval(()=>setDashboardDate(formatDashboardDate()),60000)
    return ()=>window.clearInterval(timer)
  },[])
  useEffect(()=>{
    if(!isHR)return undefined
    const timer=window.setInterval(loadDashboard,60000)
    return ()=>window.clearInterval(timer)
  },[isHR,loadDashboard])

  const departments=useMemo(()=>{
    const byDepartment=new Map()
    reviews.forEach(review=>{
      const name=review.department_name||'Unassigned'
      const item=byDepartment.get(name)||{name,employeeTotal:0,selfTotal:0,selfCount:0,hodTotal:0,hodCount:0}
      item.employeeTotal+=1
      if(typeof review.self_rating==='number'){item.selfTotal+=review.self_rating;item.selfCount+=1}
      if(typeof review.hod_rating==='number'){item.hodTotal+=review.hod_rating;item.hodCount+=1}
      byDepartment.set(name,item)
    })
    return [...byDepartment.values()].sort((a,b)=>a.name.localeCompare(b.name))
  },[reviews])

  const markRead=async notification=>{
    setNotificationError('')
    try{
      await axios.post(`${API_BASE}/notifications/hr/${notification.id}/read`,{},authConfig())
      setNotifications(items=>items.map(item=>item.id===notification.id?{...item,is_read:true}:item))
    }catch{setNotificationError('The notification could not be marked as read.')}
  }

  const resetEmployeePassword=async event=>{
    event.preventDefault()
    if(!selectedEmployee){setActionMessage('Select an employee first.');return}
    setBusy(true);setActionMessage('');setCredentials(null)
    try{
      const {data}=await axios.post(`${API_BASE}/employees/${selectedEmployee}/generate-login`,{},authConfig())
      const employee=employees.find(item=>item.id===selectedEmployee)
      setCredentials({email:data.login_email,password:data.temporary_password,name:employee?.full_name||`${employee?.first_name||''} ${employee?.last_name||''}`.trim()})
      setActionMessage(data.message);await loadDashboard()
    }catch(requestError){setActionMessage(requestError.response?.data?.detail||'A temporary password could not be generated.')}
    finally{setBusy(false)}
  }

  const resolveDisciplinaryCase=async item=>{
    const note=(caseNotes[item.id]||'').trim()
    if(note.length<5){setActionMessage('Enter a resolution note of at least 5 characters.');return}
    setQueueBusy(item.id);setActionMessage('')
    try{
      await axios.put(`${API_BASE}/disciplinary/${item.id}/resolve`,{resolution_note:note},authConfig())
      setCaseNotes(current=>({...current,[item.id]:''}));setActionMessage('Disciplinary case resolved.');await loadDashboard()
    }catch(requestError){setActionMessage(requestError.response?.data?.detail||'The disciplinary case could not be resolved.')}
    finally{setQueueBusy('')}
  }

  const reviewExitClearance=async item=>{
    const note=(exitNotes[item.id]||'').trim()
    if(note.length<5){setActionMessage('Enter a clearance note of at least 5 characters.');return}
    setQueueBusy(item.id);setActionMessage('')
    try{
      await axios.put(`${API_BASE}/exit/${item.id}/clearance`,{clearance_status:exitStatuses[item.id]||'IN_PROGRESS',note},authConfig())
      setExitNotes(current=>({...current,[item.id]:''}));setActionMessage('Exit clearance updated.');await loadDashboard()
    }catch(requestError){setActionMessage(requestError.response?.data?.detail||'The exit clearance could not be updated.')}
    finally{setQueueBusy('')}
  }

  const statCards=[
    {label:'Active employees',value:employees.filter(item=>item.status==='ACTIVE').length,detail:`${employees.length} directory records`,icon:Users,tone:'violet'},
    {label:'Leave awaiting review',value:leaves.length,detail:'Pending HOD decision',icon:CalendarCheck2,tone:'amber'},
    {label:'Performance awaiting HOD',value:pendingReviews.length,detail:'Employee self-assessments submitted',icon:Activity,tone:'blue'},
    {label:'Contracts nearing expiry',value:contracts.filter(item=>item.days_to_expiry!==null&&item.days_to_expiry>=0&&item.expiry_reminder_days!==null&&item.expiry_reminder_days!==undefined&&item.days_to_expiry<=item.expiry_reminder_days&&['SIGNED','ACTIVE'].includes(item.status)).length,detail:'Within HR-selected reminder period',icon:Clock3,tone:'green'},
    {label:'Expired contracts',value:contracts.filter(item=>item.status==='EXPIRED').length,detail:'Review and arrange renewal or exit',icon:FileText,tone:'amber'},
    {label:'Onboarding to review',value:onboarding.length,detail:'Check new hire details and documents',icon:Users,tone:'blue'},
    {label:'Requisitions awaiting HR',value:requisitions.filter(item=>item.status==='PENDING_HR').length,detail:'Approve or reject hiring requests',icon:BriefcaseBusiness,tone:'violet'},
    {label:'Open disciplinary cases',value:disciplinary.filter(item=>item.status==='OPEN').length,detail:'Document resolution and outcome',icon:FileText,tone:'amber'},
    {label:'Exit clearances pending',value:exits.filter(item=>item.clearance_status!=='CLEARED').length,detail:'Review and record clearance progress',icon:ArrowRight,tone:'green'},
  ]

  if(!isHR)return <section className="module-page"><header className="module-heading"><p className="eyebrow">MASTER DASHBOARD</p><h1>HR dashboard access required</h1><p>This dashboard is available to HR and administrators. Open the ESS Portal for your employee services.</p><Link className="btn-primary" to="/ess">Open ESS Portal</Link></header></section>

  return <section className="module-page">
    <header className="module-heading" style={{display:'flex',justifyContent:'space-between',alignItems:'center',gap:12,flexWrap:'wrap'}}>
      <div><p className="eyebrow">{dashboardDate}</p><h1>HR master dashboard</h1><p>People operations, employee updates, and decisions requiring attention.</p></div>
      <button className="module-secondary-button" type="button" onClick={loadDashboard}>Refresh dashboard</button>
    </header>
    {loadError&&<p className="module-alert error" role="alert">{loadError}</p>}

    <section className="summary-grid" aria-label="Live HR statistics">
      {statCards.map(({label,value,detail,icon:Icon,tone})=><article className="summary-card" key={label}><div className="card-topline"><span className={`summary-icon ${tone}`}><Icon size={19} aria-hidden="true"/></span></div><p className="summary-label">{label}</p><strong className="summary-value">{value}</strong><span className="summary-detail">{detail}</span></article>)}
    </section>

    <section className="card" style={{marginTop:20}}>
      <div className="panel-heading"><div><h2><Bell size={18} style={{verticalAlign:'middle',marginRight:8}}/>HR response inbox</h2><p className="heading-subtitle">Leave decisions from HODs, first-login updates, signatures, contract alerts, and other HR notifications.</p></div><strong>{notifications.filter(item=>!item.is_read).length} unread</strong></div>
      {notificationError&&<p className="module-alert error" role="alert">{notificationError}</p>}
      {notifications.length===0?<p className="ess-muted">No HR notifications yet.</p>:<div style={{display:'grid',gap:8}}>{notifications.slice(0,20).map(item=><article key={item.id} style={{display:'grid',gridTemplateColumns:'minmax(0,1fr) auto',gap:12,padding:'12px 0',borderTop:'1px solid #e6edf2',opacity:item.is_read ? 0.65 : 1}}>
        <div><strong>{item.title}</strong><p style={{margin:'4px 0'}}>{item.message}</p><small>{new Date(item.created_at).toLocaleString()}</small>
          {expandedNotification===item.id&&item.details&&<dl style={{display:'grid',gridTemplateColumns:'repeat(auto-fit,minmax(170px,1fr))',gap:'8px 18px',margin:'10px 0 0'}}>{Object.entries(item.details).map(([key,value])=><div key={key}><dt style={{fontSize:12,color:'#687887'}}>{key.replaceAll('_',' ')}</dt><dd style={{margin:0,fontWeight:600}}>{String(value)}</dd></div>)}</dl>}
        </div><div style={{display:'flex',gap:7,alignItems:'flex-start',flexWrap:'wrap'}}><button className="module-secondary-button" type="button" onClick={()=>setExpandedNotification(id=>id===item.id?'':item.id)}>{expandedNotification===item.id?'Hide':'Details'}</button>{!item.is_read&&<button className="module-secondary-button" type="button" onClick={()=>markRead(item)}>Mark read</button>}</div>
      </article>)}</div>}
    </section>

    <section className="card" style={{marginTop:20}}>
      <div className="panel-heading"><div><h2>Action queues</h2><p className="heading-subtitle">Open items that require an HR/admin review or decision.</p></div></div>
      <div style={{display:'grid',gridTemplateColumns:'repeat(auto-fit,minmax(210px,1fr))',gap:10}}>
        {[['Onboarding to review',onboarding.length,'/onboarding'],['Requisitions awaiting HR',requisitions.filter(item=>item.status==='PENDING_HR').length,'/recruitment?section=requisitions'],['Leave awaiting HOD',leaves.length,'/leave'],['Performance awaiting HOD',pendingReviews.length,'/performance'],['Open disciplinary cases',disciplinary.filter(item=>item.status==='OPEN').length,'/disciplinary'],['Exit clearances pending',exits.filter(item=>item.clearance_status!=='CLEARED').length,'/exit']].map(([label,count,path])=><Link key={label} to={path} className="module-secondary-button" style={{display:'flex',justifyContent:'space-between',gap:10,textDecoration:'none',padding:12}}><span>{label}</span><strong>{count}</strong></Link>)}
      </div>
      {disciplinary.some(item=>item.status==='OPEN')&&<div style={{marginTop:18}}><h3>Disciplinary cases awaiting resolution</h3><div style={{display:'grid',gap:12}}>{disciplinary.filter(item=>item.status==='OPEN').map(item=>{
        const employee=employees.find(person=>person.id===item.employee_id)
        const name=employee?.full_name||`${employee?.first_name||''} ${employee?.last_name||''}`.trim()||item.employee_id
        return <article key={item.id} style={{padding:12,border:'1px solid #e6edf2',borderRadius:8}}><strong>{name} · {item.incident_date}</strong><p>{item.description}</p>{item.action_taken&&<p className="ess-muted">Initial action: {item.action_taken}</p>}<label style={{display:'grid',gap:6}}>Resolution note<textarea minLength="5" maxLength="1000" rows="2" value={caseNotes[item.id]||''} onChange={event=>setCaseNotes(current=>({...current,[item.id]:event.target.value}))}/></label><button className="module-secondary-button" type="button" disabled={queueBusy===item.id} onClick={()=>resolveDisciplinaryCase(item)} style={{marginTop:8}}>{queueBusy===item.id?'Saving…':'Resolve case'}</button></article>
      })}</div></div>}
      {exits.some(item=>item.clearance_status!=='CLEARED')&&<div style={{marginTop:18}}><h3>Exit clearances awaiting review</h3><div style={{display:'grid',gap:12}}>{exits.filter(item=>item.clearance_status!=='CLEARED').map(item=>{
        const employee=employees.find(person=>person.id===item.employee_id)
        const name=employee?.full_name||`${employee?.first_name||''} ${employee?.last_name||''}`.trim()||item.employee_id
        return <article key={item.id} style={{padding:12,border:'1px solid #e6edf2',borderRadius:8}}><strong>{name} · Last day {item.last_working_day}</strong><p>{item.reason}</p>{item.clearance_note&&<p className="ess-muted">Previous note: {item.clearance_note}</p>}<div style={{display:'flex',gap:10,flexWrap:'wrap',alignItems:'end'}}><label style={{display:'grid',gap:6}}>Clearance status<select value={exitStatuses[item.id]||(item.clearance_status==='PENDING'?'IN_PROGRESS':item.clearance_status)} onChange={event=>setExitStatuses(current=>({...current,[item.id]:event.target.value}))}><option value="IN_PROGRESS">In progress</option><option value="BLOCKED">Blocked</option><option value="CLEARED">Cleared</option></select></label><label style={{display:'grid',gap:6,flex:'1 1 260px'}}>Clearance note<input minLength="5" maxLength="1000" value={exitNotes[item.id]||''} onChange={event=>setExitNotes(current=>({...current,[item.id]:event.target.value}))}/></label><button className="module-secondary-button" type="button" disabled={queueBusy===item.id} onClick={()=>reviewExitClearance(item)}>{queueBusy===item.id?'Saving…':'Save clearance'}</button></div></article>
      })}</div></div>}
    </section>

    <section className="card" style={{marginTop:20}}>
      <div className="panel-heading"><div><h2>Employee performance by department</h2><p className="heading-subtitle">Average monthly employee self-ratings and HOD ratings, on a 1–5 scale.</p></div><Link className="text-button" to="/performance">Open performance <ArrowRight size={15}/></Link></div>
      {departments.length===0?<p className="ess-muted">No monthly performance ratings have been recorded yet.</p>:<div style={{display:'grid',gap:16}}>{departments.map(item=><div key={item.name} style={{display:'grid',gridTemplateColumns:'minmax(130px,1fr) minmax(180px,3fr) auto',gap:'6px 14px',alignItems:'center',paddingBottom:12,borderBottom:'1px solid #e6edf2'}}>
        <strong>{item.name}</strong><div><div style={{height:9,background:'#e7edf2',borderRadius:8,overflow:'hidden'}}><span title="Employee self-rating average" style={{display:'block',height:'100%',width:`${item.selfCount?item.selfTotal/item.selfCount*20:0}%`,background:'#4f8fc2'}}/></div><small>Employee self: {item.selfCount?(item.selfTotal/item.selfCount).toFixed(2):'—'} / 5</small><div style={{height:9,marginTop:5,background:'#e7edf2',borderRadius:8,overflow:'hidden'}}><span title="HOD rating average" style={{display:'block',height:'100%',width:`${item.hodCount?item.hodTotal/item.hodCount*20:0}%`,background:'#48a782'}}/></div><small>HOD rating: {item.hodCount?(item.hodTotal/item.hodCount).toFixed(2):'Pending'} / 5</small></div><span className="ess-muted">{item.employeeTotal} review{item.employeeTotal===1?'':'s'}</span>
      </div>)}</div>}
    </section>

    <section className="card" style={{marginTop:20}}>
      <div className="panel-heading"><div><h2><KeyRound size={18} style={{verticalAlign:'middle',marginRight:8}}/>Reset employee login</h2><p className="heading-subtitle">Generate a one-time temporary password when an employee cannot access their account. They must change it at next sign-in.</p></div></div>
      <form onSubmit={resetEmployeePassword} style={{display:'flex',gap:10,alignItems:'center',flexWrap:'wrap'}}><select required aria-label="Employee to reset password" value={selectedEmployee} onChange={event=>setSelectedEmployee(event.target.value)} style={{minWidth:260,minHeight:38}}><option value="">Select employee</option>{employees.filter(item=>item.has_account).map(item=><option key={item.id} value={item.id}>{item.full_name||`${item.first_name} ${item.last_name}`} · {item.employee_number}</option>)}</select><button className="module-secondary-button" type="submit" disabled={busy||!selectedEmployee}>{busy?'Generating…':'Generate temporary password'}</button></form>
      {actionMessage&&<p className="ess-muted" role="status">{actionMessage}</p>}
      {credentials&&<div role="status" style={{marginTop:12,padding:14,border:'1px solid #b8d9e9',borderRadius:8,background:'#f2f9fc'}}><strong>{credentials.name}</strong><p>Login: {credentials.email}</p><p>Temporary password: <code>{credentials.password}</code></p><p className="ess-muted">Share securely. It is shown only once, and the employee must set a personal password.</p><button className="module-secondary-button" type="button" onClick={()=>setCredentials(null)}>Dismiss</button></div>}
    </section>

    <section className="card" style={{marginTop:20}}>
      <div className="panel-heading"><div><h2>HR action centre</h2><p className="heading-subtitle">Open the matching module to review records and complete HR/admin actions.</p></div></div>
      <div style={{display:'grid',gridTemplateColumns:'repeat(auto-fit,minmax(230px,1fr))',gap:10}}>{QUEUE_LINKS.map(({label,path,icon:Icon})=><Link key={path} to={path} className="module-secondary-button" style={{display:'flex',alignItems:'center',justifyContent:'space-between',gap:10,textDecoration:'none',padding:12}}><span><Icon size={16} style={{verticalAlign:'middle',marginRight:8}}/>{label}</span><ArrowRight size={15}/></Link>)}</div>
    </section>
  </section>
}

export default Home
