import { Routes, Route, Link } from 'react-router-dom';
import ErrorBoundary from '@/components/ErrorBoundary';
import Home from '@/pages/Home';
import About from '@/pages/About';
import Contact from '@/pages/Contact';
import UploadPage from '@/pages/UploadPage';
import DocumentSearchPage from '@/pages/DocumentSearchPage';
import KnowledgeBaseDashboard from '@/pages/admin/KnowledgeBaseDashboard';
import AuthPage from '@/auth/pages/AuthPage';
import { Button } from '@/components/ui/button';
import { getAccessToken } from '@/config/auth';

function App() {
  const isAuthenticated = !!getAccessToken();

  return (
    <ErrorBoundary>
      <div className="min-h-screen bg-background">
        {/* Header / Navigation */}
        <header className="border-b">
          <div className="container mx-auto flex h-16 items-center justify-between px-4">
            <div className="flex items-center space-x-4">
              <h1 className="text-2xl font-bold text-primary">APFA</h1>
              <nav className="hidden space-x-6 md:flex">
                <Link
                  to="/"
                  className="text-sm font-medium transition-colors hover:text-primary"
                >
                  Home
                </Link>
                <Link
                  to="/about"
                  className="text-sm font-medium transition-colors hover:text-primary"
                >
                  About
                </Link>
                <Link
                  to="/contact"
                  className="text-sm font-medium transition-colors hover:text-primary"
                >
                  Contact
                </Link>
                {isAuthenticated && (
                  <>
                    <Link
                      to="/search"
                      className="text-sm font-medium transition-colors hover:text-primary"
                    >
                      Search
                    </Link>
                    <Link
                      to="/upload"
                      className="text-sm font-medium transition-colors hover:text-primary"
                    >
                      Upload
                    </Link>
                    <Link
                      to="/admin/dashboard"
                      className="text-sm font-medium transition-colors hover:text-primary"
                    >
                      Admin
                    </Link>
                  </>
                )}
              </nav>
            </div>
            {isAuthenticated ? (
              <Button variant="default" size="sm" onClick={() => {
                localStorage.clear();
                window.location.href = '/';
              }}>
                Logout
              </Button>
            ) : (
              <Link to="/auth">
                <Button variant="default" size="sm">
                  Login
                </Button>
              </Link>
            )}
          </div>
        </header>

        {/* Main Content */}
        <main className="container mx-auto px-4 py-8">
          <Routes>
            <Route path="/" element={<Home />} />
            <Route path="/about" element={<About />} />
            <Route path="/contact" element={<Contact />} />
            <Route path="/search" element={<DocumentSearchPage />} />
            <Route path="/upload" element={<UploadPage />} />
            <Route path="/admin/dashboard" element={<KnowledgeBaseDashboard />} />
            <Route path="/auth" element={<AuthPage />} />
          </Routes>
        </main>

        {/* Footer */}
        <footer className="border-t">
          <div className="container mx-auto px-4 py-6 text-center text-sm text-muted-foreground">
            © 2025 APFA - Agentic Personalized Financial Advisor
          </div>
        </footer>
      </div>
    </ErrorBoundary>
  );
}

export default App;

