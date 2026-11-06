import {
  BarChart3,
  Banknote,
  BriefcaseBusiness,
  CalendarCheck,
  CalendarDays,
  ChartNoAxesCombined,
  FileText,
  LayoutDashboard,
  LogOut,
  ShieldAlert,
  Users,
  UserRoundPlus,
} from 'lucide-react'

export const navigationItems = [
  { label: 'Dashboard', path: '/', icon: LayoutDashboard },
  { label: 'Employees', path: '/employees', icon: Users },
  { label: 'Recruitment', path: '/recruitment', icon: BriefcaseBusiness },
  { label: 'Onboarding', path: '/onboarding', icon: UserRoundPlus },
  { label: 'Contracts', path: '/contracts', icon: FileText },
  { label: 'Attendance', path: '/attendance', icon: CalendarDays },
  { label: 'Leave', path: '/leave', icon: CalendarCheck },
  { label: 'Payroll', path: '/payroll', icon: Banknote },
  { label: 'Performance', path: '/performance', icon: ChartNoAxesCombined },
  { label: 'Disciplinary', path: '/disciplinary', icon: ShieldAlert },
  { label: 'Exit', path: '/exit', icon: LogOut },
  { label: 'Analytics', path: '/analytics', icon: BarChart3 },
]
