import {
  Banknote,
  BriefcaseBusiness,
  CalendarCheck,
  CalendarDays,
  ChartNoAxesCombined,
  FileText,
  LayoutDashboard,
  LogOut,
  BarChart3,
  ShieldAlert,
  Users,
  UserRoundPlus,
} from 'lucide-react'
import { NavLink, Outlet, useNavigate } from 'react-router-dom'

const navigationItems = [
  { label: 'Dashboard', path: '/', icon: LayoutDashboard },
  { label: 'Employees', path: '/employees', hideForStaff: true, icon: Users },
  { label: 'Recruitment', path: '/recruitment', hideForStaff: true, icon: BriefcaseBusiness },
  { label: 'Onboarding', path: '/onboarding', icon: UserRoundPlus },
  { label: 'Contracts', path: '/contracts', hideForStaff: true, icon: FileText },
  { label: 'Attendance', path: '/attendance', icon: CalendarDays },
  { label: 'Leave', path: '/leave', icon: CalendarCheck },
  { label: 'Payroll', path: '/payroll', hideForStaff: true, icon: Banknote },
  { label: 'Performance', path: '/performance', hideForStaff: true, icon: ChartNoAxesCombined },
  { label: 'Disciplinary', path: '/disciplinary', hideForStaff: true, icon: ShieldAlert },
  { label: 'Exit', path: '/exit', hideForStaff: true, icon: LogOut },
  { label: 'Analytics', path: '/analytics', icon: BarChart3 },
]

function getUserRole() {
  const savedRole = window.localStorage.getItem('role')
  if (savedRole) return savedRole

  const token = window.localStorage.getItem('access_token')
  if (!token) return 'Guest'

  try {
    const payload = token.split('.')[1]
    const base64 = payload.replace(/-/g, '+').replace(/_/g, '/')
    const paddedBase64 = base64.padEnd(Math.ceil(base64.length / 4) * 4, '=')
    const claims = JSON.parse(window.atob(paddedBase64))
    return claims.role || 'User'
  } catch {
    return 'User'
  }
}

function Layout({ children }) {
  const navigate = useNavigate()
  const role = getUserRole()

  function handleLogout() {
    window.localStorage.removeItem('access_token')
    window.localStorage.removeItem('role')
    window.localStorage.removeItem('email')
    navigate('/login', { replace: true })
  }

  return (
    <div className="hrms-layout">
      <aside className="hrms-sidebar">
        <NavLink className="hrms-brand" to="/" aria-label="Chap Chap HRMS home">
          <span className="hrms-brand-mark">CC</span>
          <span>CHAP CHAP HRMS</span>
        </NavLink>

        <nav className="hrms-navigation" aria-label="Main navigation">
          {navigationItems.map(({ label, path, icon: Icon }) => (
            <NavLink
              key={path}
              to={path}
              end={path === '/'}
              className={({ isActive }) =>
                `hrms-nav-link${isActive ? ' active' : ''}`
              }
            >
              <Icon size={18} aria-hidden="true" />
              <span>{label}</span>
            </NavLink>
          ))}
        </nav>
      </aside>

      <div className="hrms-main">
        <header className="hrms-header">
          <span className="hrms-role">
            Role: <strong>{role}</strong>
          </span>
          <button className="hrms-logout" type="button" onClick={handleLogout}>
            <LogOut size={16} aria-hidden="true" />
            Logout
          </button>
        </header>
        <main className="page-content">{children ?? <Outlet />}</main>
      </div>
    </div>
  )
}

export default Layout
