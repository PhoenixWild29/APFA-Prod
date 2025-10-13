/**
 * Authentication Hook
 * 
 * Provides easy access to authentication state and actions
 * from the Zustand store.
 */
import { useAuthStore } from '@/store/authStore';
import { useCallback } from 'react';

export function useAuth() {
  const {
    isAuthenticated,
    user,
    session,
    tokens,
    isLoading,
    error,
    login,
    logout,
    refreshToken,
    setUser,
    clearError,
  } = useAuthStore();

  // Memoized login handler
  const handleLogin = useCallback(
    async (username: string, password: string) => {
      return login({ username, password });
    },
    [login]
  );

  // Memoized logout handler
  const handleLogout = useCallback(async () => {
    return logout();
  }, [logout]);

  return {
    // State
    isAuthenticated,
    user,
    session,
    tokens,
    isLoading,
    error,
    
    // Actions
    login: handleLogin,
    logout: handleLogout,
    refreshToken,
    setUser,
    clearError,
    
    // Computed
    isAdmin: user?.role === 'admin',
    isAdvisor: user?.role === 'advisor' || user?.role === 'admin',
    permissions: user?.permissions || [],
    
    // Permission checker
    hasPermission: (permission: string) => {
      return user?.permissions?.includes(permission) || false;
    },
  };
}

