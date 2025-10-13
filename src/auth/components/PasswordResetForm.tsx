/**
 * Password Reset Form Component
 * 
 * Enables users to request password reset via email with
 * validation and accessibility features (WCAG 2.1 AA compliant).
 */
import React, { useState } from 'react';
import { useApiMutation } from '@/api/useApi';
import { Button } from '@/components/ui/button';
import LoadingIndicator from '@/components/LoadingIndicator';
import { AlertCircle, CheckCircle2, ArrowLeft } from 'lucide-react';

interface PasswordResetFormProps {
  onSuccess?: () => void;
  onSwitchToLogin?: () => void;
}

export default function PasswordResetForm({
  onSuccess,
  onSwitchToLogin,
}: PasswordResetFormProps) {
  const { mutate: requestReset, isPending, isSuccess } = useApiMutation('/auth/reset-password', 'post');

  const [email, setEmail] = useState('');
  const [validationError, setValidationError] = useState<string>('');
  const [errorMessage, setErrorMessage] = useState<string>('');

  const validateEmail = (value: string): string | null => {
    if (!value.trim()) return 'Email is required';
    if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(value)) return 'Invalid email format';
    return null;
  };

  const handleEmailChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const value = e.target.value;
    setEmail(value);
    
    // Clear errors
    setValidationError('');
    setErrorMessage('');
    
    // Real-time validation
    if (value.length > 0) {
      const error = validateEmail(value);
      if (error) setValidationError(error);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    // Validate email
    const error = validateEmail(email);
    if (error) {
      setValidationError(error);
      return;
    }

    // Submit reset request
    requestReset(
      { email },
      {
        onSuccess: () => {
          if (onSuccess) {
            onSuccess();
          }
        },
        onError: (error: any) => {
          const message = error.response?.data?.detail || 'Failed to send reset email';
          setErrorMessage(message);
        },
      }
    );
  };

  if (isSuccess) {
    return (
      <div className="space-y-6" aria-live="polite" role="status">
        <div className="flex flex-col items-center text-center">
          <div className="mb-4 flex h-16 w-16 items-center justify-center rounded-full bg-green-100">
            <CheckCircle2 className="h-8 w-8 text-green-600" />
          </div>
          <h2 className="text-2xl font-bold text-foreground">Check Your Email</h2>
          <p className="mt-2 text-sm text-muted-foreground">
            We've sent password reset instructions to <strong>{email}</strong>
          </p>
        </div>

        <div className="space-y-2 rounded-md border bg-card p-4 text-sm">
          <p className="font-medium">Next steps:</p>
          <ol className="ml-4 list-decimal space-y-1 text-muted-foreground">
            <li>Check your email inbox (and spam folder)</li>
            <li>Click the password reset link</li>
            <li>Create a new password</li>
            <li>Login with your new credentials</li>
          </ol>
        </div>

        {onSwitchToLogin && (
          <Button onClick={onSwitchToLogin} variant="outline" className="w-full">
            <ArrowLeft className="mr-2 h-4 w-4" />
            Back to Login
          </Button>
        )}
      </div>
    );
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-6" aria-label="Password reset form">
      <div>
        <h2 className="text-2xl font-bold text-foreground">Reset Password</h2>
        <p className="mt-2 text-sm text-muted-foreground">
          Enter your email address and we'll send you instructions to reset your password
        </p>
      </div>

      {errorMessage && (
        <div role="alert" aria-live="polite" className="flex items-center gap-2 rounded-md border border-destructive/50 bg-destructive/10 p-3 text-sm text-destructive">
          <AlertCircle className="h-4 w-4" />
          <span>{errorMessage}</span>
        </div>
      )}

      <div>
        <label htmlFor="email" className="mb-2 block text-sm font-medium text-foreground">
          Email Address <span className="text-destructive" aria-label="required">*</span>
        </label>
        <input
          type="email"
          id="email"
          name="email"
          value={email}
          onChange={handleEmailChange}
          disabled={isPending}
          required
          aria-required="true"
          aria-invalid={!!validationError}
          aria-describedby={validationError ? 'email-error' : undefined}
          className="w-full rounded-md border bg-background px-3 py-2 text-sm ring-offset-background placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50"
          placeholder="your.email@example.com"
        />
        {validationError && (
          <p id="email-error" role="alert" className="mt-1 text-sm text-destructive">
            {validationError}
          </p>
        )}
      </div>

      <Button type="submit" disabled={isPending || !!validationError} className="w-full">
        {isPending ? (
          <span className="flex items-center gap-2">
            <LoadingIndicator size="small" />
            <span>Sending reset email...</span>
          </span>
        ) : (
          'Send Reset Instructions'
        )}
      </Button>

      {onSwitchToLogin && (
        <button
          type="button"
          onClick={onSwitchToLogin}
          className="flex w-full items-center justify-center gap-2 text-sm text-muted-foreground hover:text-foreground"
        >
          <ArrowLeft className="h-4 w-4" />
          Back to Login
        </button>
      )}
    </form>
  );
}

