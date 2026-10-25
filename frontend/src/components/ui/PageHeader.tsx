/**
 * @file PageHeader.tsx
 * @description Standard page header displaying the section title, subtitle, and primary actions.
 */

import React from 'react';
import { cn } from '@/lib/utils';

export interface PageHeaderProps {
  /** Screen or module title */
  title: string;
  /** Explanatory subtitle */
  description?: string;
  /** Header action buttons or badges */
  action?: React.ReactNode;
  className?: string;
}

export function PageHeader({ title, description, action, className }: PageHeaderProps) {
  return (
    <div
      className={cn(
        'flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 pb-6 border-b border-border',
        className
      )}
    >
      <div>
        <h1 className="text-xl font-bold tracking-tight text-foreground sm:text-2xl">{title}</h1>
        {description && <p className="text-xs sm:text-sm text-muted-foreground mt-1">{description}</p>}
      </div>
      {action && <div className="flex items-center gap-3 shrink-0">{action}</div>}
    </div>
  );
}
