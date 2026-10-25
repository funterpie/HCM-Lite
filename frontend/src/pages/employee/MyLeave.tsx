/**
 * @file MyLeave.tsx
 * @description Leave management, balance monitoring, and AI-assisted application ("Smart Leave").
 *
 * SPECIFICATION (PROJECT.md section 7 & section 12 & FARHAN_GUIDE.txt Task F8):
 * - Displays computed balance cards (`quota - approved_days`).
 * - History table with cancellation for pending requests.
 * - Application form: skips weekends and holidays automatically.
 * - Displays HTTP 422 error codes clearly (`overlap` and `insufficient_balance`).
 * - "Smart Leave" AI box: user types natural language (e.g. "need next Monday and Tuesday off for my sister's wedding").
 *   Invokes `POST /ai/smart-leave`, pre-fills form with validated JSON, labels with "AI-generated",
 *   and strictly requires human confirmation before saving.
 */

import React, { useState, useEffect } from 'react';
import { api, ApiError } from '@/api/client';
import { PageHeader } from '@/components/ui/PageHeader';
import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';
import { Select } from '@/components/ui/Select';
import { Textarea } from '@/components/ui/Textarea';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/Card';
import { Table, TableHeader, TableRow, TableHead, TableBody, TableCell } from '@/components/ui/Table';
import { Badge } from '@/components/ui/Badge';
import { AiBadge } from '@/components/ui/AiBadge';
import { useToast } from '@/components/ui/Toast';
import { formatDate } from '@/lib/utils';
import { Sparkles, Send, AlertCircle } from 'lucide-react';

