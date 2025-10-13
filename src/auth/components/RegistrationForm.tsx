/**
 * Registration Form Component
 * 
 * Provides user registration interface with comprehensive validation,
 * password strength checking, and accessibility features (WCAG 2.1 AA compliant).
 */
import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useApiMutation } from '@/api/useApi';
import { Button } from '@/components/ui/button';
import LoadingIndicator from '@/components/LoadingIndicator';
import { Eye, EyeOff, AlertCircle, CheckCircle2, XCircle } from 'lucide-react';

interface RegistrationFormProps {
  onSuccess?: () => void;
  onSwitchToLogin?: () => void;
}

export default function RegistrationForm({
  onSuccess,
  onSwitchToLogin,
}: RegistrationFormProps) {
  const navigate = useNavigate();
  const { mutate: register, isPending } = useApiMutation('/register', 'post');

  const [formData, setFormData] = useState({
    username: '',
    email: '',
    password: '',
    confirm_password: '',
    first_name: '',
    last_name: '',
    terms_accepted: false,
    marketing_consent: false,
  });

  const [validationErrors, setValidationErrors] = useState<Record<string, string>>({});
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);
  const [passwordStrength, setPasswordStrength] = useState<{
    score: number;
    feedback: string[];
  }>({ score: 0, feedback: [] });

  // Password strength validation
  const checkPasswordStrength = (password: string) => {
    const feedback: string[] = [];
    let score = 0;

    if (password.length >= 8) {
      score++;
    } else {
      feedback.push('At least 8 characters');
    }

    if (/[A-Z]/.test(password)) {
      score++;
    } else {
      feedback.push('One uppercase letter');
    }

    if (/[a-z]/.test(password)) {
      score++;
    } else {
      feedback.push('One lowercase letter');
    }

    if (/\d/.test(password)) {
      score++;
    } else {
      feedback.push('One number');
    }

    if (/[!@#$%^&*(),.?":{}|<>]/.test(password)) {
      score++;
    } else {
      feedback.push('One special character');
    }

    return { score, feedback };
  };

  // Field validation
  const validateField = (name: string, value: string): string | null => {
    switch (name) {
      case 'username':
        if (!value.trim()) return 'Username is required';
        if (value.length < 3) return 'Username must be at least 3 characters';
        if (value.length > 50) return 'Username must be less than 50 characters';
        if (!/^[a-zA-Z0-9_-]+$/.test(value)) return 'Username can only contain letters, numbers, _ and -';
        return null;
      
      case 'email':
        if (!value.trim()) return 'Email is required';
        if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(value)) return 'Invalid email format';
        return null;
      
      case 'password':
        if (!value) return 'Password is required';
        const strength = checkPasswordStrength(value);
        if (strength.score < 5) return 'Password does not meet complexity requirements';
        return null;
      
      case 'confirm_password':
        if (!value) return 'Please confirm your password';
        if (value !== formData.password) return 'Passwords do not match';
        return null;
      
      case 'first_name':
      case 'last_name':
        if (!value.trim()) return `${name === 'first_name' ? 'First' : 'Last'} name is required`;
        if (value.length > 100) return 'Name must be less than 100 characters';
        return null;
      
      default:
        return null;
    }
  };

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value, type, checked } = e.target;
    const newValue = type === 'checkbox' ? checked : value;

    setFormData((prev) => ({ ...prev, [name]: newValue }));

    // Update password strength indicator
    if (name === 'password' && typeof newValue === 'string') {
      setPasswordStrength(checkPasswordStrength(newValue));
    }

    // Clear validation error
    if (validationErrors[name]) {
      setValidationErrors((prev) => {
        const updated = { ...prev };
        delete updated[name];
        return updated;
      });
    }

    // Real-time validation (on blur or change)
    if (type !== 'checkbox' && typeof newValue === 'string') {
      const error = validateField(name, newValue);
      if (error && newValue.length > 0) {
        setValidationErrors((prev) => ({ ...prev, [name]: error }));
      }
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    // Validate all fields
    const errors: Record<string, string> = {};
    Object.keys(formData).forEach((key) => {
      if (key !== 'remember_me' && key !== 'marketing_consent') {
        const error = validateField(key, formData[key as keyof typeof formData] as string);
        if (error) errors[key] = error;
      }
    });

    // Check terms accepted
    if (!formData.terms_accepted) {
      errors.terms_accepted = 'You must accept the terms and conditions';
    }

    if (Object.keys(errors).length > 0) {
      setValidationErrors(errors);
      return;
    }

    // Submit registration
    register(formData, {
      onSuccess: (data) => {
        if (onSuccess) {
          onSuccess();
        } else {
          navigate('/login?registered=true');
        }
      },
      onError: (error: any) => {
        const message = error.response?.data?.detail || 'Registration failed';
        setValidationErrors({ general: message });
      },
    });
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-4" aria-label="Registration form">
      <div>
        <h2 className="text-2xl font-bold text-foreground">Create Account</h2>
        <p className="mt-2 text-sm text-muted-foreground">
          Register to start using APFA
        </p>
      </div>

      {validationErrors.general && (
        <div role="alert" aria-live="polite" className="flex items-center gap-2 rounded-md border border-destructive/50 bg-destructive/10 p-3 text-sm text-destructive">
          <AlertCircle className="h-4 w-4" />
          <span>{validationErrors.general}</span>
        </div>
      )}

      <div className="grid gap-4 sm:grid-cols-2">
        {/* First Name */}
        <div>
          <label htmlFor="first_name" className="mb-2 block text-sm font-medium">
            First Name <span className="text-destructive">*</span>
          </label>
          <input
            type="text"
            id="first_name"
            name="first_name"
            value={formData.first_name}
            onChange={handleInputChange}
            disabled={isPending}
            required
            aria-required="true"
            aria-invalid={!!validationErrors.first_name}
            className="w-full rounded-md border bg-background px-3 py-2 text-sm focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring disabled:opacity-50"
          />
          {validationErrors.first_name && (
            <p role="alert" className="mt-1 text-sm text-destructive">{validationErrors.first_name}</p>
          )}
        </div>

        {/* Last Name */}
        <div>
          <label htmlFor="last_name" className="mb-2 block text-sm font-medium">
            Last Name <span className="text-destructive">*</span>
          </label>
          <input
            type="text"
            id="last_name"
            name="last_name"
            value={formData.last_name}
            onChange={handleInputChange}
            disabled={isPending}
            required
            aria-required="true"
            className="w-full rounded-md border bg-background px-3 py-2 text-sm focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring disabled:opacity-50"
          />
          {validationErrors.last_name && (
            <p role="alert" className="mt-1 text-sm text-destructive">{validationErrors.last_name}</p>
          )}
        </div>
      </div>

      {/* Username */}
      <div>
        <label htmlFor="username" className="mb-2 block text-sm font-medium">
          Username <span className="text-destructive">*</span>
        </label>
        <input
          type="text"
          id="username"
          name="username"
          value={formData.username}
          onChange={handleInputChange}
          disabled={isPending}
          required
          className="w-full rounded-md border bg-background px-3 py-2 text-sm focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring disabled:opacity-50"
        />
        {validationErrors.username && (
          <p role="alert" className="mt-1 text-sm text-destructive">{validationErrors.username}</p>
        )}
      </div>

      {/* Email */}
      <div>
        <label htmlFor="email" className="mb-2 block text-sm font-medium">
          Email <span className="text-destructive">*</span>
        </label>
        <input
          type="email"
          id="email"
          name="email"
          value={formData.email}
          onChange={handleInputChange}
          disabled={isPending}
          required
          className="w-full rounded-md border bg-background px-3 py-2 text-sm focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring disabled:opacity-50"
        />
        {validationErrors.email && (
          <p role="alert" className="mt-1 text-sm text-destructive">{validationErrors.email}</p>
        )}
      </div>

      {/* Password */}
      <div>
        <label htmlFor="password" className="mb-2 block text-sm font-medium">
          Password <span className="text-destructive">*</span>
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
            className="w-full rounded-md border bg-background px-3 py-2 pr-10 text-sm focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring disabled:opacity-50"
          />
          <button
            type="button"
            onClick={() => setShowPassword(!showPassword)}
            className="absolute right-2 top-1/2 -translate-y-1/2"
            aria-label={showPassword ? 'Hide password' : 'Show password'}
          >
            {showPassword ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
          </button>
        </div>
        
        {/* Password strength indicator */}
        {formData.password && (
          <div className="mt-2">
            <div className="flex gap-1">
              {[1, 2, 3, 4, 5].map((level) => (
                <div
                  key={level}
                  className={`h-1 flex-1 rounded ${
                    level <= passwordStrength.score
                      ? passwordStrength.score < 3
                        ? 'bg-destructive'
                        : passwordStrength.score < 5
                        ? 'bg-yellow-500'
                        : 'bg-green-500'
                      : 'bg-gray-200'
                  }`}
                />
              ))}
            </div>
            {passwordStrength.feedback.length > 0 && (
              <p className="mt-1 text-xs text-muted-foreground">
                Needs: {passwordStrength.feedback.join(', ')}
              </p>
            )}
          </div>
        )}
        
        {validationErrors.password && (
          <p role="alert" className="mt-1 text-sm text-destructive">{validationErrors.password}</p>
        )}
      </div>

      {/* Confirm Password */}
      <div>
        <label htmlFor="confirm_password" className="mb-2 block text-sm font-medium">
          Confirm Password <span className="text-destructive">*</span>
        </label>
        <div className="relative">
          <input
            type={showConfirmPassword ? 'text' : 'password'}
            id="confirm_password"
            name="confirm_password"
            value={formData.confirm_password}
            onChange={handleInputChange}
            disabled={isPending}
            required
            className="w-full rounded-md border bg-background px-3 py-2 pr-10 text-sm focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring disabled:opacity-50"
          />
          <button
            type="button"
            onClick={() => setShowConfirmPassword(!showConfirmPassword)}
            className="absolute right-2 top-1/2 -translate-y-1/2"
            aria-label={showConfirmPassword ? 'Hide password' : 'Show password'}
          >
            {showConfirmPassword ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
          </button>
        </div>
        {validationErrors.confirm_password && (
          <p role="alert" className="mt-1 text-sm text-destructive">{validationErrors.confirm_password}</p>
        )}
      </div>

      {/* Terms and Conditions */}
      <div>
        <div className="flex items-start">
          <input
            type="checkbox"
            id="terms_accepted"
            name="terms_accepted"
            checked={formData.terms_accepted}
            onChange={handleInputChange}
            disabled={isPending}
            required
            aria-required="true"
            className="mt-1 h-4 w-4 rounded border-gray-300 text-primary focus:ring-2 focus:ring-primary"
          />
          <label htmlFor="terms_accepted" className="ml-2 text-sm text-foreground">
            I accept the{' '}
            <a href="/terms" target="_blank" className="text-primary hover:underline">
              Terms and Conditions
            </a>{' '}
            <span className="text-destructive">*</span>
          </label>
        </div>
        {validationErrors.terms_accepted && (
          <p role="alert" className="mt-1 text-sm text-destructive">{validationErrors.terms_accepted}</p>
        )}
      </div>

      {/* Marketing Consent */}
      <div className="flex items-start">
        <input
          type="checkbox"
          id="marketing_consent"
          name="marketing_consent"
          checked={formData.marketing_consent}
          onChange={handleInputChange}
          disabled={isPending}
          className="mt-1 h-4 w-4 rounded border-gray-300 text-primary focus:ring-2 focus:ring-primary"
        />
        <label htmlFor="marketing_consent" className="ml-2 text-sm text-muted-foreground">
          I want to receive updates and marketing communications
        </label>
      </div>

      {/* Submit button */}
      <Button type="submit" disabled={isPending} className="w-full">
        {isPending ? (
          <span className="flex items-center gap-2">
            <LoadingIndicator size="small" />
            <span>Creating account...</span>
          </span>
        ) : (
          'Create Account'
        )}
      </Button>

      {/* Switch to login */}
      {onSwitchToLogin && (
        <div className="text-center text-sm text-muted-foreground">
          Already have an account?{' '}
          <button
            type="button"
            onClick={onSwitchToLogin}
            className="font-medium text-primary hover:underline"
          >
            Login here
          </button>
        </div>
      )}
    </form>
  );
}

