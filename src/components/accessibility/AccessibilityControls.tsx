/**
 * Accessibility Controls Component
 * 
 * Provides users with:
 * - High contrast mode toggle
 * - Language selector
 * - Font size adjustment
 * - Skip navigation links
 */
import React from 'react';
import { useTranslation } from 'react-i18next';
import { toggleHighContrastMode, isHighContrastEnabled, setDocumentDirection } from '../../utils/accessibility';

export const AccessibilityControls: React.FC = () => {
  const { t, i18n } = useTranslation();
  const [highContrast, setHighContrast] = React.useState(isHighContrastEnabled());

  const handleHighContrastToggle = () => {
    const newValue = !highContrast;
    toggleHighContrastMode(newValue);
    setHighContrast(newValue);
  };

  const handleLanguageChange = (language: string) => {
    i18n.changeLanguage(language);
    setDocumentDirection(language);
  };

  return (
    <div className="accessibility-controls" role="region" aria-label="Accessibility settings">
      {/* Skip to main content link */}
      <a href="#main-content" className="skip-link">
        {t('accessibility.skipToMain')}
      </a>
      
      {/* High contrast toggle */}
      <button
        onClick={handleHighContrastToggle}
        aria-label={t('accessibility.toggleHighContrast')}
        aria-pressed={highContrast}
        className="accessibility-button"
      >
        {highContrast ? '🌙' : '☀️'} High Contrast
      </button>
      
      {/* Language selector */}
      <div className="language-selector">
        <label htmlFor="language-select">
          {t('accessibility.languageSelector')}
        </label>
        <select
          id="language-select"
          value={i18n.language}
          onChange={(e) => handleLanguageChange(e.target.value)}
          aria-label="Select language"
        >
          <option value="en">English</option>
          <option value="es">Español</option>
        </select>
      </div>
    </div>
  );
};

