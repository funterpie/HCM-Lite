import React from 'react';
import { cn } from '@/lib/utils';
import { Card } from './Card';

export interface StatCardProps {
  title: string;
  value: string | number;
  subtext?: string;
  icon?: React.ReactNode;
  trend?: {
    value: string;
    positive?: boolean;
  };
  className?: string;
}

export function StatCard({ title, value, subtext, icon, trend, className }: StatCardProps) {
  return (
    <Card className={cn('relative overflow-hidden', className)}>
      <div className="flex items-center justify-between">
        <p className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">{title}</p>
        {icon && <div className="text-muted-foreground">{icon}</div>}
      </div>
      <div className="mt-3 flex items-baseline gap-2">
        <span className="text-2xl font-bold tracking-tight text-foreground">{value}</span>
        {trend && (
          <span
            className={cn(
              'text-xs font-medium',
              trend.positive ? 'text-emerald-600' : 'text-rose-600'
            )}
          >
            {trend.value}
          </span>
        )}
      </div>
      {subtext && <p className="text-xs text-muted-foreground mt-1.5">{subtext}</p>}
    </Card>
  );
}
