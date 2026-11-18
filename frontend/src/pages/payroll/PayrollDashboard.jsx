import { useCallback, useEffect, useMemo, useState } from 'react'
import axios from 'axios'
import {
  AlertTriangle, ArrowDownRight, ArrowUpRight, Banknote, CalendarDays,
  Check, ChevronDown, ChevronUp, CircleAlert, Clock3, Download, FileCheck2,
  LockKeyhole, RefreshCw, Search, ShieldCheck, Upload, Wallet,
} from 'lucide-react'
import './Payroll.css'
import { getDepartmentName } from '../../constants/departments'

const API_BASE = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api'
const ORG_ROLES = new Set(['HR', 'HR_ADMIN', 'ADMIN', 'FINANCE', 'MANAGEMENT', 'DEVELOPER'])
const PAY_CODES = {
  BASE_WAGES: 'Wages',
  BONUS: 'Bonus',
  OVERTIME: 'Overtime',
  RETRO: 'Retroactive pay',
}
const NOW_TIMESTAMP = Date.now()
const api = axios.create({ baseURL: API_BASE })
api.interceptors.request.use(config => {
  const token = localStorage.getItem('token') || localStorage.getItem('access_token')
  if (token) config.headers.Authorization = `Bearer ${token}`
  return config
})

const currentPeriod = () => {
  const date = new Date()
  return `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}`
}
const amount = value => Number(value ?? 0)
const formatMoney = value => `UGX ${new Intl.NumberFormat('en-UG', { maximumFractionDigits: 0 }).format(amount(value))}`
const displayPeriod = value => {
  if (!value) return 'No pay period'
  const [year, month] = value.split('-')
  return new Date(Number(year), Number(month) - 1, 1).toLocaleDateString(undefined, { month: 'long', year: 'numeric' })
}
const errorMessage = error => {
  const detail = error.response?.data?.detail
  if (Array.isArray(detail)) return detail.map(item => item.msg).filter(Boolean).join('; ')
  return detail || error.message || 'Payroll information could not be loaded.'
}
const employeeName = employee => employee.employee_valid === false
  ? `Invalid employee mapping · ${employee.employee_id}`
  : employee.employee_name || employee.full_name || employee.name || `Employee ${employee.employee_number || ''}`.trim()
const getMappedRecord = item => ({
  ...item,
  mappedCategory: item.reporting_category || PAY_CODES[item.pay_code || 'BASE_WAGES'] || null,
})
const rowsToCsv = (headers, rows) => [headers, ...rows].map(row => row.map(value => `"${String(value ?? '').replaceAll('"', '""')}"`).join(',')).join('\r\n')
const downloadCsv = (filename, headers, rows) => {
  const url = URL.createObjectURL(new Blob([rowsToCsv(headers, rows)], { type: 'text/csv;charset=utf-8' }))
  const link = document.createElement('a')
  link.href = url
  link.download = filename
  link.click()
  URL.revokeObjectURL(url)
}

function Metric({ label, value, note, icon: Icon, tone = 'blue', onClick }) {
  return (
    <button className={`payroll-metric ${tone}`} type="button" onClick={onClick} disabled={!onClick}>
      <span className="payroll-metric-icon"><Icon size={18} /></span>
      <span className="payroll-metric-label">{label}</span>
      <strong>{value}</strong>
      <small>{note}</small>
    </button>
  )
}

function SectionTitle({ eyebrow, title, description, action }) {
  return (
    <div className="payroll-section-title">
      <div>
        {eyebrow && <span className="payroll-eyebrow">{eyebrow}</span>}
        <h2>{title}</h2>
        {description && <p>{description}</p>}
      </div>
      {action}
    </div>
  )
}

function StateBadge({ value }) {
  const pass = value === 'MATCH' || value === 'PASS' || value === 'POSTED'
  return <span className={`payroll-badge ${pass ? 'good' : value === 'MISMATCH' || value === 'FAIL' ? 'bad' : 'pending'}`}>{value}</span>
}

function LineChart({ rows, threshold, activeEmployees }) {
  const width = 720
  const height = 220
  const inset = 25
  const maxCost = Math.max(1, ...rows.map(row => row.cost))
  const maxPeople = Math.max(1, ...rows.map(row => row.count), activeEmployees)
  const getX = index => rows.length < 2 ? width / 2 : inset + (index * (width - inset * 2)) / (rows.length - 1)
  const getY = value => height - inset - (value / Math.max(maxCost, activeEmployees * (maxCost / maxPeople), 1)) * (height - inset * 2)
  const getHeadcountY = value => height - inset - (value / maxPeople) * (height - inset * 2)
  const costs = rows.map((row, index) => `${getX(index)},${getY(row.cost)}`).join(' ')
  const people = rows.map((row, index) => `${getX(index)},${getHeadcountY(row.count)}`).join(' ')
  return (
    <div className="payroll-chart-wrap">
      <svg className="payroll-trend-chart" viewBox={`0 0 ${width} ${height}`} role="img" aria-label="Payroll cost and paid headcount trend">
        {[0, 1, 2, 3].map(step => <line key={step} x1={inset} x2={width - inset} y1={inset + step * ((height - inset * 2) / 3)} y2={inset + step * ((height - inset * 2) / 3)} className="payroll-chart-grid" />)}
        {rows.length > 1 && <>
          <polyline points={costs} className="payroll-chart-line cost" />
          <polyline points={people} className="payroll-chart-line people" />
        </>}
        {rows.map((row, index) => {
          const previous = rows[index - 1]
          const spike = previous && previous.cost > 0 && ((row.cost - previous.cost) / previous.cost) * 100 >= threshold
          return (
            <g key={row.period}>
              <circle cx={getX(index)} cy={getY(row.cost)} r={spike ? 6 : 4} className={spike ? 'payroll-chart-point spike' : 'payroll-chart-point cost'} />
              <circle cx={getX(index)} cy={getHeadcountY(row.count)} r="3.5" className="payroll-chart-point people" />
              {spike && <text x={getX(index)} y={Math.max(inset, getY(row.cost) - 12)} className="payroll-chart-alert">Spike +{Math.round(((row.cost - previous.cost) / previous.cost) * 100)}%</text>}
              <text x={getX(index)} y={height - 5} textAnchor="middle" className="payroll-chart-label">{row.period.slice(2)}</text>
            </g>
          )
        })}
      </svg>
      {rows.length < 2 && <p className="payroll-empty">At least two cycles are required to draw a trend.</p>}
      <div className="payroll-chart-legend">
        <span><i className="cost" />Payroll spend</span>
        <span><i className="people" />Paid headcount</span>
        <small>Headcount is based on valid payslips in each cycle.</small>
      </div>
    </div>
  )
}

function PayrollTotalsChart({ rows }) {
  const width = 720
  const height = 190
  const inset = 25
  const maxValue = Math.max(1, ...rows.flatMap(row => [row.gross, row.net, row.tax]))
  const getX = index => rows.length < 2 ? width / 2 : inset + (index * (width - inset * 2)) / (rows.length - 1)
  const getY = value => height - inset - (value / maxValue) * (height - inset * 2)
  const series = [
    { key: 'gross', color: 'gross', label: 'Gross' },
    { key: 'net', color: 'net', label: 'Net' },
    { key: 'tax', color: 'tax', label: 'Tax' },
  ]
  return (
    <div className="payroll-chart-wrap">
      <svg className="payroll-trend-chart" viewBox={`0 0 ${width} ${height}`} role="img" aria-label="Gross, net, and tax totals by pay cycle">
        {[0, 1, 2, 3].map(step => <line key={step} x1={inset} x2={width - inset} y1={inset + step * ((height - inset * 2) / 3)} y2={inset + step * ((height - inset * 2) / 3)} className="payroll-chart-grid" />)}
        {series.map(item => <polyline key={item.key} points={rows.map((row, index) => `${getX(index)},${getY(row[item.key])}`).join(' ')} className={`payroll-chart-line ${item.color}`} />)}
        {rows.map((row, index) => <g key={row.period}>
          {series.map(item => <circle key={item.key} cx={getX(index)} cy={getY(row[item.key])} r="3.5" className={`payroll-chart-point ${item.color}`} />)}
          <text x={getX(index)} y={height - 5} textAnchor="middle" className="payroll-chart-label">{row.period.slice(2)}</text>
        </g>)}
      </svg>
      {rows.length < 2 && <p className="payroll-empty">At least two cycles are required to draw a trend.</p>}
      <div className="payroll-chart-legend">
        {series.map(item => <span key={item.key}><i className={item.color} />{item.label}</span>)}
      </div>
    </div>
  )
}

