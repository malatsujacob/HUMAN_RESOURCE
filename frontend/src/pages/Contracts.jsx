import { useCallback, useEffect, useState } from 'react'
import axios from 'axios'

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api'

function getErrorMessage(error) {
  const detail = error.response?.data?.detail
  if (Array.isArray(detail)) {
    const messages = detail.map((item) => item.msg).filter(Boolean).join('; ')
    if (messages) return messages
  }
  return detail || error.message || 'Unable to load contracts.'
}

function Contracts() {
  const [employees, setEmployees] = useState([])
  const [contracts, setContracts] = useState([])
  const [loading, setLoading] = useState(true)
  const [submitting, setSubmitting] = useState(false)
  const [activatingId, setActivatingId] = useState('')
  const [error, setError] = useState('')
  const [success, setSuccess] = useState('')

  const loadData = useCallback(async () => {
    const token = window.localStorage.getItem('access_token')
    const headers = token ? { Authorization: `Bearer ${token}` } : {}
    const [employeeResponse, contractResponse] = await Promise.all([
      axios.get(`${API_BASE_URL}/employees/`, { headers }),
      axios.get(`${API_BASE_URL}/contracts`, { headers }),
    ])
    setEmployees(
      employeeResponse.data.filter(
        (employee) => (employee.status || '').toUpperCase() === 'ACTIVE',
      ),
    )
    setContracts(contractResponse.data)
  }, [])

  useEffect(() => {
    let active = true
    async function fetchData() {
      try {
        await loadData()
      } catch (requestError) {
        if (active) setError(getErrorMessage(requestError))
      } finally {
        if (active) setLoading(false)
      }
    }
    fetchData()
    return () => {
      active = false
    }
  }, [loadData])

  async function handleSubmit(event) {
    event.preventDefault()
    setSubmitting(true)
    setError('')
    setSuccess('')

    const form = event.currentTarget
    const formData = new FormData(event.currentTarget)
    const token = window.localStorage.getItem('access_token')
    const headers = token ? { Authorization: `Bearer ${token}` } : {}

    try {
      await axios.post(
        `${API_BASE_URL}/contracts/`,
        {
          employee_id: formData.get('employee_id'),
          contract_type: formData.get('contract_type'),
          start_date: formData.get('start_date'),
          end_date: formData.get('end_date') || null,
          base_salary: Number(formData.get('base_salary')),
        },
        { headers },
      )
      form.reset()
      setSuccess('Contract created as a draft.')
      await loadData()
    } catch (requestError) {
      setError(getErrorMessage(requestError))
    } finally {
      setSubmitting(false)
    }
  }

  async function handleActivate(contractId) {
    setActivatingId(contractId)
    setError('')
    setSuccess('')
    const token = window.localStorage.getItem('access_token')
    const headers = token ? { Authorization: `Bearer ${token}` } : {}

    try {
      await axios.put(`${API_BASE_URL}/contracts/${contractId}/activate`, {}, { headers })
      setSuccess('Contract activated.')
      await loadData()
    } catch (requestError) {
      setError(getErrorMessage(requestError))
    } finally {
      setActivatingId('')
    }
  }

  const employeesById = new Map(employees.map((employee) => [employee.id, employee]))

  return (
    <section>
      <div className="page-heading">
        <div>
          <p className="eyebrow">PEOPLE &amp; CULTURE</p>
          <h1>Contracts</h1>
          <p className="heading-subtitle">Create and manage employee contracts.</p>
        </div>
      </div>

      {error && <p className="form-message error" role="alert">{error}</p>}
      {success && <p className="form-message success" role="status">{success}</p>}

      <section className="panel contract-form-panel">
        <h2>Generate Contract</h2>
        <form className="contract-form" onSubmit={handleSubmit}>
          <div className="input-group">
            <label htmlFor="contract-employee">Employee</label>
            <select id="contract-employee" name="employee_id" defaultValue="" required>
              <option value="" disabled>Select an active employee</option>
              {employees.map((employee) => (
                <option key={employee.id} value={employee.id}>
                  {employee.first_name} {employee.last_name} ({employee.employee_number})
                </option>
              ))}
            </select>
            {!loading && employees.length === 0 && (
              <small>No active employees are available.</small>
            )}
          </div>
          <div className="contract-field-grid">
            <div className="input-group">
              <label htmlFor="contract-type">Contract Type</label>
              <select id="contract-type" name="contract_type" defaultValue="Permanent" required>
                <option value="Permanent">Permanent</option>
                <option value="Fixed-Term">Fixed-Term</option>
              </select>
            </div>
            <div className="input-group">
              <label htmlFor="contract-salary">Base Salary</label>
              <input
                id="contract-salary"
                name="base_salary"
                type="number"
                min="0.01"
                step="0.01"
                required
              />
            </div>
            <div className="input-group">
              <label htmlFor="contract-start">Start Date</label>
              <input id="contract-start" name="start_date" type="date" required />
            </div>
            <div className="input-group">
              <label htmlFor="contract-end">End Date (optional)</label>
              <input id="contract-end" name="end_date" type="date" />
            </div>
          </div>
          <button
            className="btn-primary"
            type="submit"
            disabled={submitting || loading || employees.length === 0}
          >
            {submitting ? 'Generating…' : 'Generate Contract'}
          </button>
        </form>
      </section>

      <section className="panel contracts-list-panel">
        <div className="panel-heading">
          <div>
            <h2>All Contracts</h2>
            <p>Draft and active employee contracts.</p>
          </div>
          <button
            className="refresh-button"
            type="button"
            onClick={async () => {
              setError('')
              try {
                await loadData()
              } catch (requestError) {
                setError(getErrorMessage(requestError))
              }
            }}
          >
            Refresh
          </button>
        </div>

        {loading ? (
          <p role="status">Loading contracts…</p>
        ) : contracts.length === 0 ? (
          <p>No contracts found.</p>
        ) : (
          <div className="table-container">
            <table>
              <thead>
                <tr>
                  <th>Employee</th>
                  <th>Contract Type</th>
                  <th>Start Date</th>
                  <th>End Date</th>
                  <th>Base Salary</th>
                  <th>Status</th>
                  <th>Action</th>
                </tr>
              </thead>
              <tbody>
                {contracts.map((contract) => {
                  const employee = employeesById.get(contract.employee_id)
                  return (
                    <tr key={contract.id}>
                      <td>
                        {employee
                          ? `${employee.first_name} ${employee.last_name}`
                          : contract.employee_id}
                      </td>
                      <td>{contract.contract_type}</td>
                      <td>{contract.start_date}</td>
                      <td>{contract.end_date || '—'}</td>
                      <td>{Number(contract.base_salary).toLocaleString()}</td>
                      <td>{contract.status}</td>
                      <td>
                        {contract.status !== 'ACTIVE' && (
                          <button
                            className="btn-primary"
                            type="button"
                            disabled={activatingId === contract.id}
                            onClick={() => handleActivate(contract.id)}
                          >
                            {activatingId === contract.id ? 'Activating…' : 'Activate Contract'}
                          </button>
                        )}
                      </td>
                    </tr>
                  )
                })}
              </tbody>
            </table>
          </div>
        )}
      </section>
    </section>
  )
}

export default Contracts
