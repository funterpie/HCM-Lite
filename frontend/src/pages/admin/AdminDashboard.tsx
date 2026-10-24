import { useState, useEffect } from 'react';
import { api } from '@/api/client';
import { PageHeader } from '@/components/ui/PageHeader';
import { StatCard } from '@/components/ui/StatCard';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { AiBadge } from '@/components/ui/AiBadge';
import { Skeleton } from '@/components/ui/Skeleton';
import { formatCurrency } from '@/lib/utils';
import { Users, DollarSign, Clock, ShieldAlert, Sparkles, TrendingUp } from 'lucide-react';
import {
  ResponsiveContainer,
  LineChart,
  Line,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  CartesianGrid,
} from 'recharts';

export function AdminDashboard() {
  const [data, setData] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [aiSummary, setAiSummary] = useState<string[] | null>(null);
  const [summarizing, setSummarizing] = useState(false);

  useEffect(() => {
    async function loadDashboard() {
      try {
        const res = await api.get('/dashboard/admin');
        setData(res);
      } catch (e) {
      } finally {
        setLoading(false);
      }
    }
    loadDashboard();
  }, []);

  const handleSummarize = async () => {
    setSummarizing(true);
    try {
      const res = await api.post<{ bullets: string[] }>('/ai/summarize', {
        dashboard: 'admin',
      });
      setAiSummary(res.bullets);
    } catch (e) {
    } finally {
      setSummarizing(false);
    }
  };

  if (loading) {
    return (
      <div className="space-y-6">
        <Skeleton className="h-10 w-48" />
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          <Skeleton className="h-28" />
          <Skeleton className="h-28" />
          <Skeleton className="h-28" />
          <Skeleton className="h-28" />
        </div>
      </div>
    );
  }

  const kpis = data?.kpis || {};

  return (
    <div className="space-y-6">
      <PageHeader
        title="Executive Overview"
        description="High-level corporate metrics, payroll expenditure, and workforce analytics."
        action={
          <Button
            onClick={handleSummarize}
            loading={summarizing}
            variant="outline"
            className="gap-2 border-purple-500/30 text-purple-700 dark:text-purple-300 hover:bg-purple-500/10"
          >
            <Sparkles className="h-4 w-4" />
            Summarize with AI
          </Button>
        }
      />

      {/* AI Summary Banner */}
      {aiSummary && (
        <Card className="border-purple-500/30 bg-purple-500/5 transition-all">
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <div className="flex items-center gap-2">
              <Sparkles className="h-4 w-4 text-purple-600" />
              <CardTitle className="text-sm">Executive AI Briefing</CardTitle>
            </div>
            <AiBadge />
          </CardHeader>
          <CardContent>
            <ul className="space-y-1.5 list-disc list-inside text-xs text-foreground/90 leading-relaxed">
              {aiSummary.map((b, idx) => (
                <li key={idx}>{b}</li>
              ))}
            </ul>
          </CardContent>
        </Card>
      )}

      {/* Primary KPI Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard
          title="Total Headcount"
          value={kpis.headcount || 0}
          subtext="Active employees across all departments"
          icon={<Users className="h-4 w-4" />}
        />
        <StatCard
          title="Monthly Payroll"
          value={formatCurrency(kpis.monthly_payroll || 0)}
          subtext="Total company gross expenditure"
          icon={<DollarSign className="h-4 w-4" />}
        />
        <StatCard
          title="Average Salary"
          value={formatCurrency(kpis.avg_salary || 0)}
          subtext="Company-wide mean package"
          icon={<TrendingUp className="h-4 w-4" />}
        />
        <StatCard
          title="Attrition Rate"
          value={`${kpis.attrition_rate || 0}%`}
          subtext="YTD turnover percentage"
          icon={<ShieldAlert className="h-4 w-4" />}
        />
      </div>

      {/* Charts Section */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Attendance Trend Line */}
        <Card>
          <CardHeader>
            <CardTitle className="text-sm">Attendance Trend (Past 5 Days)</CardTitle>
            <CardDescription>Daily verified physical & remote check-in percentage</CardDescription>
          </CardHeader>
          <CardContent className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={data?.attendance_trend || []}>
                <CartesianGrid strokeDasharray="3 3" opacity={0.15} />
                <XAxis dataKey="date" stroke="#888888" fontSize={11} />
                <YAxis domain={[80, 100]} stroke="#888888" fontSize={11} />
                <Tooltip
                  contentStyle={{
                    backgroundColor: 'var(--surface-elevated)',
                    borderColor: 'var(--border)',
                    fontSize: '12px',
                    borderRadius: '6px',
                  }}
                />
                <Line
                  type="monotone"
                  dataKey="rate"
                  name="Rate (%)"
                  stroke="#18181B"
                  strokeWidth={2}
                  dot={{ r: 4 }}
                />
              </LineChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>

        {/* Absenteeism by Department */}
        <Card>
          <CardHeader>
            <CardTitle className="text-sm">Absenteeism Rate by Department</CardTitle>
            <CardDescription>Unplanned leaves and missed check-ins (%)</CardDescription>
          </CardHeader>
          <CardContent className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={data?.absenteeism_by_dept || []}>
                <CartesianGrid strokeDasharray="3 3" opacity={0.15} />
                <XAxis dataKey="department" stroke="#888888" fontSize={11} />
                <YAxis stroke="#888888" fontSize={11} />
                <Tooltip
                  contentStyle={{
                    backgroundColor: 'var(--surface-elevated)',
                    borderColor: 'var(--border)',
                    fontSize: '12px',
                    borderRadius: '6px',
                  }}
                />
                <Bar dataKey="pct" name="Absenteeism %" fill="#18181B" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>
      </div>

      {/* Top Late-Comers Summary */}
      <Card>
        <CardHeader>
          <div className="flex items-center gap-2">
            <Clock className="h-4 w-4 text-amber-500" />
            <CardTitle className="text-sm">Most Frequent Late Arrivals This Month</CardTitle>
          </div>
          <CardDescription>Employees exceeding the 15-minute grace threshold</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="divide-y divide-border/60">
            {data?.top_late?.map((item: any, i: number) => (
              <div key={i} className="flex items-center justify-between py-2.5 text-xs">
                <span className="font-medium text-foreground">{item.employee}</span>
                <span className="px-2 py-0.5 rounded bg-amber-500/10 text-amber-700 font-semibold border border-amber-500/20">
                  {item.count} late {item.count === 1 ? 'arrival' : 'arrivals'}
                </span>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
