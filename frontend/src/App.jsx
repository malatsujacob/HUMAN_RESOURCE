import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { useState, useEffect } from 'react';
import Login from './pages/Login';
import Layout from './components/Layout';
import Home from './pages/Home';
import ContractsDashboard from './pages/contracts/ContractsDashboard';
import OnboardingDashboard from './pages/onboarding/OnboardingDashboard';
import EmployeeDashboard from './pages/employees/EmployeeDashboard';
import RecruitmentDashboard from './pages/recruitment/RecruitmentDashboard';
import PublicApply from './pages/recruitment/PublicApply';
import AttendanceDashboard from './pages/attendance/AttendanceDashboard';
import LeaveDashboard from './pages/leave/LeaveDashboard';
import PayrollDashboard from './pages/payroll/PayrollDashboard';
import PerformanceDashboard from './pages/performance/PerformanceDashboard';
import DisciplinaryDashboard from './pages/disciplinary/DisciplinaryDashboard';
import ExitDashboard from './pages/exit/ExitDashboard';

// Protected Route Wrapper
function ProtectedRoute({ children }) {
  const token = localStorage.getItem('token');
  if (!token) {
    return <Navigate to="/login" replace />;
  }
  return <Layout>{children}</Layout>;
}

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        {/* Public Routes */}
        <Route path="/login" element={<Login />} />
        <Route path="/apply" element={<PublicApply />} />

        {/* Protected Routes (Require Login) */}
        <Route path="/" element={<ProtectedRoute><Home /></ProtectedRoute>} />
        <Route path="/employees" element={<ProtectedRoute><EmployeeDashboard /></ProtectedRoute>} />
        <Route path="/onboarding" element={<ProtectedRoute><OnboardingDashboard /></ProtectedRoute>} />
<Route path="/contracts" element={<ProtectedRoute><ContractsDashboard /></ProtectedRoute>} />
<Route path="/recruitment" element={<ProtectedRoute><RecruitmentDashboard /></ProtectedRoute>} />
        <Route path="/attendance" element={<ProtectedRoute><AttendanceDashboard /></ProtectedRoute>} />
        <Route path="/leave" element={<ProtectedRoute><LeaveDashboard /></ProtectedRoute>} />
        <Route path="/payroll" element={<ProtectedRoute><PayrollDashboard /></ProtectedRoute>} />
        <Route path="/performance" element={<ProtectedRoute><PerformanceDashboard /></ProtectedRoute>} />
        <Route path="/disciplinary" element={<ProtectedRoute><DisciplinaryDashboard /></ProtectedRoute>} />
        <Route path="/exit" element={<ProtectedRoute><ExitDashboard /></ProtectedRoute>} />
        
        {/* Fallback */}
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </BrowserRouter>
  );
}
