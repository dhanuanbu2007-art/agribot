import React, { useRef, useEffect } from 'react';
import WelcomeScreen from './WelcomeScreen';
import ChatMessage from './ChatMessage';
import LoadingIndicator from './LoadingIndicator';
import ChatInput from './ChatInput';
import { AlertCircle } from 'lucide-react';

export default function ChatWindow({
  messages,
  isLoading,
  error,
  language = 'en',
  onSendMessage,
  onClearError,
}) {
  const messagesEndRef = useRef(null);
  const scrollContainerRef = useRef(null);

  // Auto-scroll to bottom whenever messages change or loading starts
  useEffect(() => {
    if (messagesEndRef.current) {
      messagesEndRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [messages, isLoading, error]);

  const hasMessages = messages.length > 0;

  return (
    <main className="chat-container" role="main">
      <div className="messages-scroll-area" ref={scrollContainerRef}>
        {!hasMessages ? (
          <WelcomeScreen
            language={language}
            onSelectSuggestion={onSendMessage}
          />
        ) : (
          <div className="messages-inner-wrapper">
            {messages.map((msg) => (
              <ChatMessage key={msg.id} message={msg} />
            ))}

            {isLoading && <LoadingIndicator />}

            {error && (
              <div className="chat-error-banner" role="alert">
                <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                  <AlertCircle size={18} />
                  <span>{error}</span>
                </div>
                {onClearError && (
                  <button
                    type="button"
                    onClick={onClearError}
                    style={{
                      background: 'none',
                      border: 'none',
                      color: 'inherit',
                      cursor: 'pointer',
                      fontWeight: 600,
                      fontSize: '0.8rem',
                    }}
                  >
                    Dismiss
                  </button>
                )}
              </div>
            )}

            <div ref={messagesEndRef} style={{ height: 1 }} />
          </div>
        )}
      </div>

      <ChatInput
        onSendMessage={onSendMessage}
        disabled={isLoading}
        language={language}
      />
    </main>
  );
}
