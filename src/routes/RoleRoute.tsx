import { Navigate } from 'react-router-dom';
import { useAuthStore } from '@/store/authStore';
import type { UserProfile } from '@/types/auth';

export default function RoleRoute({
  role,
  children,
}: {
  role: UserProfile['role'];
  children: React.ReactNode;
}) {
  const user = useAuthStore((s) => s.user);

  if (!user || user.role !== role) {
    return <Navigate to="/app/advisor" replace />;
  }

  return <>{children}</>;
}
