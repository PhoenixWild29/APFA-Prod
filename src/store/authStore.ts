/**
 * Authentication State Store (Zustand)
 * 
 * Manages global authentication state including:
 * - User login status and profile
 * - Session metadata
 * - Token management
 * - Automatic token refresh
 */
import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import apiClient from '@/api/apiClient';
import { AuthState, UserProfile, SessionMetadata, AuthTokens, LoginResponse } from '@/types/auth';
import { setAccessToken, clearAccessToken, getAccessToken } from '@/config/auth';

export const useAuthStore = create<AuthState>()(
  persist(
    (set, get) => ({
      // Initial state
      isAuthenticated: false,
      user: null,
      session: null,
      tokens: null,
      isLoading: false,
      error: null,

      // Login action
      login: async (credentials: { username: string; password: string }) => {
        set({ isLoading: true, error: null });
        
        try {
          // Call login API
          const response = await apiClient.post<LoginResponse>('/token', credentials);
          const data = response.data;
          
          // Store tokens
          setAccessToken(data.access_token, data.expires_in);
          
          // Update state
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
        } catch (error: any) {
          const errorMessage = error.response?.data?.detail || 'Login failed';
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

      // Logout action
      logout: async () => {
        set({ isLoading: true });
        
        try {
          // Call logout API (optional - backend may not need this)
          await apiClient.post('/logout').catch(() => {
            // Ignore logout API errors
          });
        } finally {
          // Clear tokens and state
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

      // Refresh token action
      refreshToken: async () => {
        const currentTokens = get().tokens;
        if (!currentTokens?.refresh_token) {
          throw new Error('No refresh token available');
        }
        
        try {
          // Call token refresh API
          const response = await apiClient.post('/token/refresh', {
            refresh_token: currentTokens.refresh_token,
          });
          
          const newTokens = response.data;
          
          // Update tokens
          setAccessToken(newTokens.access_token, newTokens.expires_in);
          
          set({
            tokens: {
              access_token: newTokens.access_token,
              refresh_token: newTokens.refresh_token,
              token_type: newTokens.token_type,
              expires_in: newTokens.expires_in,
            },
          });
        } catch (error) {
          // Refresh failed - logout user
          await get().logout();
          throw error;
        }
      },

      // Set user (for updates)
      setUser: (user: UserProfile) => {
        set({ user });
      },

      // Clear error
      clearError: () => {
        set({ error: null });
      },
    }),
    {
      name: 'auth-storage',
      partialize: (state) => ({
        // Only persist these fields (not tokens - handled by cookies)
        isAuthenticated: state.isAuthenticated,
        user: state.user,
        session: state.session,
      }),
    }
  )
);

// Auto-refresh token before expiration
setInterval(() => {
  const state = useAuthStore.getState();
  
  if (state.isAuthenticated && state.tokens) {
    const expiresIn = state.tokens.expires_in;
    const now = Math.floor(Date.now() / 1000);
    
    // Refresh if token expires in < 5 minutes
    if (expiresIn - now < 300) {
      state.refreshToken().catch((err) => {
        console.error('Auto token refresh failed:', err);
      });
    }
  }
}, 60000); // Check every minute

