'use client';

import * as React from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { cn } from '@/lib/utils';

export interface InputProps extends React.InputHTMLAttributes<HTMLInputElement> {
  label?: string;
  error?: string;
  icon?: React.ReactNode;
}


const Input = React.forwardRef<HTMLInputElement, InputProps>(
  ({ className, type, label, error, icon, ...props }, ref) => {
    const [isFocused, setIsFocused] = React.useState(false);
    const [hasValue, setHasValue] = React.useState(false);
    const inputId = React.useId();

    const handleFocus = () => setIsFocused(true);
    const handleBlur = (e: React.FocusEvent<HTMLInputElement>) => {
      setIsFocused(false);
      setHasValue(e.target.value.length > 0);
      props.onBlur?.(e);
    };

    const shouldFloat = isFocused || hasValue || props.value;

    return (
      <div className="relative w-full">
        <div className="relative">
          {icon && (
            <div className="absolute left-3 top-1/2 -translate-y-1/2 text-muted-foreground">
              {icon}
            </div>
          )}
          <input
            type={type}
            className={cn(
              'flex h-12 w-full rounded-lg border border-input bg-background px-3 py-3 text-base shadow-sm transition-colors',
              'file:border-0 file:bg-transparent file:text-sm file:font-medium file:text-foreground',
              'placeholder:text-muted-foreground',
              'focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:border-primary',
              'disabled:cursor-not-allowed disabled:opacity-50',
              error && 'border-destructive focus-visible:ring-destructive',
              icon && 'pl-10',
              label && 'pt-6',
              className
            )}
            ref={ref}
            id={inputId}
            onFocus={handleFocus}
            onBlur={handleBlur}
            aria-invalid={error ? 'true' : 'false'}
            aria-describedby={error ? `${inputId}-error` : undefined}
            {...props}
          />
          
          {label && (
            <motion.label
              htmlFor={inputId}
              className={cn(
                'absolute left-3 text-muted-foreground pointer-events-none transition-all',
                icon && 'left-10'
              )}
              animate={{
                top: shouldFloat ? '0.5rem' : '50%',
                fontSize: shouldFloat ? '0.75rem' : '1rem',
                y: shouldFloat ? 0 : '-50%',
              }}
              transition={{
                type: 'spring',
                stiffness: 300,
                damping: 30,
              }}
            >
              {label}
            </motion.label>
          )}
        </div>

        <AnimatePresence mode="wait">
          {error && (
            <motion.p
              id={`${inputId}-error`}
              className="mt-1.5 text-sm text-destructive"
              initial={{ opacity: 0, y: -10 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -10 }}
              transition={{ duration: 0.2 }}
              role="alert"
              aria-live="polite"
            >
              {error}
            </motion.p>
          )}
        </AnimatePresence>
      </div>
    );
  }
);

Input.displayName = 'Input';

export { Input };
