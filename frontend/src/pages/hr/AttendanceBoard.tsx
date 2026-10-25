/**
 * @file AttendanceBoard.tsx
 * @description Daily enterprise attendance board displaying check-in times, check-outs, and computed statuses.
 *
 * SPECIFICATION (PROJECT.md section 7 & section 8):
 * - Date and department filters (`GET /attendance/board?date&department_id`).
 * - Displays aggregate count pill badges (Present, Late, Absent).
 * - Read-only oversight for HR and Admin.
 */

import { useState, useEffect } from 'react';
import { api } from '@/api/client';
import { PageHeader } from '@/components/ui/PageHeader';
import { Input } from '@/components/ui/Input';
import { Select } from '@/components/ui/Select';
import { Card, CardContent } from '@/components/ui/Card';
import { Table, TableHeader, TableRow, TableHead, TableBody, TableCell } from '@/components/ui/Table';
import { Badge } from '@/components/ui/Badge';
import { formatTime } from '@/lib/utils';
import { CheckCircle2, AlertTriangle, UserX } from 'lucide-react';

export function AttendanceBoard() {
  const [boardDate, setBoardDate] = useState(new Date().toISOString().split('T')[0]);
  const [deptFilter, setDeptFilter] = useState('');
  const [boardData, setBoardData] = useState<any>(null);
  const [departments, setDepartments] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  /**
   * Fetches attendance board summary and records for the selected date and department.
   */
  const loadBoard = async () => {
    try {
      setLoading(true);
      const [res, depts] = await Promise.all([
        api.get<any>('/attendance/board', { date: boardDate, department_id: deptFilter }),
        api.get<any[]>('/departments'),
      ]);
      setBoardData(res);
      if (Array.isArray(depts)) setDepartments(depts);
    } catch (e) {
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadBoard();
  }, [boardDate, deptFilter]);

  return (
    <div className="space-y-6">
      <PageHeader
        title="Live Attendance Board"
        description="Daily company attendance status, physical check-ins, check-outs, and computed absences."
      />

      {/* Date & Dept Filter */}
      <div className="flex flex-col sm:flex-row gap-4 items-center justify-between">
        <div className="flex flex-wrap items-center gap-3 w-full sm:w-auto">
          <Input
            type="date"
            value={boardDate}
            onChange={(e) => setBoardDate(e.target.value)}
            className="w-44"
          />
          <div className="w-48">
            <Select
              placeholder="All Departments"
              value={deptFilter}
              onChange={(e) => setDeptFilter(e.target.value)}
              options={departments.map((d) => ({ label: d.name, value: d.id }))}
            />
          </div>
        </div>

        {/* Status Count Badges */}
        {boardData && (
          <div className="flex items-center gap-2 text-xs font-semibold">
            <span className="px-2.5 py-1 rounded bg-emerald-500/10 text-emerald-700 border border-emerald-500/20 inline-flex items-center gap-1">
              <CheckCircle2 className="h-3 w-3" />
              {boardData.present_count || 0} Present
            </span>
            <span className="px-2.5 py-1 rounded bg-amber-500/10 text-amber-700 border border-amber-500/20 inline-flex items-center gap-1">
              <AlertTriangle className="h-3 w-3" />
              {boardData.late_count || 0} Late
            </span>
            <span className="px-2.5 py-1 rounded bg-rose-500/10 text-rose-700 border border-rose-500/20 inline-flex items-center gap-1">
              <UserX className="h-3 w-3" />
              {boardData.absent_count || 0} Absent
            </span>
          </div>
        )}
      </div>

      {/* Records Table */}
      <Card>
        <CardContent className="p-0">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Code</TableHead>
                <TableHead>Employee</TableHead>
                <TableHead>Department</TableHead>
                <TableHead>Check In</TableHead>
                <TableHead>Check Out</TableHead>
                <TableHead>Status</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {boardData?.records?.length === 0 ? (
                <TableRow>
                  <TableCell colSpan={6} className="text-center py-8 text-xs text-muted-foreground">
                    No attendance records for the selected date.
                  </TableCell>
                </TableRow>
              ) : (
                boardData?.records?.map((rec: any) => (
                  <TableRow key={rec.employee_id}>
                    <TableCell className="font-mono text-xs font-semibold text-foreground">
                      {rec.employee_code}
                    </TableCell>
                    <TableCell className="font-medium text-xs text-foreground">
                      {rec.employee_name}
                    </TableCell>
                    <TableCell className="text-xs text-muted-foreground">{rec.department}</TableCell>
                    <TableCell className="font-mono text-xs">
                      {rec.check_in ? formatTime(rec.check_in) : '-'}
                    </TableCell>
                    <TableCell className="font-mono text-xs">
                      {rec.check_out ? formatTime(rec.check_out) : '-'}
                    </TableCell>
                    <TableCell>
                      <Badge variant="status" status={rec.status} />
                    </TableCell>
                  </TableRow>
                ))
              )}
            </TableBody>
          </Table>
        </CardContent>
      </Card>
    </div>
  );
}
