/**
 * @file AppShell.tsx
 * @description Master responsive application layout for HCM Lite.
 *
 * SPECIFICATION (FARHAN.md & FARHAN_GUIDE.txt Task F4):
 * - Renders dynamic role menus strictly filtered for:
 *   * Admin: Dashboard, Setup, Org, Logins, Employees, Payroll Finalize, Announcements, Audit Log, AI Assistant
 *   * HR: Dashboard, Employees, Attendance Board, Corrections, Leave Inbox, Payroll Draft, Check-in, Leave, AI Assistant
 *   * Employee: Dashboard, Check-in, Attendance, Leave, Payslips, Profile, Announcements, AI Assistant
 * - Fully responsive: transforms sidebar into mobile overlay drawer on screens >= 375px.
 * - Features a Quick Role Preview switcher allowing judges to toggle roles with zero friction.
 */

import React, { useState } from 'react';
import { NavLink, Outlet, useNavigate } from 'react-router-dom';
import { useAuth } from '@/auth/AuthProvider';
import { NotificationsBell } from '@/components/NotificationsBell';
import { Button } from '@/components/ui/Button';
import {
  LayoutDashboard,
  Settings,
  Users,
  Clock,
  CalendarCheck2,
  DollarSign,
  Bot,
  Megaphone,
  Shield,
  Menu,
  X,
  LogOut,
  UserCheck,
  Building2,
  Briefcase,
  FileCheck,
} from 'lucide-react';

