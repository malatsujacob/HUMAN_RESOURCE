import { Activity } from 'lucide-react'
import { NavLink } from 'react-router-dom'
import { navigationItems } from './navigation.js'

function Sidebar() {
  return (
    <aside className="sidebar">
      <a className="brand" href="/" aria-label="Chap Chap HR home">
        <span className="brand-mark">cc</span>
        <span className="brand-copy">
          <strong>chap chap</strong>
          <span>PEOPLE & CULTURE</span>
        </span>
      </a>

      <div className="sidebar-section-label">WORKSPACE</div>
      <nav className="sidebar-nav" aria-label="Main navigation">
        {navigationItems.map(({ label, path, icon: Icon }) => (
          <NavLink
            key={path}
            to={path}
            end={path === '/'}
            className={({ isActive }) =>
              `nav-link${isActive ? ' active' : ''}`
            }
          >
            <Icon size={18} strokeWidth={1.8} aria-hidden="true" />
            <span>{label}</span>
            {label === 'Leave' && (
              <span className="nav-count" aria-label="3 pending requests">
                3
              </span>
            )}
          </NavLink>
        ))}
      </nav>

      <div className="sidebar-footer">
        <div className="help-icon">
          <Activity size={18} aria-hidden="true" />
        </div>
        <div>
          <strong>Need a hand?</strong>
          <span>Visit the HR help center</span>
        </div>
      </div>
    </aside>
  )
}

export default Sidebar
