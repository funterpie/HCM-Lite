import { useState, useEffect } from 'react';
import { api } from '@/api/client';
import { PageHeader } from '@/components/ui/PageHeader';
import { Button } from '@/components/ui/Button';
import { Card, CardContent } from '@/components/ui/Card';
import { Table, TableHeader, TableRow, TableHead, TableBody, TableCell } from '@/components/ui/Table';
import { Badge } from '@/components/ui/Badge';
import { Modal } from '@/components/ui/Modal';
import { Textarea } from '@/components/ui/Textarea';
import { useToast } from '@/components/ui/Toast';
import { formatDate } from '@/lib/utils';
import { Check, X, CalendarCheck2 } from 'lucide-react';

export function LeaveInbox() {
  const { success, error } = useToast();
  const [leaves, setLeaves] = useState<any[]>([]);
  const [selectedLeave, setSelectedLeave] = useState<any>(null);
  const [decision, setDecision] = useState<'approved' | 'rejected'>('approved');
  const [comment, setComment] = useState('');
  const [processing, setProcessing] = useState(false);

  const loadLeaves = async () => {
    try {
      const res = await api.get<any[]>('/leave');
      if (Array.isArray(res)) setLeaves(res);
    } catch (e) {}
  };

  useEffect(() => {
    loadLeaves();
  }, []);

  const handleDecide = async () => {
    if (!selectedLeave) return;
    if (decision === 'rejected' && !comment.trim()) {
      error('A comment is strictly required when rejecting a leave application.');
      return;
    }

    setProcessing(true);
    try {
      await api.patch(`/leave/${selectedLeave.id}/decide`, {
        decision,
        comment,
      });
      success(`Leave application ${decision}.`);
      setSelectedLeave(null);
      setComment('');
      loadLeaves();
    } catch (err: any) {
      error(err.message || 'Action failed');
    } finally {
      setProcessing(false);
    }
  };

  return (
    <div className="space-y-6">
      <PageHeader
        title="Leave Inbox & Approvals"
        description="Review incoming annual, sick, and casual leave applications submitted by staff."
      />

      <Card>
        <CardContent className="p-0">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Employee</TableHead>
                <TableHead>Category</TableHead>
                <TableHead>Duration</TableHead>
                <TableHead>Working Days</TableHead>
                <TableHead>Employee Justification</TableHead>
                <TableHead>Status</TableHead>
                <TableHead className="text-right">Actions</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {leaves.length === 0 ? (
                <TableRow>
                  <TableCell colSpan={7} className="text-center py-8 text-xs text-muted-foreground">
                    No leave requests found.
                  </TableCell>
                </TableRow>
              ) : (
                leaves.map((l) => (
                  <TableRow key={l.id}>
                    <TableCell className="font-semibold text-xs text-foreground">
                      {l.employee_name}
                    </TableCell>
                    <TableCell className="text-xs font-medium">{l.leave_type_name}</TableCell>
                    <TableCell className="font-mono text-xs text-muted-foreground">
                      {formatDate(l.start_date)} to {formatDate(l.end_date)}
                    </TableCell>
                    <TableCell className="font-semibold text-xs">
                      {l.days} {l.days === 1 ? 'day' : 'days'}
                    </TableCell>
                    <TableCell className="text-xs text-foreground max-w-xs truncate">
                      {l.reason}
                    </TableCell>
                    <TableCell>
                      <Badge variant="request" requestStatus={l.status} />
                    </TableCell>
                    <TableCell className="text-right space-x-1">
                      {l.status === 'pending' && (
                        <>
                          <Button
                            size="sm"
                            variant="outline"
                            onClick={() => {
                              setSelectedLeave(l);
                              setDecision('approved');
                            }}
                            className="text-xs text-emerald-600 hover:bg-emerald-50 border-emerald-500/30 gap-1"
                          >
                            <Check className="h-3.5 w-3.5" />
                            Approve
                          </Button>
                          <Button
                            size="sm"
                            variant="outline"
                            onClick={() => {
                              setSelectedLeave(l);
                              setDecision('rejected');
                            }}
                            className="text-xs text-rose-600 hover:bg-rose-50 border-rose-500/30 gap-1"
                          >
                            <X className="h-3.5 w-3.5" />
                            Reject
                          </Button>
                        </>
                      )}
                    </TableCell>
                  </TableRow>
                ))
              )}
            </TableBody>
          </Table>
        </CardContent>
      </Card>

      <Modal
        isOpen={!!selectedLeave}
        onClose={() => setSelectedLeave(null)}
        title={`${decision === 'approved' ? 'Approve' : 'Reject'} Leave Request`}
      >
        <div className="space-y-4">
          <p className="text-xs text-muted-foreground">
            Employee: <span className="font-bold text-foreground">{selectedLeave?.employee_name}</span> (
            {selectedLeave?.leave_type_name}, {selectedLeave?.days} working days).
          </p>
          <Textarea
            label="HR Decision Comments"
            required={decision === 'rejected'}
            value={comment}
            onChange={(e) => setComment(e.target.value)}
            placeholder={
              decision === 'rejected'
                ? 'Mandatory: Explain reason for leave rejection...'
                : 'Optional notes for employee record...'
            }
          />
          <div className="flex justify-end gap-2 pt-2">
            <Button variant="outline" onClick={() => setSelectedLeave(null)}>
              Cancel
            </Button>
            <Button
              loading={processing}
              onClick={handleDecide}
              className={
                decision === 'approved'
                  ? 'bg-emerald-600 hover:bg-emerald-700 text-white'
                  : 'bg-rose-600 hover:bg-rose-700 text-white'
              }
            >
              Confirm {decision === 'approved' ? 'Approval' : 'Rejection'}
            </Button>
          </div>
        </div>
      </Modal>
    </div>
  );
}
