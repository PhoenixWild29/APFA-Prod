/**
 * Login Form Component
 *
 * Auth lifecycle:
 * - Calls authStore.login() directly (not useLogin hook — that's dead code)
 * - Local useState for isPending/error (login loading is per-form, not in store)
 * - Navigation via useEffect on isAuthenticated (works for login, SSO, rehydration)
 * - mapLoginError translates HTTP status codes to user-friendly messages
 *
 * WCAG 2.1 AA compliant: aria-labels, role="alert", aria-invalid, etc.
 */
import React, { useEffect, useRef, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuthStore } from '@/store/authStore';
import { Button } from '@/components/ui/button';
import LoadingIndicator from '@/components/LoadingIndicator';
import { Eye, EyeOff, AlertCircle } from 'lucide-react';

interface LoginFormProps {
  onSuccess?: () => void;
  onSwitchToRegister?: () => void;
  onSwitchToPasswordReset?: () => void;
}

/**
 * Map API error responses to user-friendly messages.
 * Translates HTTP status + backend detail into actionable copy.
 */
function mapLoginError(error: unknown): string {
  const axiosErr = error as {
    response?: { status?: number; data?: { detail?: string } };
    code?: string;
  };

  const status = axiosErr.response?.status;
  const detail = axiosErr.response?.data?.detail;

  switch (status) {
    case 401:
      return 'Invalid username or password.';
    case 403:
      return 'Account disabled. Contact support.';
    case 422:
      return detail || 'Invalid request. Check your input.';
    case 429:
      return 'Too many attempts. Please wait a moment and try again.';
    case 500:
    case 502:
    case 503:
      return 'Server error. Please try again in a few minutes.';
    default:
      break;
  }

  if (axiosErr.code === 'CIRCUIT_BREAKER_OPEN') {
    return 'Service temporarily unavailable. Please try again shortly.';
  }

  if (axiosErr.code === 'ERR_NETWORK' || axiosErr.code === 'ECONNABORTED') {
    return 'Network error. Check your connection and try again.';
  }

  return detail || 'Login failed. Please try again.';
}

