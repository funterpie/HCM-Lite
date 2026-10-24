import { useState, useEffect } from 'react';
import { api } from '@/api/client';
import { PageHeader } from '@/components/ui/PageHeader';
import { StatCard } from '@/components/ui/StatCard';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { AiBadge } from '@/components/ui/AiBadge';
import { Skeleton } from '@/components/ui/Skeleton';
import { Users, UserCheck, CalendarCheck, Clock, FileQuestion, Sparkles } from 'lucide-react';
import {
  ResponsiveContainer,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  CartesianGrid,
} from 'recharts';

export function HrDashboard() {
  const [data, setData] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [aiSummary, setAiSummary] = useState<string[] | null>(null);
  const [summarizing, setSummarizing] = useState(false);

  useEffect(() => {
    async function load() {
      try {
        const res = await api.get('/dashboard/hr');
        setData(res);
      } catch (e) {
      } finally {
        setLoading(false);
      }
    }
    load();
  }, []);

  const handleSummarize = async () => {
    setSummarizing(true);
    try {
      const res = await api.post<{ bullets: string[] }>('/ai/summarize', {
        dashboard: 'hr',
      });
      setAiSummary(res.bullets);
    } catch (e) {
    } finally {
      setSummarizing(false);
    }
  };

  if (loading) {
    return <Skeleton className="h-96 w-full" />;
  }

  const kpis = data?.kpis || {};

  return (
    <div className="space-y-6">
      <PageHeader
        title="Human Resources Dashboard"
        description="Daily workforce operational KPIs, real-time presence tracking, and pending action items."
        action={
          <Button
            onClick={handleSummarize}
            loading={summarizing}
            variant="outline"
            className="gap-2 border-purple-500/30 text-purple-700 dark:text-purple-300 hover:bg-purple-500/10"
          >
            <Sparkles className="h-4 w-4" />
            Summarize HR Activity
          </Button>
        }
      />

      {/* AI Summary Banner */}
      {aiSummary && (
        <Card className="border-purple-500/30 bg-purple-500/5">
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <div className="flex items-center gap-2">
              <Sparkles className="h-4 w-4 text-purple-600" />
              <CardTitle className="text-sm">HR Operations Intelligence</CardTitle>
            </div>
            <AiBadge />
          </CardHeader>
          <CardContent>
            <ul className="space-y-1.5 list-disc list-inside text-xs leading-relaxed text-foreground/90">
              {aiSummary.map((b, idx) => (
                <li key={idx}>{b}</li>
              ))}
            </ul>
          </CardContent>
        </Card>
      )}

      {/* Operational KPIs */}
      <div className="grid grid-cols-2 md:grid-cols-5 gap-3">
        <StatCard
          title="Headcount"
          value={kpis.headcount || 0}
          icon={<Users className="h-4 w-4" />}
        />
        <StatCard
          title="Present Today"
          value={kpis.present || 0}
          icon={<UserCheck className="h-4 w-4 text-emerald-600" />}
        />
        <StatCard
          title="On Leave"
          value={kpis.on_leave || 0}
          icon={<CalendarCheck className="h-4 w-4 text-blue-600" />}
        />
        <StatCard
          title="Late Today"
          value={kpis.late_today || 0}
          icon={<Clock className="h-4 w-4 text-amber-600" />}
        />
        <StatCard
          title="Pending Inbox"
          value={kpis.pending_approvals || 0}
          icon={<FileQuestion className="h-4 w-4 text-rose-600" />}
        />
      </div>

      {/* Visual Analytics */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card>
          <CardHeader>
            <CardTitle className="text-sm">Leave Utilization by Category (Days)</CardTitle>
            <CardDescription>Approved leave volume taken across the organization</CardDescription>
          </CardHeader>
          <CardContent className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={data?.leave_by_type || []}>
                <CartesianGrid strokeDasharray="3 3" opacity={0.15} />
                <XAxis dataKey="type" stroke="#888888" fontSize={11} />
                <YAxis stroke="#888888" fontSize={11} />
                <Tooltip
                  contentStyle={{
                    backgroundColor: 'var(--surface-elevated)',
                    borderColor: 'var(--border)',
                    fontSize: '12px',
                    borderRadius: '6px',
                  }}
                />
                <Bar dataKey="days" name="Days Taken" fill="#18181B" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="text-sm">Top Frequent Late-Comers</CardTitle>
            <CardDescription>Team members flagged after 09:15 AM</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="divide-y divide-border/60">
              {data?.top_late?.map((item: any, i: number) => (
                <div key={i} className="flex items-center justify-between py-3 text-xs">
                  <span className="font-semibold text-foreground">{item.employee}</span>
                  <span className="px-2.5 py-1 rounded bg-amber-500/10 text-amber-700 font-semibold border border-amber-500/20">
                    {item.count} Late Marks
                  </span>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
