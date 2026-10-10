import React, { useMemo, useState, useEffect, useRef } from 'react';
import { Sprout, User, AlertTriangle, Volume2, VolumeX, X } from 'lucide-react';
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
 * Preserves Tamil Unicode characters (\u0B80 - \u0BFF) and general punctuation
 */
function cleanTextForSpeech(text) {
  if (!text) return '';
  let clean = text;
  // Remove markdown source notes
  clean = clean.replace(/\*?\(?\s*(?:Sources?|References?|Source Note):?[\s\S]*?\)?\*?/gi, '');
  // Remove markdown links [text](url) -> text
  clean = clean.replace(/\[([^\]]+)\]\([^)]+\)/g, '$1');
  // Remove markdown formatting symbols like *, _, #, `, >, ~
  clean = clean.replace(/[\*\_#`>~]/g, '');
  // Remove list bullets / numbering at start of lines
  clean = clean.replace(/^(?:\s*[-+*]|\s*\d+\.)\s+/gm, '');
  return clean.trim();
}

/**
 * Find suitable voice from browser SpeechSynthesis
 */
function getBestVoice(voices, langCode) {
  if (!voices || voices.length === 0) return null;

  const targetLang = langCode.toLowerCase().replace('_', '-'); // e.g. "ta-in"
  const targetPrefix = targetLang.split('-')[0]; // e.g. "ta"

  // 1. Exact language match (e.g. ta-IN or ta_IN)
  let voice = voices.find((v) => v.lang && v.lang.toLowerCase().replace('_', '-') === targetLang);
  if (voice) return voice;

  // 2. Prefix language match (e.g. ta)
  voice = voices.find((v) => v.lang && v.lang.toLowerCase().startsWith(targetPrefix));
  if (voice) return voice;

  // 3. Name match (voice name contains "tamil" or "ta-in")
  voice = voices.find(
    (v) =>
      v.name &&
      (v.name.toLowerCase().includes('tamil') || v.name.toLowerCase().includes('ta-in'))
  );
  if (voice) return voice;

  return null;
}

export default function ChatMessage({ message, language = 'en' }) {
  const isUser = message.role === 'user';
  const rawText = message.content || message.text || '';
  const isError = Boolean(message.isError);

  const [isSpeaking, setIsSpeaking] = useState(false);
  const [voices, setVoices] = useState([]);
  const [ttsError, setTtsError] = useState(null);
  const utteranceRef = useRef(null);

  const { body, sources } = useMemo(() => {
    if (isUser) return { body: rawText, sources: null };
    return parseMessageContent(rawText);
  }, [isUser, rawText]);

  const time = formatTimestamp(message.timestamp);

  // Load browser voices asynchronously (handles onvoiceschanged event)
  useEffect(() => {
    if (typeof window === 'undefined' || !window.speechSynthesis) return;

    const updateVoices = () => {
      const avail = window.speechSynthesis.getVoices();
      if (avail && avail.length > 0) {
        setVoices(avail);
      }
    };

    updateVoices();

    if (window.speechSynthesis.onvoiceschanged !== undefined) {
      window.speechSynthesis.onvoiceschanged = updateVoices;
    }
  }, []);

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
    console.log('[TTS Debug] Speaker button clicked for message:', { isUser, isError, bodySnippet: body?.slice(0, 40) });

    if (typeof window === 'undefined' || !window.speechSynthesis) {
      console.warn('[TTS Debug] SpeechSynthesis is not supported by window');
      setTtsError('Text-to-speech is not supported in this browser.');
      return;
    }

    if (isSpeaking) {
      console.log('[TTS Debug] Stopping current speech');
      window.speechSynthesis.cancel();
      setIsSpeaking(false);
      return;
    }

    // Always cancel any existing speech across the browser before starting new utterance
    window.speechSynthesis.cancel();
    setTtsError(null);

    const printableText = cleanTextForSpeech(body);
    console.log('[TTS Debug] Raw body length:', body?.length, '| Clean text length:', printableText?.length);
    console.log('[TTS Debug] Clean text snippet:', printableText?.slice(0, 80));

    if (!printableText) {
      console.warn('[TTS Debug] Text is empty after markdown cleaning');
      return;
    }

    // Detect Tamil text vs English text
    const hasTamil = /[\u0B80-\u0BFF]/.test(printableText);
    const langCode = hasTamil ? 'ta-IN' : (language === 'ta' ? 'ta-IN' : 'en-IN');

    console.log('[TTS Debug] Language detection:', { hasTamil, langCode });

    // Fetch latest available voices
    let currentVoices = voices;
    if (!currentVoices || currentVoices.length === 0) {
      currentVoices = window.speechSynthesis.getVoices() || [];
    }

    console.log('[TTS Debug] Total available browser voices:', currentVoices.length);

    const selectedVoice = getBestVoice(currentVoices, langCode);
    console.log('[TTS Debug] Selected voice:', selectedVoice ? `${selectedVoice.name} (${selectedVoice.lang})` : 'NONE (Using browser default)');

    const utterance = new SpeechSynthesisUtterance(printableText);
    utterance.lang = langCode;

    if (selectedVoice) {
      utterance.voice = selectedVoice;
    } else if (hasTamil) {
      // Warn the user that no specific Tamil voice was found, but still attempt speech
      setTtsError('No Tamil voice found. Attempting to use default browser voice, which may not sound correct.');
    }

    utterance.onstart = () => {
      console.log('[TTS Debug] Utterance onstart event fired');
      setIsSpeaking(true);
    };

    utterance.onend = () => {
      console.log('[TTS Debug] Utterance onend event fired');
      setIsSpeaking(false);
      utteranceRef.current = null;
    };

    utterance.onerror = (event) => {
      console.error('[TTS Debug] Utterance onerror event fired:', event.error || event);
      setIsSpeaking(false);
      utteranceRef.current = null;

      if (event.error === 'language-unavailable' || event.error === 'voice-unavailable') {
        setTtsError(
          hasTamil
            ? 'Tamil speech is unavailable in your browser/OS. Please install Tamil speech data or try Google Chrome.'
            : 'English speech voice is unavailable in your browser.'
        );
      } else if (event.error !== 'interrupted' && event.error !== 'canceled') {
        setTtsError('Failed to play audio answer. Please try again.');
      }
    };

    utteranceRef.current = utterance;
    setIsSpeaking(true);

    try {
      console.log('[TTS Debug] Executing window.speechSynthesis.speak() with lang =', utterance.lang);
      window.speechSynthesis.speak(utterance);
    } catch (err) {
      console.error('[TTS Debug] Exception when calling speak():', err);
      setIsSpeaking(false);
      setTtsError('Failed to start speech playback.');
    }
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

        {/* TTS Error Toast */}
        {ttsError && (
          <div className="msg-tts-error-toast" role="alert">
            <span>{ttsError}</span>
            <button
              type="button"
              className="msg-tts-error-close"
              onClick={() => setTtsError(null)}
              aria-label="Dismiss TTS error"
            >
              <X size={12} />
            </button>
          </div>
        )}

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
