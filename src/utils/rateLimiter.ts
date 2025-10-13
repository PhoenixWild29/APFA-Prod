/**
 * Client-Side Rate Limiting
 * 
 * Implements progressive delays for failed authentication attempts
 * to prevent brute force attacks.
 */

interface RateLimitState {
  attempts: number;
  lastAttempt: number;
  blockedUntil: number | null;
}

const rateLimitStore: Map<string, RateLimitState> = new Map();

/**
 * Calculate delay based on number of failed attempts
 */
function calculateDelay(attempts: number): number {
  // Progressive delays: 1s, 2s, 4s, 8s, 16s, 30s (max)
  const baseDelay = 1000; // 1 second
  const maxDelay = 30000; // 30 seconds
  const delay = Math.min(baseDelay * Math.pow(2, attempts - 1), maxDelay);
  return delay;
}

/**
 * Check if action is rate limited
 */
export function isRateLimited(identifier: string): {
  isLimited: boolean;
  remainingTime: number;
} {
  const state = rateLimitStore.get(identifier);
  
  if (!state || !state.blockedUntil) {
    return { isLimited: false, remainingTime: 0 };
  }
  
  const now = Date.now();
  const remainingTime = Math.max(0, state.blockedUntil - now);
  
  if (remainingTime > 0) {
    return { isLimited: true, remainingTime };
  }
  
  // Block period expired
  return { isLimited: false, remainingTime: 0 };
}

/**
 * Record failed attempt and update rate limit state
 */
export function recordFailedAttempt(identifier: string): void {
  const now = Date.now();
  const state = rateLimitStore.get(identifier) || {
    attempts: 0,
    lastAttempt: now,
    blockedUntil: null,
  };
  
  state.attempts += 1;
  state.lastAttempt = now;
  
  // Calculate block duration
  const delay = calculateDelay(state.attempts);
  state.blockedUntil = now + delay;
  
  rateLimitStore.set(identifier, state);
  
  console.warn(
    `Rate limit: ${state.attempts} failed attempts for ${identifier}. Blocked for ${delay / 1000}s`
  );
}

/**
 * Reset rate limit state after successful attempt
 */
export function resetRateLimit(identifier: string): void {
  rateLimitStore.delete(identifier);
}

/**
 * Get remaining time until unblocked (in seconds)
 */
export function getRemainingBlockTime(identifier: string): number {
  const { remainingTime } = isRateLimited(identifier);
  return Math.ceil(remainingTime / 1000);
}

/**
 * Clear all rate limit states (for testing or admin purposes)
 */
export function clearAllRateLimits(): void {
  rateLimitStore.clear();
}

