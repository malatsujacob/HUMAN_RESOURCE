import {
  ArrowDownRight,
  ArrowRight,
  ArrowUpRight,
  Banknote,
  CalendarCheck2,
  Clock3,
  Users,
} from 'lucide-react'

const summaryCards = [
  {
    label: 'Total employees',
    value: '248',
    detail: '12 added this month',
    change: '+5.1%',
    direction: 'up',
    icon: Users,
    tone: 'violet',
  },
  {
    label: 'Present today',
    value: '219',
    detail: '88% of your workforce',
    change: '+2.4%',
    direction: 'up',
    icon: CalendarCheck2,
    tone: 'green',
  },
  {
    label: 'On leave',
    value: '14',
    detail: '3 requests need review',
    change: '-1.2%',
    direction: 'down',
    icon: Clock3,
    tone: 'amber',
  },
  {
    label: 'Monthly payroll',
    value: 'KES 8.42M',
    detail: 'Scheduled for 28 Nov',
    change: '+3.8%',
    direction: 'up',
    icon: Banknote,
    tone: 'blue',
  },
]

const activityItems = [
  {
    initials: 'JM',
    name: 'Joyce Mwangi',
    action: 'submitted a leave request',
    time: '10 min ago',
    tone: 'pink',
  },
  {
    initials: 'DO',
    name: 'David Otieno',
    action: 'joined the Tech department',
    time: '1 hour ago',
    tone: 'blue',
  },
  {
    initials: 'AK',
    name: 'Amina Kamau',
    action: 'completed her performance review',
    time: '3 hours ago',
    tone: 'green',
  },
]

function Home() {
  return (
    <div className="dashboard">
      <div className="page-heading">
        <div>
          <p className="eyebrow">WEDNESDAY, 4 NOVEMBER 2026</p>
          <h1>Good morning, Admin <span aria-hidden="true">✦</span></h1>
          <p className="heading-subtitle">
            Here&apos;s what&apos;s happening with your people today.
          </p>
        </div>
        <button className="date-filter" type="button">
          <CalendarCheck2 size={16} aria-hidden="true" />
          This month
        </button>
      </div>

      <section className="summary-grid" aria-label="HR summary">
        {summaryCards.map(
          ({ label, value, detail, change, direction, icon: Icon, tone }) => (
            <article className="summary-card" key={label}>
              <div className="card-topline">
                <span className={`summary-icon ${tone}`}>
                  <Icon size={19} strokeWidth={1.8} aria-hidden="true" />
                </span>
                <span className={`change-indicator ${direction}`}>
                  {direction === 'up' ? (
                    <ArrowUpRight size={14} aria-hidden="true" />
                  ) : (
                    <ArrowDownRight size={14} aria-hidden="true" />
                  )}
                  {change}
                </span>
              </div>
              <p className="summary-label">{label}</p>
              <strong className="summary-value">{value}</strong>
              <span className="summary-detail">{detail}</span>
            </article>
          ),
        )}
      </section>

      <section className="dashboard-lower">
        <article className="panel activity-panel">
          <div className="panel-heading">
            <div>
              <h2>Recent activity</h2>
              <p>Latest updates from your team</p>
            </div>
            <button className="text-button" type="button">
              View all <ArrowRight size={15} aria-hidden="true" />
            </button>
          </div>
          <ul className="activity-list">
            {activityItems.map(({ initials, name, action, time, tone }) => (
              <li className="activity-item" key={name}>
                <span className={`activity-avatar ${tone}`}>{initials}</span>
                <span className="activity-description">
                  <span>
                    <strong>{name}</strong> {action}
                  </span>
                  <time>{time}</time>
                </span>
              </li>
            ))}
          </ul>
        </article>

        <article className="panel quick-panel">
          <div className="panel-heading">
            <div>
              <h2>Quick overview</h2>
              <p>Your team at a glance</p>
            </div>
            <span className="overview-icon">
              <Users size={18} aria-hidden="true" />
            </span>
          </div>
          <div className="overview-stat">
            <span>Open positions</span>
            <strong>8</strong>
          </div>
          <div className="overview-stat">
            <span>Reviews due this month</span>
            <strong>23</strong>
          </div>
          <div className="overview-stat">
            <span>Departments</span>
            <strong>7</strong>
          </div>
          <div className="overview-progress">
            <div className="progress-label">
              <span>Attendance rate</span>
              <strong>88%</strong>
            </div>
            <div className="progress-track" aria-label="Attendance rate 88%">
              <span />
            </div>
          </div>
        </article>
      </section>
    </div>
  )
}

export default Home
