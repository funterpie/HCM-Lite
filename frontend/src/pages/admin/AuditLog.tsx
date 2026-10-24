import { useState } from 'react';
import { PageHeader } from '@/components/ui/PageHeader';
import { Card, CardContent } from '@/components/ui/Card';
import { Table, TableHeader, TableRow, TableHead, TableBody, TableCell } from '@/components/ui/Table';
import { formatDate } from '@/lib/utils';
import { ShieldCheck, ChevronDown, ChevronRight } from 'lucide-react';

export function AuditLog() {
  const [expandedId, setExpandedId] = useState<number | null>(null);

  // Mocked audit records conforming to schema.sql
  const logs = [
    {
      id: 1,
      actor: 'admin@nexustech.com',
      action: 'FINALIZE_PAYROLL',
      entity: 'payroll_runs',
      entity_id: 'pr-1',
      before: { status: 'draft' },
      after: { status: 'finalized', finalized_at: '2026-10-25T04:00:00Z' },
      created_at: new Date().toISOString(),
    },
    {
      id: 2,
      actor: 'hr@nexustech.com',
      action: 'APPROVE_LEAVE',
      entity: 'leave_requests',
      entity_id: 'lr-1',
      before: { status: 'pending' },
      after: { status: 'approved', hr_comment: 'Approved for family event' },
      created_at: new Date(Date.now() - 3600000).toISOString(),
    },
    {
      id: 3,
      actor: 'admin@nexustech.com',
      action: 'UPDATE_SETTINGS',
      entity: 'settings',
      entity_id: '1',
      before: { grace_minutes: 10 },
      after: { grace_minutes: 15 },
      created_at: new Date(Date.now() - 7200000).toISOString(),
    },
    {
      id: 4,
      actor: 'hr@nexustech.com',
      action: 'REGISTER_EMPLOYEE',
      entity: 'employees',
      entity_id: 'emp-dev-1',
      before: null,
      after: { code: 'EMP003', full_name: 'Zeeshan Ahmed', basic_salary: 200000 },
      created_at: new Date(Date.now() - 86400000).toISOString(),
    },
  ];

  return (
    <div className="space-y-6">
      <PageHeader
        title="Immutable Audit Trail"
        description="Append-only regulatory activity log capturing all Administrative, HR and Authorization events."
        action={
          <span className="text-xs text-muted-foreground flex items-center gap-1.5 font-medium">
            <ShieldCheck className="h-4 w-4 text-emerald-600" />
            PostgreSQL Append-Only Guard
          </span>
        }
      />

      <Card>
        <CardContent className="p-0">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead className="w-10"></TableHead>
                <TableHead>Timestamp</TableHead>
                <TableHead>Actor</TableHead>
                <TableHead>Action</TableHead>
                <TableHead>Entity</TableHead>
                <TableHead>Entity ID</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {logs.map((log) => {
                const isExpanded = expandedId === log.id;
                return (
                  <React.Fragment key={log.id}>
                    <TableRow
                      onClick={() => setExpandedId(isExpanded ? null : log.id)}
                      className="cursor-pointer"
                    >
                      <TableCell className="text-muted-foreground">
                        {isExpanded ? <ChevronDown className="h-4 w-4" /> : <ChevronRight className="h-4 w-4" />}
                      </TableCell>
                      <TableCell className="font-mono text-xs text-muted-foreground">
                        {formatDate(log.created_at)}
                      </TableCell>
                      <TableCell className="font-medium text-xs text-foreground">{log.actor}</TableCell>
                      <TableCell>
                        <span className="font-mono text-[11px] font-semibold px-2 py-0.5 rounded bg-muted text-foreground border border-border">
                          {log.action}
                        </span>
                      </TableCell>
                      <TableCell className="text-xs font-mono">{log.entity}</TableCell>
                      <TableCell className="text-xs font-mono text-muted-foreground">{log.entity_id}</TableCell>
                    </TableRow>
                    {isExpanded && (
                      <TableRow className="bg-surface/50">
                        <TableCell colSpan={6} className="p-4">
                          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs font-mono">
                            <div className="p-3 rounded border border-border bg-background">
                              <span className="text-[10px] uppercase font-bold text-muted-foreground block mb-1">
                                Before State:
                              </span>
                              <pre className="text-rose-600 dark:text-rose-400 overflow-x-auto whitespace-pre-wrap">
                                {JSON.stringify(log.before, null, 2) || 'null'}
                              </pre>
                            </div>
                            <div className="p-3 rounded border border-border bg-background">
                              <span className="text-[10px] uppercase font-bold text-muted-foreground block mb-1">
                                After State:
                              </span>
                              <pre className="text-emerald-600 dark:text-emerald-400 overflow-x-auto whitespace-pre-wrap">
                                {JSON.stringify(log.after, null, 2)}
                              </pre>
                            </div>
                          </div>
                        </TableCell>
                      </TableRow>
                    )}
                  </React.Fragment>
                );
              })}
            </TableBody>
          </Table>
        </CardContent>
      </Card>
    </div>
  );
}
