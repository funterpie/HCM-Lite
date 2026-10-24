import React, { useState, useEffect } from 'react';
import { api } from '@/api/client';
import { PageHeader } from '@/components/ui/PageHeader';
import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';
import { Textarea } from '@/components/ui/Textarea';
import { Card, CardContent } from '@/components/ui/Card';
import { Table, TableHeader, TableRow, TableHead, TableBody, TableCell } from '@/components/ui/Table';
import { Badge } from '@/components/ui/Badge';
import { Modal } from '@/components/ui/Modal';
import { useToast } from '@/components/ui/Toast';
import { formatDate, formatTime } from '@/lib/utils';
import { FileEdit } from 'lucide-react';

export function MyAttendance() {
  const { success, error } = useToast();
  const [records, setRecords] = useState<any[]>([]);
  const [modalOpen, setModalOpen] = useState(false);
  const [corrDate, setCorrDate] = useState('');
  const [corrIn, setCorrIn] = useState('');
  const [corrOut, setCorrOut] = useState('');
  const [corrReason, setCorrReason] = useState('');
  const [submitting, setSubmitting] = useState(false);

  // Generate sample monthly calendar data
  useEffect(() => {
    // Mock sample attendance log for employee
    const sampleRecords = [
      {
        id: 'att-1',
        date: '2026-10-24',
        check_in: '2026-10-24T09:04:00Z',
        check_out: '2026-10-24T18:00:00Z',
        status: 'present',
      },
      {
        id: 'att-2',
        date: '2026-10-23',
        check_in: '2026-10-23T09:18:00Z',
        check_out: '2026-10-23T18:05:00Z',
        status: 'late',
      },
      {
        id: 'att-3',
        date: '2026-10-22',
        check_in: '2026-10-22T09:00:00Z',
        check_out: '2026-10-22T17:30:00Z',
        status: 'present',
      },
      {
        id: 'att-4',
        date: '2026-10-21',
        check_in: '2026-10-21T09:10:00Z',
        check_out: '2026-10-21T13:30:00Z',
        status: 'half_day',
      },
      {
        id: 'att-5',
        date: '2026-10-20',
        check_in: null,
        check_out: null,
        status: 'on_leave',
      },
    ];
    setRecords(sampleRecords);
  }, []);

  const handleRequestCorrection = async (e: React.FormEvent) => {
    e.preventDefault();
    setSubmitting(true);
    try {
      await api.post('/attendance/corrections', {
        date: corrDate,
        new_check_in: corrIn ? `${corrDate}T${corrIn}:00Z` : undefined,
        new_check_out: corrOut ? `${corrDate}T${corrOut}:00Z` : undefined,
        reason: corrReason,
      });
      success('Correction appeal submitted for HR review.');
      setModalOpen(false);
      setCorrReason('');
    } catch (err: any) {
      error(err.message || 'Submission failed');
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="space-y-6">
      <PageHeader
        title="Personal Attendance History"
        description="Daily biometric timestamps, calculated status, and attendance correction appeals."
        action={
          <Button onClick={() => setModalOpen(true)} className="gap-2 text-xs">
            <FileEdit className="h-4 w-4" />
            Request Attendance Correction
          </Button>
        }
      />

      <Card>
        <CardContent className="p-0">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Date</TableHead>
                <TableHead>Check In Time</TableHead>
                <TableHead>Check Out Time</TableHead>
                <TableHead>Calculated Status</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {records.map((r) => (
                <TableRow key={r.id}>
                  <TableCell className="font-mono text-xs font-semibold text-foreground">
                    {formatDate(r.date)}
                  </TableCell>
                  <TableCell className="font-mono text-xs">
                    {r.check_in ? formatTime(r.check_in) : '--:--'}
                  </TableCell>
                  <TableCell className="font-mono text-xs">
                    {r.check_out ? formatTime(r.check_out) : '--:--'}
                  </TableCell>
                  <TableCell>
                    <Badge variant="status" status={r.status} />
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </CardContent>
      </Card>

      {/* Correction Modal */}
      <Modal
        isOpen={modalOpen}
        onClose={() => setModalOpen(false)}
        title="Request Attendance Correction"
        description="Submit an appeal if biometric hardware failed or timings require manual reconciliation."
      >
        <form onSubmit={handleRequestCorrection} className="space-y-4">
          <Input
            label="Correction Date"
            type="date"
            required
            value={corrDate}
            onChange={(e) => setCorrDate(e.target.value)}
          />

          <div className="grid grid-cols-2 gap-3">
            <Input
              label="Actual Check In"
              type="time"
              required
              value={corrIn}
              onChange={(e) => setCorrIn(e.target.value)}
            />
            <Input
              label="Actual Check Out"
              type="time"
              required
              value={corrOut}
              onChange={(e) => setCorrOut(e.target.value)}
            />
          </div>

          <Textarea
            label="Justification Reason"
            required
            value={corrReason}
            onChange={(e) => setCorrReason(e.target.value)}
            placeholder="Explain why biometric check-in was missed..."
          />

          <div className="flex justify-end gap-2 pt-2">
            <Button type="button" variant="outline" onClick={() => setModalOpen(false)}>
              Cancel
            </Button>
            <Button type="submit" loading={submitting}>
              Submit Appeal
            </Button>
          </div>
        </form>
      </Modal>
    </div>
  );
}
