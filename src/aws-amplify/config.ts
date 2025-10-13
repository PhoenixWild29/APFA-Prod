/**
 * Authentication Configuration
 * 
 * Adapted from AWS Amplify pattern to work with JWT-based FastAPI backend
 * 
 * Note: This file provides a configuration structure compatible with
 * AWS Amplify patterns, but connects to our JWT-based authentication API.
 * For full AWS Cognito integration, update these values with your Cognito settings.
 */

export const authConfig = {
  // API Configuration
  API: {
    endpoints: [
      {
        name: 'apfa-api',
        endpoint: import.meta.env.VITE_API_URL || 'http://localhost:8000',
        custom_header: async () => {
          // Get token from localStorage
          const token = localStorage.getItem('apfa_access_token');
          return token ? { Authorization: `Bearer ${token}` } : {};
        },
      },
    ],
  },

  // Auth Configuration (JWT-based, not Cognito)
  Auth: {
    region: 'us-east-1', // Placeholder - not used with JWT
    userPoolId: 'us-east-1_xxxxxx', // Placeholder - not used with JWT
    userPoolWebClientId: 'xxxxxxxxxx', // Placeholder - not used with JWT
    
    // Authentication endpoints
    endpoints: {
      login: '/token',
      register: '/register',
      resetPassword: '/auth/reset-password',
      verifyEmail: '/auth/verify-email',
    },

    // Token configuration
    token: {
      storageKey: 'apfa_access_token',
      refreshStorageKey: 'apfa_refresh_token',
      expiryKey: 'apfa_token_expiry',
    },
  },
};

/**
 * For AWS Cognito integration, replace with:
 * 
 * import { Amplify } from 'aws-amplify';
 * 
 * Amplify.configure({
 *   Auth: {
 *     region: 'us-east-1',
 *     userPoolId: 'your-user-pool-id',
 *     userPoolWebClientId: 'your-client-id',
 *     mandatorySignIn: true,
 *     authenticationFlowType: 'USER_SRP_AUTH',
 *   },
 * });
 */

export default authConfig;

