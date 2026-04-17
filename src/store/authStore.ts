/**
 * Authentication State Store (Zustand)
 *
 * Access token lives in-memory only (config/auth.ts module scope).
 * User profile and role are kept in Zustand (non-persisted).
 * Refresh token flow will use httpOnly cookies once POST /token/refresh ships.
 * Until then, token expiry forces re-login.
 */
import { create } from 'zustand';
import apiClient from '@/api/apiClient';
import type { AuthState, LoginResponse } from '@/types/auth';
import { setAccessToken, clearAccessToken, getAccessToken, shouldRefreshToken } from '@/config/auth';

export const useAuthStore = create<AuthState>()((set, get) => ({
  isAuthenticated: false,
  user: null,
  session: null,
  tokens: null,
  isLoading: false,
  error: null,

  login: async (credentials: { username: string; password: string }) => {
    set({ isLoading: true, error: null });

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
        isLoading: false,
        error: null,
      });
    } catch (error: unknown) {
      const axiosErr = error as { response?: { data?: { detail?: string } } };
      const errorMessage = axiosErr.response?.data?.detail || 'Login failed';
      set({
        isAuthenticated: false,
        user: null,
        session: null,
        tokens: null,
        isLoading: false,
        error: errorMessage,
      });
      throw error;
    }
  },

  logout: async () => {
    set({ isLoading: true });
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

  refreshToken: async () => {
    const currentTokens = get().tokens;
    if (!currentTokens?.refresh_token) {
      // No refresh token — force re-login
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
