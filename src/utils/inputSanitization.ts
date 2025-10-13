/**
 * Input Sanitization Utilities
 * 
 * Provides DOMPurify-based sanitization for user inputs
 * to prevent XSS and injection attacks.
 */
import DOMPurify from 'dompurify';

/**
 * Sanitize string input to prevent XSS attacks
 */
export function sanitizeInput(input: string): string {
  if (!input) return '';
  
  // Configure DOMPurify for strict sanitization
  const clean = DOMPurify.sanitize(input, {
    ALLOWED_TAGS: [], // No HTML tags allowed
    ALLOWED_ATTR: [],
    KEEP_CONTENT: true, // Keep text content
  });
  
  return clean.trim();
}

/**
 * Sanitize email input
 */
export function sanitizeEmail(email: string): string {
  const sanitized = sanitizeInput(email);
  return sanitized.toLowerCase();
}

/**
 * Sanitize username (alphanumeric + _ -)
 */
export function sanitizeUsername(username: string): string {
  const sanitized = sanitizeInput(username);
  // Remove any non-alphanumeric except _ and -
  return sanitized.replace(/[^a-zA-Z0-9_-]/g, '');
}

/**
 * Sanitize object (recursive sanitization)
 */
export function sanitizeObject<T extends Record<string, any>>(obj: T): T {
  const sanitized = {} as T;
  
  for (const key in obj) {
    const value = obj[key];
    
    if (typeof value === 'string') {
      sanitized[key] = sanitizeInput(value) as any;
    } else if (typeof value === 'object' && value !== null && !Array.isArray(value)) {
      sanitized[key] = sanitizeObject(value);
    } else {
      sanitized[key] = value;
    }
  }
  
  return sanitized;
}

