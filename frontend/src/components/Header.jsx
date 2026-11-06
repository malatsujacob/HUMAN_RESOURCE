import { Bell, ChevronDown, Search } from 'lucide-react'

function Header() {
  return (
    <header className="topbar">
      <label className="search-box">
        <Search size={18} aria-hidden="true" />
        <input type="search" placeholder="Search anything..." aria-label="Search" />
        <kbd>⌘ K</kbd>
      </label>

      <div className="topbar-actions">
        <button className="icon-button notification-button" type="button" aria-label="Notifications">
          <Bell size={19} strokeWidth={1.8} />
          <span className="notification-dot" />
        </button>
        <span className="topbar-divider" />
        <button className="profile-button" type="button" aria-label="Open account menu">
          <span className="avatar">SA</span>
          <span className="profile-copy">
            <strong>System Admin</strong>
            <span>HR Manager</span>
          </span>
          <ChevronDown size={16} aria-hidden="true" />
        </button>
      </div>
    </header>
  )
}

export default Header
