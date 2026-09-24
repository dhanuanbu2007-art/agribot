import React from 'react';
import { Menu, Sprout, Wifi, WifiOff } from 'lucide-react';

export default function Header({
  onToggleSidebar,
  backendStatus = 'checking', // 'online' | 'checking' | 'offline'
  language = 'en',
  onLanguageChange,
}) {
  const isOnline = backendStatus === 'online';
  const isChecking = backendStatus === 'checking';

  return (
    <header className="agriguide-header" role="banner">
      <div className="header-left">
        <button
          type="button"
          className="header-menu-btn"
          onClick={onToggleSidebar}
          aria-label="Toggle sidebar navigation"
          title="Toggle sidebar"
        >
          <Menu size={20} />
        </button>

        <div className="header-brand-wrap">
          <div className="header-icon-box" aria-hidden="true">
            <Sprout size={20} strokeWidth={2.4} />
          </div>
          <div className="header-titles">
            <h1 className="header-title">AgriGuide</h1>
            <span className="header-subtitle">
              {language === 'ta'
                ? 'உங்கள் அறிவார்ந்த விவசாய உதவியாளர்'
                : 'Your intelligent agriculture assistant'}
            </span>
          </div>
        </div>
      </div>

      <div className="header-right">
        {/* Language Selector: English | தமிழ் */}
        <div className="lang-pill-selector" role="group" aria-label="Language selection">
          <button
            type="button"
            className={`lang-pill-btn ${language === 'en' ? 'active' : ''}`}
            onClick={() => onLanguageChange && onLanguageChange('en')}
            aria-pressed={language === 'en'}
          >
            English
          </button>
          <button
            type="button"
            className={`lang-pill-btn ${language === 'ta' ? 'active' : ''}`}
            onClick={() => onLanguageChange && onLanguageChange('ta')}
            aria-pressed={language === 'ta'}
          >
            தமிழ்
          </button>
        </div>

        {/* Backend Status Indicator */}
        <div
          className={`status-pill ${backendStatus}`}
          role="status"
          aria-live="polite"
          title={
            isOnline
              ? "FastAPI & RAG backend connected"
              : isChecking
              ? "Connecting to agriculture AI..."
              : "Backend offline - start FastAPI backend"
          }
        >
          {isOnline ? (
            <Wifi size={14} className="status-icon" />
          ) : (
            <WifiOff size={14} className="status-icon" />
          )}
          <span className="status-pulse-dot" />
          <span className="status-label">
            {isOnline
              ? (language === 'ta' ? 'AI ஆன்லைன்' : 'AI Online')
              : isChecking
              ? (language === 'ta' ? 'இணைக்கிறது...' : 'Connecting...')
              : (language === 'ta' ? 'AI ஆஃப்லைன்' : 'AI Offline')}
          </span>
        </div>
      </div>
    </header>
  );
}
