import { lazy, Suspense, useEffect, useState } from 'react';
import { Routes, Route, Navigate } from 'react-router-dom';
import ErrorBoundary from '@/components/ErrorBoundary';
import PublicLayout from '@/components/layout/PublicLayout';
import AppLayout from '@/components/layout/AppLayout';
import AdminLayout from '@/components/layout/AdminLayout';
import ProtectedRoute from '@/routes/ProtectedRoute';
import RoleRoute from '@/routes/RoleRoute';
import RedirectIfAuth from '@/routes/RedirectIfAuth';
import CommandPalette from '@/components/CommandPalette';
import { useAuthStore } from '@/store/authStore';
import { Skeleton } from '@/components/ui/skeleton';

// --- Public pages ---
const Landing = lazy(() => import('@/pages/Landing'));
const About = lazy(() => import('@/pages/About'));
const Contact = lazy(() => import('@/pages/Contact'));
const AuthPage = lazy(() => import('@/auth/pages/AuthPage'));

// --- App pages ---
const AdvisorPage = lazy(() => import('@/features/advisor/AdvisorPage'));
const DashboardPage = lazy(() => import('@/features/dashboard/DashboardPage'));
const DocumentsPage = lazy(() => import('@/features/documents/DocumentsPage'));
const DocumentDetailPage = lazy(() => import('@/features/documents/DocumentDetailPage'));
const UploadPage = lazy(() => import('@/features/documents/UploadPage'));
const InsightsPage = lazy(() => import('@/features/insights/InsightsPage'));
const SettingsPage = lazy(() => import('@/features/settings/SettingsPage'));

// --- Admin pages ---
const AdminMonitoringPage = lazy(() => import('@/features/admin/AdminMonitoringPage'));
const AdminKnowledgeBasePage = lazy(() => import('@/features/admin/AdminKnowledgeBasePage'));
const AdminUsersPage = lazy(() => import('@/features/admin/AdminUsersPage'));
const AdminAuditPage = lazy(() => import('@/features/admin/AdminAuditPage'));

function PageLoader() {
  return (
    <div className="flex flex-col gap-4 p-8">
      <Skeleton className="h-8 w-48" />
      <Skeleton className="h-4 w-96" />
      <Skeleton className="h-64 w-full" />
    </div>
  );
}

function App() {
  const [cmdkOpen, setCmdkOpen] = useState(false);
  const rehydrate = useAuthStore((s) => s.rehydrate);

  // Rehydrate auth state on app mount (page refresh recovery).
  // Calls POST /token/refresh with the httpOnly cookie to get a new
  // access token. If the cookie is expired/missing, redirects to /auth.
  useEffect(() => {
    rehydrate();
  }, [rehydrate]);

  return (
    <ErrorBoundary>
      <CommandPalette open={cmdkOpen} onOpenChange={setCmdkOpen} />
      <Suspense fallback={<PageLoader />}>
        <Routes>
          {/* ── Public zone ── */}
          <Route element={<PublicLayout />}>
            <Route path="/" element={<Landing />} />
            <Route path="/about" element={<About />} />
            <Route path="/contact" element={<Contact />} />
            <Route
              path="/auth"
              element={
                <RedirectIfAuth>
                  <AuthPage />
                </RedirectIfAuth>
              }
            />
          </Route>

          {/* ── App zone (authenticated) ── */}
          <Route
            element={
              <ProtectedRoute>
                <AppLayout />
              </ProtectedRoute>
            }
          >
            <Route path="/app" element={<Navigate to="/app/advisor" replace />} />
            <Route path="/app/advisor" element={<AdvisorPage />} />
            <Route path="/app/advisor/c/:conversationId" element={<AdvisorPage />} />
            <Route path="/app/dashboard" element={<DashboardPage />} />
            <Route path="/app/calculators" element={<div className="p-8"><h1 className="font-serif text-2xl font-semibold">Calculators</h1><p className="mt-2 text-muted-foreground">Investment growth, asset allocation, and retirement projection calculators coming soon.</p></div>} />
            <Route path="/app/calculators/:tool" element={<div className="p-8">Calculator tool — coming soon</div>} />
            <Route path="/app/documents" element={<DocumentsPage />} />
            <Route path="/app/documents/upload" element={<UploadPage />} />
            <Route path="/app/documents/:documentId" element={<DocumentDetailPage />} />
            <Route path="/app/insights" element={<InsightsPage />} />
            <Route path="/app/settings" element={<SettingsPage />} />
          </Route>

          {/* ── Admin zone (role = admin) ── */}
          <Route
            element={
              <ProtectedRoute>
                <RoleRoute role="admin">
                  <AdminLayout />
                </RoleRoute>
              </ProtectedRoute>
            }
          >
            <Route path="/admin" element={<Navigate to="/admin/monitoring" replace />} />
            <Route path="/admin/monitoring" element={<AdminMonitoringPage />} />
            <Route path="/admin/knowledge-base" element={<AdminKnowledgeBasePage />} />
            <Route path="/admin/users" element={<AdminUsersPage />} />
            <Route path="/admin/audit" element={<AdminAuditPage />} />
          </Route>

          {/* Catch-all */}
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </Suspense>
    </ErrorBoundary>
  );
}

export default App;
