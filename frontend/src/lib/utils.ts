/**
 * @file utils.ts
 * @description General utility functions for styling and locale-aware data formatting.
 * Provides CSS class merging via clsx/twMerge and Pakistani currency/date formatters.
 */

import { clsx, type ClassValue } from 'clsx';
import { twMerge } from 'tailwind-merge';

/**
 * Combines conditional class names and resolves Tailwind CSS class conflicts.
 *
 * @param inputs - Variable list of class values, objects, or arrays.
 * @returns Merged class name string with duplicate Tailwind rules resolved.
 */
export function cn(...inputs: ClassValue[]): string {
  return twMerge(clsx(inputs));
}

/**
 * Formats a numeric value into Pakistani Rupee (PKR) currency display format.
 *
 * @param amount - The numeric or string monetary amount.
 * @returns Formatted currency string, e.g. "PKR 150,000".
 */
export function formatCurrency(amount: number | string): string {
  const num = typeof amount === 'string' ? parseFloat(amount) : amount;
  if (isNaN(num)) return 'PKR 0';
  return new Intl.NumberFormat('en-PK', {
    style: 'currency',
    currency: 'PKR',
    maximumFractionDigits: 0,
  }).format(num);
}

/**
 * Formats an ISO date string or Date object into human-readable date (e.g., "Oct 24, 2026").
 *
 * @param dateStr - ISO string or Date instance.
 * @returns Formatted date string, or '-' if input is falsy.
 */
export function formatDate(dateStr: string | Date | undefined): string {
  if (!dateStr) return '-';
  const d = new Date(dateStr);
  return d.toLocaleDateString('en-US', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
  });
}

/**
 * Formats an ISO timestamp or time string into 12-hour AM/PM format (e.g., "09:15 AM").
 *
 * @param timeStr - ISO timestamp or time string.
 * @returns Formatted time string.
 */
export function formatTime(timeStr: string | Date | undefined): string {
  if (!timeStr) return '-';
  const d = new Date(timeStr);
  if (isNaN(d.getTime())) return timeStr.toString();
  return d.toLocaleTimeString('en-US', {
    hour: '2-digit',
    minute: '2-digit',
    hour12: true,
  });
}
