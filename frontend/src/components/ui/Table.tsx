/**
 * @file Table.tsx
 * @description Accessible, scrollable tabular data presentation primitives.
 */

import React from 'react';
import { cn } from '@/lib/utils';

/** Responsive table container */
export function Table({ className, children, ...props }: React.HTMLAttributes<HTMLTableElement>) {
  return (
    <div className="w-full overflow-x-auto rounded border border-border">
      <table className={cn('w-full caption-bottom text-sm', className)} {...props}>
        {children}
      </table>
    </div>
  );
}

/** Table Header section */
export function TableHeader({ className, children, ...props }: React.HTMLAttributes<HTMLTableSectionElement>) {
  return (
    <thead
      className={cn(
        'border-b border-border bg-surface text-left font-semibold text-muted-foreground text-xs uppercase tracking-wider',
        className
      )}
      {...props}
    >
      {children}
    </thead>
  );
}

/** Table Body section */
export function TableBody({ className, children, ...props }: React.HTMLAttributes<HTMLTableSectionElement>) {
  return (
    <tbody className={cn('divide-y divide-border/60 bg-background', className)} {...props}>
      {children}
    </tbody>
  );
}

/** Table Row element */
export function TableRow({ className, children, ...props }: React.HTMLAttributes<HTMLTableRowElement>) {
  return (
    <tr className={cn('transition-colors hover:bg-surface/60', className)} {...props}>
      {children}
    </tr>
  );
}

/** Table Column Header element */
export function TableHead({ className, children, ...props }: React.ThHTMLAttributes<HTMLTableCellElement>) {
  return (
    <th className={cn('h-10 px-4 text-left align-middle font-medium text-xs', className)} {...props}>
      {children}
    </th>
  );
}

/** Table Data Cell element */
export function TableCell({ className, children, ...props }: React.TdHTMLAttributes<HTMLTableCellElement>) {
  return (
    <td className={cn('p-4 align-middle text-sm text-foreground', className)} {...props}>
      {children}
    </td>
  );
}
