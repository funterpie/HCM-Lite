/**
 * @file Button.tsx
 * @description Accessible button component adhering to the ultra-minimal high-contrast design system.
 * Features built-in spinner loading state and large touch targets (responsive for >= 375px screens).
 */

import React from 'react';
import { cn } from '@/lib/utils';
import { Loader2 } from 'lucide-react';

export interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  /** Visual button style */
  variant?: 'primary' | 'secondary' | 'outline' | 'ghost' | 'danger';
  /** Button dimensions */
  size?: 'sm' | 'md' | 'lg' | 'icon';
  /** Indicates asynchronous task in progress; disables button and displays spinner */
  loading?: boolean;
}

export const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant = 'primary', size = 'md', loading, disabled, children, ...props }, ref) => {
    // Base styles: large touch targets, clear focus outline, and minimal motion
    const base =
      'inline-flex items-center justify-center font-medium transition-colors select-none focus:outline-none focus:ring-1 focus:ring-accent disabled:opacity-50 disabled:pointer-events-none active:scale-[0.99]';

    const variants = {
      primary: 'bg-accent text-accent-foreground hover:bg-accent-hover shadow-sm',
      secondary: 'bg-surface text-foreground border border-border hover:bg-muted',
      outline: 'bg-transparent text-foreground border border-border hover:bg-surface',
      ghost: 'bg-transparent text-foreground hover:bg-surface',
      danger: 'bg-danger text-white hover:bg-red-600 shadow-sm',
    };

    const sizes = {
      sm: 'h-8 px-3 text-xs rounded',
      md: 'h-10 px-4 text-sm rounded',
      lg: 'h-12 px-6 text-base rounded-md',
      icon: 'h-9 w-9 p-0 rounded flex items-center justify-center',
    };

    return (
      <button
        ref={ref}
        disabled={disabled || loading}
        className={cn(base, variants[variant], sizes[size], className)}
        {...props}
      >
        {loading && <Loader2 className="mr-2 h-4 w-4 animate-spin text-current" />}
        {children}
      </button>
    );
  }
);

Button.displayName = 'Button';
