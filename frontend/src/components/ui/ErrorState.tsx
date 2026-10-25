/**
 * @file ErrorState.tsx
 * @description Standardized error state component with a retry button for unexpected server failures.
 */

import { AlertTriangle } from 'lucide-react';
import { cn } from '@/lib/utils';
import { Button } from './Button';

export interface ErrorStateProps {
  /** Error heading title */
  title?: string;
  /** Detailed error message */
  message?: string;
  /** Optional retry callback */
  onRetry?: () => void;
  className?: string;
}

export function ErrorState({
  title = 'Something went wrong',
  message = 'An unexpected error occurred. Please try again.',
  onRetry,
  className,
}: ErrorStateProps) {
  return (
    <div
      className={cn(
        'flex flex-col items-center justify-center p-8 text-center rounded-lg border border-danger-border bg-danger-surface',
        className
      )}
    >
      <div className="flex h-10 w-10 items-center justify-center rounded-full bg-danger/10 text-danger mb-3">
        <AlertTriangle className="h-5 w-5" />
      </div>
      <h3 className="text-sm font-semibold text-danger">{title}</h3>
      <p className="text-xs text-danger/80 mt-1 max-w-sm">{message}</p>
      {onRetry && (
        <Button
          onClick={onRetry}
          variant="outline"
          size="sm"
          className="mt-4 border-danger/30 text-danger hover:bg-danger/10"
        >
          Try Again
        </Button>
      )}
    </div>
  );
}
