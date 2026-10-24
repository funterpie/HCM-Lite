import { Sparkles } from 'lucide-react';
import { cn } from '@/lib/utils';

export function AiBadge({ className }: { className?: string }) {
  return (
    <span
      className={cn(
        'inline-flex items-center gap-1 px-2 py-0.5 rounded text-[10px] font-semibold tracking-wide uppercase bg-purple-500/10 text-purple-700 dark:text-purple-300 border border-purple-500/30',
        className
      )}
    >
      <Sparkles className="h-3 w-3 text-purple-600 dark:text-purple-400" />
      AI-generated
    </span>
  );
}
