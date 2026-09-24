import React from 'react';
import {
  Sprout,
  ArrowRight,
  Sparkles,
} from 'lucide-react';

const SUGGESTIONS = {
  en: [
    {
      id: 'paddy-fertilizer',
      icon: '🌾',
      title: 'Paddy fertilizer',
      desc: 'NPK ratio, basal dose & top dressing schedules',
      question: 'What is the recommended fertilizer schedule and NPK dosage for paddy?',
      color: '#166534',
    },
    {
      id: 'crop-disease',
      icon: '🐛',
      title: 'Crop disease identification',
      desc: 'Leaf blast, blight symptoms & bio-fungicides',
      question: 'How can I identify and manage common crop diseases like leaf blast and blight?',
      color: '#b45309',
    },
    {
      id: 'pest-management',
      icon: '🦋',
      title: 'Pest management',
      desc: 'Integrated pest management (IPM) & organic traps',
      question: 'What are effective organic and bio-control methods for crop pest management?',
      color: '#047857',
    },
    {
      id: 'crop-cultivation',
      icon: '🌱',
      title: 'Crop cultivation guidance',
      desc: 'Soil prep, seed treatment & spacing techniques',
      question: 'What are best cultivation practices to maximize crop yield and soil health?',
      color: '#15803d',
    },
    {
      id: 'irrigation-guidance',
      icon: '💧',
      title: 'Irrigation guidance',
      desc: 'Drip systems, critical watering stages & conservation',
      question: 'What is the optimal irrigation schedule and water conservation method for crops?',
      color: '#0369a1',
    },
    {
      id: 'gov-schemes',
      icon: '🏛️',
      title: 'Government schemes',
      desc: 'PM-Kisan, crop insurance & subsidy programs',
      question: 'What agricultural government schemes, subsidies, and grants are available for farmers?',
      color: '#7c3aed',
    },
  ],
  ta: [
    {
      id: 'paddy-fertilizer',
      icon: '🌾',
      title: 'நெல் பயிர் உரம்',
      desc: 'NPK விகிதம், அடி உரம் மற்றும் மேலுர அட்டவணை',
      question: 'நெல் பயிருக்கு பரிந்துரைக்கப்பட்ட உரம் மற்றும் NPK அளவு என்ன?',
      color: '#166534',
    },
    {
      id: 'crop-disease',
      icon: '🐛',
      title: 'பயிர் நோய் கண்டறிதல்',
      desc: 'இலை கருகல் அறிகுறிகள் மற்றும் தடுப்பு முறைகள்',
      question: 'இலை கருகல் போன்ற பயிர் நோய்களை எவ்வாறு கண்டறிந்து நிர்வகிப்பது?',
      color: '#b45309',
    },
    {
      id: 'pest-management',
      icon: '🦋',
      title: 'பூச்சி மேலாண்மை',
      desc: 'ஒருங்கிணைந்த பூச்சி கட்டுப்பாடு மற்றும் இயற்கை மருந்துகள்',
      question: 'பயிர் பூச்சி மேலாண்மைக்கான இயற்கை மற்றும் உயிரியல் முறைகள் என்ன?',
      color: '#047857',
    },
    {
      id: 'crop-cultivation',
      icon: '🌱',
      title: 'பயிர் சாகுபடி வழிகாட்டுதல்',
      desc: 'விதை நேர்த்தி, நிலம் தயாரிப்பு மற்றும் நடவு முறைகள்',
      question: 'பயிர் விளைச்சலையும் மண் வளத்தையும் அதிகரிக்க சிறந்த சாகுபடி முறைகள் யாவை?',
      color: '#15803d',
    },
    {
      id: 'irrigation-guidance',
      icon: '💧',
      title: 'நீர்ப்பாசன வழிகாட்டுதல்',
      desc: 'சொட்டு நீர் பாசனம் மற்றும் நீர் மேலாண்மை முறைகள்',
      question: 'பயிர்களுக்கான உகந்த நீர்ப்பாசன அட்டவணை மற்றும் நீர் சேமிப்பு முறைகள் என்ன?',
      color: '#0369a1',
    },
    {
      id: 'gov-schemes',
      icon: '🏛️',
      title: 'அரசு திட்டங்கள்',
      desc: 'விவசாய மானியங்கள், பயிர் காப்பீடு மற்றும் உதவிகள்',
      question: 'விவசாயிகளுக்கு என்னென்ன அரசு திட்டங்கள், மானியங்கள் மற்றும் உதவிகள் உள்ளன?',
      color: '#7c3aed',
    },
  ],
};