function PayrollDeadlineCalendar({ period, approvalDeadline, postingDeadline }) {
  const [year, month] = (period || currentPeriod()).split('-').map(Number)
  const daysInMonth = new Date(year, month, 0).getDate()
  const firstDay = new Date(year, month - 1, 1).getDay()
  const cells = [...Array(firstDay).fill(null), ...Array.from({ length: daysInMonth }, (_, index) => index + 1)]
  const deadlineLabels = new Map()
  if (approvalDeadline?.startsWith(period)) deadlineLabels.set(Number(approvalDeadline.slice(-2)), 'Approval')
  if (postingDeadline?.startsWith(period)) {
    const day = Number(postingDeadline.slice(-2))
    deadlineLabels.set(day, deadlineLabels.has(day) ? 'Approval + posting' : 'Posting')
  }
  return (
    <div className="payroll-calendar">
      <h3>{displayPeriod(period)} deadlines</h3>
      <div className="payroll-calendar-grid">
        {['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'].map(day => <span className="weekday" key={day}>{day}</span>)}
        {cells.map((day, index) => <span className={`day ${day && deadlineLabels.has(day) ? 'deadline' : ''}`} key={`${day || 'blank'}-${index}`}>
          {day && <>{day}{deadlineLabels.has(day) && <small>{deadlineLabels.get(day)}</small>}</>}
        </span>)}
      </div>
      {deadlineLabels.size === 0 && <p>No approval or posting deadlines have been configured.</p>}
    </div>
  )
}

