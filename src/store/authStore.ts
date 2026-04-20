/**
 * Authentication State Store (Zustand)
 *
 * Access token lives in-memory only (config/auth.ts module scope).
 * User profile and role are kept in Zustand (non-persisted).
 * Refresh token flow will use httpOnly cookies once POST /token/refresh ships.
 * Until then, token expiry or page refresh forces re-login.
 *
 * Auth lifecycle:
 *   1. App mount → rehydrate() tries to restore session
 *   2. Login → authStore.login() → sets token + user + isAuthenticated
 *   3. Navigation via useEffect on isAuthenticated (not inline in handleSubmit)
 *   4. Page refresh → rehydrate() runs again → restores or redirects
 */
import { create } from 'zustand';
import apiClient from '@/api/apiClient';
import type { AuthState, LoginResponse } from '@/types/auth';
import { setAccessToken, clearAccessToken, getAccessToken, shouldRefreshToken } from '@/config/auth';

interface AuthStore extends AuthState {
  rehydrationStatus: 'pending' | 'done';
  login: (credentials: { username: string; password: string }) => Promise<void>;
  logout: () => Promise<void>;
  refreshToken: () => Promise<void>;
  rehydrate: () => Promise<void>;
  setUser: (user: AuthState['user']) => void;
  clearError: () => void;
}

export const useAuthStore = create<AuthStore>()((set, get) => ({
  isAuthenticated: false,
  user: null,
  session: null,
  tokens: null,
  isLoading: false,
  error: null,
  rehydrationStatus: 'pending',

  login: async (credentials: { username: string; password: string }) => {
    // No isLoading in store — login loading state is per-form (local useState).
    // Store only tracks auth outcome, not transient UI state.
    try {
      const response = await apiClient.post<LoginResponse>('/token', credentials);
      const data = response.data;

      // Store token in-memory only — never localStorage
      setAccessToken(data.access_token, data.expires_in);

      set({
        isAuthenticated: true,
        user: data.user_profile,
        session: data.session_metadata,
        tokens: {
          access_token: data.access_token,
          refresh_token: data.refresh_token,
          token_type: data.token_type,
          expires_in: data.expires_in,
        },
        error: null,
      });
    } catch (error: unknown) {
      // Don't set error in store — the form handles its own error display.
      // Just ensure auth state is clean.
      set({
        isAuthenticated: false,
        user: null,
        session: null,
        tokens: null,
      });
      throw error;
    }
  },

  logout: async () => {
    try {
      await apiClient.post('/logout').catch(() => {});
    } finally {
      clearAccessToken();
      set({
        isAuthenticated: false,
        user: null,
        session: null,
        tokens: null,
        isLoading: false,
        error: null,
      });
    }
  },

  rehydrate: async () => {
    // Try to restore session after page refresh.
    // Currently: check if in-memory token survives (it won't after refresh).
    // Future: POST /token/refresh with httpOnly cookie will go here.
    const token = getAccessToken();

    if (!token) {
      // No in-memory token → session lost on refresh.
      // This is expected until POST /token/refresh ships.
      set({ isAuthenticated: false, rehydrationStatus: 'done' });
      return;
    }

    // Token exists in memory (same tab, no refresh) — verify it's still valid
    try {
      const response = await apiClient.get('/users/me');
      set({
        isAuthenticated: true,
        user: response.data,
        rehydrationStatus: 'done',
      });
    } catch {
      clearAccessToken();
      set({
        isAuthenticated: false,
        user: null,
        session: null,
        tokens: null,
        rehydrationStatus: 'done',
      });
    }
  },

  refreshToken: async () => {
    const currentTokens = get().tokens;
    if (!currentTokens?.refresh_token) {
      await get().logout();
      return;
    }

    try {
      const response = await apiClient.post('/token/refresh', {
        refresh_token: currentTokens.refresh_token,
      });
      const newTokens = response.data;

      setAccessToken(newTokens.access_token, newTokens.expires_in);

      set({
        tokens: {
          access_token: newTokens.access_token,
          refresh_token: newTokens.refresh_token,
          token_type: newTokens.token_type,
          expires_in: newTokens.expires_in,
        },
      });
    } catch {
      await get().logout();
    }
  },

  setUser: (user) => {
    set({ user });
  },

  clearError: () => {
    set({ error: null });
  },
}));

// Auto-refresh check every 60s
setInterval(() => {
  const state = useAuthStore.getState();
  if (state.isAuthenticated) {
    const token = getAccessToken();
    if (token && shouldRefreshToken(token)) {
      state.refreshToken().catch(() => {});
    }
  }
}, 60_000);
