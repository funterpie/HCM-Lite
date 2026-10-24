import { cn } from '@/lib/utils';
import { STATUS_CONFIG, REQ_STATUS_CONFIG, type AttendanceStatus, type RequestStatus } from '@/lib/tokens';

export interface BadgeProps {
  children?: React.ReactNode;
  variant?: 'default' | 'outline' | 'status' | 'request' | 'locked';
  status?: AttendanceStatus;
  requestStatus?: RequestStatus;
  className?: string;
}

export function Badge({ children, variant = 'default', status, requestStatus, className }: BadgeProps) {
  if (variant === 'status' && status && STATUS_CONFIG[status]) {
    const conf = STATUS_CONFIG[status];
    return (
      <span
        className={cn(
          'inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-medium border',
          conf.bg,
          conf.text,
          conf.border,
          className
        )}
      >
        <span className={cn('h-1.5 w-1.5 rounded-full', conf.dot)} />
        {children || conf.label}
      </span>
    );
  }

  if (variant === 'request' && requestStatus && REQ_STATUS_CONFIG[requestStatus]) {
    const conf = REQ_STATUS_CONFIG[requestStatus];
    return (
      <span
        className={cn(
          'inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium border',
          conf.bg,
          conf.text,
          conf.border,
          className
        )}
      >
        {children || conf.label}
      </span>
    );
  }

  if (variant === 'locked') {
    return (
      <span
        className={cn(
          'inline-flex items-center px-2 py-0.5 rounded text-xs font-semibold uppercase tracking-wider bg-zinc-800 text-zinc-100 dark:bg-zinc-200 dark:text-zinc-900',
          className
        )}
      >
        Locked
      </span>
    );
  }

  return (
    <span
      className={cn(
        'inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-muted text-muted-foreground border border-border',
        className
      )}
    >
      {children}
    </span>
  );
}
