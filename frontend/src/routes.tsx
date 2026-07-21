import { createBrowserRouter, Navigate } from 'react-router-dom';
import App, { ProtectedLayout } from './App';
import LoginPage from './pages/LoginPage';

import AttendancePage from './pages/AttendancePage';
import EmployeeSearchPage from './pages/EmployeeSearchPage';
import ShiftActivityPage from './pages/ShiftActivityPage';
import EmployeeManagementPage from './pages/EmployeeManagementPage';
import FaceEnrollmentPage from './pages/FaceEnrollmentPage';

export const router = createBrowserRouter([
  {
    path: '/',
    element: <App />,
    children: [
      { path: 'login', element: <LoginPage /> },
      {
        element: <ProtectedLayout />,
        children: [
          { path: '', element: <Navigate to="/attendance" replace /> },
          { path: 'attendance', element: <AttendancePage /> },
          { path: 'search', element: <EmployeeSearchPage /> },
          { path: 'shift-activity', element: <ShiftActivityPage /> },
          { path: 'manage', element: <EmployeeManagementPage /> },
          { path: 'enroll', element: <FaceEnrollmentPage /> }
        ]
      }
    ]
  }
]);