export function AppShell() {
  const { user, logout, switchMockRole } = useAuth();
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const navigate = useNavigate();

  const handleLogout = async () => {
    await logout();
    navigate('/login');
  };

  /**
   * Generates navigation menu items based strictly on current user role.
   */
  const navItems = React.useMemo(() => {
    if (!user) return [];

    if (user.role === 'admin') {
      return [
        { label: 'Dashboard', path: '/admin/dashboard', icon: LayoutDashboard },
        { label: 'Company Settings', path: '/admin/setup', icon: Settings },
        { label: 'Departments & Org', path: '/admin/organization', icon: Building2 },
        { label: 'HR Logins', path: '/admin/logins', icon: UserCheck },
        { label: 'All Employees', path: '/admin/employees', icon: Users },
        { label: 'Payroll & Finalize', path: '/admin/payroll', icon: DollarSign },
        { label: 'Announcements', path: '/announcements', icon: Megaphone },
        { label: 'Audit Log', path: '/admin/audit', icon: Shield },
        { label: 'AI Assistant', path: '/ai-assistant', icon: Bot },
      ];
    }

    if (user.role === 'hr') {
      return [
        { label: 'HR Dashboard', path: '/hr/dashboard', icon: LayoutDashboard },
        { label: 'Employee Directory', path: '/hr/employees', icon: Users },
        { label: 'Attendance Board', path: '/hr/attendance-board', icon: Clock },
        { label: 'Corrections Inbox', path: '/hr/corrections', icon: FileCheck },
        { label: 'Leave Inbox', path: '/hr/leave-inbox', icon: CalendarCheck2 },
        { label: 'Payroll Drafts', path: '/hr/payroll', icon: DollarSign },
        { label: 'My Check-In', path: '/employee/check-in', icon: Clock },
        { label: 'My Leave', path: '/employee/leave', icon: CalendarCheck2 },
        { label: 'Announcements', path: '/announcements', icon: Megaphone },
        { label: 'AI Assistant', path: '/ai-assistant', icon: Bot },
      ];
    }

    // Default: Employee navigation
    return [
      { label: 'My Dashboard', path: '/employee/dashboard', icon: LayoutDashboard },
      { label: 'Check In / Out', path: '/employee/check-in', icon: Clock },
      { label: 'My Attendance', path: '/employee/attendance', icon: CalendarCheck2 },
      { label: 'Leave & Smart Leave', path: '/employee/leave', icon: CalendarCheck2 },
      { label: 'My Payslips', path: '/employee/payslips', icon: DollarSign },
      { label: 'My Profile', path: '/employee/profile', icon: Briefcase },
      { label: 'Announcements', path: '/announcements', icon: Megaphone },
      { label: 'AI Assistant', path: '/ai-assistant', icon: Bot },
    ];
  }, [user]);

  return (
    <div className="min-h-screen bg-background flex flex-col md:flex-row">
      {/* ------------------------------------------------------------- */}
      {/* Mobile Top Header (<= 768px) */}
      {/* ------------------------------------------------------------- */}
      <header className="md:hidden flex items-center justify-between p-4 border-b border-border bg-surface-elevated sticky top-0 z-40">
        <div className="flex items-center gap-2">
          <Button
            variant="ghost"
            size="icon"
            onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
            aria-label="Toggle navigation menu"
          >
            {mobileMenuOpen ? <X className="h-5 w-5" /> : <Menu className="h-5 w-5" />}
          </Button>
          <span className="font-bold text-sm tracking-tight text-foreground">HCM Lite</span>
        </div>
        <div className="flex items-center gap-2">
          <NotificationsBell />
          <span className="text-[10px] uppercase font-bold px-2 py-0.5 rounded bg-accent text-accent-foreground">
            {user?.role}
          </span>
        </div>
      </header>

      {/* ------------------------------------------------------------- */}
      {/* Sidebar Navigation (Desktop Fixed + Mobile Drawer) */}
      {/* ------------------------------------------------------------- */}
      <aside
        className={`fixed md:sticky top-0 left-0 z-50 h-screen w-64 border-r border-border bg-surface-elevated flex flex-col justify-between transition-transform duration-200 md:translate-x-0 ${
          mobileMenuOpen ? 'translate-x-0' : '-translate-x-full md:translate-x-0'
        }`}
      >
        <div>
          {/* Logo Header */}
          <div className="p-5 border-b border-border flex items-center justify-between">
            <div>
              <div className="flex items-center gap-2">
                <div className="h-6 w-6 rounded bg-accent text-accent-foreground flex items-center justify-center font-bold text-xs">
                  H
                </div>
                <h1 className="font-bold text-base tracking-tight text-foreground">HCM Lite</h1>
              </div>
              <p className="text-[11px] text-muted-foreground mt-0.5">Enterprise Core HR</p>
            </div>
            <span className="hidden md:inline-block text-[10px] uppercase font-bold px-2 py-0.5 rounded bg-muted text-muted-foreground border border-border">
              {user?.role}
            </span>
          </div>

          {/* Quick Role Switcher for Hackathon Judges */}
          <div className="px-4 py-2 bg-surface/50 border-b border-border text-[11px]">
            <span className="text-muted-foreground block mb-1 font-semibold uppercase tracking-wider text-[9px]">
              Demo Role Preview
            </span>
            <div className="grid grid-cols-3 gap-1">
              {(['admin', 'hr', 'employee'] as const).map((r) => (
                <button
                  key={r}
                  onClick={() => switchMockRole(r)}
                  className={`px-1.5 py-1 rounded text-center font-medium capitalize text-[10px] transition-colors ${
                    user?.role === r
                      ? 'bg-accent text-accent-foreground shadow-sm font-semibold'
                      : 'bg-background hover:bg-muted text-muted-foreground'
                  }`}
                >
                  {r}
                </button>
              ))}
            </div>
          </div>

          {/* Navigation Links List */}
          <nav className="p-3 space-y-1 overflow-y-auto max-h-[calc(100vh-220px)]">
            {navItems.map((item) => {
              const Icon = item.icon;
              return (
                <NavLink
                  key={item.path}
                  to={item.path}
                  onClick={() => setMobileMenuOpen(false)}
                  className={({ isActive }) =>
                    `flex items-center gap-3 px-3 py-2 rounded text-xs font-medium transition-colors ${
                      isActive
                        ? 'bg-accent text-accent-foreground font-semibold'
                        : 'text-muted-foreground hover:text-foreground hover:bg-surface'
                    }`
                  }
                >
                  <Icon className="h-4 w-4 shrink-0" />
                  <span>{item.label}</span>
                </NavLink>
              );
            })}
          </nav>
        </div>

        {/* User Identity & Logout Footer */}
        <div className="p-4 border-t border-border bg-surface/30">
          <div className="flex items-center justify-between mb-3">
            <div className="truncate mr-2">
              <p className="text-xs font-semibold text-foreground truncate">{user?.full_name || user?.email}</p>
              <p className="text-[10px] text-muted-foreground truncate">{user?.email}</p>
            </div>
            <div className="hidden md:block">
              <NotificationsBell />
            </div>
          </div>
          <Button
            variant="outline"
            size="sm"
            onClick={handleLogout}
            className="w-full justify-center text-xs gap-1.5"
          >
            <LogOut className="h-3.5 w-3.5" />
            Sign Out
          </Button>
        </div>
      </aside>

      {/* Mobile Drawer Backdrop Overlay */}
      {mobileMenuOpen && (
        <div
          onClick={() => setMobileMenuOpen(false)}
          className="fixed inset-0 z-40 bg-black/50 md:hidden"
        />
      )}

      {/* ------------------------------------------------------------- */}
      {/* Main Routed Content Area */}
      {/* ------------------------------------------------------------- */}
      <main className="flex-1 p-4 md:p-8 max-w-7xl w-full mx-auto overflow-y-auto">
        <Outlet />
      </main>
    </div>
  );
}
