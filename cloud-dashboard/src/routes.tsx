import React from 'react';
import { Routes, Route, Navigate, Outlet } from 'react-router-dom';
import { useSession } from './auth/SessionContext';
import { LoginPage } from './pages/LoginPage';

const ProtectedRoute = ({ allowedRoles }: { allowedRoles?: string[] }) => {
  const { user } = useSession();

  if (!user) {
    return <Navigate to="/login" replace />;
  }

  if (allowedRoles && !allowedRoles.includes(user.role)) {
    // If not allowed, redirect to overview
    return <Navigate to="/" replace />;
  }

  return <Outlet />;
};

import { EmployeeListPage } from './pages/EmployeeListPage';
import { EmployeeHistoryPage } from './pages/EmployeeHistoryPage';
import { ReportsPage } from './pages/ReportsPage';
import { UserManagementPage } from './pages/UserManagementPage';

const OverviewPage = () => <div>Overview</div>;

export const AppRoutes: React.FC = () => {
  return (
    <Routes>
      <Route path="/login" element={<LoginPage />} />
      
      <Route element={<ProtectedRoute />}>
        <Route path="/" element={<OverviewPage />} />
        <Route path="/employees" element={<EmployeeListPage />} />
        <Route path="/employees/:id/history" element={<EmployeeHistoryPage />} />
        <Route path="/reports" element={<ReportsPage />} />
        
        {/* Owner only */}
        <Route element={<ProtectedRoute allowedRoles={['owner']} />}>
          <Route path="/users" element={<UserManagementPage />} />
        </Route>
      </Route>
      
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
};
