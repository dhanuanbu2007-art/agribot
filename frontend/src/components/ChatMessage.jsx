import React, { useMemo, useState, useEffect, useRef } from 'react';
import { Sprout, User, AlertTriangle, Volume2, VolumeX } from 'lucide-react';
import Markdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import SourceCard from './SourceCard';

/**
 * Parses assistant response text to extract any trailing source section.
 * e.g., "*(Source: Fertilizer & Nutrient Management, pages 1, 2, 4, 8)*"
 */
function parseMessageContent(text) {
  if (!text) return { body: '', sources: null };

  const sourceRegex = /(?:(?:\r?\n)+)(?:[\*\_\(\[\{]{0,3}\s*(?:Sources?|References?|Source Note):?\s*)([\s\S]*)$/i;
  const match = text.match(sourceRegex);

  if (match && match.index !== undefined) {
    const body = text.substring(0, match.index).trim();
    let rawSources = match[1].trim();
    rawSources = rawSources.replace(/[\)\*\_\]\}\s]+$/, '').trim();
    if (body.length > 0 && rawSources.length > 0) {
      return { body, sources: rawSources };
    }
  }

  return { body: text, sources: null };
}

function formatTimestamp(timeValue) {
  if (!timeValue) return '';
  try {
    const date = new Date(timeValue);
    if (isNaN(date.getTime())) return '';
    return date.toLocaleTimeString([], {
      hour: '2-digit',
      minute: '2-digit',
    });
  } catch {
    return '';
  }
}

/**
 * Strips markdown markup to prepare clean text for text-to-speech
 */
function cleanTextForSpeech(text) {
  if (!text) return '';
  let clean = text;
  // Remove markdown source notes
  clean = clean.replace(/\*?\(?\s*(?:Sources?|References?|Source Note):?[\s\S]*?\)?\*?/gi, '');
  // Remove markdown links [text](url) -> text
  clean = clean.replace(/\[([^\]]+)\]\([^)]+\)/g, '$1');
  // Remove markdown headers, bold, italics, code blocks
  clean = clean.replace(/[\*\_#`>~]/g, '');
  clean = clean.replace(/^(?:\s*[-+*]|\s*\d+\.)\s+/gm, '');
  return clean.trim();
}

/**
 * Find suitable voice from browser SpeechSynthesis
 */
function getBestVoice(langCode) {
  if (typeof window === 'undefined' || !window.speechSynthesis) return null;
  const voices = window.speechSynthesis.getVoices();
  if (!voices || voices.length === 0) return null;

  const targetLang = langCode.toLowerCase().replace('_', '-');
  const targetPrefix = targetLang.split('-')[0];

  // Exact match (e.g. ta-IN or en-IN)
  let voice = voices.find((v) => v.lang && v.lang.toLowerCase().replace('_', '-') === targetLang);
  if (voice) return voice;

  // Prefix match (e.g. ta or en)
  voice = voices.find((v) => v.lang && v.lang.toLowerCase().startsWith(targetPrefix));
  if (voice) return voice;

  return null;
}

export default function ChatMessage({ message, language = 'en' }) {
  const isUser = message.role === 'user';
  const rawText = message.content || message.text || '';
  const isError = Boolean(message.isError);

  const [isSpeaking, setIsSpeaking] = useState(false);
  const utteranceRef = useRef(null);

  const { body, sources } = useMemo(() => {
    if (isUser) return { body: rawText, sources: null };
    return parseMessageContent(rawText);
  }, [isUser, rawText]);

  const time = formatTimestamp(message.timestamp);

  // Stop speech on unmount
  useEffect(() => {
    return () => {
      if (typeof window !== 'undefined' && window.speechSynthesis) {
        if (isSpeaking) {
          window.speechSynthesis.cancel();
        }
      }
    };
  }, [isSpeaking]);

  const handleToggleSpeech = () => {
    if (typeof window === 'undefined' || !window.speechSynthesis) return;

    if (isSpeaking) {
      window.speechSynthesis.cancel();
      setIsSpeaking(false);
      return;
    }

    // Cancel any current speech in progress across the app
    window.speechSynthesis.cancel();

    const printableText = cleanTextForSpeech(body);
    if (!printableText) return;

    // Detect Tamil text vs English text
    const hasTamil = /[\u0B80-\u0BFF]/.test(printableText);
    const langCode = hasTamil ? 'ta-IN' : (language === 'ta' ? 'ta-IN' : 'en-IN');

    const utterance = new SpeechSynthesisUtterance(printableText);
    utterance.lang = langCode;

    const voice = getBestVoice(langCode);
    if (voice) {
      utterance.voice = voice;
    }

    utterance.onend = () => {
      setIsSpeaking(false);
      utteranceRef.current = null;
    };

    utterance.onerror = (err) => {
      console.warn('[TTS] Speech error:', err);
      setIsSpeaking(false);
      utteranceRef.current = null;
    };

    utteranceRef.current = utterance;
    setIsSpeaking(true);
    window.speechSynthesis.speak(utterance);
  };

  const isTtsSupported = typeof window !== 'undefined' && 'speechSynthesis' in window;

  return (
    <div className={`agriguide-msg-row ${isUser ? 'user-msg' : 'assistant-msg'} ${isError ? 'error-msg' : ''}`}>
      {/* Avatar */}
      <div className={`msg-avatar-box ${isUser ? 'user-avatar' : 'assistant-avatar'}`} aria-hidden="true">
        {isUser ? (
          <User size={16} />
        ) : isError ? (
          <AlertTriangle size={16} className="error-icon" />
        ) : (
          <Sprout size={16} strokeWidth={2.4} />
        )}
      </div>

      {/* Message Bubble Container */}
      <div className="msg-content-wrapper">
        <div className="msg-header-info">
          <span className="msg-sender-name">
            {isUser ? 'You' : 'AgriGuide'}
          </span>
          {!isUser && !isError && (
            <span className="msg-role-tag">Agriculture Advisory</span>
          )}
          {time && <span className="msg-timestamp">{time}</span>}

          {/* Text-to-Speech Speaker Button */}
          {!isUser && !isError && isTtsSupported && body && (
            <button
              type="button"
              className={`msg-speaker-btn ${isSpeaking ? 'speaking' : ''}`}
              onClick={handleToggleSpeech}
              title={isSpeaking ? (language === 'ta' ? 'வாசிப்பதை நிறுத்து' : 'Stop speaking') : (language === 'ta' ? 'பதிலை உரக்க வாசி' : 'Read answer aloud')}
              aria-label={isSpeaking ? 'Stop speaking' : 'Read answer aloud'}
            >
              {isSpeaking ? <VolumeX size={15} /> : <Volume2 size={15} />}
            </button>
          )}
        </div>

        <div className={`msg-bubble-box ${isUser ? 'bubble-user' : 'bubble-assistant'}`}>
          {isUser ? (
            <p className="user-text-content">{body}</p>
          ) : isError ? (
            <div className="error-text-content">
              <p>{body || 'Failed to connect with AgriGuide AI. Please try again.'}</p>
            </div>
          ) : (
            <>
              <div className="markdown-render-area">
                <Markdown remarkPlugins={[remarkGfm]}>{body}</Markdown>
              </div>
              {sources && <SourceCard sourceContent={sources} />}
            </>
          )}
        </div>
      </div>
    </div>
  );
}