export default function LoginForm({
  onSuccess,
  onSwitchToRegister,
  onSwitchToPasswordReset,
}: LoginFormProps) {
  const navigate = useNavigate();
  const login = useAuthStore((s) => s.login);
  const isAuthenticated = useAuthStore((s) => s.isAuthenticated);

  // Local form state — login loading/error is per-form, not in store
  const [isPending, setIsPending] = useState(false);
  const [loginError, setLoginError] = useState<string | null>(null);
  const submittingRef = useRef(false); // gate against StrictMode double-submit

  const [formData, setFormData] = useState({
    username: '',
    password: '',
    remember_me: false,
  });

  const [validationErrors, setValidationErrors] = useState<Record<string, string>>({});
  const [showPassword, setShowPassword] = useState(false);

  // Issue 3: Navigate via useEffect on isAuthenticated — one navigation policy
  // Works for login, SSO, and rehydration. replace: true prevents /auth in history.
  useEffect(() => {
    if (isAuthenticated) {
      if (onSuccess) {
        onSuccess();
      } else {
        navigate('/app/advisor', { replace: true });
      }
    }
  }, [isAuthenticated, navigate, onSuccess]);

  // Real-time validation
  const validateField = (name: string, value: string): string | null => {
    switch (name) {
      case 'username':
        if (!value.trim()) return 'Username is required';
        if (value.length < 3) return 'Username must be at least 3 characters';
        return null;
      case 'password':
        if (!value) return 'Password is required';
        return null;
      default:
        return null;
    }
  };

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value, type, checked } = e.target;
    const newValue = type === 'checkbox' ? checked : value;

    setFormData((prev) => ({ ...prev, [name]: newValue }));

    // Clear errors on input change
    if (validationErrors[name]) {
      setValidationErrors((prev) => {
        const updated = { ...prev };
        delete updated[name];
        return updated;
      });
    }
    if (loginError) {
      setLoginError(null);
    }

    // Real-time field validation
    if (type !== 'checkbox') {
      const fieldError = validateField(name, value);
      if (fieldError) {
        setValidationErrors((prev) => ({ ...prev, [name]: fieldError }));
      }
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    // Gate against double-submit (React StrictMode double-render)
    if (submittingRef.current) return;

    // Validate all fields
    const errors: Record<string, string> = {};
    Object.keys(formData).forEach((key) => {
      if (key !== 'remember_me') {
        const fieldError = validateField(key, formData[key as keyof typeof formData] as string);
        if (fieldError) errors[key] = fieldError;
      }
    });

    if (Object.keys(errors).length > 0) {
      setValidationErrors(errors);
      return;
    }

    // Call authStore.login() directly — no useLogin hook
    submittingRef.current = true;
    setIsPending(true);
    setLoginError(null);

    try {
      await login({
        username: formData.username,
        password: formData.password,
      });
      // Navigation happens via useEffect on isAuthenticated — not here
    } catch (error: unknown) {
      setLoginError(mapLoginError(error));
    } finally {
      setIsPending(false);
      submittingRef.current = false;
    }
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-6" aria-label="Login form">
      <div>
        <h2 className="text-2xl font-bold text-foreground">Login</h2>
        <p className="mt-2 text-sm text-muted-foreground">
          Enter your credentials to access your account
        </p>
      </div>

      {/* Login error message */}
      {loginError && (
        <div
          role="alert"
          aria-live="polite"
          className="flex items-center gap-2 rounded-md border border-destructive/50 bg-destructive/10 p-3 text-sm text-destructive"
        >
          <AlertCircle className="h-4 w-4" />
          <span>{loginError}</span>
        </div>
      )}

      {/* Username field */}
      <div>
        <label
          htmlFor="username"
          className="mb-2 block text-sm font-medium text-foreground"
        >
          Username <span className="text-destructive" aria-label="required">*</span>
        </label>
        <input
          type="text"
          id="username"
          name="username"
          value={formData.username}
          onChange={handleInputChange}
          disabled={isPending}
          required
          aria-required="true"
          aria-invalid={!!validationErrors.username}
          aria-describedby={validationErrors.username ? 'username-error' : undefined}
          className="w-full rounded-md border bg-background px-3 py-2 text-sm ring-offset-background placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50"
          placeholder="Enter your username"
        />
        {validationErrors.username && (
          <p id="username-error" role="alert" className="mt-1 text-sm text-destructive">
            {validationErrors.username}
          </p>
        )}
      </div>

      {/* Password field */}
      <div>
        <label
          htmlFor="password"
          className="mb-2 block text-sm font-medium text-foreground"
        >
          Password <span className="text-destructive" aria-label="required">*</span>
        </label>
        <div className="relative">
          <input
            type={showPassword ? 'text' : 'password'}
            id="password"
            name="password"
            value={formData.password}
            onChange={handleInputChange}
            disabled={isPending}
            required
            aria-required="true"
            aria-invalid={!!validationErrors.password}
            aria-describedby={validationErrors.password ? 'password-error' : undefined}
            className="w-full rounded-md border bg-background px-3 py-2 pr-10 text-sm ring-offset-background placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50"
            placeholder="Enter your password"
          />
          <button
            type="button"
            onClick={() => setShowPassword(!showPassword)}
            className="absolute right-2 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground"
            aria-label={showPassword ? 'Hide password' : 'Show password'}
          >
            {showPassword ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
          </button>
        </div>
        {validationErrors.password && (
          <p id="password-error" role="alert" className="mt-1 text-sm text-destructive">
            {validationErrors.password}
          </p>
        )}
      </div>

      {/* Remember me checkbox */}
      <div className="flex items-center justify-between">
        <div className="flex items-center">
          <input
            type="checkbox"
            id="remember_me"
            name="remember_me"
            checked={formData.remember_me}
            onChange={handleInputChange}
            disabled={isPending}
            className="h-4 w-4 rounded border-gray-300 text-primary focus:ring-2 focus:ring-primary"
          />
          <label htmlFor="remember_me" className="ml-2 text-sm text-foreground">
            Remember me
          </label>
        </div>

        {onSwitchToPasswordReset && (
          <button
            type="button"
            onClick={onSwitchToPasswordReset}
            className="text-sm text-primary hover:underline"
          >
            Forgot password?
          </button>
        )}
      </div>

      {/* Submit button */}
      <Button
        type="submit"
        disabled={isPending}
        className="w-full"
        aria-busy={isPending}
      >
        {isPending ? (
          <span className="flex items-center gap-2">
            <LoadingIndicator size="small" />
            <span>Logging in...</span>
          </span>
        ) : (
          'Login'
        )}
      </Button>

      {/* Switch to registration */}
      {onSwitchToRegister && (
        <div className="text-center text-sm text-muted-foreground">
          Don&apos;t have an account?{' '}
          <button
            type="button"
            onClick={onSwitchToRegister}
            className="font-medium text-primary hover:underline"
          >
            Register here
          </button>
        </div>
      )}
    </form>
  );
}
