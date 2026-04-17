import { lazy, Suspense, useState } from 'react';
import { Routes, Route, Navigate } from 'react-router-dom';
import ErrorBoundary from '@/components/ErrorBoundary';
import PublicLayout from '@/components/layout/PublicLayout';
import AppLayout from '@/components/layout/AppLayout';
import AdminLayout from '@/components/layout/AdminLayout';
import ProtectedRoute from '@/routes/ProtectedRoute';
import RoleRoute from '@/routes/RoleRoute';
import RedirectIfAuth from '@/routes/RedirectIfAuth';
import CommandPalette from '@/components/CommandPalette';
import { Skeleton } from '@/components/ui/skeleton';

// --- Public pages ---
const Landing = lazy(() => import('@/pages/Landing'));
const About = lazy(() => import('@/pages/About'));
const Contact = lazy(() => import('@/pages/Contact'));
const AuthPage = lazy(() => import('@/auth/pages/AuthPage'));

// --- App pages ---
const AdvisorPage = lazy(() => import('@/features/advisor/AdvisorPage'));
const DashboardPage = lazy(() => import('@/features/dashboard/DashboardPage'));
const Home = lazy(() => import('@/pages/Home'));
const DocumentSearchPage = lazy(() => import('@/pages/DocumentSearchPage'));
const UploadPage = lazy(() => import('@/pages/UploadPage'));

// --- Admin pages ---
const KnowledgeBaseDashboard = lazy(
  () => import('@/pages/admin/KnowledgeBaseDashboard')
);
const SystemMonitoringDashboard = lazy(
  () => import('@/pages/admin/SystemMonitoringDashboard')
);

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
            <Route path="/app/calculators" element={<div className="p-8">Calculators index — Phase 2</div>} />
            <Route path="/app/calculators/:tool" element={<div className="p-8">Calculator tool — Phase 2</div>} />
            <Route path="/app/documents" element={<DocumentSearchPage />} />
            <Route path="/app/documents/upload" element={<UploadPage />} />
            <Route path="/app/insights" element={<div className="p-8">Insights — Phase 3</div>} />
            <Route path="/app/settings" element={<div className="p-8">Settings — Phase 3</div>} />
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
            <Route path="/admin/monitoring" element={<SystemMonitoringDashboard />} />
            <Route path="/admin/knowledge-base" element={<KnowledgeBaseDashboard />} />
            <Route path="/admin/users" element={<div className="p-8">User management — Phase 4</div>} />
            <Route path="/admin/audit" element={<div className="p-8">Audit log — Phase 4</div>} />
          </Route>

          {/* Catch-all */}
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </Suspense>
    </ErrorBoundary>
  );
}

export default App;
