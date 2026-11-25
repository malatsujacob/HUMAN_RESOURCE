import { BrowserRouter, Routes, Route, Navigate, useLocation } from 'react-router-dom';
import Login from './pages/Login';
import ChangePassword from './pages/ChangePassword';
import Layout from './components/Layout';
import Home from './pages/Home';
import ContractsDashboard from './pages/contracts/ContractsDashboard';
import OnboardingDashboard from './pages/onboarding/OnboardingDashboard';
import EmployeeDashboard from './pages/employees/EmployeeDashboard';
import RecruitmentDashboard from './pages/recruitment/RecruitmentDashboard';
import PublicApply from './pages/recruitment/PublicApply';
import OfferResponse from './pages/recruitment/OfferResponse';
import OnboardingResponse from './pages/onboarding/OnboardingResponse';
import AttendanceDashboard from './pages/attendance/AttendanceDashboard';
import LeaveDashboard from './pages/leave/LeaveDashboard';
import PayrollDashboard from './pages/payroll/PayrollDashboard';
import PerformanceDashboard from './pages/performance/PerformanceDashboard';
import DisciplinaryDashboard from './pages/disciplinary/DisciplinaryDashboard';
import CaseDetail from './pages/disciplinary/CaseDetail';
import ExitDashboard from './pages/exit/ExitDashboard';
import AnalyticsDashboard from './pages/analytics/AnalyticsDashboard';
import ESSPortal from './pages/ess/ESSPortal';
import TrainingDashboard from './pages/training/TrainingDashboard';

// Protected Route Wrapper
function ProtectedRoute({ children }) {
  const token = localStorage.getItem('token');
  const location = useLocation();
  if (!token) {
    return <Navigate to="/login" replace />;
  }
  const mustChangePassword = localStorage.getItem('must_change_password') === 'true';
  if (mustChangePassword && location.pathname !== '/change-password') return <Navigate to="/change-password" replace />;
  if (!mustChangePassword && location.pathname === '/change-password') return <Navigate to="/ess" replace />;
  return <Layout>{children}</Layout>;
}

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        {/* Public Routes */}
        <Route path="/login" element={<Login />} />
        <Route path="/apply" element={<PublicApply />} />
        <Route path="/offer-response" element={<OfferResponse />} />
        <Route path="/onboarding-response" element={<OnboardingResponse />} />

        {/* Protected Routes (Require Login) */}
        <Route path="/" element={<ProtectedRoute><Home /></ProtectedRoute>} />
        <Route path="/ess" element={<ProtectedRoute><ESSPortal /></ProtectedRoute>} />
        <Route path="/training" element={<ProtectedRoute><TrainingDashboard /></ProtectedRoute>} />
        <Route path="/change-password" element={<ProtectedRoute><ChangePassword /></ProtectedRoute>} />
        <Route path="/employees" element={<ProtectedRoute><EmployeeDashboard /></ProtectedRoute>} />
        <Route path="/onboarding" element={<ProtectedRoute><OnboardingDashboard /></ProtectedRoute>} />
        <Route path="/contracts" element={<ProtectedRoute><ContractsDashboard /></ProtectedRoute>} />
        <Route path="/recruitment" element={<ProtectedRoute><RecruitmentDashboard /></ProtectedRoute>} />
        <Route path="/attendance" element={<ProtectedRoute><AttendanceDashboard /></ProtectedRoute>} />
        <Route path="/leave" element={<ProtectedRoute><LeaveDashboard /></ProtectedRoute>} />
        <Route path="/payroll" element={<ProtectedRoute><PayrollDashboard /></ProtectedRoute>} />
        <Route path="/performance" element={<ProtectedRoute><PerformanceDashboard /></ProtectedRoute>} />
        <Route path="/disciplinary" element={<ProtectedRoute><DisciplinaryDashboard /></ProtectedRoute>} />
        <Route path="/disciplinary/:id" element={<ProtectedRoute><CaseDetail /></ProtectedRoute>} />
        <Route path="/exit" element={<ProtectedRoute><ExitDashboard /></ProtectedRoute>} />
        <Route path="/analytics" element={<ProtectedRoute><AnalyticsDashboard /></ProtectedRoute>} />
        
        {/* Fallback */}
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </BrowserRouter>
  );
}
