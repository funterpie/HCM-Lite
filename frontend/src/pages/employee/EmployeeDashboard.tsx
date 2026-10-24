import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { api } from '@/api/client';
import { PageHeader } from '@/components/ui/PageHeader';
import { StatCard } from '@/components/ui/StatCard';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { Badge } from '@/components/ui/Badge';
import { Skeleton } from '@/components/ui/Skeleton';
import { Clock, CalendarCheck, AlertTriangle, Bot, CheckCircle2, ArrowRight } from 'lucide-react';

export function EmployeeDashboard() {
  const navigate = useNavigate();
  const [data, setData] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function load() {
      try {
        const res = await api.get('/dashboard/me');
        setData(res);
      } catch (e) {
      } finally {
        setLoading(false);
      }
    }
    load();
  }, []);

  if (loading) {
    return <Skeleton className="h-96 w-full" />;
  }

  return (
    <div className="space-y-6">
      <PageHeader
        title="Personal Workspace"
        description="Individual timesheet hours, leave entitlement balances, and quick actions."
        action={
          <Button
            onClick={() => navigate('/ai-assistant')}
            className="gap-2 bg-purple-600 hover:bg-purple-700 text-white"
          >
            <Bot className="h-4 w-4" />
            Ask My Assistant
          </Button>
        }
      />

      {/* KPI Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <StatCard
          title="Hours Logged This Week"
          value={`${data?.hours_worked_this_week || 36} / 40`}
          subtext="Target: 40 hours standard shift"
          icon={<Clock className="h-4 w-4" />}
        />
        <StatCard
          title="Late Check-ins This Month"
          value={data?.late_count_month || 1}
          subtext="Threshold: 3 late check-ins deduct 0.5 day"
          icon={<AlertTriangle className="h-4 w-4 text-amber-500" />}
        />
        <StatCard
          title="Today's Terminal Status"
          value={data?.today_status || 'Present'}
          subtext={`Checked in at ${data?.check_in_time || '09:05 AM'}`}
          icon={<CheckCircle2 className="h-4 w-4 text-emerald-500" />}
        />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Quick Check-in Jump */}
        <Card>
          <CardHeader>
            <CardTitle className="text-sm">Attendance Terminal</CardTitle>
            <CardDescription>Log physical entry or departure for today's shift</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="p-4 bg-surface rounded-lg border border-border flex items-center justify-between">
              <div>
                <span className="text-xs text-muted-foreground block">Current Work Day</span>
                <span className="text-sm font-bold text-foreground">Shift Active</span>
              </div>
              <Badge variant="status" status="present" />
            </div>
            <Button
              onClick={() => navigate('/employee/check-in')}
              className="w-full justify-between"
            >
              Open Terminal & Punch Time
              <ArrowRight className="h-4 w-4" />
            </Button>
          </CardContent>
        </Card>

        {/* Leave Allowances */}
        <Card>
          <CardHeader>
            <CardTitle className="text-sm">Leave Balance Quotas</CardTitle>
            <CardDescription>Available allowances for this calendar year</CardDescription>
          </CardHeader>
          <CardContent className="space-y-3">
            <div className="grid grid-cols-3 gap-2 text-center">
              <div className="p-3 bg-surface rounded border border-border">
                <span className="text-[10px] text-muted-foreground uppercase font-bold">Annual</span>
                <p className="text-xl font-bold text-foreground mt-1">12</p>
                <span className="text-[10px] text-muted-foreground">days left</span>
              </div>
              <div className="p-3 bg-surface rounded border border-border">
                <span className="text-[10px] text-muted-foreground uppercase font-bold">Casual</span>
                <p className="text-xl font-bold text-foreground mt-1">7</p>
                <span className="text-[10px] text-muted-foreground">days left</span>
              </div>
              <div className="p-3 bg-surface rounded border border-border">
                <span className="text-[10px] text-muted-foreground uppercase font-bold">Sick</span>
                <p className="text-xl font-bold text-foreground mt-1">7</p>
                <span className="text-[10px] text-muted-foreground">days left</span>
              </div>
            </div>
            <Button
              variant="outline"
              onClick={() => navigate('/employee/leave')}
              className="w-full text-xs"
            >
              Apply Leave or Use Smart Leave AI
            </Button>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
