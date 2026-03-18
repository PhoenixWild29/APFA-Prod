/**
 * Theme Toggle Component
 * 
 * Allows users to manually switch between light and dark themes
 * with automatic system preference detection.
 */
import React, { useEffect, useState, useMemo } from 'react';
import { Moon, Sun } from 'lucide-react';
import { Button } from '@/components/ui/button';

type Theme = 'light' | 'dark' | 'system';

export default function ThemeToggle() {
  const savedTheme = localStorage.getItem('theme') as Theme | null;
  const [theme, setTheme] = useState<Theme>(savedTheme || 'system');

  const resolvedTheme = useMemo(() => {
    if (theme === 'system') {
      const systemTheme = window.matchMedia('(prefers-color-scheme: dark)').matches
        ? 'dark'
        : 'light';
      return systemTheme;
    } else {
      return theme;
    }
  }, [theme]);

  useEffect(() => {
    // Apply theme to document
    const root = window.document.documentElement;
    root.classList.remove('light', 'dark');

    root.classList.add(resolvedTheme);

    // Save preference
    localStorage.setItem('theme', theme);
  }, [theme, resolvedTheme]);

  const toggleTheme = () => {
    setTheme((prev) => {
      if (prev === 'light') return 'dark';
      if (prev === 'dark') return 'system';
      return 'light';
    });
  };

  return (
    <Button
      variant="outline"
      size="icon"
      onClick={toggleTheme}
      aria-label={`Current theme: ${theme}. Click to change theme`}
      title={`Current theme: ${theme}`}
    >
      {resolvedTheme === 'dark' ? (
        <Moon className="h-4 w-4" />
      ) : (
        <Sun className="h-4 w-4" />
      )}
      <span className="sr-only">Toggle theme</span>
    </Button>
  );
}

