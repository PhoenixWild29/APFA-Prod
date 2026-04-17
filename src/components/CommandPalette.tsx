import { useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  MessageSquare,
  LayoutDashboard,
  Calculator,
  FileText,
  TrendingUp,
  Settings,
  Plus,
  Search,
} from 'lucide-react';
import {
  CommandDialog,
  CommandInput,
  CommandList,
  CommandEmpty,
  CommandGroup,
  CommandItem,
  CommandSeparator,
  CommandShortcut,
} from '@/components/ui/command';
import { useAuthStore } from '@/store/authStore';

interface CommandPaletteProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

export default function CommandPalette({ open, onOpenChange }: CommandPaletteProps) {
  const navigate = useNavigate();
  const isAuthenticated = useAuthStore((s) => s.isAuthenticated);

  // ⌘K / Ctrl+K to toggle
  useEffect(() => {
    const handler = (e: KeyboardEvent) => {
      if ((e.metaKey || e.ctrlKey) && e.key === 'k') {
        e.preventDefault();
        onOpenChange(!open);
      }
    };
    document.addEventListener('keydown', handler);
    return () => document.removeEventListener('keydown', handler);
  }, [open, onOpenChange]);

  const runAction = useCallback(
    (path: string) => {
      onOpenChange(false);
      navigate(path);
    },
    [navigate, onOpenChange]
  );

  return (
    <CommandDialog open={open} onOpenChange={onOpenChange}>
      <CommandInput placeholder="Type a command or search..." />
      <CommandList>
        <CommandEmpty>No results found.</CommandEmpty>

        {isAuthenticated && (
          <>
            <CommandGroup heading="Actions">
              <CommandItem onSelect={() => runAction('/app/advisor')}>
                <Plus className="mr-2 h-4 w-4" />
                New conversation
                <CommandShortcut>⌘N</CommandShortcut>
              </CommandItem>
            </CommandGroup>

            <CommandSeparator />

            <CommandGroup heading="Navigate">
              <CommandItem onSelect={() => runAction('/app/advisor')}>
                <MessageSquare className="mr-2 h-4 w-4" />
                Advisor
              </CommandItem>
              <CommandItem onSelect={() => runAction('/app/dashboard')}>
                <LayoutDashboard className="mr-2 h-4 w-4" />
                Dashboard
              </CommandItem>
              <CommandItem onSelect={() => runAction('/app/calculators')}>
                <Calculator className="mr-2 h-4 w-4" />
                Calculators
              </CommandItem>
              <CommandItem onSelect={() => runAction('/app/documents')}>
                <FileText className="mr-2 h-4 w-4" />
                Documents
              </CommandItem>
              <CommandItem onSelect={() => runAction('/app/insights')}>
                <TrendingUp className="mr-2 h-4 w-4" />
                Insights
              </CommandItem>
              <CommandItem onSelect={() => runAction('/app/settings')}>
                <Settings className="mr-2 h-4 w-4" />
                Settings
              </CommandItem>
            </CommandGroup>
          </>
        )}

        {!isAuthenticated && (
          <CommandGroup heading="Navigate">
            <CommandItem onSelect={() => runAction('/')}>
              <Search className="mr-2 h-4 w-4" />
              Home
            </CommandItem>
            <CommandItem onSelect={() => runAction('/about')}>
              <Search className="mr-2 h-4 w-4" />
              About
            </CommandItem>
            <CommandItem onSelect={() => runAction('/auth')}>
              <Search className="mr-2 h-4 w-4" />
              Sign in
            </CommandItem>
          </CommandGroup>
        )}
      </CommandList>
    </CommandDialog>
  );
}