export default function WelcomeScreen({ onSelectSuggestion, language = 'en' }) {
  const isTamil = language === 'ta';
  const suggestions = isTamil ? SUGGESTIONS.ta : SUGGESTIONS.en;

  return (
    <div className="agriguide-welcome-area" aria-label="Welcome and Agriculture Guidance">
      {/* ── Top Hero Banner with Realistic Agriculture Imagery ──────── */}
      <div className="welcome-banner-card">
        <div className="welcome-banner-img-wrap">
          <img
            src="/agri-hero-field.jpg"
            alt="Terraced agricultural paddy fields at sunrise"
            className="welcome-banner-img"
          />
          <div className="welcome-banner-overlay" />
        </div>

        <div className="welcome-banner-content">
          <div className="welcome-tag-pill">
            <Sparkles size={13} className="sparkle-icon" />
            <span>
              {isTamil
                ? 'RAG AI தொழில்நுட்பத்தில் இயங்கும் விவசாய வழிகாட்டி'
                : 'Intelligent RAG Agriculture Advisory'}
            </span>
          </div>

          <div className="welcome-main-heading">
            <span className="welcome-seed-emoji" role="img" aria-label="Sprout">
              🌱
            </span>
            <h2>
              {isTamil ? 'வணக்கம்! AgriGuide-க்கு வரவேற்கிறோம்' : 'Welcome to AgriGuide'}
            </h2>
          </div>

          <p className="welcome-lead-text">
            {isTamil
              ? 'பயிர் வழிகாட்டல், நோய் மேலாண்மை, உரங்கள், பூச்சி மேலாண்மை மற்றும் அரசு திட்டங்களுக்கான உங்கள் அறிவார்ந்த விவசாய உதவியாளர்.'
              : 'Your intelligent agriculture assistant for crop guidance, disease management, fertilizers, pest management and government schemes.'}
          </p>
        </div>
      </div>

      {/* ── 6 Agriculture Suggestion Cards ──────────────────────────── */}
      <div className="welcome-cards-section">
        <div className="welcome-cards-title">
          <Sprout size={16} className="title-sprout-icon" />
          <span>
            {isTamil ? 'அடிக்கடி கேட்கப்படும் விவசாய தலைப்புகள்' : 'Recommended Agriculture Topics'}
          </span>
        </div>

        <div className="welcome-cards-grid" role="region" aria-label="Quick suggestion cards">
          {suggestions.map((card) => (
            <button
              key={card.id}
              type="button"
              className="agri-suggestion-card"
              onClick={() => onSelectSuggestion && onSelectSuggestion(card.question)}
              aria-label={`Ask AgriGuide: ${card.question}`}
            >
              <div className="card-top-row">
                <span className="card-emoji" role="img" aria-hidden="true">
                  {card.icon}
                </span>
                <div className="card-action-icon" aria-hidden="true">
                  <ArrowRight size={14} />
                </div>
              </div>

              <div className="card-text-block">
                <strong className="card-title">{card.title}</strong>
                <p className="card-desc">{card.desc}</p>
              </div>

              <div className="card-bottom-prompt">
                <span>"{card.question}"</span>
              </div>
            </button>
          ))}
        </div>
      </div>
    </div>
  );
}
