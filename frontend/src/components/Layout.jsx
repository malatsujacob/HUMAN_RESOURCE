import { Link, useNavigate, useLocation } from 'react-router-dom';
import { Activity, BookOpen, Briefcase, Calendar, ClipboardCheck, DollarSign, FileText, GraduationCap, LayoutDashboard, LogOut, LogOutIcon, Plane, ShieldAlert, Target, Users } from 'lucide-react';

export default function Layout({ children }) {
  const navigate = useNavigate();
  const location = useLocation();
  const role = (localStorage.getItem('role') || 'EMPLOYEE').toUpperCase();
  const email = localStorage.getItem('email') || 'User';
  const isHR = ['HR', 'HR_ADMIN', 'ADMIN', 'MANAGEMENT', 'DEVELOPER'].includes(role);
  const isHOD = role === 'HOD';

  const handleLogout = () => {
    localStorage.clear();
    navigate('/login');
  };

  const navItems = [
    { path: '/', label: 'Dashboard', icon: <LayoutDashboard size={20} /> },
    { path: '/ess', label: 'My Portal', icon: <Users size={20} /> },
    { path: '/attendance', label: 'Attendance', icon: <Calendar size={20} /> },
    { path: isHR ? '/leave' : '/ess?section=leave', label: 'Leave', icon: <Plane size={20} /> },
    { path: isHR ? '/performance' : '/ess?section=performance', label: 'Performance', icon: <Target size={20} /> },
    ...((isHOD || role === 'DEVELOPER') ? [{ path: '/ess?section=team', label: 'Team Approvals', icon: <ClipboardCheck size={20} /> }] : []),
    { path: isHR ? '/training' : '/ess?section=training', label: 'Training', icon: <GraduationCap size={20} /> },
    ...(role === 'FINANCE'
      ? [{ path: '/payroll', label: 'Payroll', icon: <DollarSign size={20} /> }]
      : !isHR
        ? [{ path: '/payroll', label: isHOD ? 'Team Payroll' : 'My Pay', icon: <DollarSign size={20} /> }]
        : []),
    ...(isHR ? [
      { path: '/employees', label: 'Employees', icon: <Users size={20} /> },
      { path: '/recruitment', label: 'Recruitment', icon: <Briefcase size={20} /> },
      { path: '/onboarding', label: 'Onboarding', icon: <FileText size={20} /> },
      { path: '/contracts', label: 'Contracts', icon: <FileText size={20} /> },
      { path: '/payroll', label: 'Payroll', icon: <DollarSign size={20} /> },
      { path: '/disciplinary', label: 'Disciplinary', icon: <ShieldAlert size={20} /> },
      { path: '/exit', label: 'Exit & Clearance', icon: <LogOutIcon size={20} /> },
      { path: '/analytics', label: 'Analytics', icon: <Activity size={20} /> },
    ] : []),
  ];

  return (
    <div className="portal-layout">
      <aside className="portal-sidebar" aria-label="Main navigation">
        <div className="portal-sidebar-header">CHAP CHAP HRMS</div>
        <nav className="portal-sidebar-nav">
          {navItems.map(item => (
            <Link key={item.path} to={item.path} className={location.pathname === item.path.split('?')[0] ? 'active' : ''} aria-current={location.pathname === item.path.split('?')[0] ? 'page' : undefined}>
              {item.icon}
              {item.label}
            </Link>
          ))}
        </nav>
      </aside>

      <div className="portal-main">
        <header className="portal-header">
          <h3>{isHR ? 'HR Command Center' : 'Employee Self-Service Portal'}</h3>
          <div style={{ display: 'flex', alignItems: 'center', gap: '20px' }}>
            <span style={{ padding: '4px 12px', background: '#e0e7ff', color: '#2563eb', borderRadius: '20px', fontSize: '12px', fontWeight: 'bold' }}>
              {role} | {email}
            </span>
            <button onClick={handleLogout} style={{ display: 'flex', alignItems: 'center', gap: '5px', background: 'none', border: 'none', color: '#dc2626', fontWeight: 'bold', cursor: 'pointer' }}>
              <LogOut size={16} /> Logout
            </button>
          </div>
        </header>
        <main className="portal-content">
          {children}
        </main>
      </div>
    </div>
  );
}
