/**
 * Accessibility Utilities
 * 
 * WCAG 2.1 AA compliance utilities:
 * - Focus management
 * - ARIA helpers
 * - Keyboard navigation
 * - High contrast mode
 */

/**
 * Focus the first focusable element in a container
 */
export const focusFirstElement = (containerRef: React.RefObject<HTMLElement>): void => {
  if (!containerRef.current) return;
  
  const focusable = containerRef.current.querySelectorAll(
    'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
  );
  
  if (focusable.length > 0) {
    (focusable[0] as HTMLElement).focus();
  }
};

/**
 * Trap focus within a modal or dialog
 */
export const trapFocus = (containerRef: React.RefObject<HTMLElement>): (() => void) => {
  if (!containerRef.current) return () => {};
  
  const focusableElements = containerRef.current.querySelectorAll(
    'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
  );
  
  const firstElement = focusableElements[0] as HTMLElement;
  const lastElement = focusableElements[focusableElements.length - 1] as HTMLElement;
  
  const handleTabKey = (e: KeyboardEvent) => {
    if (e.key !== 'Tab') return;
    
    if (e.shiftKey) {
      if (document.activeElement === firstElement) {
        e.preventDefault();
        lastElement.focus();
      }
    } else {
      if (document.activeElement === lastElement) {
        e.preventDefault();
        firstElement.focus();
      }
    }
  };
  
  document.addEventListener('keydown', handleTabKey);
  
  return () => {
    document.removeEventListener('keydown', handleTabKey);
  };
};

/**
 * Announce message to screen readers
 */
export const announceToScreenReader = (message: string, priority: 'polite' | 'assertive' = 'polite'): void => {
  const announcement = document.createElement('div');
  announcement.setAttribute('role', 'status');
  announcement.setAttribute('aria-live', priority);
  announcement.setAttribute('aria-atomic', 'true');
  announcement.className = 'sr-only';
  announcement.textContent = message;
  
  document.body.appendChild(announcement);
  
  setTimeout(() => {
    document.body.removeChild(announcement);
  }, 1000);
};

/**
 * Toggle high contrast mode
 */
export const toggleHighContrastMode = (enabled: boolean): void => {
  if (enabled) {
    document.documentElement.classList.add('high-contrast');
    localStorage.setItem('highContrast', 'enabled');
  } else {
    document.documentElement.classList.remove('high-contrast');
    localStorage.setItem('highContrast', 'disabled');
  }
};

/**
 * Check if high contrast mode is enabled
 */
export const isHighContrastEnabled = (): boolean => {
  return localStorage.getItem('highContrast') === 'enabled' ||
         document.documentElement.classList.contains('high-contrast');
};

/**
 * Set document direction for RTL languages
 */
export const setDocumentDirection = (language: string): void => {
  const rtlLanguages = ['ar', 'he', 'fa', 'ur'];
  const isRTL = rtlLanguages.includes(language);
  
  document.documentElement.dir = isRTL ? 'rtl' : 'ltr';
  document.documentElement.lang = language;
};

/**
 * Generate unique ID for ARIA associations
 */
export const generateAriaId = (prefix: string): string => {
  return `${prefix}-${Math.random().toString(36).substr(2, 9)}`;
};

