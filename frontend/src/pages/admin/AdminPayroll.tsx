/**
 * @file AdminPayroll.tsx
 * @description Executive payroll authorization & finalization screen.
 *
 * SPECIFICATION (PROJECT.md section 7 & section 8):
 * - HR creates/reviews a draft run. ONLY Admin finalizes (`POST /payroll/runs/{id}/finalize`).
 * - Finalized runs are locked permanently via database trigger `lock_finalized_run()` and backend checks.
 * - Displays a visible "Locked" badge and disables recomputations once finalized.
 */

import { useState, useEffect } from 'react';
import { api } from '@/api/client';
import { PageHeader } from '@/components/ui/PageHeader';
import { Button } from '@/components/ui/Button';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/Card';
import { Table, TableHeader, TableRow, TableHead, TableBody, TableCell } from '@/components/ui/Table';
import { Badge } from '@/components/ui/Badge';
import { Modal } from '@/components/ui/Modal';
import { useToast } from '@/components/ui/Toast';
import { formatCurrency } from '@/lib/utils';
import { Lock, CheckCircle2, ShieldCheck } from 'lucide-react';

export function AdminPayroll() {
  const { success, error } = useToast();
  const [runs, setRuns] = useState<any[]>([]);
  const [activeRun, setActiveRun] = useState<any>(null);
  const [finalizeModal, setFinalizeModal] = useState(false);
  const [finalizing, setFinalizing] = useState(false);

  /**
   * Loads payroll runs and defaults to the most recent run.
   */
  const loadRuns = async () => {
    try {
      const res = await api.get<any[]>('/payroll/runs');
      if (Array.isArray(res)) {
        setRuns(res);
        if (res.length > 0 && !activeRun) {
          setActiveRun(res[0]);
        } else if (activeRun) {
          const updated = res.find((r) => r.id === activeRun.id);
          if (updated) setActiveRun(updated);
        }
      }
    } catch (e) {}
  };

  useEffect(() => {
    loadRuns();
  }, []);

  /**
   * Finalizes the current active payroll run and locks records.
   */
  const handleFinalize = async () => {
    if (!activeRun) return;
    setFinalizing(true);
    try {
      await api.post(`/payroll/runs/${activeRun.id}/finalize`);
      success(`Payroll run for ${activeRun.month} finalized and locked permanently.`);
      setFinalizeModal(false);
      loadRuns();
    } catch (err: any) {
      error(err.message || 'Finalization failed');
    } finally {
      setFinalizing(false);
    }
  };

  const isFinalized = activeRun?.status === 'finalized';

  return (
    <div className="space-y-6">
      <PageHeader
        title="Payroll Authorization & Finalization"
        description="Master approval and locking of monthly compensation runs. Only Administrators can finalize."
        action={
          activeRun && (
            <div className="flex items-center gap-3">
              {isFinalized ? (
                <Badge variant="locked" className="px-3 py-1 text-xs gap-1.5">
                  <Lock className="h-3.5 w-3.5" />
                  Finalized & Locked
                </Badge>
              ) : (
                <Button
                  onClick={() => setFinalizeModal(true)}
                  className="gap-2 bg-emerald-600 hover:bg-emerald-700 text-white"
                >
                  <ShieldCheck className="h-4 w-4" />
                  Finalize Payroll Run
                </Button>
              )}
            </div>
          )
        }
      />

      {/* Month Selector Tabs */}
      <div className="flex gap-2">
        {runs.map((r) => (
          <button
            key={r.id}
            onClick={() => setActiveRun(r)}
            className={`px-4 py-2 rounded text-xs font-semibold uppercase tracking-wider border transition-colors ${
              activeRun?.id === r.id
                ? 'bg-accent text-accent-foreground border-accent'
                : 'bg-surface text-muted-foreground border-border hover:bg-muted'
            }`}
          >
            {r.month} ({r.status})
          </button>
        ))}
      </div>

      {activeRun && (
        <Card>
          <CardHeader className="flex flex-row items-center justify-between">
            <div>
              <CardTitle className="text-sm">
                Payroll Statement for {activeRun.month}
              </CardTitle>
              <CardDescription>
                Gross compensation, attendance deductions, progressive tax slabs, and net payout.
              </CardDescription>
            </div>
            {isFinalized && (
              <span className="text-[11px] text-emerald-600 font-semibold inline-flex items-center gap-1">
                <CheckCircle2 className="h-4 w-4" />
                Immutable Record (DB Locked)
              </span>
            )}
          </CardHeader>
          <CardContent>
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Employee</TableHead>
                  <TableHead>Department</TableHead>
                  <TableHead>Basic</TableHead>
                  <TableHead>Gross (1.5x)</TableHead>
                  <TableHead>Deductions</TableHead>
                  <TableHead>Tax</TableHead>
                  <TableHead className="text-right">Net Payable</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {activeRun.payslips?.map((ps: any) => (
                  <TableRow key={ps.id}>
                    <TableCell className="font-semibold text-foreground">
                      {ps.employee_name}
                    </TableCell>
                    <TableCell className="text-xs text-muted-foreground">{ps.department}</TableCell>
                    <TableCell className="font-mono text-xs">{formatCurrency(ps.basic)}</TableCell>
                    <TableCell className="font-mono text-xs font-medium">{formatCurrency(ps.gross)}</TableCell>
                    <TableCell className="font-mono text-xs text-rose-600">
                      {formatCurrency(ps.deduction || 0)}
                    </TableCell>
                    <TableCell className="font-mono text-xs">{formatCurrency(ps.tax || 0)}</TableCell>
                    <TableCell className="font-mono text-xs font-bold text-emerald-700 dark:text-emerald-400 text-right">
                      {formatCurrency(ps.net)}
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </CardContent>
        </Card>
      )}

      {/* Confirmation Modal */}
      <Modal
        isOpen={finalizeModal}
        onClose={() => setFinalizeModal(false)}
        title="Finalize Payroll Run"
      >
        <div className="space-y-4">
          <p className="text-xs text-muted-foreground leading-relaxed">
            Finalizing this payroll run will permanently lock all payslips for <span className="font-bold text-foreground">{activeRun?.month}</span>.
            Database triggers will reject any further edits. Payslips will become immediately downloadable by employees.
          </p>
          <div className="p-3 bg-amber-500/10 border border-amber-500/20 rounded text-xs text-amber-700 font-medium">
            This action cannot be undone. Are you sure you wish to proceed?
          </div>
          <div className="flex justify-end gap-2 pt-2">
            <Button variant="outline" onClick={() => setFinalizeModal(false)}>
              Cancel
            </Button>
            <Button
              loading={finalizing}
              onClick={handleFinalize}
              className="bg-emerald-600 hover:bg-emerald-700 text-white"
            >
              Confirm Finalize & Lock
            </Button>
          </div>
        </div>
      </Modal>
    </div>
  );
}
