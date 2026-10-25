/**
 * @file tokens.ts
 * @description Centralized design tokens, type definitions, and status color mappings.
 * Strictly adheres to PROJECT.md section 7 & section 9 status definitions:
 * - Attendance: 'present', 'late', 'half_day', 'absent', 'missing_checkout', 'on_leave'
 * - Requests: 'pending', 'approved', 'rejected', 'cancelled'
 * - Payroll: 'draft', 'finalized'
 */

/**
 * Valid attendance status values matching the Postgres enum `att_status` in schema.sql.
 * Note: 'absent' and 'missing_checkout' are computed by rules.daily_status(), never stored.
 */
export type AttendanceStatus =
  | 'present'
  | 'late'
  | 'half_day'
  | 'absent'
  | 'missing_checkout'
  | 'on_leave';

/**
 * Valid request status values matching `req_status` in schema.sql.
 * Used for leave requests and attendance correction appeals.
 */
export type RequestStatus = 'pending' | 'approved' | 'rejected' | 'cancelled';

/**
 * Payroll cycle state matching `payroll_status` in schema.sql.
 * 'draft' allows HR recomputation; 'finalized' locks records permanently.
 */
export type PayrollStatus = 'draft' | 'finalized';

/**
 * Core application user roles matching `user_role` in schema.sql.
 */
export type UserRole = 'admin' | 'hr' | 'employee';

/**
 * Visual styling configuration for attendance statuses.
 * Follows the ultra-minimal high-contrast design language.
 */
export const STATUS_CONFIG: Record<
  AttendanceStatus,
  { label: string; bg: string; text: string; border: string; dot: string }
> = {
  present: {
    label: 'Present',
    bg: 'bg-emerald-500/10',
    text: 'text-emerald-700 dark:text-emerald-400',
    border: 'border-emerald-500/30',
    dot: 'bg-emerald-500',
  },
  late: {
    label: 'Late',
    bg: 'bg-amber-500/10',
    text: 'text-amber-700 dark:text-amber-400',
    border: 'border-amber-500/30',
    dot: 'bg-amber-500',
  },
  half_day: {
    label: 'Half Day',
    bg: 'bg-blue-500/10',
    text: 'text-blue-700 dark:text-blue-400',
    border: 'border-blue-500/30',
    dot: 'bg-blue-500',
  },
  absent: {
    label: 'Absent',
    bg: 'bg-rose-500/10',
    text: 'text-rose-700 dark:text-rose-400',
    border: 'border-rose-500/30',
    dot: 'bg-rose-500',
  },
  missing_checkout: {
    label: 'Missing Checkout',
    bg: 'bg-purple-500/10',
    text: 'text-purple-700 dark:text-purple-400',
    border: 'border-purple-500/30',
    dot: 'bg-purple-500',
  },
  on_leave: {
    label: 'On Leave',
    bg: 'bg-zinc-500/10',
    text: 'text-zinc-700 dark:text-zinc-400',
    border: 'border-zinc-500/30',
    dot: 'bg-zinc-500',
  },
};

/**
 * Visual styling configuration for approval requests (Leaves, Corrections).
 */
export const REQ_STATUS_CONFIG: Record<
  RequestStatus,
  { label: string; bg: string; text: string; border: string }
> = {
  pending: {
    label: 'Pending',
    bg: 'bg-amber-500/10',
    text: 'text-amber-700 dark:text-amber-400',
    border: 'border-amber-500/30',
  },
  approved: {
    label: 'Approved',
    bg: 'bg-emerald-500/10',
    text: 'text-emerald-700 dark:text-emerald-400',
    border: 'border-emerald-500/30',
  },
  rejected: {
    label: 'Rejected',
    bg: 'bg-rose-500/10',
    text: 'text-rose-700 dark:text-rose-400',
    border: 'border-rose-500/30',
  },
  cancelled: {
    label: 'Cancelled',
    bg: 'bg-zinc-500/10',
    text: 'text-zinc-600 dark:text-zinc-400',
    border: 'border-zinc-500/30',
  },
};
