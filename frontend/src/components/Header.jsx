import React from 'react';
import { Menu, Sprout } from 'lucide-react';

export default function Header({
  onToggleSidebar,
  isOnline,
  isCheckingHealth,
  language = 'en',
  onLanguageChange,
}) {
  return (
    <header className="header" role="banner">
      <div className="header-left">
        <button
          type="button"
          className="header-menu-btn"
          onClick={onToggleSidebar}
          aria-label="Toggle Navigation Sidebar"
        >
          <Menu size={20} />
        </button>

        <div className="header-brand-container">
          <div className="header-logo-badge" aria-hidden="true">
            <Sprout size={18} strokeWidth={2.4} />
          </div>
          <div className="header-title-box">
            <h1 className="header-title">AgriGuide</h1>
            <span className="header-subtitle">
              {language === 'ta'
                ? 'விவசாய அறிவு மற்றும் ஆலோசனை உதவியாளர்'
                : 'Agriculture Knowledge & Advisory Assistant'}
            </span>
          </div>
        </div>
      </div>

      <div className="header-right">
        {/* Language Selector: English | தமிழ் */}
        <div className="lang-toggle-container" role="group" aria-label="Select Language">
          <button
            type="button"
            className={`lang-toggle-btn ${language === 'en' ? 'active' : ''}`}
            onClick={() => onLanguageChange && onLanguageChange('en')}
            aria-pressed={language === 'en'}
            title="English"
          >
            English
          </button>
          <span className="lang-divider" aria-hidden="true">|</span>
          <button
            type="button"
            className={`lang-toggle-btn ${language === 'ta' ? 'active' : ''}`}
            onClick={() => onLanguageChange && onLanguageChange('ta')}
            aria-pressed={language === 'ta'}
            title="தமிழ் (Tamil)"
          >
            தமிழ்
          </button>
        </div>

        <div
          className={`status-badge ${isOnline ? 'online' : 'offline'}`}
          role="status"
          aria-live="polite"
        >
          <span
            className={`status-dot ${isOnline ? 'pulsing' : 'offline'}`}
            aria-hidden="true"
          />
          <span>
            {isCheckingHealth
              ? (language === 'ta' ? 'நிலை சரிபார்க்கப்படுகிறது...' : 'Checking status...')
              : isOnline
              ? (language === 'ta' ? 'AI உதவியாளர் ஆன்லைனில் உள்ளது' : 'AI Assistant Online')
              : (language === 'ta' ? 'சர்வர் ஆஃப்லைனில் உள்ளது' : 'Backend Offline')}
          </span>
        </div>
      </div>
    </header>
  );
}
