/**
 * Authentication configuration — Vite env, in-memory token storage.
 *
 * Access token lives in a module-scoped variable (never localStorage).
 * Refresh token lives in an httpOnly cookie (path=/token, SameSite=Strict).
 * On page refresh, authStore.rehydrate() calls POST /token/refresh to
 * exchange the cookie for a new access token.
 */

export const authConfig = {
  apiEndpoint: import.meta.env.VITE_API_URL || 'http://localhost:8000',
  tokenEndpoint: '/token',
  tokenRefreshThreshold: 300, // 5 minutes before expiry (seconds)
};

// ── In-memory token store ──────────────────────────────────────────
let accessToken: string | null = null;
let tokenExpiry: number | null = null; // ms since epoch

export function getAccessToken(): string | null {
  return accessToken;
}

export function setAccessToken(token: string, expiresIn?: number): void {
  accessToken = token;
  if (expiresIn) {
    tokenExpiry = Date.now() + expiresIn * 1000;
  }
}

export function clearAccessToken(): void {
  accessToken = null;
  tokenExpiry = null;
}

export function isTokenExpired(token?: string | null): boolean {
  const t = token ?? accessToken;
  if (!t) return true;

  try {
    const payload = JSON.parse(atob(t.split('.')[1]));
    if (payload.exp) {
      return payload.exp * 1000 < Date.now();
    }
    return false;
  } catch {
    return true;
  }
}

export function getTokenExpiry(token?: string | null): number | null {
  const t = token ?? accessToken;
  if (!t) return null;

  try {
    const payload = JSON.parse(atob(t.split('.')[1]));
    return payload.exp ? payload.exp * 1000 : null;
  } catch {
    return null;
  }
}

export function shouldRefreshToken(token?: string | null): boolean {
  const expiry = getTokenExpiry(token);
  if (!expiry) return false;
  return expiry - Date.now() < authConfig.tokenRefreshThreshold * 1000;
}

export function getUsernameFromToken(token?: string | null): string | null {
  const t = token ?? accessToken;
  if (!t) return null;

  try {
    const payload = JSON.parse(atob(t.split('.')[1]));
    return payload.sub || null;
  } catch {
    return null;
  }
}
