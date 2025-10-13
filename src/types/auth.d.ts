/**
 * Authentication Type Definitions
 */

export interface UserProfile {
  user_id: string;
  username: string;
  email: string;
  role: 'standard' | 'advisor' | 'admin';
  permissions: string[];
  created_at?: string;
  last_login?: string;
}

export interface SessionMetadata {
  session_id: string;
  user_id: string;
  created_at: string;
  last_activity: string;
  ip_address: string;
  user_agent: string;
  is_active: boolean;
  security_flags: string[];
}

export interface AuthTokens {
  access_token: string;
  refresh_token: string;
  token_type: string;
  expires_in: number;
}

export interface LoginResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
  expires_in: number;
  user_profile: UserProfile;
  session_metadata: SessionMetadata;
  requires_mfa: boolean;
  mfa_methods: string[];
}

export interface AuthState {
  // State
  isAuthenticated: boolean;
  user: UserProfile | null;
  session: SessionMetadata | null;
  tokens: AuthTokens | null;
  isLoading: boolean;
  error: string | null;
  
  // Actions
  login: (credentials: { username: string; password: string }) => Promise<void>;
  logout: () => Promise<void>;
  refreshToken: () => Promise<void>;
  setUser: (user: UserProfile) => void;
  clearError: () => void;
}

