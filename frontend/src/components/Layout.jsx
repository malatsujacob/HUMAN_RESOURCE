import {
  Banknote,
  BriefcaseBusiness,
  CalendarCheck,
  CalendarDays,
  ChartNoAxesCombined,
  ChevronLeft,
  FileText,
  LayoutDashboard,
  LogOut,
  BarChart3,
  ShieldAlert,
  Users,
  UserRoundPlus,
} from 'lucide-react'
import { NavLink, Outlet, useLocation, useNavigate } from 'react-router-dom'

const navigationItems = [
  { label: 'Dashboard', path: '/', icon: LayoutDashboard },
  { label: 'ESS Portal', path: '/ess', icon: UserRoundPlus },
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

  const token = window.localStorage.getItem('token') || window.localStorage.getItem('access_token')
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
  const location = useLocation()
  const role = getUserRole()
  const currentPage = navigationItems.find((item) => item.path === location.pathname)

  function handleBack() {
    if (window.history.state?.idx > 0) {
      navigate(-1)
      return
    }
    navigate('/', { replace: true })
  }

  function handleLogout() {
    window.localStorage.removeItem('access_token')
    window.localStorage.removeItem('token')
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
          {navigationItems.filter(item => !(role.toUpperCase() === 'HOD' && item.path === '/performance')).map(({ label, path, icon: Icon }) => (
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
          <div className="hrms-header-context">
            {location.pathname !== '/' && (
              <button className="hrms-back-button" type="button" onClick={handleBack} aria-label="Go back">
                <ChevronLeft size={18} aria-hidden="true" />
                <span>Back</span>
              </button>
            )}
            <span className="hrms-page-title">{currentPage?.label || 'HR workspace'}</span>
          </div>
          <div className="hrms-header-actions">
            <span className="hrms-role">
              Role: <strong>{role}</strong>
            </span>
            <button className="hrms-logout" type="button" onClick={handleLogout}>
              <LogOut size={16} aria-hidden="true" />
              Logout
            </button>
          </div>
        </header>
        <main className="page-content">{children ?? <Outlet />}</main>
      </div>
    </div>
  )
}

export default Layout
