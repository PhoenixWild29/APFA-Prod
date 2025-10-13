/**
 * Authentication configuration for JWT-based backend
 * Adapted from AWS Amplify pattern to work with FastAPI JWT tokens
 */

export const authConfig = {
  apiEndpoint: process.env.REACT_APP_API_URL || 'http://localhost:8000',
  tokenEndpoint: '/token',
  tokenStorageKey: 'apfa_access_token',
  tokenRefreshThreshold: 300, // 5 minutes before expiry (in seconds)
  tokenExpiryKey: 'apfa_token_expiry',
};

/**
 * Get access token from localStorage
 * @returns {string|null} JWT access token
 */
export const getAccessToken = () => {
  return localStorage.getItem(authConfig.tokenStorageKey);
};

/**
 * Set access token in localStorage
 * @param {string} token - JWT access token
 * @param {number} expiresIn - Token expiry in seconds (optional)
 */
export const setAccessToken = (token, expiresIn = null) => {
  localStorage.setItem(authConfig.tokenStorageKey, token);
  
  if (expiresIn) {
    const expiryTime = Date.now() + expiresIn * 1000;
    localStorage.setItem(authConfig.tokenExpiryKey, expiryTime.toString());
  }
};

/**
 * Clear access token from localStorage
 */
export const clearAccessToken = () => {
  localStorage.removeItem(authConfig.tokenStorageKey);
  localStorage.removeItem(authConfig.tokenExpiryKey);
};

/**
 * Check if token is expired
 * @param {string} token - JWT access token
 * @returns {boolean} True if token is expired
 */
export const isTokenExpired = (token) => {
  if (!token) return true;
  
  try {
    // Decode JWT payload (second part of token)
    const payload = JSON.parse(atob(token.split('.')[1]));
    
    // Check expiry time (exp is in seconds, Date.now() is in milliseconds)
    if (payload.exp) {
      return payload.exp * 1000 < Date.now();
    }
    
    return false;
  } catch (error) {
    console.error('Error decoding token:', error);
    return true;
  }
};

/**
 * Get token expiry time
 * @param {string} token - JWT access token
 * @returns {number|null} Expiry timestamp in milliseconds
 */
export const getTokenExpiry = (token) => {
  if (!token) return null;
  
  try {
    const payload = JSON.parse(atob(token.split('.')[1]));
    return payload.exp ? payload.exp * 1000 : null;
  } catch {
    return null;
  }
};

/**
 * Check if token needs refresh (within threshold)
 * @param {string} token - JWT access token
 * @returns {boolean} True if token should be refreshed
 */
export const shouldRefreshToken = (token) => {
  const expiry = getTokenExpiry(token);
  if (!expiry) return false;
  
  const now = Date.now();
  const threshold = authConfig.tokenRefreshThreshold * 1000;
  
  return expiry - now < threshold;
};

/**
 * Get username from token
 * @param {string} token - JWT access token
 * @returns {string|null} Username from token
 */
export const getUsernameFromToken = (token) => {
  if (!token) return null;
  
  try {
    const payload = JSON.parse(atob(token.split('.')[1]));
    return payload.sub || null;
  } catch {
    return null;
  }
};

