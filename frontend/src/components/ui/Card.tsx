/**
 * @file Card.tsx
 * @description Card surface primitives conforming to the hairline-border, no-gradient aesthetic.
 */

import React from 'react';
import { cn } from '@/lib/utils';

/**
 * Main Card surface container.
 */
export function Card({ className, children, ...props }: React.HTMLAttributes<HTMLDivElement>) {
  return (
    <div
      className={cn(
        'rounded-lg border border-border bg-surface-elevated p-5 transition-all',
        className
      )}
      {...props}
    >
      {children}
    </div>
  );
}

/**
 * Top header within a Card.
 */
export function CardHeader({ className, children, ...props }: React.HTMLAttributes<HTMLDivElement>) {
  return (
    <div className={cn('flex flex-col space-y-1.5 pb-4 border-b border-border/50 mb-4', className)} {...props}>
      {children}
    </div>
  );
}

/**
 * Primary title heading within a CardHeader.
 */
export function CardTitle({ className, children, ...props }: React.HTMLAttributes<HTMLHeadingElement>) {
  return (
    <h3 className={cn('text-base font-semibold leading-none tracking-tight text-foreground', className)} {...props}>
      {children}
    </h3>
  );
}

/**
 * Subtitle description within a CardHeader.
 */
export function CardDescription({ className, children, ...props }: React.HTMLAttributes<HTMLParagraphElement>) {
  return (
    <p className={cn('text-xs text-muted-foreground mt-1', className)} {...props}>
      {children}
    </p>
  );
}

/**
 * Main inner body of a Card.
 */
export function CardContent({ className, children, ...props }: React.HTMLAttributes<HTMLDivElement>) {
  return (
    <div className={cn('', className)} {...props}>
      {children}
    </div>
  );
}
