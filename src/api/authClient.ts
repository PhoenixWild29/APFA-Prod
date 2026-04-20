/**
 * Auth-specific Axios client for /token/* endpoints.
 *
 * Separated from apiClient per CoWork requirement #2:
 * - withCredentials: true — sends httpOnly refresh_token cookie
 * - No Authorization header — refresh uses cookies, not Bearer tokens
 * - No retry logic — auth failures should surface immediately
 * - No circuit breaker — /token/* is critical path
 *
 * apiClient handles everything else (withCredentials: false).
 */
import axios from 'axios';
import { authConfig } from '@/config/auth';

const authClient = axios.create({
  baseURL: authConfig.apiEndpoint,
  timeout: 10_000,
  withCredentials: true, // Send httpOnly cookies to /token/*
  headers: { 'Content-Type': 'application/json' },
});

export default authClient;
