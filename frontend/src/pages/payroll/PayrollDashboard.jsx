import { useCallback, useEffect, useMemo, useState } from 'react'
import {
  generatePayroll,
  getCompanyPayslips,
  getMyPayslips,
  getPayrollError,
} from '../../api/payroll.js'
import './Payroll.css'

const COMPANY_PAYROLL_ROLES = new Set(['HR', 'HR_ADMIN', 'FINANCE', 'MANAGEMENT'])

function formatCurrency(value) {
  return new Intl.NumberFormat(undefined, {
    style: 'currency',
    currency: 'UGX',
    maximumFractionDigits: 2,
  }).format(Number(value || 0))
}

function PayslipTable({ payslips, loading, companyView }) {
  if (loading) {
    return <p className="payroll-message" role="status">Loading payslips…</p>
  }
  if (payslips.length === 0) {
    return <p className="payroll-message">No payslips are available yet.</p>
  }

  return (
    <div className="payroll-table-wrap">
      <table className="payroll-table">
        <thead>
          <tr>
            {companyView && <th>Employee ID</th>}
            <th>Pay period</th>
            <th>Gross salary</th>
            <th>PAYE tax</th>
            <th>NSSF deduction</th>
            <th>Net salary</th>
          </tr>
        </thead>
        <tbody>
          {payslips.map((payslip) => (
            <tr key={payslip.id}>
              {companyView && <td>{payslip.employee_id}</td>}
              <td>{payslip.pay_period}</td>
              <td>{formatCurrency(payslip.gross_salary)}</td>
              <td>{formatCurrency(payslip.paye_tax)}</td>
              <td>{formatCurrency(payslip.nssf_deduction)}</td>
              <td className="payroll-net">{formatCurrency(payslip.net_salary)}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}

function PayrollDashboard() {
  const role = (window.localStorage.getItem('role') || '').toUpperCase()
  const canManagePayroll = COMPANY_PAYROLL_ROLES.has(role)
  const [payslips, setPayslips] = useState([])
  const [loading, setLoading] = useState(true)
  const [generating, setGenerating] = useState(false)
  const [error, setError] = useState('')
  const [notice, setNotice] = useState('')

  const loadPayslips = useCallback(async () => {
    setError('')
    try {
      setPayslips(
        canManagePayroll ? await getCompanyPayslips() : await getMyPayslips(),
      )
    } catch (requestError) {
      setError(getPayrollError(requestError))
    } finally {
      setLoading(false)
    }
  }, [canManagePayroll])

  useEffect(() => {
    loadPayslips()
  }, [loadPayslips])

  const currentPayPeriod = useMemo(() => {
    const today = new Date()
    return `${today.getFullYear()}-${String(today.getMonth() + 1).padStart(2, '0')}`
  }, [])

  async function handleGeneratePayroll() {
    setGenerating(true)
    setError('')
    setNotice('')
    try {
      const result = await generatePayroll(currentPayPeriod)
      setNotice(
        `Payroll generated for ${result.pay_period}: ${result.generated_count} payslip(s) created, ${result.skipped_count} already existed.`,
      )
      await loadPayslips()
    } catch (requestError) {
      setError(getPayrollError(requestError))
    } finally {
      setGenerating(false)
    }
  }

  return (
    <section className="payroll-page">
      <header className="payroll-heading">
        <div>
          <p className="eyebrow">COMPENSATION</p>
          <h1>Payroll</h1>
          <p>{canManagePayroll ? 'Review company payslips and run monthly payroll.' : 'Review your personal payslips.'}</p>
        </div>
        {canManagePayroll && (
          <button
            className="btn-primary"
            type="button"
            onClick={handleGeneratePayroll}
            disabled={generating}
          >
            {generating ? 'Generating…' : `Run Payroll for Current Month (${currentPayPeriod})`}
          </button>
        )}
      </header>

      {error && <p className="payroll-alert error" role="alert">{error}</p>}
      {notice && <p className="payroll-alert success" role="status">{notice}</p>}

      <section className="payroll-panel">
        <div className="payroll-section-heading">
          <div>
            <h2>{canManagePayroll ? 'Company payslips' : 'My payslips'}</h2>
            <p>{canManagePayroll ? 'Payslips across all available pay periods.' : 'Your salary and deductions by pay period.'}</p>
          </div>
          <button className="payroll-refresh" type="button" onClick={loadPayslips} disabled={loading}>
            Refresh
          </button>
        </div>
        <PayslipTable
          payslips={payslips}
          loading={loading}
          companyView={canManagePayroll}
        />
      </section>
    </section>
  )
}

export default PayrollDashboard
