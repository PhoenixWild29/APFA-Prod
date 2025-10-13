/**
 * User Preferences Hook
 * 
 * Manages and persists:
 * - Dashboard layouts
 * - Theme choices
 * - Language settings
 * - Accessibility preferences
 */
import { useState, useEffect } from 'react';

interface UserPreferences {
  theme: 'light' | 'dark';
  language: string;
  highContrast: boolean;
  dashboardLayout: any;
  fontSize: 'small' | 'medium' | 'large';
}

const DEFAULT_PREFERENCES: UserPreferences = {
  theme: 'light',
  language: 'en',
  highContrast: false,
  dashboardLayout: null,
  fontSize: 'medium'
};

export const useUserPreferences = () => {
  const [preferences, setPreferences] = useState<UserPreferences>(() => {
    const saved = localStorage.getItem('userPreferences');
    return saved ? JSON.parse(saved) : DEFAULT_PREFERENCES;
  });

  // Persist preferences on change
  useEffect(() => {
    localStorage.setItem('userPreferences', JSON.stringify(preferences));
  }, [preferences]);

  // Detect system theme preference
  useEffect(() => {
    const mediaQuery = window.matchMedia('(prefers-color-scheme: dark)');
    
    const handleChange = (e: MediaQueryListEvent) => {
      if (!localStorage.getItem('userThemeOverride')) {
        updatePreference('theme', e.matches ? 'dark' : 'light');
      }
    };
    
    mediaQuery.addEventListener('change', handleChange);
    
    return () => mediaQuery.removeEventListener('change', handleChange);
  }, []);

  const updatePreference = <K extends keyof UserPreferences>(
    key: K,
    value: UserPreferences[K]
  ): void => {
    setPreferences(prev => ({ ...prev, [key]: value }));
  };

  const resetPreferences = (): void => {
    setPreferences(DEFAULT_PREFERENCES);
    localStorage.removeItem('userPreferences');
    localStorage.removeItem('userThemeOverride');
  };

  return {
    preferences,
    updatePreference,
    resetPreferences
  };
};

