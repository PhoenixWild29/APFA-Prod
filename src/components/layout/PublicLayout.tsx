import { Link, Outlet } from 'react-router-dom';
import { Button } from '@/components/ui/button';
import ThemeToggle from '@/components/ThemeToggle';
import { useAuthStore } from '@/store/authStore';

export default function PublicLayout() {
  const isAuthenticated = useAuthStore((s) => s.isAuthenticated);

  return (
    <div className="flex min-h-screen flex-col">
      {/* Slim top bar */}
      <header className="sticky top-0 z-40 border-b bg-background/80 backdrop-blur-sm">
        <div className="container mx-auto flex h-14 items-center justify-between px-4">
          <Link to="/" className="flex items-center gap-2">
            <span className="font-serif text-xl font-semibold text-teal-700 dark:text-teal-300">
              APFA
            </span>
          </Link>

          <nav className="hidden items-center gap-6 md:flex">
            <Link
              to="/about"
              className="text-sm font-medium text-muted-foreground transition-colors hover:text-foreground"
            >
              About
            </Link>
            <Link
              to="/contact"
              className="text-sm font-medium text-muted-foreground transition-colors hover:text-foreground"
            >
              Contact
            </Link>
          </nav>

          <div className="flex items-center gap-2">
            <ThemeToggle />
            {isAuthenticated ? (
              <Button asChild size="sm">
                <Link to="/app/advisor">Open App</Link>
              </Button>
            ) : (
              <Button asChild size="sm">
                <Link to="/auth">Sign in</Link>
              </Button>
            )}
          </div>
        </div>
      </header>

      {/* Main content */}
      <main className="flex-1">
        <Outlet />
      </main>

      {/* Footer */}
      <footer className="border-t bg-muted/30">
        <div className="container mx-auto px-4 py-8">
          <div className="flex flex-col items-center justify-between gap-4 md:flex-row">
            <p className="text-sm text-muted-foreground">
              &copy; {new Date().getFullYear()} APFA &mdash; AI-Powered Financial Advisor
            </p>
            <nav className="flex gap-4 text-sm text-muted-foreground">
              <Link to="/about" className="hover:text-foreground">
                About
              </Link>
              <Link to="/contact" className="hover:text-foreground">
                Contact
              </Link>
            </nav>
          </div>
        </div>
      </footer>
    </div>
  );
}