export function MyLeave() {
  const { success, error } = useToast();

  const [balances, setBalances] = useState<any[]>([]);
  const [leaveTypes, setLeaveTypes] = useState<any[]>([]);
  const [history, setHistory] = useState<any[]>([]);

  // Smart Leave AI State
  const [smartPrompt, setSmartPrompt] = useState('');
  const [smartLoading, setSmartLoading] = useState(false);
  const [aiFilled, setAiFilled] = useState(false);

  // Application Form State
  const [leaveTypeId, setLeaveTypeId] = useState('');
  const [startDate, setStartDate] = useState('');
  const [endDate, setEndDate] = useState('');
  const [reason, setReason] = useState('');
  const [applying, setApplying] = useState(false);
  const [formError, setFormError] = useState('');

  /**
   * Loads personal leave quotas, categories, and previous submission records.
   */
  const loadData = async () => {
    try {
      const [b, lt, h] = await Promise.all([
        api.get<any[]>('/leave/balance'),
        api.get<any[]>('/leave-types'),
        api.get<any[]>('/leave'),
      ]);
      if (Array.isArray(b)) setBalances(b);
      if (Array.isArray(lt)) {
        setLeaveTypes(lt);
        if (lt.length > 0 && !leaveTypeId) setLeaveTypeId(lt[0].id);
      }
      if (Array.isArray(h)) setHistory(h);
    } catch (e) {}
  };

  useEffect(() => {
    loadData();
  }, []);

  /**
   * Smart Leave AI Handler.
   * Sends user's natural language sentence to the backend and pre-fills the form with interpreted fields.
   */
  const handleSmartLeave = async () => {
    if (!smartPrompt.trim()) return;
    setSmartLoading(true);
    setFormError('');
    try {
      const res = await api.post<any>('/ai/smart-leave', { text: smartPrompt });
      if (res) {
        if (res.leave_type_id) setLeaveTypeId(res.leave_type_id);
        if (res.start_date) setStartDate(res.start_date);
        if (res.end_date) setEndDate(res.end_date);
        if (res.reason) setReason(res.reason);
        setAiFilled(true);
        success('Form populated from natural language prompt. Please verify and confirm below.');
      }
    } catch (err: any) {
      error('Could not interpret prompt automatically. Please complete the form manually.');
    } finally {
      setSmartLoading(false);
    }
  };

  /**
   * Submits verified leave application.
   * Handles 422 overlap and insufficient_balance responses with clear user feedback.
   */
  const handleApply = async (e: React.FormEvent) => {
    e.preventDefault();
    setFormError('');
    setApplying(true);
    try {
      await api.post('/leave', {
        leave_type_id: leaveTypeId,
        start_date: startDate,
        end_date: endDate,
        reason,
      });
      success('Leave application submitted for supervisor approval.');
      setReason('');
      setAiFilled(false);
      setSmartPrompt('');
      loadData();
    } catch (err: any) {
      if (err instanceof ApiError) {
        if (err.code === 'overlap') {
          setFormError('Leave dates overlap with another pending or approved request.');
        } else if (err.code === 'insufficient_balance') {
          setFormError('Insufficient leave balance available for the requested duration.');
        } else {
          setFormError(err.message);
        }
      } else {
        setFormError('Submission failed');
      }
    } finally {
      setApplying(false);
    }
  };

  return (
    <div className="space-y-6">
      <PageHeader
        title="Leave Management & Allowances"
        description="View remaining annual quotas, request working-day leaves, or use AI Smart Leave."
      />

      {/* Balance Quota Summary Cards */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
        {balances.map((b) => (
          <Card key={b.leave_type_id} className="p-4">
            <span className="text-[10px] font-bold uppercase tracking-wider text-muted-foreground block">
              {b.name}
            </span>
            <div className="mt-2 flex items-baseline justify-between">
              <span className="text-2xl font-bold tracking-tight text-foreground">
                {b.remaining}
              </span>
              <span className="text-xs text-muted-foreground">
                {b.quota !== null ? `of ${b.quota} days` : 'unlimited'}
              </span>
            </div>
            <div className="mt-2 text-[11px] text-muted-foreground">
              Used: <span className="font-semibold text-foreground">{b.used} days</span>
            </div>
          </Card>
        ))}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Application & Smart Leave Column */}
        <div className="lg:col-span-1 space-y-6">
          {/* Smart Leave AI Input Card */}
          <Card className="border-purple-500/30 bg-purple-500/5">
            <CardHeader className="flex flex-row items-center justify-between pb-2">
              <div className="flex items-center gap-2">
                <Sparkles className="h-4 w-4 text-purple-600" />
                <CardTitle className="text-sm">Smart Leave AI</CardTitle>
              </div>
              <AiBadge />
            </CardHeader>
            <CardContent className="space-y-3">
              <p className="text-xs text-muted-foreground">
                Type in natural language (e.g. <em>"need next Monday and Tuesday off for my sister's wedding"</em>).
              </p>
              <Textarea
                placeholder="Explain in plain words when and why you need off..."
                value={smartPrompt}
                onChange={(e) => setSmartPrompt(e.target.value)}
                className="bg-background text-xs"
                rows={3}
              />
              <Button
                size="sm"
                variant="outline"
                loading={smartLoading}
                onClick={handleSmartLeave}
                className="w-full text-xs gap-1.5 border-purple-500/30 text-purple-700 dark:text-purple-300 hover:bg-purple-500/10"
              >
                <Sparkles className="h-3.5 w-3.5" />
                Auto-Fill Application Form
              </Button>
            </CardContent>
          </Card>

          {/* Leave Application Form */}
          <Card>
            <CardHeader className="flex flex-row items-center justify-between pb-2">
              <div>
                <CardTitle className="text-sm">Apply for Leave</CardTitle>
                <CardDescription>Working days only (weekends skipped)</CardDescription>
              </div>
              {aiFilled && <AiBadge />}
            </CardHeader>
            <CardContent>
              <form onSubmit={handleApply} className="space-y-4">
                {formError && (
                  <div className="p-3 bg-rose-500/10 border border-rose-500/20 rounded text-xs text-rose-600 font-medium flex items-center gap-2">
                    <AlertCircle className="h-4 w-4 shrink-0" />
                    <span>{formError}</span>
                  </div>
                )}

                <Select
                  label="Leave Category"
                  required
                  value={leaveTypeId}
                  onChange={(e) => setLeaveTypeId(e.target.value)}
                  options={leaveTypes.map((lt) => ({ label: lt.name, value: lt.id }))}
                />

                <div className="grid grid-cols-2 gap-3">
                  <Input
                    label="Start Date"
                    type="date"
                    required
                    value={startDate}
                    onChange={(e) => setStartDate(e.target.value)}
                  />
                  <Input
                    label="End Date"
                    type="date"
                    required
                    value={endDate}
                    onChange={(e) => setEndDate(e.target.value)}
                  />
                </div>

                <Textarea
                  label="Reason / Purpose"
                  required
                  value={reason}
                  onChange={(e) => setReason(e.target.value)}
                  placeholder="Reason for requesting time off..."
                  rows={2}
                />

                <Button type="submit" loading={applying} className="w-full gap-2">
                  <Send className="h-3.5 w-3.5" />
                  Confirm & Apply
                </Button>
              </form>
            </CardContent>
          </Card>
        </div>

        {/* History Records Column */}
        <div className="lg:col-span-2">
          <Card>
            <CardHeader>
              <CardTitle className="text-sm">Leave History & Status</CardTitle>
              <CardDescription>Track pending requests and past approved leaves</CardDescription>
            </CardHeader>
            <CardContent className="p-0">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Type</TableHead>
                    <TableHead>Period</TableHead>
                    <TableHead>Working Days</TableHead>
                    <TableHead>Reason</TableHead>
                    <TableHead>Status</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {history.length === 0 ? (
                    <TableRow>
                      <TableCell colSpan={5} className="text-center py-8 text-xs text-muted-foreground">
                        No previous leave records found.
                      </TableCell>
                    </TableRow>
                  ) : (
                    history.map((h) => (
                      <TableRow key={h.id}>
                        <TableCell className="font-semibold text-xs text-foreground">
                          {h.leave_type_name}
                        </TableCell>
                        <TableCell className="font-mono text-xs text-muted-foreground">
                          {formatDate(h.start_date)} to {formatDate(h.end_date)}
                        </TableCell>
                        <TableCell className="text-xs font-semibold">{h.days} days</TableCell>
                        <TableCell className="text-xs text-foreground max-w-xs truncate">
                          {h.reason}
                        </TableCell>
                        <TableCell>
                          <Badge variant="request" requestStatus={h.status} />
                        </TableCell>
                      </TableRow>
                    ))
                  )}
                </TableBody>
              </Table>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}
