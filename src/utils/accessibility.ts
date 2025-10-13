/**
 * Accessibility Utilities
 * 
 * Helper functions for managing focus, announcing content to screen readers,
 * and ensuring WCAG 2.1 AA compliance.
 */

/**
 * Announce message to screen readers using ARIA live region
 */
export function announceToScreenReader(message: string, priority: 'polite' | 'assertive' = 'polite') {
  const liveRegion = document.getElementById('aria-live-region') || createLiveRegion(priority);
  liveRegion.textContent = message;
  
  // Clear after 1 second to allow re-announcement
  setTimeout(() => {
    liveRegion.textContent = '';
  }, 1000);
}

/**
 * Create ARIA live region if it doesn't exist
 */
function createLiveRegion(priority: 'polite' | 'assertive' = 'polite'): HTMLElement {
  const existingRegion = document.getElementById('aria-live-region');
  if (existingRegion) return existingRegion;
  
  const liveRegion = document.createElement('div');
  liveRegion.id = 'aria-live-region';
  liveRegion.setAttribute('aria-live', priority);
  liveRegion.setAttribute('aria-atomic', 'true');
  liveRegion.className = 'sr-only';
  document.body.appendChild(liveRegion);
  
  return liveRegion;
}

/**
 * Trap focus within a specific element (for modals, dialogs)
 */
export function trapFocus(element: HTMLElement) {
  const focusableElements = element.querySelectorAll<HTMLElement>(
    'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
  );
  
  const firstElement = focusableElements[0];
  const lastElement = focusableElements[focusableElements.length - 1];
  
  const handleTabKey = (e: KeyboardEvent) => {
    if (e.key !== 'Tab') return;
    
    if (e.shiftKey && document.activeElement === firstElement) {
      e.preventDefault();
      lastElement.focus();
    } else if (!e.shiftKey && document.activeElement === lastElement) {
      e.preventDefault();
      firstElement.focus();
    }
  };
  
  element.addEventListener('keydown', handleTabKey);
  
  // Return cleanup function
  return () => {
    element.removeEventListener('keydown', handleTabKey);
  };
}

/**
 * Set focus to element with optional delay
 */
export function setFocus(element: HTMLElement | null, delay: number = 0) {
  if (!element) return;
  
  if (delay > 0) {
    setTimeout(() => element.focus(), delay);
  } else {
    element.focus();
  }
}

/**
 * Check if element is visible and focusable
 */
export function isFocusable(element: HTMLElement): boolean {
  if (element.tabIndex < 0) return false;
  if (element.hasAttribute('disabled')) return false;
  if (getComputedStyle(element).display === 'none') return false;
  if (getComputedStyle(element).visibility === 'hidden') return false;
  
  return true;
}

/**
 * Get all focusable elements within a container
 */
export function getFocusableElements(container: HTMLElement): HTMLElement[] {
  const selector =
    'button:not([disabled]), [href], input:not([disabled]), select:not([disabled]), textarea:not([disabled]), [tabindex]:not([tabindex="-1"])';
  
  return Array.from(container.querySelectorAll<HTMLElement>(selector)).filter(isFocusable);
}

/**
 * Move focus to next/previous focusable element
 */
export function moveFocus(direction: 'next' | 'previous', container: HTMLElement = document.body) {
  const focusableElements = getFocusableElements(container);
  const currentIndex = focusableElements.indexOf(document.activeElement as HTMLElement);
  
  let nextIndex;
  if (direction === 'next') {
    nextIndex = currentIndex + 1;
    if (nextIndex >= focusableElements.length) nextIndex = 0;
  } else {
    nextIndex = currentIndex - 1;
    if (nextIndex < 0) nextIndex = focusableElements.length - 1;
  }
  
  focusableElements[nextIndex]?.focus();
}

/**
 * Check color contrast ratio (WCAG 2.1 AA requires 4.5:1 for normal text)
 */
export function checkColorContrast(foreground: string, background: string): number {
  const getLuminance = (color: string): number => {
    // Simple approximation - for production use a proper color library
    const rgb = parseInt(color.slice(1), 16);
    const r = ((rgb >> 16) & 0xff) / 255;
    const g = ((rgb >> 8) & 0xff) / 255;
    const b = (rgb & 0xff) / 255;
    
    const [rs, gs, bs] = [r, g, b].map((c) =>
      c <= 0.03928 ? c / 12.92 : Math.pow((c + 0.055) / 1.055, 2.4)
    );
    
    return 0.2126 * rs + 0.7152 * gs + 0.0722 * bs;
  };
  
  const l1 = getLuminance(foreground);
  const l2 = getLuminance(background);
  
  const lighter = Math.max(l1, l2);
  const darker = Math.min(l1, l2);
  
  return (lighter + 0.05) / (darker + 0.05);
}

/**
 * Initialize accessibility features
 */
export function initializeAccessibility() {
  // Create ARIA live region
  createLiveRegion();
  
  // Skip to main content link
  addSkipLink();
  
  // Keyboard shortcuts help
  document.addEventListener('keydown', (e) => {
    // Show keyboard shortcuts on '?'
    if (e.key === '?' && e.shiftKey) {
      showKeyboardShortcutsHelp();
    }
  });
}

/**
 * Add skip to main content link
 */
function addSkipLink() {
  const skipLink = document.createElement('a');
  skipLink.href = '#main-content';
  skipLink.textContent = 'Skip to main content';
  skipLink.className = 'sr-only focus:not-sr-only focus:absolute focus:top-0 focus:left-0 focus:z-50 focus:p-4 focus:bg-primary focus:text-primary-foreground';
  document.body.insertBefore(skipLink, document.body.firstChild);
}

/**
 * Show keyboard shortcuts help modal
 */
function showKeyboardShortcutsHelp() {
  announceToScreenReader('Keyboard shortcuts help opened', 'polite');
  // Implementation depends on UI framework
  console.log('Keyboard shortcuts: Tab = navigate, Enter = submit, Escape = cancel');
}

