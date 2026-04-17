import { useState } from 'react';
import { Link, Outlet, useLocation } from 'react-router-dom';
import {
  MessageSquare,
  LayoutDashboard,
  Calculator,
  FileText,
  TrendingUp,
  Settings,
  PanelLeftClose,
  PanelLeft,
  LogOut,
} from 'lucide-react';
import { cn } from '@/lib/utils';
import { Button } from '@/components/ui/button';
import { Separator } from '@/components/ui/separator';
import { ScrollArea } from '@/components/ui/scroll-area';
import {
  Tooltip,
  TooltipContent,
  TooltipTrigger,
} from '@/components/ui/tooltip';
import ThemeToggle from '@/components/ThemeToggle';
import { useAuthStore } from '@/store/authStore';

const NAV_ITEMS = [
  { to: '/app/advisor', icon: MessageSquare, label: 'Advisor' },
  { to: '/app/dashboard', icon: LayoutDashboard, label: 'Dashboard' },
  { to: '/app/calculators', icon: Calculator, label: 'Calculators' },
  { to: '/app/documents', icon: FileText, label: 'Documents' },
  { to: '/app/insights', icon: TrendingUp, label: 'Insights' },
] as const;

export default function AppLayout() {
  const [collapsed, setCollapsed] = useState(() => {
    return localStorage.getItem('sidebar-collapsed') === 'true';
  });
  const location = useLocation();
  const user = useAuthStore((s) => s.user);
  const logout = useAuthStore((s) => s.logout);

  const toggleCollapsed = () => {
    setCollapsed((prev) => {
      localStorage.setItem('sidebar-collapsed', String(!prev));
      return !prev;
    });
  };

  return (
    <div className="flex h-screen overflow-hidden bg-background">
      {/* Sidebar */}
      <aside
        className={cn(
          'hidden flex-col border-r bg-sidebar transition-[width] duration-default ease-expressive-out md:flex',
          collapsed ? 'w-16' : 'w-56'
        )}
      >
        {/* Logo */}
        <div className="flex h-14 items-center border-b px-4">
          <Link to="/app/advisor" className="flex items-center gap-2 overflow-hidden">
            <span className="font-serif text-xl font-semibold text-teal-700 dark:text-teal-300">
              A
            </span>
            {!collapsed && (
              <span className="font-serif text-xl font-semibold text-teal-700 dark:text-teal-300">
                PFA
              </span>
            )}
          </Link>
        </div>

        {/* Nav items */}
        <ScrollArea className="flex-1 py-2">
          <nav className="flex flex-col gap-1 px-2">
            {NAV_ITEMS.map(({ to, icon: Icon, label }) => {
              const isActive =
                location.pathname === to ||
                location.pathname.startsWith(to + '/');
              return (
                <Tooltip key={to} delayDuration={collapsed ? 0 : 1000}>
                  <TooltipTrigger asChild>
                    <Link
                      to={to}
                      className={cn(
                        'flex items-center gap-3 rounded-md px-3 py-2 text-sm font-medium transition-colors',
                        isActive
                          ? 'bg-sidebar-accent text-sidebar-accent-foreground'
                          : 'text-sidebar-foreground/70 hover:bg-sidebar-accent hover:text-sidebar-accent-foreground'
                      )}
                    >
                      <Icon className="h-4 w-4 shrink-0" />
                      {!collapsed && <span>{label}</span>}
                    </Link>
                  </TooltipTrigger>
                  {collapsed && (
                    <TooltipContent side="right">{label}</TooltipContent>
                  )}
                </Tooltip>
              );
            })}
          </nav>
        </ScrollArea>

        {/* Bottom actions */}
        <div className="border-t p-2">
          <Tooltip delayDuration={collapsed ? 0 : 1000}>
            <TooltipTrigger asChild>
              <Link
                to="/app/settings"
                className="flex items-center gap-3 rounded-md px-3 py-2 text-sm font-medium text-sidebar-foreground/70 transition-colors hover:bg-sidebar-accent hover:text-sidebar-accent-foreground"
              >
                <Settings className="h-4 w-4 shrink-0" />
                {!collapsed && <span>Settings</span>}
              </Link>
            </TooltipTrigger>
            {collapsed && (
              <TooltipContent side="right">Settings</TooltipContent>
            )}
          </Tooltip>

          <Button
            variant="ghost"
            size="sm"
            className="w-full justify-start gap-3 px-3 text-sidebar-foreground/70"
            onClick={toggleCollapsed}
          >
            {collapsed ? (
              <PanelLeft className="h-4 w-4" />
            ) : (
              <>
                <PanelLeftClose className="h-4 w-4" />
                <span>Collapse</span>
              </>
            )}
          </Button>
        </div>
      </aside>

      {/* Main area */}
      <div className="flex flex-1 flex-col overflow-hidden">
        {/* Top bar */}
        <header className="flex h-14 items-center justify-between border-b bg-background px-4">
          <div className="flex items-center gap-2">
            {/* Mobile menu button placeholder */}
            <span className="text-sm font-medium text-muted-foreground md:hidden">
              APFA
            </span>
          </div>

          <div className="flex items-center gap-2">
            <ThemeToggle />
            {user && (
              <span className="hidden text-sm text-muted-foreground md:inline">
                {user.username}
              </span>
            )}
            <Separator orientation="vertical" className="mx-1 h-5" />
            <Button
              variant="ghost"
              size="icon"
              onClick={() => logout()}
              aria-label="Log out"
            >
              <LogOut className="h-4 w-4" />
            </Button>
          </div>
        </header>

        {/* Page content */}
        <main className="flex-1 overflow-auto">
          <Outlet />
        </main>
      </div>
    </div>
  );
}