export default function PayrollDashboard() {
  const role = (localStorage.getItem('role') || '').toUpperCase()
  const isOrgRole = ORG_ROLES.has(role)
  const isTeamRole = role === 'HOD'
  const hasPayrollControl = isOrgRole
  const isSelfService = !isOrgRole && !isTeamRole
  const [records, setRecords] = useState([])
  const [cycles, setCycles] = useState([])
  const [employees, setEmployees] = useState([])
  const [overtimeRows, setOvertimeRows] = useState([])
  const [profile, setProfile] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [notice, setNotice] = useState('')
  const [busy, setBusy] = useState(false)
  const [selectedPeriod, setSelectedPeriod] = useState(currentPeriod())
  const [activeTab, setActiveTab] = useState(hasPayrollControl ? 'Overview' : isTeamRole ? 'Team overview' : 'My payslips')
  const [showPayrollDetails, setShowPayrollDetails] = useState(false)
  const [showLaborComponents, setShowLaborComponents] = useState(false)
  const [selectedGroup, setSelectedGroup] = useState('')
  const [grouping, setGrouping] = useState('department')
  const [budgetInputs, setBudgetInputs] = useState({})
  const [complianceFilter, setComplianceFilter] = useState('all')
  const [complianceSearch, setComplianceSearch] = useState('')
  const [auditSearch, setAuditSearch] = useState('')
  const [auditType, setAuditType] = useState('')
  const [auditRows, setAuditRows] = useState([])
  const [reconciliations, setReconciliations] = useState({})
  const [reconciliationFiles, setReconciliationFiles] = useState({})
  const [reconciliationPreview, setReconciliationPreview] = useState(null)
  const [selectedEmployee, setSelectedEmployee] = useState(null)
  const [hoursThreshold, setHoursThreshold] = useState(40)
  const [anomalyThreshold, setAnomalyThreshold] = useState(20)
  const [trendRange, setTrendRange] = useState(6)
  const [electionForm, setElectionForm] = useState({ bank_name: '', account_number: '' })
  const [electionMessage, setElectionMessage] = useState('')
  const [approvalDeadline, setApprovalDeadline] = useState('')
  const [postingDeadline, setPostingDeadline] = useState('')
  const [deadlineMessage, setDeadlineMessage] = useState('')

  const loadData = useCallback(async () => {
    setLoading(true)
    setError('')
    try {
      const payslipResponse = await api.get(isOrgRole || isTeamRole ? '/payroll/all' : '/payroll/my-payslips')
      setRecords((payslipResponse.data || []).map(getMappedRecord))
      let cyclePeriods = []
      if (isOrgRole || isTeamRole) {
        const [cycleResponse, complianceResponse] = await Promise.all([
          api.get('/payroll/cycles'),
          api.get('/payroll/compliance'),
        ])
        setCycles(cycleResponse.data || [])
        setEmployees(complianceResponse.data || [])
        cyclePeriods = (cycleResponse.data || []).map(item => item.pay_period)
      } else {
        const { data } = await api.get('/employees/me')
        setProfile(data)
        setElectionForm({ bank_name: data.bank_name || '', account_number: '' })
      }
      const periods = [...new Set([...(payslipResponse.data || []).map(item => item.pay_period), ...cyclePeriods])]
        .filter(Boolean).sort().reverse()
      setSelectedPeriod(current => periods.includes(current) ? current : (periods[0] || current))
    } catch (requestError) {
      setError(errorMessage(requestError))
    } finally {
      setLoading(false)
    }
  }, [isOrgRole, isTeamRole])

  useEffect(() => { loadData() }, [loadData])

  useEffect(() => {
    if (!isOrgRole && !isTeamRole) return
    api.get('/payroll/overtime', { params: { pay_period: selectedPeriod } })
      .then(({ data }) => setOvertimeRows(data || []))
      .catch(requestError => setError(errorMessage(requestError)))
  }, [isOrgRole, isTeamRole, selectedPeriod])

  const loadCycleControls = useCallback(async () => {
    if (!hasPayrollControl || !selectedPeriod) return
    try {
      const [reconResponse, auditResponse] = await Promise.all([
        api.get(`/payroll/cycles/${selectedPeriod}/reconciliations`),
        api.get(`/payroll/cycles/${selectedPeriod}/audit`, { params: { search: auditSearch || undefined, action_type: auditType || undefined } }),
      ])
      setReconciliations(Object.fromEntries((reconResponse.data || []).map(item => [item.reconciliation_type, item])))
      setAuditRows(auditResponse.data || [])
    } catch (requestError) {
      setError(errorMessage(requestError))
    }
  }, [hasPayrollControl, selectedPeriod, auditSearch, auditType])

  useEffect(() => { loadCycleControls() }, [loadCycleControls])

  const activeCycle = cycles.find(cycle => cycle.pay_period === selectedPeriod) || {
    pay_period: selectedPeriod, stage: 'DATA_ENTRY', approval_deadline: null, posting_deadline: null,
  }
  useEffect(() => {
    setApprovalDeadline(activeCycle.approval_deadline || '')
    setPostingDeadline(activeCycle.posting_deadline || '')
  }, [activeCycle.approval_deadline, activeCycle.posting_deadline])

  const cycleRecords = useMemo(
    () => records.filter(item => item.pay_period === selectedPeriod),
    [records, selectedPeriod],
  )
  const includedRecords = useMemo(
    () => cycleRecords.filter(item => item.employee_valid !== false
      && (!hasPayrollControl && !isTeamRole || item.department_valid)
      && (!hasPayrollControl && !isTeamRole || Boolean(item.mappedCategory))),
    [cycleRecords, hasPayrollControl, isTeamRole],
  )
  const validRecordsAllCycles = useMemo(
    () => records.filter(item => item.employee_valid !== false
      && (!hasPayrollControl && !isTeamRole || item.department_valid)
      && (!hasPayrollControl && !isTeamRole || Boolean(item.mappedCategory))),
    [records, hasPayrollControl, isTeamRole],
  )
  const totals = useMemo(() => includedRecords.reduce((sum, item) => {
    sum.gross += amount(item.gross_salary)
    sum.employeeDeductions += amount(item.nssf_deduction)
    sum.taxes += amount(item.paye_tax)
    sum.net += amount(item.net_salary)
    sum.employerPension += amount(item.employer_pension)
    sum.employerSocial += amount(item.employer_social_contribution)
    sum.employerOther += amount(item.employer_contribution)
    sum.employer += amount(item.employer_contribution) + amount(item.employer_pension) + amount(item.employer_social_contribution)
    sum.bonus += amount(item.bonus_amount)
    sum.overtime += amount(item.overtime_amount)
    sum.retro += amount(item.retro_amount)
    return sum
  }, { gross: 0, employeeDeductions: 0, taxes: 0, net: 0, employer: 0, employerPension: 0, employerSocial: 0, employerOther: 0, bonus: 0, overtime: 0, retro: 0 }), [includedRecords])
  const reconciliationPass = Math.abs(totals.gross - totals.employeeDeductions - totals.taxes - totals.net) < 0.01
  const costBreakdown = {
    wages: totals.gross + totals.retro,
    employer: totals.employer,
    bonus: totals.bonus,
    overtime: totals.overtime,
    total: totals.gross + totals.employer + totals.bonus + totals.overtime,
  }
  const selectedNetAlerts = cycleRecords.filter(item => item.net_salary == null || amount(item.net_salary) <= 0)
  const paidEmployeeIds = new Set(cycleRecords.map(item => item.employee_id))
  const preRunMissing = activeCycle.stage === 'DATA_ENTRY'
    ? employees.filter(item => !paidEmployeeIds.has(item.employee_id))
    : []
  const invalidMappingRows = cycleRecords.filter(item => item.employee_valid === false || !item.department_valid)
  const unmappedPayCodes = cycleRecords.filter(item => !item.mappedCategory)
  const complianceExceptions = useMemo(() => employees.flatMap(employee => {
    const exceptions = []
    if (!employee.department_valid) exceptions.push({ field: 'Current department mapping', key: 'department' })
    if (!employee.tax_id_present) exceptions.push({ field: 'Tax ID (TIN)', key: 'tax_id' })
    if (!employee.tax_form_present) exceptions.push({ field: 'Tax form', key: 'tax_form' })
    if (!employee.jurisdiction_address) exceptions.push({ field: 'Jurisdiction address', key: 'address' })
    else if (!employee.jurisdiction_updated_at || (NOW_TIMESTAMP - new Date(employee.jurisdiction_updated_at).getTime()) > 365 * 24 * 60 * 60 * 1000) {
      exceptions.push({ field: 'Jurisdiction address review (over 12 months)', key: 'address_old' })
    }
    return exceptions.map(exception => ({ ...employee, ...exception }))
  }), [employees])
  const filteredCompliance = complianceExceptions.filter(item => {
    const matchesField = complianceFilter === 'all' || item.key === complianceFilter
    const search = complianceSearch.trim().toLowerCase()
    const matchesSearch = !search || [item.employee_name, item.employee_number, item.department_name, item.field]
      .some(value => String(value || '').toLowerCase().includes(search))
    return matchesField && matchesSearch
  })

  const costGroups = useMemo(() => {
    const groupRows = new Map()
    for (const item of includedRecords) {
      const key = grouping === 'department'
        ? getDepartmentName(item.department_name) || 'Unassigned department'
        : grouping === 'location'
          ? item.work_location || 'Location not set'
          : item.cost_center || 'Cost center not assigned'
      const row = groupRows.get(key) || { name: key, cost: 0, people: 0, employees: [] }
      row.cost += amount(item.gross_salary) + amount(item.employer_contribution) + amount(item.employer_pension) + amount(item.employer_social_contribution) + amount(item.bonus_amount) + amount(item.overtime_amount) + amount(item.retro_amount)
      row.people += 1
      row.employees.push(item)
      groupRows.set(key, row)
    }
    return [...groupRows.values()].sort((a, b) => b.cost - a.cost)
  }, [includedRecords, grouping])
  const overtimeByEmployee = useMemo(() => {
    const grouped = new Map()
    for (const item of overtimeRows) {
      const row = grouped.get(item.employee_id) || { ...item, hours: 0, sourceRecords: [] }
      row.hours += amount(item.hours)
      row.sourceRecords.push(item)
      grouped.set(item.employee_id, row)
    }
    return [...grouped.values()].filter(item => item.hours > Number(hoursThreshold)).sort((a, b) => b.hours - a.hours)
  }, [overtimeRows, hoursThreshold])
  const retroRows = cycleRecords.filter(item => amount(item.retro_amount) > 0)
  const trendRows = useMemo(() => {
    const grouped = new Map()
    for (const item of validRecordsAllCycles) {
      const row = grouped.get(item.pay_period) || { period: item.pay_period, cost: 0, gross: 0, net: 0, tax: 0, count: 0 }
      row.cost += amount(item.gross_salary) + amount(item.employer_contribution) + amount(item.employer_pension) + amount(item.employer_social_contribution) + amount(item.bonus_amount) + amount(item.overtime_amount) + amount(item.retro_amount)
      row.gross += amount(item.gross_salary)
      row.net += amount(item.net_salary)
      row.tax += amount(item.paye_tax)
      row.count += 1
      grouped.set(item.pay_period, row)
    }
    return [...grouped.values()].sort((a, b) => a.period.localeCompare(b.period)).slice(-Number(trendRange))
  }, [validRecordsAllCycles, trendRange])
  const periods = [...new Set([...cycles.map(item => item.pay_period), ...records.map(item => item.pay_period)])].sort().reverse()
  const activeHeadcount = employees.length
  const displayedEmployee = selectedEmployee

  const runPayroll = async () => {
    setBusy(true); setError(''); setNotice('')
    try {
      const { data } = await api.post('/payroll/generate', { pay_period: selectedPeriod })
      setNotice(`Cycle generated: ${data.generated_count} payslip(s) created; ${data.skipped_count} skipped (already run or missing department mapping).`)
      await loadData()
      await loadCycleControls()
    } catch (requestError) {
      setError(errorMessage(requestError))
    } finally { setBusy(false) }
  }

  const updateStage = async nextStage => {
    setBusy(true); setError(''); setNotice('')
    try {
      await api.put(`/payroll/cycles/${selectedPeriod}/stage`, { stage: nextStage })
      setNotice(`Cycle moved to ${nextStage.replaceAll('_', ' ').toLowerCase()}.`)
      await loadData()
      await loadCycleControls()
    } catch (requestError) {
      setError(errorMessage(requestError))
    } finally { setBusy(false) }
  }

  const saveDeadlines = async event => {
    event.preventDefault()
    setDeadlineMessage('')
    try {
      await api.put(`/payroll/cycles/${selectedPeriod}/deadlines`, {
        approval_deadline: approvalDeadline || null,
        posting_deadline: postingDeadline || null,
      })
      setDeadlineMessage('Cycle deadlines saved and recorded in the audit log.')
      await loadData()
      await loadCycleControls()
    } catch (requestError) { setDeadlineMessage(errorMessage(requestError)) }
  }

  const saveReconciliation = async () => {
    if (!reconciliationPreview) return
    setBusy(true); setError('')
    try {
      await api.put(`/payroll/cycles/${selectedPeriod}/reconciliations/${reconciliationPreview.type}`, {
        register_total: reconciliationPreview.registerTotal,
        source_total: reconciliationPreview.sourceTotal,
        source_filename: reconciliationPreview.filename,
        discrepancies: reconciliationPreview.discrepancies,
      })
      setNotice(`${reconciliationPreview.type === 'bank' ? 'Bank' : 'Tax'} reconciliation saved for ${displayPeriod(selectedPeriod)}.`)
      setReconciliationPreview(null)
      await loadCycleControls()
    } catch (requestError) { setError(errorMessage(requestError)) }
    finally { setBusy(false) }
  }

  const compareReconciliationFile = async (type, file) => {
    if (!file) return
    setError('')
    try {
      const text = await file.text()
      const lines = text.trim().split(/\r?\n/).filter(Boolean)
      if (lines.length < 2) throw new Error('The CSV must include a header and at least one employee row.')
      const headers = lines[0].split(',').map(value => value.trim().replace(/^"|"$/g, '').toLowerCase())
      const idColumn = headers.findIndex(value => ['employee_id', 'employee_number', 'employee'].includes(value))
      const amountColumn = headers.findIndex(value => ['amount', 'net_salary', 'paye_tax', 'tax'].includes(value))
      if (idColumn < 0 || amountColumn < 0) throw new Error('CSV needs an employee_id (or employee_number) and amount (or net_salary / paye_tax) column.')
      const sourceValues = new Map()
      for (const line of lines.slice(1)) {
        const columns = line.split(',').map(value => value.trim().replace(/^"|"$/g, '').replaceAll('""', '"'))
        const key = columns[idColumn]
        const value = Number(columns[amountColumn].replaceAll(',', ''))
        if (!key || !Number.isFinite(value)) throw new Error(`Invalid employee or amount on CSV row ${sourceValues.size + 2}.`)
        if (sourceValues.has(key)) throw new Error(`Duplicate employee ${key} in the source file.`)
        sourceValues.set(key, value)
      }
      const registerAmount = item => type === 'bank' ? amount(item.net_salary) : amount(item.paye_tax)
      const registerKey = item => item.employee_number || item.employee_id
      const matchedSources = new Set()
      const discrepancies = []
      for (const item of includedRecords) {
        const key = registerKey(item)
        const sourceKey = sourceValues.has(key) ? key : sourceValues.has(item.employee_id) ? item.employee_id : null
        const source = sourceKey === null ? undefined : sourceValues.get(sourceKey)
        if (source === undefined) {
          discrepancies.push({ employee_id: item.employee_id, employee_number: item.employee_number, employee_name: employeeName(item), register_amount: String(registerAmount(item)), source_amount: null, reason: 'Missing from source file' })
        } else {
          matchedSources.add(sourceKey)
          if (Math.abs(registerAmount(item) - source) >= 0.01) {
            discrepancies.push({ employee_id: item.employee_id, employee_number: item.employee_number, employee_name: employeeName(item), register_amount: String(registerAmount(item)), source_amount: String(source), reason: 'Amount mismatch' })
          }
        }
      }
      for (const [key, value] of sourceValues) {
        if (!matchedSources.has(key) && !includedRecords.some(item => item.employee_id === key)) {
          discrepancies.push({ employee_id: null, employee_number: key, employee_name: 'Unmatched source row', register_amount: null, source_amount: String(value), reason: 'Not in payroll register' })
        }
      }
      if (discrepancies.length > 1000) throw new Error('The file has more than 1,000 discrepancies; please split it before saving.')
      setReconciliationFiles(state => ({ ...state, [type]: file.name }))
      setReconciliationPreview({
        type,
        filename: file.name,
        registerTotal: includedRecords.reduce((sum, item) => sum + registerAmount(item), 0).toFixed(2),
        sourceTotal: [...sourceValues.values()].reduce((sum, value) => sum + value, 0).toFixed(2),
        discrepancies,
      })
    } catch (requestError) {
      setError(requestError.message || errorMessage(requestError))
    }
  }

  const savePaymentElection = async event => {
    event.preventDefault()
    setBusy(true); setElectionMessage('')
    try {
      const { data } = await api.put('/payroll/my-payment-election', electionForm)
      setElectionMessage(`Saved. This account election is effective for ${displayPeriod(data.effective_period)}. Bank account ending ${data.account_last_four}.`)
      setProfile(current => ({ ...current, bank_name: data.bank_name, account_number: `••••${data.account_last_four}` }))
      setElectionForm(current => ({ ...current, account_number: '' }))
    } catch (requestError) { setElectionMessage(errorMessage(requestError)) }
    finally { setBusy(false) }
  }

  const openEmployeePayslip = item => setSelectedEmployee(item)
  const revealDiscrepancyEmployee = item => {
    const payrollRecord = includedRecords.find(record => record.employee_id === item.employee_id)
    if (payrollRecord) setSelectedEmployee(payrollRecord)
  }
  const exportCompliance = () => downloadCsv(
    `payroll-compliance-${selectedPeriod}.csv`,
    ['Employee', 'Employee number', 'Department', 'Exception'],
    filteredCompliance.map(item => [item.employee_name, item.employee_number, getDepartmentName(item.department_name) || 'Unassigned department', item.field]),
  )

  const navTabs = hasPayrollControl
    ? ['Overview', 'Exceptions', 'Reconciliation', 'Cycle & audit', 'Trends', 'Payslips']
    : isTeamRole
      ? ['Team overview', 'Exceptions', 'Trends', 'Payslips']
      : ['My payslips', 'Payment elections']

  return (
    <section className="payroll-page">
      <header className="payroll-heading">
        <div>
          <span className="payroll-eyebrow">{isSelfService ? 'EMPLOYEE SELF-SERVICE' : 'PAYROLL CONTROL CENTER'}</span>
          <h1>{isSelfService ? 'My pay' : 'Payroll'}</h1>
          <p>{isSelfService ? 'Review your payslips, compare periods, and manage your payment election.' : 'Control, reconcile, and audit each payroll cycle.'}</p>
        </div>
        <div className="payroll-cycle-tools">
          <label htmlFor="payroll-period">Pay cycle</label>
          <select id="payroll-period" value={selectedPeriod} onChange={event => setSelectedPeriod(event.target.value)}>
            {!periods.includes(selectedPeriod) && <option value={selectedPeriod}>{displayPeriod(selectedPeriod)}</option>}
            {periods.map(period => <option key={period} value={period}>{displayPeriod(period)}</option>)}
          </select>
          <button type="button" className="payroll-icon-button" onClick={loadData} disabled={loading} aria-label="Refresh payroll data"><RefreshCw size={17} /></button>
          {hasPayrollControl && <button type="button" className="payroll-primary" onClick={runPayroll} disabled={busy || loading || activeCycle.stage !== 'DATA_ENTRY'}><Banknote size={16} />{busy ? 'Working…' : 'Run cycle'}</button>}
        </div>
      </header>

      {error && <div className="payroll-alert error" role="alert"><CircleAlert size={17} />{error}</div>}
      {notice && <div className="payroll-alert success" role="status"><Check size={17} />{notice}</div>}
      {loading ? <div className="payroll-loading"><RefreshCw size={19} /> Loading payroll cycle…</div> : (
        <>
          <nav className="payroll-tabs" aria-label="Payroll sections">
            {navTabs.map(tab => <button key={tab} type="button" className={activeTab === tab ? 'active' : ''} onClick={() => setActiveTab(tab)}>{tab}</button>)}
          </nav>

          {(activeTab === 'Overview' || activeTab === 'Team overview') && (
            <>
              {(hasPayrollControl || isTeamRole) && (
                <div className="payroll-stage-strip">
                  {['DATA_ENTRY', 'APPROVAL', 'POSTING', 'POSTED'].map((stage, index) => (
                    <div className={`payroll-stage ${activeCycle.stage === stage ? 'current' : ['DATA_ENTRY', 'APPROVAL', 'POSTING', 'POSTED'].indexOf(activeCycle.stage) > index ? 'complete' : ''}`} key={stage}>
                      <span>{index + 1}</span><div><strong>{stage.replaceAll('_', ' ')}</strong><small>{['Build and validate register', 'Payroll approver review', 'Finance funding and posting', 'Cycle closed'][index]}</small></div>
                    </div>
                  ))}
                </div>
              )}
              {hasPayrollControl && (
                <div className="payroll-metric-grid">
                  <Metric label="Gross pay" value={formatMoney(totals.gross)} note={`${includedRecords.length} valid payroll record(s)`} icon={Wallet} />
                  <Metric label="Employee deductions" value={formatMoney(totals.employeeDeductions)} note="NSSF deductions recorded" icon={ArrowDownRight} tone="amber" onClick={() => setShowPayrollDetails(true)} />
                  <Metric label="Employer contributions" value={formatMoney(totals.employer)} note="Pension / social contributions" icon={ArrowUpRight} tone="violet" onClick={() => setShowPayrollDetails(true)} />
                  <Metric label="Taxes" value={formatMoney(totals.taxes)} note="PAYE tax withheld" icon={FileCheck2} tone="blue" onClick={() => setShowPayrollDetails(true)} />
                  <Metric label="Net pay" value={formatMoney(totals.net)} note="Employee take-home" icon={Banknote} tone="green" onClick={() => setShowPayrollDetails(true)} />
                </div>
              )}
              <div className="payroll-grid two">
                <section className="payroll-panel">
                  <SectionTitle eyebrow="RECONCILIATION" title="Gross to net" description="Net = gross − employee deductions − taxes." />
                  {hasPayrollControl ? (
                    <>
                      <div className={`payroll-reconcile-callout ${reconciliationPass ? 'pass' : 'fail'}`}>
                        {reconciliationPass ? <ShieldCheck size={20} /> : <AlertTriangle size={20} />}
                        <div><strong>{reconciliationPass ? 'Reconciliation passed' : 'Reconciliation failed'}</strong><small>{reconciliationPass ? 'Payroll register totals balance.' : `Difference: ${formatMoney(totals.gross - totals.employeeDeductions - totals.taxes - totals.net)}`}</small></div>
                        <StateBadge value={reconciliationPass ? 'PASS' : 'FAIL'} />
                      </div>
                      <div className="payroll-breakdown">
                        {[['Gross pay', totals.gross], ['Employee deductions · NSSF', totals.employeeDeductions], ['Taxes · PAYE', totals.taxes], ['Net pay', totals.net]].map(([label, value], index) => <div key={label} className={index === 3 ? 'emphasis' : ''}><span>{label}</span><strong>{formatMoney(value)}</strong></div>)}
                      </div>
                      <button className="payroll-text-button" type="button" onClick={() => setShowPayrollDetails(!showPayrollDetails)}>{showPayrollDetails ? 'Hide' : 'Drill into'} employee payroll details {showPayrollDetails ? <ChevronUp size={15} /> : <ChevronDown size={15} />}</button>
                      {showPayrollDetails && <PayrollRecordTable rows={includedRecords} onEmployeeClick={openEmployeePayslip} />}
                    </>
                  ) : <p className="payroll-muted">Financial control totals are available to payroll and finance roles only.</p>}
                </section>

                <section className="payroll-panel">
                  <SectionTitle eyebrow="EMPLOYER COST" title="Total labor cost" description="Wages + employer contributions + bonuses + overtime." />
                  {hasPayrollControl ? (
                    <>
                      <strong className="payroll-labor-total">{formatMoney(costBreakdown.total)}</strong>
                      <button className="payroll-text-button" type="button" onClick={() => setShowLaborComponents(!showLaborComponents)}>{showLaborComponents ? 'Hide' : 'Expand'} cost components {showLaborComponents ? <ChevronUp size={15} /> : <ChevronDown size={15} />}</button>
                      {showLaborComponents && <div className="payroll-breakdown">
                        {[['Wages incl. retro pay', costBreakdown.wages], ['Employer pension', totals.employerPension], ['Employer social contributions', totals.employerSocial], ['Other employer contributions', totals.employerOther], ['Bonuses', costBreakdown.bonus], ['Overtime pay', costBreakdown.overtime]].map(([label, value]) => <div key={label}><span>{label}</span><strong>{formatMoney(value)}</strong></div>)}
                      </div>}
                      <p className="payroll-data-note">Components are read from the payroll register. Unrecorded components remain UGX 0; no contribution rate or bonus is inferred.</p>
                    </>
                  ) : <p className="payroll-muted">Labor cost totals are available to payroll and finance roles only.</p>}
                </section>
              </div>

              {hasPayrollControl && (
                <section className="payroll-panel">
                  <SectionTitle eyebrow="COST ALLOCATION" title="Cost distribution" description="Group actual payroll cost and compare it with your entered cycle budget." action={<div className="payroll-inline-tools"><label htmlFor="cost-group">Group by</label><select id="cost-group" value={grouping} onChange={event => { setGrouping(event.target.value); setSelectedGroup('') }}><option value="department">Department</option><option value="cost_center">Cost center</option><option value="location">Location</option></select></div>} />
                  {grouping === 'cost_center' && <p className="payroll-data-note">Employees without a configured cost center are grouped as unassigned; cost centers are maintained in the employee profile.</p>}
                  <div className="payroll-table-wrap"><table className="payroll-table"><thead><tr><th>Group</th><th>Headcount</th><th>Actual cost</th><th>Cycle budget (UGX)</th><th>Variance</th><th>Drill-down</th></tr></thead><tbody>
                    {costGroups.map(row => {
                      const budget = Number(budgetInputs[`${selectedPeriod}:${grouping}:${row.name}`] || 0)
                      const variance = budget ? row.cost - budget : null
                      return <tr key={row.name}><td><strong>{row.name}</strong></td><td>{row.people}</td><td>{formatMoney(row.cost)}</td><td><input aria-label={`${row.name} cycle budget`} className="payroll-budget-input" type="number" min="0" value={budgetInputs[`${selectedPeriod}:${grouping}:${row.name}`] || ''} placeholder="Not set" onChange={event => setBudgetInputs(current => ({ ...current, [`${selectedPeriod}:${grouping}:${row.name}`]: event.target.value }))} /></td><td>{variance === null ? <span className="payroll-muted">Set budget</span> : <strong className={variance > 0 ? 'payroll-negative' : 'payroll-positive'}>{variance > 0 ? '+' : ''}{formatMoney(variance)}</strong>}</td><td><button className="payroll-text-button" type="button" onClick={() => setSelectedGroup(selectedGroup === row.name ? '' : row.name)}>{selectedGroup === row.name ? 'Hide people' : 'View people'}</button></td></tr>
                    })}
                    {costGroups.length === 0 && <tr><td colSpan="6" className="payroll-empty">No valid mapped payroll records in this cycle.</td></tr>}
                  </tbody></table></div>
                  <p className="payroll-data-note">Budgets entered here are session-only. Persisted budget baselines are not configured.</p>
                  {selectedGroup && <PayrollRecordTable rows={costGroups.find(row => row.name === selectedGroup)?.employees || []} onEmployeeClick={openEmployeePayslip} />}
                </section>
              )}

              <div className="payroll-metric-grid compact">
                <Metric label="Zero / null net alerts" value={selectedNetAlerts.length} note={activeCycle.stage === 'DATA_ENTRY' ? `${preRunMissing.length} missing cycle records before run` : 'Employees with zero or missing net pay'} icon={AlertTriangle} tone={selectedNetAlerts.length ? 'red' : 'green'} onClick={() => setActiveTab('Exceptions')} />
                <Metric label="Compliance exceptions" value={complianceExceptions.length} note="Tax, jurisdiction, and department checks" icon={FileCheck2} tone={complianceExceptions.length ? 'amber' : 'green'} onClick={() => setActiveTab('Exceptions')} />
                <Metric label="Overtime flags" value={overtimeByEmployee.length} note={`Above ${hoursThreshold} overtime hours this cycle`} icon={Clock3} tone="violet" onClick={() => setActiveTab('Exceptions')} />
                <Metric label="Unmapped pay codes" value={unmappedPayCodes.length} note="Records missing a reporting category" icon={CircleAlert} tone={unmappedPayCodes.length ? 'red' : 'green'} onClick={() => setActiveTab('Exceptions')} />
              </div>
              {selectedEmployee && <EmployeeDetail item={selectedEmployee} onClose={() => setSelectedEmployee(null)} />}
            </>
          )}

          {activeTab === 'Exceptions' && (
            <div className="payroll-stack">
              <section className="payroll-panel">
                <SectionTitle eyebrow="PAY REVIEW" title="Zero / null net pay" description="Alerts are evaluated from the selected cycle; before the first run, unmatched active employees are shown as missing records." />
                {preRunMissing.length > 0 && <div className="payroll-alert warning"><AlertTriangle size={17} />{preRunMissing.length} active employees do not yet have a payslip for this cycle.</div>}
                <PayrollRecordTable rows={selectedNetAlerts} onEmployeeClick={openEmployeePayslip} />
                {selectedNetAlerts.length === 0 && <p className="payroll-empty">No zero or null net pay amounts in this cycle.</p>}
                {preRunMissing.length > 0 && <div className="payroll-table-wrap"><table className="payroll-table"><thead><tr><th>Employee</th><th>Department</th><th>Issue</th></tr></thead><tbody>{preRunMissing.map(item => <tr key={item.employee_id}><td>{item.employee_name} <small>{item.employee_number}</small></td><td>{getDepartmentName(item.department_name) || 'Unassigned'}</td><td><StateBadge value="NO PAYSLIP YET" /></td></tr>)}</tbody></table></div>}
              </section>

              <section className="payroll-panel">
                <SectionTitle eyebrow="COMPLIANCE" title="Employee compliance exceptions" description="Missing tax IDs/forms, absent or stale jurisdiction addresses, and unmapped departments." action={<button className="payroll-secondary" type="button" onClick={exportCompliance}><Download size={15} />Export CSV</button>} />
                <div className="payroll-toolbar"><label className="payroll-search"><Search size={16} /><input value={complianceSearch} onChange={event => setComplianceSearch(event.target.value)} placeholder="Search employee, ID, department…" /></label>                <select value={complianceFilter} onChange={event => setComplianceFilter(event.target.value)}><option value="all">All exception fields</option><option value="department">Missing department mapping</option><option value="tax_id">Missing tax ID</option><option value="tax_form">Missing tax form</option><option value="address">Missing / outdated jurisdiction</option><option value="address_old">Outdated jurisdiction only</option></select></div>
                <div className="payroll-table-wrap"><table className="payroll-table"><thead><tr><th>Employee</th><th>Department</th><th>Missing / invalid field</th><th>Review status</th></tr></thead><tbody>{filteredCompliance.map((item, index) => <tr key={`${item.employee_id}:${item.key}:${index}`}><td>{item.employee_name}<small>{item.employee_number}</small></td><td>{getDepartmentName(item.department_name) || 'Unassigned'}</td><td><strong>{item.field}</strong></td><td><StateBadge value="ACTION REQUIRED" /></td></tr>)}{filteredCompliance.length === 0 && <tr><td className="payroll-empty" colSpan="4">No compliance exceptions match these filters.</td></tr>}</tbody></table></div>
                {invalidMappingRows.length > 0 && <div className="payroll-alert warning"><AlertTriangle size={17} />{invalidMappingRows.length} payroll record(s) without valid employee or department mapping are excluded from totals.</div>}
                {invalidMappingRows.length > 0 && <PayrollRecordTable rows={invalidMappingRows} onEmployeeClick={openEmployeePayslip} />}
                {unmappedPayCodes.length > 0 && <><div className="payroll-alert warning"><CircleAlert size={17} />{unmappedPayCodes.length} record(s) use pay codes without a reporting category and are excluded from dashboard totals.</div><PayrollRecordTable rows={unmappedPayCodes} onEmployeeClick={openEmployeePayslip} /></>}
              </section>

              <div className="payroll-grid two">
                <section className="payroll-panel">
                  <SectionTitle eyebrow="TIME CONTROL" title="Overtime monitoring" description="Attendance overtime hours compared with the configured cycle threshold." action={<label className="payroll-inline-tools">Threshold <input type="number" min="0" value={hoursThreshold} onChange={event => setHoursThreshold(event.target.value)} /> hrs</label>} />
                  <div className="payroll-table-wrap"><table className="payroll-table"><thead><tr><th>Employee</th><th>Hours</th><th>Threshold</th><th>Source records</th></tr></thead><tbody>{overtimeByEmployee.map(item => <tr key={item.employee_id}><td><button className="payroll-link-button" onClick={() => setSelectedEmployee(item.employee_id)}>{item.employee_name}<small>{item.employee_number}</small></button></td><td><strong className="payroll-negative">{item.hours.toFixed(2)}</strong></td><td>{hoursThreshold} hrs</td><td>{item.sourceRecords.map(source => <span className="payroll-source-chip" key={source.attendance_id}>{source.date}: {amount(source.hours).toFixed(2)}h</span>)}</td></tr>)}{overtimeByEmployee.length === 0 && <tr><td className="payroll-empty" colSpan="4">No employee exceeds {hoursThreshold} overtime hours in this period.</td></tr>}</tbody></table></div>
                </section>
                <section className="payroll-panel">
                  <SectionTitle eyebrow="RETRO REVIEW" title="Retroactive pay" description="Back-pay amount, reason, source, and verification state from the payroll register." />
                  <div className="payroll-table-wrap"><table className="payroll-table"><thead><tr><th>Employee</th><th>Adjustment</th><th>Reason</th><th>Source / verification</th></tr></thead><tbody>{retroRows.map(item => <tr key={item.id}><td><button className="payroll-link-button" onClick={() => openEmployeePayslip(item)}>{employeeName(item)}<small>{item.employee_number}</small></button></td><td>{formatMoney(item.retro_amount)}</td><td>{item.retro_reason || 'Reason not recorded'}</td><td>{item.retro_source || 'Source not recorded'}<small><StateBadge value={item.retro_verified || 'PENDING'} /></small></td></tr>)}{retroRows.length === 0 && <tr><td className="payroll-empty" colSpan="4">No retroactive adjustments recorded for this cycle.</td></tr>}</tbody></table></div>
                </section>
              </div>
              {selectedEmployee && <EmployeeDetail item={displayedEmployee} onClose={() => setSelectedEmployee(null)} />}
            </div>
          )}

          {activeTab === 'Reconciliation' && hasPayrollControl && (
            <div className="payroll-stack">
              <section className="payroll-panel">
                <SectionTitle eyebrow="EXTERNAL FUNDING" title="Payroll register reconciliation" description="Upload CSV files with employee_id (or employee_number) and amount columns. Files are parsed in this browser; only totals and discrepancies are saved." />
                <div className="payroll-grid two">
                  {[['bank', 'Register vs bank disbursement', 'net_salary'], ['tax', 'Register vs tax funding invoice', 'paye_tax']].map(([type, title, amountColumn]) => {
                    const saved = reconciliations[type]
                    return <article className="payroll-recon-card" key={type}>
                      <div className="payroll-recon-heading"><div><h3>{title}</h3><p>Compare employee-level {amountColumn === 'net_salary' ? 'net pay' : 'PAYE tax'} amounts.</p></div><StateBadge value={saved?.status || 'NOT SAVED'} /></div>
                      {saved && <div className="payroll-recon-summary"><span>Register <strong>{formatMoney(saved.details.register_total)}</strong></span><span>Source <strong>{formatMoney(saved.details.source_total)}</strong></span><small>Saved {saved.updated_at ? new Date(saved.updated_at).toLocaleString() : ''}</small></div>}
                      <label className="payroll-upload"><Upload size={18} /><span>{reconciliationFiles[type] || 'Choose a CSV source file'}</span><input type="file" accept=".csv,text/csv" onChange={event => compareReconciliationFile(type, event.target.files?.[0])} /></label>
                      {reconciliationPreview?.type === type && <div className="payroll-recon-preview"><strong>{reconciliationPreview.filename}</strong><span>Register: {formatMoney(reconciliationPreview.registerTotal)}</span><span>Source: {formatMoney(reconciliationPreview.sourceTotal)}</span><StateBadge value={reconciliationPreview.discrepancies.length ? 'MISMATCH' : 'MATCH'} /><button className="payroll-primary" type="button" onClick={saveReconciliation} disabled={busy}>{busy ? 'Saving…' : 'Save reconciliation'}</button></div>}
                      {saved?.details?.discrepancies?.length > 0 && <details className="payroll-discrepancies"><summary>{saved.details.discrepancies.length} discrepancy detail(s)</summary><div className="payroll-table-wrap"><table className="payroll-table"><thead><tr><th>Employee</th><th>Register</th><th>Source</th><th>Reason</th></tr></thead><tbody>{saved.details.discrepancies.map((item, index) => <tr key={`${item.employee_id || item.employee_number}:${index}`}><td>{item.employee_id ? <button className="payroll-link-button" type="button" onClick={() => revealDiscrepancyEmployee(item)}>{item.employee_name || item.employee_number}<small>Open payroll record</small></button> : item.employee_name || item.employee_number}</td><td>{item.register_amount == null ? '—' : formatMoney(item.register_amount)}</td><td>{item.source_amount == null ? '—' : formatMoney(item.source_amount)}</td><td>{item.reason}</td></tr>)}</tbody></table></div></details>}
                    </article>
                  })}
                </div>
              </section>
              {reconciliationPreview && <section className="payroll-panel"><SectionTitle title="Employee discrepancy preview" description={`Review ${reconciliationPreview.discrepancies.length} mismatch(es) before saving.`} /><div className="payroll-table-wrap"><table className="payroll-table"><thead><tr><th>Employee</th><th>Register</th><th>Source</th><th>Reason</th></tr></thead><tbody>{reconciliationPreview.discrepancies.map((item, index) => <tr key={`${item.employee_id || item.employee_number}:${index}`}><td>{item.employee_id ? <button className="payroll-link-button" type="button" onClick={() => revealDiscrepancyEmployee(item)}>{item.employee_name || item.employee_number}<small>Open payroll record</small></button> : item.employee_name || item.employee_number}</td><td>{item.register_amount == null ? '—' : formatMoney(item.register_amount)}</td><td>{item.source_amount == null ? '—' : formatMoney(item.source_amount)}</td><td>{item.reason}</td></tr>)}</tbody></table></div></section>}
              {selectedEmployee && <EmployeeDetail item={selectedEmployee} onClose={() => setSelectedEmployee(null)} />}
            </div>
          )}

          {activeTab === 'Cycle & audit' && hasPayrollControl && (
            <div className="payroll-stack">
              <section className="payroll-panel">
                <SectionTitle eyebrow="APPROVAL GATES" title="Cycle progress and calendar" description={`${displayPeriod(selectedPeriod)} · Current stage ${activeCycle.stage.replaceAll('_', ' ').toLowerCase()}.`} />
                <div className="payroll-stage-actions">
                  {activeCycle.stage === 'DATA_ENTRY' && <button className="payroll-primary" type="button" onClick={() => updateStage('APPROVAL')} disabled={busy || !['HR', 'HR_ADMIN', 'ADMIN', 'MANAGEMENT', 'DEVELOPER'].includes(role)}>Submit for approval</button>}
                  {activeCycle.stage === 'APPROVAL' && <button className="payroll-primary" type="button" onClick={() => updateStage('POSTING')} disabled={busy || !['FINANCE', 'ADMIN', 'MANAGEMENT', 'DEVELOPER'].includes(role) || reconciliations.bank?.status !== 'MATCH' || reconciliations.tax?.status !== 'MATCH'}>Approve &amp; move to posting</button>}
                  {activeCycle.stage === 'POSTING' && <button className="payroll-primary" type="button" onClick={() => updateStage('POSTED')} disabled={busy || !['FINANCE', 'ADMIN', 'MANAGEMENT', 'DEVELOPER'].includes(role)}>Mark posted</button>}
                  {activeCycle.stage === 'POSTED' && <StateBadge value="POSTED" />}
                  {activeCycle.stage === 'APPROVAL' && reconciliations.bank?.status !== 'MATCH' && <small className="payroll-inline-warning">Both saved reconciliations must match before approval.</small>}
                </div>
                <div className="payroll-deadline-grid">
                  {[['Approval deadline', activeCycle.approval_deadline], ['Posting deadline', activeCycle.posting_deadline]].map(([label, value]) => <div className="payroll-deadline" key={label}><CalendarDays size={18} /><div><span>{label}</span><strong>{value ? new Date(`${value}T00:00:00`).toLocaleDateString() : 'Not configured'}</strong></div></div>)}
                </div>
                <PayrollDeadlineCalendar period={selectedPeriod} approvalDeadline={activeCycle.approval_deadline} postingDeadline={activeCycle.posting_deadline} />
                <form className="payroll-deadline-form" onSubmit={saveDeadlines}>
                  <label>Set approval deadline<input type="date" value={approvalDeadline} onChange={event => setApprovalDeadline(event.target.value)} /></label>
                  <label>Set posting deadline<input type="date" value={postingDeadline} onChange={event => setPostingDeadline(event.target.value)} /></label>
                  <button type="submit" className="payroll-secondary"><CalendarDays size={15} />Save deadlines</button>
                </form>
                {deadlineMessage && <p className="payroll-inline-message" role="status">{deadlineMessage}</p>}
                <div className="payroll-approval-note"><LockKeyhole size={17} /><span>Approval is limited to payroll approver roles. Posting requires Finance (or an elevated admin role) and both matching reconciliations.</span></div>
              </section>

              <section className="payroll-panel">
                <SectionTitle eyebrow="IMMUTABLE CYCLE LOG" title="Audit trail" description="Payroll generation, stage changes, deadlines, reconciliation saves, and payment election changes are timestamped with before / after values." />
                <div className="payroll-toolbar"><label className="payroll-search"><Search size={16} /><input value={auditSearch} onChange={event => setAuditSearch(event.target.value)} placeholder="Search actor, action, or value…" /></label><select value={auditType} onChange={event => setAuditType(event.target.value)}><option value="">All action types</option>{[...new Set(auditRows.map(item => item.action_type))].map(type => <option value={type} key={type}>{type}</option>)}</select></div>
                <div className="payroll-table-wrap"><table className="payroll-table"><thead><tr><th>Timestamp</th><th>User</th><th>Action</th><th>Target</th><th>Before</th><th>After</th></tr></thead><tbody>{auditRows.map(row => <tr key={row.id}><td>{row.timestamp ? new Date(row.timestamp).toLocaleString() : '—'}</td><td>{row.user}</td><td><StateBadge value={row.action_type} /></td><td>{row.target}</td><td>{row.before_value || '—'}</td><td>{row.after_value || '—'}</td></tr>)}{auditRows.length === 0 && <tr><td className="payroll-empty" colSpan="6">No audit entries for this cycle yet.</td></tr>}</tbody></table></div>
                <div className="payroll-approval-note"><ShieldCheck size={17} /><span>Audit events cannot be edited or deleted through the application. Access uses the signed-in JWT session.</span></div>
              </section>
            </div>
          )}

          {activeTab === 'Trends' && (
            <section className="payroll-panel">
              <SectionTitle eyebrow="ANALYTICS" title="Pay period trends" description="Gross, net, and PAYE totals by cycle, with cost anomaly highlighting." action={<div className="payroll-inline-tools"><label htmlFor="trend-range">Cycles</label><select id="trend-range" value={trendRange} onChange={event => setTrendRange(event.target.value)}><option value="3">Last 3</option><option value="6">Last 6</option><option value="12">Last 12</option></select><label htmlFor="anomaly-threshold">Spike threshold</label><input id="anomaly-threshold" type="number" min="1" value={anomalyThreshold} onChange={event => setAnomalyThreshold(event.target.value)} />%</div>} />
              <div className="payroll-grid two"><div className="payroll-trend-panel"><h3>Spend vs paid headcount</h3><LineChart rows={trendRows} threshold={Number(anomalyThreshold)} activeEmployees={activeHeadcount} /></div><div className="payroll-trend-panel"><h3>Gross, net &amp; tax by cycle</h3><PayrollTotalsChart rows={trendRows} /><div className="payroll-table-wrap"><table className="payroll-table"><thead><tr><th>Cycle</th><th>Gross</th><th>Net</th><th>Tax</th><th>Paid people</th></tr></thead><tbody>{trendRows.map(row => <tr key={row.period}><td>{displayPeriod(row.period)}</td><td>{formatMoney(row.gross)}</td><td>{formatMoney(row.net)}</td><td>{formatMoney(row.tax)}</td><td>{row.count}</td></tr>)}{trendRows.length === 0 && <tr><td colSpan="5" className="payroll-empty">No historical cycle records.</td></tr>}</tbody></table></div><p className="payroll-data-note">Headcount reflects valid paid records per cycle; historical active-roster snapshots are not stored.</p></div></div>
            </section>
          )}

          {activeTab === 'Payslips' && (
            <section className="payroll-panel"><SectionTitle eyebrow="PAYROLL REGISTER" title="Employee payslips" description={`${displayPeriod(selectedPeriod)} · Select an employee row to inspect the payroll breakdown.`} /><PayrollRecordTable rows={cycleRecords} onEmployeeClick={openEmployeePayslip} />{selectedEmployee && <EmployeeDetail item={displayedEmployee} onClose={() => setSelectedEmployee(null)} />}</section>
          )}
          {activeTab === 'Team overview' && (
            <section className="payroll-panel"><SectionTitle eyebrow="TEAM PAYROLL" title="Department payroll" description={`Only team records for ${displayPeriod(selectedPeriod)} are returned by the payroll API.`} /><PayrollRecordTable rows={includedRecords} onEmployeeClick={openEmployeePayslip} />{selectedEmployee && <EmployeeDetail item={displayedEmployee} onClose={() => setSelectedEmployee(null)} />}</section>
          )}
          {activeTab === 'My payslips' && (
            <>
              <section className="payroll-panel"><SectionTitle eyebrow="MY PAY HISTORY" title="Payslips" description="Your personal salary, statutory deductions, and period history." /><PayrollRecordTable rows={records} onEmployeeClick={openEmployeePayslip} /></section>
              {records.length > 1 && <section className="payroll-panel"><SectionTitle title="Period comparison" description="Compare your latest two payslips." /><div className="payroll-comparison">{records.slice(0, 2).map(item => <article key={item.id}><span>{displayPeriod(item.pay_period)}</span><strong>{formatMoney(item.gross_salary)} gross</strong><small>{formatMoney(item.net_salary)} net · {formatMoney(amount(item.paye_tax) + amount(item.nssf_deduction))} deductions</small></article>)}</div></section>}
            </>
          )}
          {activeTab === 'Payment elections' && (
            <section className="payroll-panel"><SectionTitle eyebrow="PAYMENT METHOD" title="Payment election" description="Changes are logged and apply to the next monthly cycle." /><div className="payroll-account-note"><LockKeyhole size={18} /><span>Current account: {profile?.bank_name || 'Bank not set'} · {profile?.account_number ? `••••${String(profile.account_number).slice(-4)}` : 'No account on file'}</span></div><form className="payroll-election-form" onSubmit={savePaymentElection}><label>Bank name<input required maxLength="100" value={electionForm.bank_name} onChange={event => setElectionForm(current => ({ ...current, bank_name: event.target.value }))} /></label><label>New account number<input required minLength="6" maxLength="50" autoComplete="off" value={electionForm.account_number} onChange={event => setElectionForm(current => ({ ...current, account_number: event.target.value }))} /></label><button className="payroll-primary" type="submit" disabled={busy}><Wallet size={16} />Save payment election</button></form>{electionMessage && <p className="payroll-inline-message" role="status">{electionMessage}</p>}</section>
          )}
        </>
      )}
    </section>
  )
}

