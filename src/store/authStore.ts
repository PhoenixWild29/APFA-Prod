/**
 * Authentication State Store (Zustand)
 *
 * Access token lives in-memory only (config/auth.ts module scope).
 * Refresh token lives in an httpOnly cookie (set by POST /token).
 *
 * Auth lifecycle:
 *   1. App mount → rehydrate() calls POST /token/refresh (cookie-based)
 *   2. Login → authStore.login() → sets access token + user profile
 *   3. Page refresh → rehydrate() gets new access token from cookie
 *   4. 401 on API call → apiClient interceptor coalesces refresh + retries
 *   5. Proactive refresh every 60s when token is near expiry
 */
import { create } from 'zustand';
import apiClient from '@/api/apiClient';
import authClient from '@/api/authClient';
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
    try {
      // Use authClient (withCredentials) so the response's Set-Cookie
      // for the refresh token is accepted by the browser.
      const response = await authClient.post<LoginResponse>('/token', credentials);
      const data = response.data;

      // Store access token in-memory only — never localStorage
      setAccessToken(data.access_token, data.expires_in);

      set({
        isAuthenticated: true,
        user: data.user_profile,
        session: data.session_metadata,
        tokens: {
          access_token: data.access_token,
          refresh_token: data.refresh_token, // "httponly_cookie" sentinel
          token_type: data.token_type,
          expires_in: data.expires_in,
        },
        error: null,
      });
    } catch (error: unknown) {
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
      // POST /token/revoke revokes the refresh token family
      // and clears the httpOnly cookie server-side.
      await authClient.post('/token/revoke').catch(() => {});
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
    // On page refresh, the in-memory access token is gone.
    // But the httpOnly refresh_token cookie survives.
    // Call POST /token/refresh to get a new access token.
    try {
      const response = await authClient.post<{
        access_token: string;
        token_type: string;
        expires_in: number;
      }>('/token/refresh');

      const { access_token, expires_in } = response.data;
      setAccessToken(access_token, expires_in);

      // Fetch user profile with the new token
      const userResponse = await apiClient.get('/users/me', {
        headers: { Authorization: `Bearer ${access_token}` },
      });

      set({
        isAuthenticated: true,
        user: userResponse.data,
        tokens: {
          access_token,
          refresh_token: 'httponly_cookie',
          token_type: 'bearer',
          expires_in,
        },
        rehydrationStatus: 'done',
      });
    } catch {
      // No valid refresh cookie — user needs to log in again.
      // This is normal for first-time visitors or expired sessions.
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
    // Proactive refresh — called by the 60s interval when token
    // is near expiry. Uses authClient (withCredentials) for the
    // httpOnly cookie.
    try {
      const response = await authClient.post<{
        access_token: string;
        token_type: string;
        expires_in: number;
      }>('/token/refresh');

      const { access_token, expires_in } = response.data;
      setAccessToken(access_token, expires_in);

      set({
        tokens: {
          access_token,
          refresh_token: 'httponly_cookie',
          token_type: 'bearer',
          expires_in,
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

// Auto-refresh check every 60s — proactively refresh when token
// is within 5 minutes of expiry.
setInterval(() => {
  const state = useAuthStore.getState();
  if (state.isAuthenticated) {
    const token = getAccessToken();
    if (token && shouldRefreshToken(token)) {
      state.refreshToken().catch(() => {});
    }
  }
}, 60_000);
