import { useState } from 'react';
import { PageHeader } from '@/components/ui/PageHeader';
import { Button } from '@/components/ui/Button';
import { Card, CardContent } from '@/components/ui/Card';
import { Table, TableHeader, TableRow, TableHead, TableBody, TableCell } from '@/components/ui/Table';
import { useToast } from '@/components/ui/Toast';
import { formatCurrency } from '@/lib/utils';
import { Download, FileText, CheckCircle2 } from 'lucide-react';

export function MyPayslips() {
  const { success } = useToast();
  const [downloadingId, setDownloadingId] = useState<string | null>(null);

  // Sample payslips for employee
  const payslips = [
    {
      id: 'ps-oct-2026',
      month: 'October 2026',
      basic: 200000,
      gross: 300000,
      deductions: 0,
      tax: 27500,
      net: 272500,
      status: 'finalized',
    },
    {
      id: 'ps-sep-2026',
      month: 'September 2026',
      basic: 200000,
      gross: 300000,
      deductions: 6818,
      tax: 27500,
      net: 265682,
      status: 'finalized',
    },
  ];

  const handleDownload = (id: string, month: string) => {
    setDownloadingId(id);
    setTimeout(() => {
      // Simulate generated PDF blob download
      const element = document.createElement('a');
      const file = new Blob(
        [
          `--- HCM LITE OFFICIAL SALARY SLIP ---\n\nMonth: ${month}\nBasic Salary: PKR 200,000\nGross (1.5x): PKR 300,000\nTax: PKR 27,500\nNet Payout: PKR 272,500\n\nGenerated via ReportLab / HCM Lite Engine.`,
        ],
        { type: 'text/plain' }
      );
      element.href = URL.createObjectURL(file);
      element.download = `Payslip_${month.replace(' ', '_')}.txt`;
      document.body.appendChild(element);
      element.click();
      document.body.removeChild(element);
      setDownloadingId(null);
      success(`Payslip for ${month} downloaded.`);
    }, 400);
  };

  return (
    <div className="space-y-6">
      <PageHeader
        title="Compensation & Payslips"
        description="Official itemized salary statements and verified PDF payslip downloads."
      />

      <Card>
        <CardContent className="p-0">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Pay Period</TableHead>
                <TableHead>Basic Salary</TableHead>
                <TableHead>Gross (1.5x)</TableHead>
                <TableHead>Deductions</TableHead>
                <TableHead>Tax</TableHead>
                <TableHead>Net Pay</TableHead>
                <TableHead className="text-right">Payslip PDF</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {payslips.map((ps) => (
                <TableRow key={ps.id}>
                  <TableCell className="font-semibold text-xs text-foreground flex items-center gap-2">
                    <FileText className="h-4 w-4 text-muted-foreground" />
                    {ps.month}
                  </TableCell>
                  <TableCell className="font-mono text-xs">{formatCurrency(ps.basic)}</TableCell>
                  <TableCell className="font-mono text-xs">{formatCurrency(ps.gross)}</TableCell>
                  <TableCell className="font-mono text-xs text-rose-600">
                    {formatCurrency(ps.deductions)}
                  </TableCell>
                  <TableCell className="font-mono text-xs">{formatCurrency(ps.tax)}</TableCell>
                  <TableCell className="font-mono text-xs font-bold text-emerald-700 dark:text-emerald-400">
                    {formatCurrency(ps.net)}
                  </TableCell>
                  <TableCell className="text-right">
                    <Button
                      size="sm"
                      variant="outline"
                      loading={downloadingId === ps.id}
                      onClick={() => handleDownload(ps.id, ps.month)}
                      className="text-xs gap-1.5"
                    >
                      <Download className="h-3.5 w-3.5" />
                      Download
                    </Button>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </CardContent>
      </Card>
    </div>
  );
}
