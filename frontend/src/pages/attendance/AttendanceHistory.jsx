function formatTime(value) {
  if (!value) return '—'
  return new Date(`1970-01-01T${value}`).toLocaleTimeString([], {
    hour: 'numeric',
    minute: '2-digit',
  })
}

function AttendanceHistory({ records, loading }) {
  if (loading) {
    return <p className="module-message" role="status">Loading attendance history…</p>
  }

  if (records.length === 0) {
    return <p className="module-message">No attendance records yet.</p>
  }

  return (
    <div className="module-table-wrap">
      <table className="module-table">
        <thead>
          <tr>
            <th>Date</th>
            <th>Check in</th>
            <th>Check out</th>
            <th>Status</th>
            <th>Overtime</th>
          </tr>
        </thead>
        <tbody>
          {records.map((record) => (
            <tr key={record.id}>
              <td>{record.date}</td>
              <td>{formatTime(record.check_in)}</td>
              <td>{formatTime(record.check_out)}</td>
              <td><span className={`module-status ${record.status.toLowerCase()}`}>{record.status}</span></td>
              <td>{Number(record.overtime_hours || 0).toFixed(2)} hrs</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}

export default AttendanceHistory
