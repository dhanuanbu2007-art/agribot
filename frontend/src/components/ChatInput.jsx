import React, { useState, useRef, useEffect } from 'react';
import { SendHorizonal, Mic, MicOff, AlertCircle, X } from 'lucide-react';

/**
 * Detect browser SpeechRecognition support (standard or webkit prefix)
 */
function getSpeechRecognitionClass() {
  if (typeof window === 'undefined') return null;
  return window.SpeechRecognition || window.webkitSpeechRecognition || null;
}

export default function ChatInput({ onSendMessage, disabled, language = 'en' }) {
  const [input, setInput] = useState('');
  const [voiceState, setVoiceState] = useState('IDLE'); // 'IDLE' | 'LISTENING' | 'ERROR' | 'UNSUPPORTED'
  const [voiceError, setVoiceError] = useState(null);

  const textareaRef = useRef(null);
  const recognitionRef = useRef(null);
  const baseTextRef = useRef('');

  // Farmer-friendly placeholder governed by language selector
  const placeholder = language === 'ta'
    ? 'உங்கள் விவசாய கேள்வியை கேளுங்கள்...'
    : 'Ask your agriculture question...';

  // Auto-resize textarea height to accommodate multiline text up to maximum height
  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
      const scrollHeight = textareaRef.current.scrollHeight;
      textareaRef.current.style.height = `${Math.min(scrollHeight, 160)}px`;
    }
  }, [input]);

  // Cleanup speech recognition on unmount
  useEffect(() => {
    return () => {
      if (recognitionRef.current) {
        try {
          recognitionRef.current.abort();
        } catch (_) {}
      }
    };
  }, []);

  // Auto-dismiss voice error toast after 7 seconds
  useEffect(() => {
    if (voiceError) {
      const timer = setTimeout(() => {
        setVoiceError(null);
        if (voiceState === 'ERROR' || voiceState === 'UNSUPPORTED') {
          setVoiceState('IDLE');
        }
      }, 7000);
      return () => clearTimeout(timer);
    }
  }, [voiceError, voiceState]);

  // Stop listening when language is toggled during an active session
  useEffect(() => {
    if (voiceState === 'LISTENING' && recognitionRef.current) {
      try {
        recognitionRef.current.stop();
      } catch (_) {}
      setVoiceState('IDLE');
    }
  }, [language]);

  const handleSubmit = (e) => {
    if (e) e.preventDefault();

    // Stop active speech recognition if user submits while recording
    if (voiceState === 'LISTENING') {
      if (recognitionRef.current) {
        try {
          recognitionRef.current.stop();
        } catch (_) {}
      }
      setVoiceState('IDLE');
    }

    const trimmed = input.trim();
    if (!trimmed || disabled) return;

    onSendMessage(trimmed);
    setInput('');

    // Reset textarea height
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
    }
  };

  const handleKeyDown = (e) => {
    // Send message on Enter without Shift
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit();
    }
  };

  /**
   * Toggle Voice Input using browser-native SpeechRecognition
   */
  const handleToggleVoice = () => {
    if (disabled) return;

    // If currently recording, user can stop by pressing mic again
    if (voiceState === 'LISTENING') {
      if (recognitionRef.current) {
        try {
          recognitionRef.current.stop();
        } catch (err) {
          console.warn('Error stopping recognition:', err);
        }
      }
      setVoiceState('IDLE');
      return;
    }

    const SpeechRecognitionClass = getSpeechRecognitionClass();

    // Browser does not support Web Speech API
    if (!SpeechRecognitionClass) {
      setVoiceState('UNSUPPORTED');
      setVoiceError(
        'Voice input is not supported in this browser. Please use Chrome or Edge, or type your question.'
      );
      return;
    }

    setVoiceError(null);

    try {
      const recognition = new SpeechRecognitionClass();

      // Language selection: English -> en-IN, Tamil -> ta-IN
      recognition.lang = language === 'ta' ? 'ta-IN' : 'en-IN';
      recognition.continuous = false; // standard single question recognition
      recognition.interimResults = true; // show recognized speech live in input
      recognition.maxAlternatives = 1;

      // Keep whatever text farmer already typed and append recognized speech
      baseTextRef.current = input;

      recognition.onstart = () => {
        setVoiceState('LISTENING');
        setVoiceError(null);
      };

      recognition.onresult = (event) => {
        let transcript = '';
        for (let i = 0; i < event.results.length; i++) {
          transcript += event.results[i][0].transcript;
        }

        const prefix = baseTextRef.current ? baseTextRef.current.trim() + ' ' : '';
        const recognizedFullText = prefix + transcript;

        // Put recognized text into the EXISTING input field
        setInput(recognizedFullText);
      };

      recognition.onerror = (event) => {
        console.warn('Speech recognition error event:', event.error);
        setVoiceState('ERROR');

        if (event.error === 'not-allowed' || event.error === 'permission-denied') {
          setVoiceError('Microphone permission is required to use voice input.');
        } else if (event.error === 'no-speech') {
          setVoiceError('Could not recognize your voice. Please try again or type your question.');
        } else if (event.error === 'network') {
          setVoiceError('Could not recognize your voice. Please try again or type your question.');
        } else {
          setVoiceError('Could not recognize your voice. Please try again or type your question.');
        }
      };

      recognition.onend = () => {
        setVoiceState((prev) => (prev === 'LISTENING' ? 'IDLE' : prev));
        recognitionRef.current = null;
      };

      recognitionRef.current = recognition;
      recognition.start();
    } catch (err) {
      console.error('Failed to start speech recognition:', err);
      setVoiceState('ERROR');
      setVoiceError('Could not recognize your voice. Please try again or type your question.');
    }
  };

  const isSendDisabled = disabled || !input.trim();
  const isListening = voiceState === 'LISTENING';

  return (
    <div className="input-floating-wrapper">
      {/* Listening Banner */}
      {isListening && (
        <div className="voice-listening-banner" role="status" aria-live="polite">
          <span className="listening-pulse-dot" aria-hidden="true" />
          <span className="listening-text">
            {language === 'ta'
              ? '🔴 கேட்கிறது... (நிறுத்த மைக்ரோஃபோனை அழுத்தவும்)'
              : '🔴 Listening... (Click microphone to stop)'}
          </span>
        </div>
      )}

      {/* Voice Error Notification */}
      {voiceError && (
        <div className="voice-error-toast" role="alert">
          <AlertCircle size={16} className="voice-error-icon" />
          <span className="voice-error-msg">{voiceError}</span>
          <button
            type="button"
            className="voice-error-dismiss"
            onClick={() => {
              setVoiceError(null);
              setVoiceState('IDLE');
            }}
            aria-label="Dismiss error"
          >
            <X size={14} />
          </button>
        </div>
      )}

      {/* Main Input Box: [ Type your question... ] [ 🎙️ ] [ Send ] */}
      <form
        className={`input-box-container ${isListening ? 'listening-active' : ''}`}
        onSubmit={handleSubmit}
        role="search"
      >
        <textarea
          ref={textareaRef}
          className="chat-textarea"
          rows={1}
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder={placeholder}
          disabled={disabled}
          aria-label="Ask AgriGuide a question"
        />

        {/* Microphone Button (🎙️ / Mic) */}
        <button
          type="button"
          className={`chat-mic-btn ${isListening ? 'listening' : ''}`}
          onClick={handleToggleVoice}
          disabled={disabled}
          aria-label={
            isListening
              ? (language === 'ta' ? 'குரல் பதிவை நிறுத்து' : 'Stop voice recording')
              : (language === 'ta' ? 'குரல் மூலம் கேள்வி கேட்க' : 'Speak your question')
          }
          title={
            isListening
              ? (language === 'ta' ? 'நிறுத்த கிளிக் செய்யவும் (கேட்கிறது...)' : 'Click to stop listening')
              : (language === 'ta' ? 'குரல் உள்ளீடு (தமிழ்)' : 'Voice input (English)')
          }
        >
          {isListening ? (
            <MicOff size={19} className="mic-icon-recording" />
          ) : (
            <Mic size={19} />
          )}
        </button>

        {/* Send Button */}
        <button
          type="submit"
          className="chat-send-btn"
          disabled={isSendDisabled}
          aria-label="Send message"
          title="Send (Enter)"
        >
          <SendHorizonal size={18} />
        </button>
      </form>
    </div>
  );
}
