/**
 * Bootstrap entry point for Module Federation
 * This file dynamically imports the main application
 */
import('./main').catch((err) => {
  console.error('Failed to load application:', err);
});

export {};

