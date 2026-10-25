/**
 * @file routes.tsx
 * @description Master router definition and role-based route guard architecture.
 *
 * SPECIFICATION & SECURITY (PROJECT.md section 6 & section 8):
 * - Guarantees users access only their assigned role routes:
 *   * `/admin/*` requires `role === 'admin'`
 *   * `/hr/*` requires `role === 'hr' || role === 'admin'`
 *   * `/employee/*` available to all authenticated employees (including HR who is also an employee)
 * - Redirects to `/setup` if the system indicates `needs_setup === true`.
 * - Intercepts users with `must_change_password === true` and forces the `/change-password` screen.
 */

import React from 'react';
import { Routes, Route, Navigate } from 'react-router-dom';
import { useAuth } from '@/auth/AuthProvider';
import { AppShell } from '@/layouts/AppShell';

// Authentication & First-Run Screens
import { Login } from '@/pages/Login';
import { Setup } from '@/pages/Setup';
import { ChangePassword } from '@/pages/ChangePassword';

// Admin Screens
import { AdminDashboard } from '@/pages/admin/AdminDashboard';
import { CompanySettings } from '@/pages/admin/CompanySettings';
import { Organization } from '@/pages/admin/Organization';
import { Logins } from '@/pages/admin/Logins';
import { AdminPayroll } from '@/pages/admin/AdminPayroll';
import { AuditLog } from '@/pages/admin/AuditLog';

// HR Screens
import { HrDashboard } from '@/pages/hr/HrDashboard';
import { Employees } from '@/pages/hr/Employees';
import { AttendanceBoard } from '@/pages/hr/AttendanceBoard';
import { CorrectionsInbox } from '@/pages/hr/CorrectionsInbox';
import { LeaveInbox } from '@/pages/hr/LeaveInbox';
import { HrPayroll } from '@/pages/hr/HrPayroll';

// Employee Screens
import { EmployeeDashboard } from '@/pages/employee/EmployeeDashboard';
import { CheckIn } from '@/pages/employee/CheckIn';
import { MyAttendance } from '@/pages/employee/MyAttendance';
import { MyLeave } from '@/pages/employee/MyLeave';
import { MyPayslips } from '@/pages/employee/MyPayslips';
import { MyProfile } from '@/pages/employee/MyProfile';

// Shared Screens
import { AnnouncementsPage } from '@/pages/AnnouncementsPage';
import { AiAssistantPage } from '@/pages/AiAssistantPage';

/**
 * Route protection higher-order component.
 * Verifies authentication, setup state, password change enforcement, and role clearance.
 */
function ProtectedRoute({
  children,
  allowedRoles,
}: {
  children: React.ReactNode;
  allowedRoles?: ('admin' | 'hr' | 'employee')[];
}) {
  const { user, loading, needsSetup } = useAuth();

  // Show minimal loading spinner while session initializes
  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-background">
        <div className="h-6 w-6 border-2 border-accent border-t-transparent rounded-full animate-spin" />
      </div>
    );
  }

  // 1. Force setup on uninitialized fresh databases
  if (needsSetup) {
    return <Navigate to="/setup" replace />;
  }

  // 2. Redirect unauthenticated visitors to login
  if (!user) {
    return <Navigate to="/login" replace />;
  }

  // 3. Force password change screen if temp password flag is set
  if (user.must_change_password) {
    return <Navigate to="/change-password" replace />;
  }

  // 4. Enforce strict role boundary (hiding a button is not security)
  if (allowedRoles && !allowedRoles.includes(user.role)) {
    return <Navigate to={`/${user.role}/dashboard`} replace />;
  }

  return <>{children}</>;
}

