/**
 * Login Form Component
 * 
 * Provides user authentication interface with real-time validation,
 * error handling, and accessibility features (WCAG 2.1 AA compliant).
 */
import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useLogin } from '@/api/useApi';
import { setAccessToken } from '@/config/auth';
import { Button } from '@/components/ui/button';
import LoadingIndicator from '@/components/LoadingIndicator';
import { Eye, EyeOff, AlertCircle } from 'lucide-react';

interface LoginFormProps {
  onSuccess?: () => void;
  onSwitchToRegister?: () => void;
  onSwitchToPasswordReset?: () => void;
}

export default function LoginForm({
  onSuccess,
  onSwitchToRegister,
  onSwitchToPasswordReset,
}: LoginFormProps) {
  const navigate = useNavigate();
  const { mutate: login, isPending, error } = useLogin();

  const [formData, setFormData] = useState({
    username: '',
    password: '',
    remember_me: false,
  });

  const [validationErrors, setValidationErrors] = useState<Record<string, string>>({});
  const [showPassword, setShowPassword] = useState(false);

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

    // Clear validation error on input change
    if (validationErrors[name]) {
      setValidationErrors((prev) => {
        const updated = { ...prev };
        delete updated[name];
        return updated;
      });
    }

    // Real-time validation
    if (type !== 'checkbox') {
      const error = validateField(name, value);
      if (error) {
        setValidationErrors((prev) => ({ ...prev, [name]: error }));
      }
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    // Validate all fields
    const errors: Record<string, string> = {};
    Object.keys(formData).forEach((key) => {
      if (key !== 'remember_me') {
        const error = validateField(key, formData[key as keyof typeof formData] as string);
        if (error) errors[key] = error;
      }
    });

    if (Object.keys(errors).length > 0) {
      setValidationErrors(errors);
      return;
    }

    // Submit login request
    login(formData, {
      onSuccess: (data) => {
        // Store token
        setAccessToken(data.access_token, data.expires_in);
        
        // Success callback
        if (onSuccess) {
          onSuccess();
        } else {
          navigate('/');
        }
      },
      onError: (error: any) => {
        // Handle authentication errors
        const message = error.response?.data?.detail || 'Authentication failed';
        setValidationErrors({ general: message });
      },
    });
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-6" aria-label="Login form">
      <div>
        <h2 className="text-2xl font-bold text-foreground">Login</h2>
        <p className="mt-2 text-sm text-muted-foreground">
          Enter your credentials to access your account
        </p>
      </div>

      {/* General error message */}
      {validationErrors.general && (
        <div
          role="alert"
          aria-live="polite"
          className="flex items-center gap-2 rounded-md border border-destructive/50 bg-destructive/10 p-3 text-sm text-destructive"
        >
          <AlertCircle className="h-4 w-4" />
          <span>{validationErrors.general}</span>
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
          Don't have an account?{' '}
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

