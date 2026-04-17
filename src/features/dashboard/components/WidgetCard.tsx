import { MoreHorizontal, Eye, EyeOff } from 'lucide-react';
import { Button } from '@/components/ui/button';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import { Skeleton } from '@/components/ui/skeleton';
import type { WidgetId } from '@/store/preferencesStore';

interface WidgetCardProps {
  id: WidgetId;
  title: string;
  children: React.ReactNode;
  isLoading?: boolean;
  onHide: (id: WidgetId) => void;
  action?: React.ReactNode;
}

export default function WidgetCard({
  id,
  title,
  children,
  isLoading,
  onHide,
  action,
}: WidgetCardProps) {
  return (
    <div className="flex flex-col rounded-xl border bg-card shadow-card">
      {/* Header */}
      <div className="flex items-center justify-between border-b px-4 py-3">
        <h3 className="text-sm font-semibold">{title}</h3>
        <div className="flex items-center gap-1">
          {action}
          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <Button variant="ghost" size="icon" className="h-7 w-7">
                <MoreHorizontal className="h-4 w-4" />
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end">
              <DropdownMenuItem onClick={() => onHide(id)}>
                <EyeOff className="mr-2 h-4 w-4" />
                Hide widget
              </DropdownMenuItem>
            </DropdownMenuContent>
          </DropdownMenu>
        </div>
      </div>

      {/* Body */}
      <div className="flex-1 p-4">
        {isLoading ? (
          <div className="space-y-3">
            <Skeleton className="h-4 w-3/4" />
            <Skeleton className="h-20 w-full" />
            <Skeleton className="h-4 w-1/2" />
          </div>
        ) : (
          children
        )}
      </div>
    </div>
  );
}