export function AppRoutes() {
  const { user } = useAuth();

  return (
    <Routes>
      {/* Public / Bootstrap routes */}
      <Route path="/login" element={<Login />} />
      <Route path="/setup" element={<Setup />} />
      <Route path="/change-password" element={<ChangePassword />} />

      {/* Main Authenticated Layout */}
      <Route
        path="/"
        element={
          <ProtectedRoute>
            <AppShell />
          </ProtectedRoute>
        }
      >
        {/* Index: Redirect to user's dashboard */}
        <Route
          index
          element={
            user ? (
              <Navigate to={`/${user.role}/dashboard`} replace />
            ) : (
              <Navigate to="/login" replace />
            )
          }
        />

        {/* ------------------------------------------------------------- */}
        {/* Admin Routes */}
        {/* ------------------------------------------------------------- */}
        <Route
          path="admin/dashboard"
          element={
            <ProtectedRoute allowedRoles={['admin']}>
              <AdminDashboard />
            </ProtectedRoute>
          }
        />
        <Route
          path="admin/setup"
          element={
            <ProtectedRoute allowedRoles={['admin']}>
              <CompanySettings />
            </ProtectedRoute>
          }
        />
        <Route
          path="admin/organization"
          element={
            <ProtectedRoute allowedRoles={['admin']}>
              <Organization />
            </ProtectedRoute>
          }
        />
        <Route
          path="admin/logins"
          element={
            <ProtectedRoute allowedRoles={['admin']}>
              <Logins />
            </ProtectedRoute>
          }
        />
        <Route
          path="admin/employees"
          element={
            <ProtectedRoute allowedRoles={['admin']}>
              <Employees />
            </ProtectedRoute>
          }
        />
        <Route
          path="admin/payroll"
          element={
            <ProtectedRoute allowedRoles={['admin']}>
              <AdminPayroll />
            </ProtectedRoute>
          }
        />
        <Route
          path="admin/audit"
          element={
            <ProtectedRoute allowedRoles={['admin']}>
              <AuditLog />
            </ProtectedRoute>
          }
        />

        {/* ------------------------------------------------------------- */}
        {/* HR Routes */}
        {/* ------------------------------------------------------------- */}
        <Route
          path="hr/dashboard"
          element={
            <ProtectedRoute allowedRoles={['hr', 'admin']}>
              <HrDashboard />
            </ProtectedRoute>
          }
        />
        <Route
          path="hr/employees"
          element={
            <ProtectedRoute allowedRoles={['hr', 'admin']}>
              <Employees />
            </ProtectedRoute>
          }
        />
        <Route
          path="hr/attendance-board"
          element={
            <ProtectedRoute allowedRoles={['hr', 'admin']}>
              <AttendanceBoard />
            </ProtectedRoute>
          }
        />
        <Route
          path="hr/corrections"
          element={
            <ProtectedRoute allowedRoles={['hr', 'admin']}>
              <CorrectionsInbox />
            </ProtectedRoute>
          }
        />
        <Route
          path="hr/leave-inbox"
          element={
            <ProtectedRoute allowedRoles={['hr', 'admin']}>
              <LeaveInbox />
            </ProtectedRoute>
          }
        />
        <Route
          path="hr/payroll"
          element={
            <ProtectedRoute allowedRoles={['hr', 'admin']}>
              <HrPayroll />
            </ProtectedRoute>
          }
        />

        {/* ------------------------------------------------------------- */}
        {/* Employee Routes (Available to Employee, HR, and Admin) */}
        {/* ------------------------------------------------------------- */}
        <Route
          path="employee/dashboard"
          element={
            <ProtectedRoute allowedRoles={['employee', 'hr', 'admin']}>
              <EmployeeDashboard />
            </ProtectedRoute>
          }
        />
        <Route
          path="employee/check-in"
          element={
            <ProtectedRoute allowedRoles={['employee', 'hr', 'admin']}>
              <CheckIn />
            </ProtectedRoute>
          }
        />
        <Route
          path="employee/attendance"
          element={
            <ProtectedRoute allowedRoles={['employee', 'hr', 'admin']}>
              <MyAttendance />
            </ProtectedRoute>
          }
        />
        <Route
          path="employee/leave"
          element={
            <ProtectedRoute allowedRoles={['employee', 'hr', 'admin']}>
              <MyLeave />
            </ProtectedRoute>
          }
        />
        <Route
          path="employee/payslips"
          element={
            <ProtectedRoute allowedRoles={['employee', 'hr', 'admin']}>
              <MyPayslips />
            </ProtectedRoute>
          }
        />
        <Route
          path="employee/profile"
          element={
            <ProtectedRoute allowedRoles={['employee', 'hr', 'admin']}>
              <MyProfile />
            </ProtectedRoute>
          }
        />

        {/* ------------------------------------------------------------- */}
        {/* Shared Organization Modules */}
        {/* ------------------------------------------------------------- */}
        <Route path="announcements" element={<AnnouncementsPage />} />
        <Route path="ai-assistant" element={<AiAssistantPage />} />
      </Route>

      {/* Fallback wildcard route */}
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}
