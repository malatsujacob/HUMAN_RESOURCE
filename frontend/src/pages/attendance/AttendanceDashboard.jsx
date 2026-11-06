import { useCallback, useEffect, useMemo, useState } from 'react'
import { checkIn, checkOut, getAttendance, getAttendanceError } from '../../api/attendance.js'
import AttendanceHistory from './AttendanceHistory.jsx'
import './Attendance.css'

function AttendanceDashboard() {
  const [records, setRecords] = useState([])
  const [loading, setLoading] = useState(true)
  const [working, setWorking] = useState(false)
  const [error, setError] = useState('')
  const [notice, setNotice] = useState('')

  const loadRecords = useCallback(async () => {
    setError('')
    try {
      setRecords(await getAttendance())
    } catch (requestError) {
      setError(getAttendanceError(requestError))
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    loadRecords()
  }, [loadRecords])

  const today = new Date().toLocaleDateString('en-CA')
  const todayRecord = useMemo(
    () => records.find((record) => record.date === today),
    [records, today],
  )

  async function recordTime(action) {
    setWorking(true)
    setError('')
    setNotice('')
    try {
      await action()
      setNotice(action === checkIn ? 'You are checked in.' : 'You are checked out.')
      await loadRecords()
    } catch (requestError) {
      setError(getAttendanceError(requestError))
    } finally {
      setWorking(false)
    }
  }

  return (
    <section className="module-page">
      <header className="module-heading">
        <div>
          <p className="eyebrow">TIME &amp; ATTENDANCE</p>
          <h1>Attendance</h1>
          <p>Record today’s attendance and review your recent history.</p>
        </div>
      </header>

      {error && <p className="module-alert error" role="alert">{error}</p>}
      {notice && <p className="module-alert success" role="status">{notice}</p>}

      <section className="attendance-clock-card" aria-label="Attendance clock">
        <div>
          <h2>Today</h2>
          <p>{todayRecord?.check_in ? `Checked in at ${todayRecord.check_in}` : 'You have not checked in yet.'}</p>
          {todayRecord?.check_out && <p>Checked out at {todayRecord.check_out}</p>}
        </div>
        <div className="attendance-clock-actions">
          <button
            className="btn-primary"
            type="button"
            disabled={working || loading || Boolean(todayRecord)}
            onClick={() => recordTime(checkIn)}
          >
            {working && !todayRecord ? 'Recording…' : 'Clock In'}
          </button>
          <button
            className="btn-secondary"
            type="button"
            disabled={working || loading || !todayRecord?.check_in || Boolean(todayRecord?.check_out)}
            onClick={() => recordTime(checkOut)}
          >
            Clock Out
          </button>
        </div>
      </section>

      <section className="module-panel">
        <div className="module-section-heading">
          <div>
            <h2>Attendance history</h2>
            <p>Your recorded check-in and check-out times.</p>
          </div>
          <button className="btn-secondary" type="button" onClick={loadRecords} disabled={loading}>
            Refresh
          </button>
        </div>
        <AttendanceHistory records={records} loading={loading} />
      </section>
    </section>
  )
}

export default AttendanceDashboard
