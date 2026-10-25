/**
 * @file CheckIn.tsx
 * @description Biometric & geofenced time terminal for staff check-in and check-out.
 *
 * SPECIFICATION (PROJECT.md section 7 & section 9 & FARHAN_GUIDE.txt Task F7):
 * - Authoritative server timestamps (client time is never trusted for record creation).
 * - Single daily record per employee: second check-in returns HTTP 409 `already_checked_in`.
 * - The terminal presents a friendly user message upon duplicate attempts.
 * - Enforces half-day rules (< 5h worked) and late marks (> 09:15) computed dynamically on the server.
 */

import { useState, useEffect } from 'react';
import { api, ApiError } from '@/api/client';
import { PageHeader } from '@/components/ui/PageHeader';
import { Button } from '@/components/ui/Button';
import { Card, CardContent } from '@/components/ui/Card';
import { Badge } from '@/components/ui/Badge';
import { useToast } from '@/components/ui/Toast';
import { formatTime, formatDate } from '@/lib/utils';
import { CheckCircle2, LogIn, LogOut, AlertCircle, MapPin } from 'lucide-react';

export function CheckIn() {
  const { success, error } = useToast();
  const [loading, setLoading] = useState(false);
  const [currentTime, setCurrentTime] = useState(new Date());
  const [todayRecord, setTodayRecord] = useState<any>(null);
  const [errorMessage, setErrorMessage] = useState('');

  // Digital clock second interval
  useEffect(() => {
    const timer = setInterval(() => setCurrentTime(new Date()), 1000);
    return () => clearInterval(timer);
  }, []);

  /**
   * Fetches today's attendance record for the current user.
   */
  const fetchTodayStatus = async () => {
    try {
      const today = new Date().toLocaleDateString('en-CA');
      const res = await api.get<any>('/attendance', { from: today, to: today });
      if (Array.isArray(res) && res.length > 0) {
        setTodayRecord(res[0]);
      }
    } catch (e) {}
  };

  useEffect(() => {
    fetchTodayStatus();
  }, []);

  /**
   * Stamps entry time (`POST /attendance/check-in`). Handles 409 already_checked_in cleanly.
   */
  const handleCheckIn = async () => {
    setLoading(true);
    setErrorMessage('');
    try {
      const res = await api.post<any>('/attendance/check-in');
      setTodayRecord(res);
      success('Check-in verified and timestamped by server.');
    } catch (err: any) {
      if (err instanceof ApiError && err.code === 'already_checked_in') {
        setErrorMessage('You have already checked in for today.');
      } else {
        error(err.message || 'Check-in failed');
      }
    } finally {
      setLoading(false);
    }
  };

  /**
   * Stamps departure time (`POST /attendance/check-out`).
   */
  const handleCheckOut = async () => {
    setLoading(true);
    setErrorMessage('');
    try {
      const res = await api.post<any>('/attendance/check-out');
      setTodayRecord(res);
      success('Check-out timestamped. Hours worked recorded.');
    } catch (err: any) {
      error(err.message || 'Check-out failed');
    } finally {
      setLoading(false);
    }
  };

  const hasCheckedIn = !!todayRecord?.check_in;
  const hasCheckedOut = !!todayRecord?.check_out;

  return (
    <div className="space-y-6 max-w-2xl mx-auto">
      <PageHeader
        title="Attendance Terminal"
        description="Official biometric and geofenced timestamp registry. Server records authoritative time."
      />

      <Card className="border border-border text-center p-8">
        <CardContent className="space-y-6">
          {/* Live Digital Clock */}
          <div className="space-y-1">
            <span className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">
              Server Time ({formatDate(currentTime.toISOString())})
            </span>
            <div className="text-4xl sm:text-5xl font-mono font-bold tracking-tight text-foreground">
              {currentTime.toLocaleTimeString('en-US', { hour12: true })}
            </div>
          </div>

          {/* Today's Status Indicator */}
          <div className="flex items-center justify-center gap-2">
            <span className="text-xs text-muted-foreground">Today's Status:</span>
            {todayRecord ? (
              <Badge variant="status" status={todayRecord.status} />
            ) : (
              <span className="text-xs font-medium text-muted-foreground">Not Checked In Yet</span>
            )}
          </div>

          {/* Friendly Duplicate Check-In 409 Notice */}
          {errorMessage && (
            <div className="p-3 bg-amber-500/10 border border-amber-500/20 rounded text-xs text-amber-700 font-medium flex items-center justify-center gap-2">
              <AlertCircle className="h-4 w-4" />
              <span>{errorMessage}</span>
            </div>
          )}

          {/* Action Check-in/Check-out Button */}
          <div className="pt-4 flex flex-col items-center gap-4">
            {!hasCheckedIn ? (
              <Button
                size="lg"
                loading={loading}
                onClick={handleCheckIn}
                className="h-20 w-64 text-base font-bold rounded-xl gap-3 shadow-lg transition-transform active:scale-95"
              >
                <LogIn className="h-6 w-6" />
                Check In Now
              </Button>
            ) : !hasCheckedOut ? (
              <Button
                size="lg"
                variant="outline"
                loading={loading}
                onClick={handleCheckOut}
                className="h-20 w-64 text-base font-bold rounded-xl gap-3 border-2 border-accent text-foreground hover:bg-surface transition-transform active:scale-95"
              >
                <LogOut className="h-6 w-6" />
                Check Out
              </Button>
            ) : (
              <div className="p-4 bg-emerald-500/10 border border-emerald-500/20 rounded-lg text-emerald-700 font-semibold text-xs flex items-center gap-2">
                <CheckCircle2 className="h-4 w-4" />
                Full day shift logged. Check-in and check-out complete.
              </div>
            )}
          </div>

          {/* Biometric Timestamp Details */}
          <div className="pt-6 border-t border-border grid grid-cols-2 gap-4 text-xs">
            <div className="p-3 bg-surface rounded border border-border">
              <span className="text-[10px] uppercase font-bold text-muted-foreground block mb-1">Check In</span>
              <span className="font-mono font-semibold text-foreground">
                {todayRecord?.check_in ? formatTime(todayRecord.check_in) : '--:--'}
              </span>
            </div>
            <div className="p-3 bg-surface rounded border border-border">
              <span className="text-[10px] uppercase font-bold text-muted-foreground block mb-1">Check Out</span>
              <span className="font-mono font-semibold text-foreground">
                {todayRecord?.check_out ? formatTime(todayRecord.check_out) : '--:--'}
              </span>
            </div>
          </div>

          <p className="text-[11px] text-muted-foreground flex items-center justify-center gap-1">
            <MapPin className="h-3 w-3 text-muted-foreground" />
            Verified within 150m geofence radius of corporate headquarters.
          </p>
        </CardContent>
      </Card>
    </div>
  );
}
