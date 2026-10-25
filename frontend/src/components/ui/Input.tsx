/**
 * @file Input.tsx
 * @description Accessible text input component with support for field-level error messages.
 *
 * SPECIFICATION (FARHAN.md):
 * "Show server validation messages from `error.fields` next to the right inputs."
 */

import React from 'react';
import { cn } from '@/lib/utils';

export interface InputProps extends React.InputHTMLAttributes<HTMLInputElement> {
  /** Optional field label rendered above the input */
  label?: string;
  /** Field-level validation error message returned by the server */
  error?: string;
  /** Supplementary helper text rendered below the input */
  helperText?: string;
}

export const Input = React.forwardRef<HTMLInputElement, InputProps>(
  ({ className, label, error, helperText, id, ...props }, ref) => {
    const inputId = id || (label ? label.toLowerCase().replace(/\s+/g, '-') : undefined);

    return (
      <div className="w-full space-y-1.5">
        {label && (
          <label
            htmlFor={inputId}
            className="block text-xs font-semibold uppercase tracking-wider text-muted-foreground"
          >
            {label}
            {props.required && <span className="text-danger ml-1">*</span>}
          </label>
        )}
        <input
          id={inputId}
          ref={ref}
          className={cn(
            'flex h-10 w-full rounded border bg-background px-3 py-2 text-sm text-foreground placeholder:text-muted-foreground/60 focus:outline-none focus:ring-1 transition-colors',
            error
              ? 'border-danger focus:ring-danger text-danger'
              : 'border-border focus:border-accent focus:ring-accent',
            'disabled:cursor-not-allowed disabled:opacity-50',
            className
          )}
          {...props}
        />
        {/* Render field-level server error if present */}
        {error && <p className="text-xs text-danger font-medium">{error}</p>}
        {/* Render helper text only when there is no active error */}
        {helperText && !error && <p className="text-xs text-muted-foreground">{helperText}</p>}
      </div>
    );
  }
);

Input.displayName = 'Input';
