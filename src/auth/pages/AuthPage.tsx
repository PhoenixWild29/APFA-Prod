/**
 * Authentication Page Component
 * 
 * Provides a unified interface for all authentication flows:
 * - Login
 * - Registration
 * - Password Reset
 */
import React, { useState } from 'react';
import LoginForm from '../components/LoginForm';
import RegistrationForm from '../components/RegistrationForm';
import PasswordResetForm from '../components/PasswordResetForm';

type AuthView = 'login' | 'register' | 'reset-password';

export default function AuthPage() {
  const [currentView, setCurrentView] = useState<AuthView>('login');

  return (
    <div className="flex min-h-screen items-center justify-center bg-background px-4 py-12">
      <div className="w-full max-w-md">
        {/* Tabs for switching between forms */}
        <div className="mb-6 flex gap-2 rounded-lg border bg-card p-1">
          <button
            onClick={() => setCurrentView('login')}
            className={`flex-1 rounded-md px-4 py-2 text-sm font-medium transition-colors ${
              currentView === 'login'
                ? 'bg-primary text-primary-foreground'
                : 'text-muted-foreground hover:bg-muted'
            }`}
            aria-current={currentView === 'login' ? 'page' : undefined}
          >
            Login
          </button>
          <button
            onClick={() => setCurrentView('register')}
            className={`flex-1 rounded-md px-4 py-2 text-sm font-medium transition-colors ${
              currentView === 'register'
                ? 'bg-primary text-primary-foreground'
                : 'text-muted-foreground hover:bg-muted'
            }`}
            aria-current={currentView === 'register' ? 'page' : undefined}
          >
            Register
          </button>
        </div>

        {/* Form container */}
        <div className="rounded-lg border bg-card p-6 shadow-lg">
          {currentView === 'login' && (
            <LoginForm
              onSwitchToRegister={() => setCurrentView('register')}
              onSwitchToPasswordReset={() => setCurrentView('reset-password')}
            />
          )}
          {currentView === 'register' && (
            <RegistrationForm onSwitchToLogin={() => setCurrentView('login')} />
          )}
          {currentView === 'reset-password' && (
            <PasswordResetForm onSwitchToLogin={() => setCurrentView('login')} />
          )}
        </div>

        {/* Footer */}
        <div className="mt-6 text-center text-sm text-muted-foreground">
          <p>© 2025 APFA - Secure Authentication</p>
        </div>
      </div>
    </div>
  );
}

