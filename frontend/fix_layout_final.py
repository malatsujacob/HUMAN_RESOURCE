import os

layout_code = '''import { Link, useNavigate, useLocation } from 'react-router-dom';
import { LayoutDashboard, Users, Briefcase, FileText, Calendar, Plane, DollarSign, Target, ShieldAlert, LogOut, BookOpen, LogOutIcon } from 'lucide-react';

export default function Layout({ children }) {
  const navigate = useNavigate();
  const location = useLocation();
  const role = localStorage.getItem('role') || 'EMPLOYEE';
  const email = localStorage.getItem('email') || 'User';
  const isHR = ['HR', 'MANAGEMENT'].includes(role);

  const handleLogout = () => {
    localStorage.clear();
    navigate('/login');
  };

  // The Master List of all 13 Modules
  const navItems = [
    { path: '/', label: 'Dashboard', icon: <LayoutDashboard size={20} /> },
    { path: '/employees', label: 'Employees', icon: <Users size={20} />, hideForStaff: true },
    { path: '/recruitment', label: 'Recruitment', icon: <Briefcase size={20} />, hideForStaff: true },
    { path: '/onboarding', label: 'Onboarding', icon: <FileText size={20} />, hideForStaff: true },
    { path: '/contracts', label: 'Contracts', icon: <FileText size={20} />, hideForStaff: true },
    { path: '/attendance', label: 'Attendance', icon: <Calendar size={20} /> },
    { path: '/leave', label: 'Leave', icon: <Plane size={20} /> },
    { path: '/payroll', label: 'Payroll', icon: <DollarSign size={20} />, hideForStaff: true },
    { path: '/performance', label: 'Performance', icon: <Target size={20} />, hideForStaff: true },
    { path: '/training', label: 'Training', icon: <BookOpen size={20} />, hideForStaff: true },
    { path: '/disciplinary', label: 'Disciplinary', icon: <ShieldAlert size={20} />, hideForStaff: true },
    { path: '/exit', label: 'Exit & Clearance', icon: <LogOutIcon size={20} />, hideForStaff: true },
  ];

  return (
    <div className="dashboard-layout">
      <aside className="sidebar">
        <div className="sidebar-header">CHAP CHAP HRMS</div>
        <nav>
          {/* This filter is the magic: if the item is marked hideForStaff AND the user is NOT HR, it hides it */}
          {navItems.filter(item => !item.hideForStaff || isHR).map(item => (
            <Link key={item.path} to={item.path} className={location.pathname === item.path ? 'active' : ''}>
              {item.icon}
              {item.label}
            </Link>
          ))}
        </nav>
      </aside>

      <div className="main-content">
        <header className="header">
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
        <main className="content-area">
          {children}
        </main>
      </div>
    </div>
  );
}
'''

with open('src/components/Layout.jsx', 'w', encoding='utf-8') as f:
    f.write(layout_code)
print("✅ Layout.jsx completely overwritten with all 13 modules and strict role hiding!")
