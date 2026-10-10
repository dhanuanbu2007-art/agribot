import React, { useMemo, useState, useEffect, useRef } from 'react';
import { Sprout, User, AlertTriangle, Volume2, VolumeX, X, Loader2 } from 'lucide-react';
import Markdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import SourceCard from './SourceCard';
import { generateTamilTTS } from '../services/api';
import { auth } from '../firebase';

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
  const [isLoadingAudio, setIsLoadingAudio] = useState(false);
  const [voices, setVoices] = useState([]);
  const [ttsError, setTtsError] = useState(null);
  
  const utteranceRef = useRef(null);
  const audioObjRef = useRef(null);

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
      if (audioObjRef.current) {
        audioObjRef.current.pause();
        audioObjRef.current.src = "";
      }
    };
  }, [isSpeaking]);

  const handleToggleSpeech = async () => {
    if (isSpeaking || isLoadingAudio) {
      if (typeof window !== 'undefined' && window.speechSynthesis) {
        window.speechSynthesis.cancel();
      }
      if (audioObjRef.current) {
        audioObjRef.current.pause();
        audioObjRef.current.currentTime = 0;
      }
      setIsSpeaking(false);
      setIsLoadingAudio(false);
      return;
    }

    if (typeof window !== 'undefined' && window.speechSynthesis) {
      window.speechSynthesis.cancel();
    }
    if (audioObjRef.current) {
      audioObjRef.current.pause();
      audioObjRef.current.currentTime = 0;
    }
    
    setTtsError(null);

    const printableText = cleanTextForSpeech(body);
    if (!printableText) return;

    const hasTamil = /[\u0B80-\u0BFF]/.test(printableText);

    if (hasTamil) {
      // Use Cloud TTS for Tamil
      setIsLoadingAudio(true);
      try {
        let token = null;
        if (auth.currentUser) {
          token = await auth.currentUser.getIdToken();
        }
        
        const audioUrl = await generateTamilTTS(printableText, token);
        const audio = new Audio(audioUrl);
        audioObjRef.current = audio;
        
        audio.onplay = () => {
          setIsLoadingAudio(false);
          setIsSpeaking(true);
        };
        
        audio.onended = () => {
          setIsSpeaking(false);
        };
        
        audio.onerror = () => {
          setIsLoadingAudio(false);
          setIsSpeaking(false);
          setTtsError("Failed to play Tamil audio.");
        };
        
        await audio.play();
      } catch (err) {
        console.error("[Cloud TTS Error]", err);
        setIsLoadingAudio(false);
        setIsSpeaking(false);
        setTtsError(err.message || "Failed to generate Tamil speech via cloud.");
      }
      return;
    }

    // Fallback to Browser TTS for English
    const langCode = 'en-IN';
    let currentVoices = voices;
    if (!currentVoices || currentVoices.length === 0) {
      currentVoices = window.speechSynthesis.getVoices() || [];
    }

    const selectedVoice = getBestVoice(currentVoices, langCode);
    const utterance = new SpeechSynthesisUtterance(printableText);
    utterance.lang = langCode;

    if (selectedVoice) {
      utterance.voice = selectedVoice;
    }

    utterance.onstart = () => setIsSpeaking(true);
    utterance.onend = () => {
      setIsSpeaking(false);
      utteranceRef.current = null;
    };
    utterance.onerror = (event) => {
      setIsSpeaking(false);
      utteranceRef.current = null;
      if (event.error === 'language-unavailable' || event.error === 'voice-unavailable') {
        setTtsError('English speech voice is unavailable in your browser.');
      } else if (event.error !== 'interrupted' && event.error !== 'canceled') {
        setTtsError('Failed to play audio answer. Please try again.');
      }
    };

    utteranceRef.current = utterance;
    setIsSpeaking(true);

    try {
      window.speechSynthesis.speak(utterance);
    } catch (err) {
      setIsSpeaking(false);
      setTtsError('Failed to start speech playback.');
    }
  };

  const isTtsSupported = true; // Since we now use Cloud API + Browser API

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
