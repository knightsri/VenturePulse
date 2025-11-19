import * as React from 'react';
import { cn } from '@/lib/utils';

export interface BadgeProps extends React.HTMLAttributes<HTMLDivElement> {
  variant?: 'default' | 'secondary' | 'destructive' | 'outline' | 'success' | 'warning';
}

function Badge({ className, variant = 'default', ...props }: BadgeProps) {
  const variants = {
    default: 'bg-indigo-100 text-indigo-700 border-transparent',
    secondary: 'bg-gray-100 text-gray-700 border-transparent',
    destructive: 'bg-red-100 text-red-700 border-transparent',
    outline: 'text-gray-700 border-gray-300',
    success: 'bg-green-100 text-green-700 border-transparent',
    warning: 'bg-yellow-100 text-yellow-700 border-transparent',
  };

  return (
    <div
      className={cn(
        'inline-flex items-center rounded-full border px-2.5 py-0.5 text-xs font-semibold transition-colors focus:outline-none focus:ring-2 focus:ring-offset-2',
        variants[variant],
        className
      )}
      {...props}
    />
  );
}

export { Badge };
