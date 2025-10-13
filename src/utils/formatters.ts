/**
 * Localized Formatting Utilities
 * 
 * Provides:
 * - Number formatting
 * - Date formatting
 * - Currency formatting
 * - Timezone handling
 */

/**
 * Format number with locale-specific formatting
 */
export const formatNumber = (
  value: number,
  locale: string = 'en-US',
  options?: Intl.NumberFormatOptions
): string => {
  return new Intl.NumberFormat(locale, options).format(value);
};

/**
 * Format currency with locale and currency code
 */
export const formatCurrency = (
  amount: number,
  currency: string = 'USD',
  locale: string = 'en-US'
): string => {
  return new Intl.NumberFormat(locale, {
    style: 'currency',
    currency: currency
  }).format(amount);
};

/**
 * Format date with locale-specific formatting
 */
export const formatDate = (
  date: Date | string,
  locale: string = 'en-US',
  options?: Intl.DateTimeFormatOptions
): string => {
  const dateObj = typeof date === 'string' ? new Date(date) : date;
  
  return new Intl.DateTimeFormat(locale, {
    year: 'numeric',
    month: 'long',
    day: 'numeric',
    ...options
  }).format(dateObj);
};

/**
 * Format time with timezone
 */
export const formatTime = (
  date: Date | string,
  locale: string = 'en-US',
  timeZone?: string
): string => {
  const dateObj = typeof date === 'string' ? new Date(date) : date;
  
  return new Intl.DateTimeFormat(locale, {
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
    timeZone: timeZone,
    timeZoneName: 'short'
  }).format(dateObj);
};

/**
 * Convert UTC to user's local timezone
 */
export const convertToLocalTimezone = (utcDate: string): Date => {
  return new Date(utcDate);
};

/**
 * Get user's timezone
 */
export const getUserTimezone = (): string => {
  return Intl.DateTimeFormat().resolvedOptions().timeZone;
};

/**
 * Format percentage with locale
 */
export const formatPercentage = (
  value: number,
  locale: string = 'en-US',
  decimals: number = 1
): string => {
  return new Intl.NumberFormat(locale, {
    style: 'percent',
    minimumFractionDigits: decimals,
    maximumFractionDigits: decimals
  }).format(value / 100);
};

