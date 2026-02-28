import React from 'react';
import { cn } from '@/lib/utils';

interface CardProps extends React.HTMLAttributes<HTMLDivElement> {}

export function Card({ className, ...props }: CardProps) {
  return (
    <div
      className={cn(
        "rounded-xl border bg-white text-slate-950 shadow-sm dark:bg-slate-900 dark:border-slate-800 dark:text-slate-50 transition-colors",
        className
      )}
      {...props}
    />
  );
}