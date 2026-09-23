import React from 'react';
import { Sprout, Sparkles, ArrowRight } from 'lucide-react';

const SUGGESTIONS = {
  en: [
    {
      icon: '🌱',
      tag: 'Crops',
      title: 'Crop Cultivation',
      question: 'How can I improve crop cultivation and yield for paddy?',
    },
    {
      icon: '🦠',
      tag: 'Protection',
      title: 'Disease & Pest Control',
      question: 'How can farmers detect and manage common crop diseases and pests?',
    },
    {
      icon: '🧪',
      tag: 'Nutrition',
      title: 'Fertilizer & Soil Health',
      question: 'What is the recommended fertilizer schedule and nutrient dosage?',
    },
    {
      icon: '📋',
      tag: 'Schemes',
      title: 'Government Schemes',
      question: 'What financial subsidies and agricultural government schemes are available?',
    },
  ],
  ta: [
    {
      icon: '🌱',
      tag: 'சாகுபடி',
      title: 'பயிர் சாகுபடி',
      question: 'நெல் பயிர் சாகுபடி முறைகளை எவ்வாறு மேம்படுத்துவது?',
    },
    {
      icon: '🦠',
      tag: 'பாதுகாப்பு',
      title: 'நோய் மற்றும் பூச்சி மேலாண்மை',
      question: 'பயிர் நோய்கள் மற்றும் பூச்சிகளை எவ்வாறு கட்டுப்படுத்துவது?',
    },
    {
      icon: '🧪',
      tag: 'உரங்கள்',
      title: 'உர மேலாண்மை',
      question: 'பயிர்களுக்கு தழை, சாம்பல் சத்து உரங்கள் எவ்வாறு இட வேண்டும்?',
    },
    {
      icon: '📋',
      tag: 'திட்டங்கள்',
      title: 'அரசு திட்டங்கள்',
      question: 'விவசாயிகளுக்கு என்னென்ன அரசு திட்டங்களும் மானியங்களும் உள்ளன?',
    },
  ],
};

export default function WelcomeScreen({ onSelectSuggestion, language = 'en' }) {
  const isTamil = language === 'ta';
  const currentSuggestions = isTamil ? SUGGESTIONS.ta : SUGGESTIONS.en;

  return (
    <section className="welcome-container" aria-label="Welcome and Suggestions">
      {/* Background Decorative Agricultural Elements */}
      <div className="welcome-decor-container" aria-hidden="true">
        <svg className="welcome-decor-svg decor-left" viewBox="0 0 100 100" fill="none">
          <path d="M10 90C30 70 45 40 40 10C55 35 65 60 90 85" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" opacity="0.3" />
          <path d="M25 80C40 60 60 45 75 35" stroke="currentColor" strokeWidth="2" strokeLinecap="round" opacity="0.2" />
        </svg>
        <svg className="welcome-decor-svg decor-right" viewBox="0 0 100 100" fill="none">
          <path d="M90 90C70 70 55 40 60 10C45 35 35 60 10 85" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" opacity="0.3" />
          <path d="M75 80C60 60 40 45 25 35" stroke="currentColor" strokeWidth="2" strokeLinecap="round" opacity="0.2" />
        </svg>
      </div>

      {/* Central Sprout Hero Icon */}
      <div className="welcome-hero-icon-container">
        <div className="welcome-hero-sprout-halo">
          <Sprout size={38} className="welcome-hero-sprout" strokeWidth={2.3} />
        </div>
      </div>

      <div className="welcome-hero-badge">
        <Sparkles size={14} className="welcome-badge-sparkle" />
        <span>
          {isTamil
            ? 'RAG அடிப்படையில் இயங்கும் விவசாய AI வழிகாட்டி'
            : 'RAG-Powered Agriculture AI Advisory'}
        </span>
      </div>

      <h2 className="welcome-title">
        {isTamil
          ? 'AgriGuide-க்கு நல்வரவு'
          : 'Welcome to AgriGuide'}
      </h2>
      <p className="welcome-subtitle">
        {isTamil
          ? 'பயிர் சாகுபடி, நோய்கள், பூச்சி கட்டுப்பாடு, உர மேலாண்மை மற்றும் அரசு திட்டங்கள் குறித்த உங்கள் விவசாய கேள்விகளை கேளுங்கள்.'
          : 'Your intelligent agriculture assistant for practical farming guidance, crop health, fertilizer advisory, and agricultural schemes.'}
      </p>

      {/* Suggestion Cards */}
      <div className="suggestions-grid" role="region" aria-label="Suggested topics">
        {currentSuggestions.map((item, index) => (
          <button
            key={index}
            type="button"
            className="suggestion-card"
            onClick={() => onSelectSuggestion(item.question)}
            aria-label={`Ask: ${item.question}`}
          >
            <div className="suggestion-header">
              <div className="suggestion-icon-tag-wrap">
                <span className="suggestion-icon" role="img" aria-hidden="true">
                  {item.icon}
                </span>
                <span className="suggestion-category-tag">{item.tag}</span>
              </div>
              <div className="suggestion-arrow-wrap">
                <ArrowRight size={14} className="suggestion-arrow" />
              </div>
            </div>
            <div className="suggestion-title">{item.title}</div>
            <p className="suggestion-prompt">{item.question}</p>
          </button>
        ))}
      </div>

      <div className="welcome-footer-prompt">
        <span>
          {isTamil
            ? 'கீழே உள்ள உள்ளீட்டுப் பெட்டியில் உங்கள் கேள்வியைத் தட்டச்சு செய்யவும் அல்லது குரல் மூலம் கேட்கவும்'
            : 'Type your agriculture question below, or use voice input to speak'}
        </span>
      </div>
    </section>
  );
}