function PayrollRecordTable({ rows, onEmployeeClick }) {
  return <div className="payroll-table-wrap"><table className="payroll-table"><thead><tr><th>Employee</th><th>Gross</th><th>Taxes</th><th>Employee deductions</th><th>Employer contributions</th><th>Net pay</th><th>Code mapping</th></tr></thead><tbody>
    {rows.map(item => <tr key={item.id}><td><button className="payroll-link-button" type="button" onClick={() => onEmployeeClick(item)}>{employeeName(item)}<small>{item.employee_number || item.employee_id}</small></button></td><td>{formatMoney(item.gross_salary)}</td><td>{formatMoney(item.paye_tax)}</td><td>{formatMoney(item.nssf_deduction)}</td><td>{formatMoney(amount(item.employer_contribution) + amount(item.employer_pension) + amount(item.employer_social_contribution))}</td><td className="payroll-net">{formatMoney(item.net_salary)}</td><td>{item.mappedCategory || <StateBadge value="UNMAPPED" />}</td></tr>)}
    {rows.length === 0 && <tr><td colSpan="7" className="payroll-empty">No payroll records for this cycle.</td></tr>}
  </tbody></table></div>
}

function EmployeeDetail({ item, onClose }) {
  if (!item) return <div className="payroll-alert warning"><AlertTriangle size={17} />The selected payroll record has no employee mapping and is excluded from financial totals.</div>
  return <div className="payroll-employee-detail"><div><div><span className="payroll-eyebrow">EMPLOYEE PAYROLL RECORD</span><h3>{employeeName(item)}</h3><p>{item.employee_number} · {getDepartmentName(item.department_name) || 'Department not mapped'} · {item.pay_period}</p></div><button className="payroll-secondary" type="button" onClick={onClose}>Close</button></div><div className="payroll-detail-grid">{[['Employee ID', item.employee_id], ['Pay code', item.pay_code || 'BASE_WAGES'], ['Gross', formatMoney(item.gross_salary)], ['PAYE tax', formatMoney(item.paye_tax)], ['NSSF deduction', formatMoney(item.nssf_deduction)], ['Employer pension', formatMoney(item.employer_pension)], ['Employer social contributions', formatMoney(item.employer_social_contribution)], ['Other employer contribution', formatMoney(item.employer_contribution)], ['Bonus', formatMoney(item.bonus_amount)], ['Overtime', formatMoney(item.overtime_amount)], ['Retro adjustment', formatMoney(item.retro_amount)], ['Retro reason', item.retro_reason || 'Not recorded'], ['Retro source', item.retro_source || 'Not recorded'], ['Back-pay verification', item.retro_verified || 'PENDING']].map(([label, value]) => <div key={label}><span>{label}</span><strong>{value}</strong></div>)}</div></div>
}
