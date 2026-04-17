import { useState } from 'react';
import { Link, Outlet, useLocation } from 'react-router-dom';
import {
  Activity,
  BookOpen,
  Users,
  ScrollText,
  PanelLeftClose,
  PanelLeft,
  ArrowLeft,
  Shield,
} from 'lucide-react';
import { cn } from '@/lib/utils';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { ScrollArea } from '@/components/ui/scroll-area';
import {
  Tooltip,
  TooltipContent,
  TooltipTrigger,
} from '@/components/ui/tooltip';
import ThemeToggle from '@/components/ThemeToggle';
import { useAuthStore } from '@/store/authStore';

const ADMIN_NAV = [
  { to: '/admin/monitoring', icon: Activity, label: 'Monitoring' },
  { to: '/admin/knowledge-base', icon: BookOpen, label: 'Knowledge Base' },
  { to: '/admin/users', icon: Users, label: 'Users' },
  { to: '/admin/audit', icon: ScrollText, label: 'Audit Log' },
] as const;

export default function AdminLayout() {
  const [collapsed, setCollapsed] = useState(() => {
    return localStorage.getItem('admin-sidebar-collapsed') === 'true';
  });
  const location = useLocation();
  const user = useAuthStore((s) => s.user);

  const toggleCollapsed = () => {
    setCollapsed((prev) => {
      localStorage.setItem('admin-sidebar-collapsed', String(!prev));
      return !prev;
    });
  };

  return (
    <div className="flex h-screen overflow-hidden bg-background">
      {/* Admin sidebar */}
      <aside
        className={cn(
          'hidden flex-col border-r bg-sidebar transition-[width] duration-default ease-expressive-out md:flex',
          collapsed ? 'w-16' : 'w-56'
        )}
      >
        {/* Logo + admin badge */}
        <div className="flex h-14 items-center border-b px-4">
          <Link to="/admin/monitoring" className="flex items-center gap-2 overflow-hidden">
            <Shield className="h-5 w-5 shrink-0 text-teal-700 dark:text-teal-300" />
            {!collapsed && (
              <>
                <span className="font-serif text-lg font-semibold text-teal-700 dark:text-teal-300">
                  APFA
                </span>
                <Badge variant="secondary" className="text-xs">
                  Admin
                </Badge>
              </>
            )}
          </Link>
        </div>

        {/* Nav items */}
        <ScrollArea className="flex-1 py-2">
          <nav className="flex flex-col gap-1 px-2">
            {ADMIN_NAV.map(({ to, icon: Icon, label }) => {
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

        {/* Bottom */}
        <div className="border-t p-2">
          <Link
            to="/app/advisor"
            className="flex items-center gap-3 rounded-md px-3 py-2 text-sm font-medium text-sidebar-foreground/70 transition-colors hover:bg-sidebar-accent hover:text-sidebar-accent-foreground"
          >
            <ArrowLeft className="h-4 w-4 shrink-0" />
            {!collapsed && <span>Back to App</span>}
          </Link>
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
        {/* Top bar with Admin badge */}
        <header className="flex h-14 items-center justify-between border-b bg-background px-4">
          <div className="flex items-center gap-2">
            <Badge className="bg-gold-500 text-ink-900 hover:bg-gold-300">
              Admin Panel
            </Badge>
          </div>

          <div className="flex items-center gap-2">
            <ThemeToggle />
            {user && (
              <span className="hidden text-sm text-muted-foreground md:inline">
                {user.username}
              </span>
            )}
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
