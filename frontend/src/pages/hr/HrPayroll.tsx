/**
 * @file HrPayroll.tsx
 * @description Monthly payroll draft compilation and compensation recalculation view for HR.
 *
 * SPECIFICATION (PROJECT.md section 7 & section 8):
 * - HR selects month and triggers draft run (`POST /payroll/runs`).
 * - Applies mathematical formulas:
 *   * Gross = 1.5 x basic (HRA 40%, Medical 10%).
 *   * Per day = gross / working days in month.
 *   * Deductions = per_day x (absent days + unpaid days + 0.5 x half days).
 *   * Progressive tax slab computation.
 * - Recalculate button is disabled once Admin finalizes the cycle.
 */

import { useState, useEffect } from 'react';
import { api } from '@/api/client';
import { PageHeader } from '@/components/ui/PageHeader';
import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/Card';
import { Table, TableHeader, TableRow, TableHead, TableBody, TableCell } from '@/components/ui/Table';
import { Badge } from '@/components/ui/Badge';
import { useToast } from '@/components/ui/Toast';
import { formatCurrency } from '@/lib/utils';
import { Play, RotateCw, Lock } from 'lucide-react';

export function HrPayroll() {
  const { success, error } = useToast();
  const [selectedMonth, setSelectedMonth] = useState('2026-10-01');
  const [runs, setRuns] = useState<any[]>([]);
  const [activeRun, setActiveRun] = useState<any>(null);
  const [computing, setComputing] = useState(false);

  /**
   * Loads payroll runs and selects the most recent cycle.
   */
  const loadRuns = async () => {
    try {
      const res = await api.get<any[]>('/payroll/runs');
      if (Array.isArray(res)) {
        setRuns(res);
        if (res.length > 0) setActiveRun(res[0]);
      }
    } catch (e) {}
  };

  useEffect(() => {
    loadRuns();
  }, []);

  /**
   * Triggers the backend service to calculate/recalculate the payroll draft for the selected month.
   */
  const handleComputeRun = async () => {
    setComputing(true);
    try {
      const res = await api.post<any>('/payroll/runs', { month: selectedMonth });
      success(`Payroll draft computed for ${selectedMonth}.`);
      setActiveRun(res);
      loadRuns();
    } catch (err: any) {
      error(err.message || 'Computation failed');
    } finally {
      setComputing(false);
    }
  };

  const isFinalized = activeRun?.status === 'finalized';

  return (
    <div className="space-y-6">
      <PageHeader
        title="Payroll Run Preparation"
        description="Compile monthly attendance records, deduct unpaid leaves & late marks, and calculate tax slabs."
        action={
          <div className="flex items-center gap-3">
            <Input
              type="date"
              value={selectedMonth}
              onChange={(e) => setSelectedMonth(e.target.value)}
              className="w-40"
            />
            <Button
              onClick={handleComputeRun}
              loading={computing}
              disabled={isFinalized}
              className="gap-2"
            >
              {activeRun ? <RotateCw className="h-4 w-4" /> : <Play className="h-4 w-4" />}
              {activeRun ? 'Recompute Draft' : 'Generate Payroll Draft'}
            </Button>
          </div>
        }
      />

      {/* Locked Payroll Alert */}
      {isFinalized && (
        <div className="p-4 rounded-lg bg-zinc-900 text-zinc-100 flex items-center justify-between">
          <div className="flex items-center gap-2 text-xs">
            <Lock className="h-4 w-4 text-amber-400" />
            <span>This payroll run has been finalized and locked by Admin. Changes are disabled.</span>
          </div>
          <Badge variant="locked">Locked</Badge>
        </div>
      )}

      {/* Active Run Statement Table */}
      {activeRun ? (
        <Card>
          <CardHeader>
            <div className="flex items-center justify-between">
              <div>
                <CardTitle className="text-sm">Compensation Draft ({activeRun.month})</CardTitle>
                <CardDescription>
                  Draft status ready for review prior to executive administrator finalization
                </CardDescription>
              </div>
              <span className="px-2.5 py-0.5 rounded text-xs font-semibold uppercase bg-amber-500/10 text-amber-700 border border-amber-500/20">
                {activeRun.status}
              </span>
            </div>
          </CardHeader>
          <CardContent className="p-0">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Employee</TableHead>
                  <TableHead>Department</TableHead>
                  <TableHead>Basic Salary</TableHead>
                  <TableHead>Gross (1.5x)</TableHead>
                  <TableHead>Attendance Deductions</TableHead>
                  <TableHead>Monthly Tax</TableHead>
                  <TableHead className="text-right">Net Compensation</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {activeRun.payslips?.map((ps: any) => (
                  <TableRow key={ps.id}>
                    <TableCell className="font-semibold text-xs text-foreground">
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
      ) : (
        <Card className="text-center p-12">
          <p className="text-sm text-muted-foreground">
            No payroll run found for this cycle. Select a date above and click Generate.
          </p>
        </Card>
      )}
    </div>
  );
}
