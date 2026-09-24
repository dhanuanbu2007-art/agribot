import React, { useRef, useEffect } from 'react';
import WelcomeScreen from './WelcomeScreen';
import ChatMessage from './ChatMessage';
import LoadingIndicator from './LoadingIndicator';
import { AlertCircle, X } from 'lucide-react';

export default function ChatWindow({
  messages = [],
  isLoading = false,
  error = null,
  language = 'en',
  onSendMessage,
  onClearError,
}) {
  const messagesEndRef = useRef(null);

  // Auto-scroll to bottom when messages change
  useEffect(() => {
    if (messagesEndRef.current) {
      messagesEndRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [messages, isLoading, error]);

  const hasMessages = messages.length > 0;

  return (
    <div className="chat-window-body">
      {/* Error Banner */}
      {error && (
        <div className="chat-error-toast" role="alert" aria-live="assertive">
          <div className="error-toast-inner">
            <AlertCircle size={17} className="toast-err-icon" />
            <span>{error}</span>
          </div>
          {onClearError && (
            <button
              type="button"
              className="toast-dismiss-btn"
              onClick={onClearError}
              aria-label="Dismiss error"
            >
              <X size={15} />
            </button>
          )}
        </div>
      )}

      {/* Scrollable Messages Area */}
      <div className="messages-scroll-container">
        {!hasMessages ? (
          <WelcomeScreen
            language={language}
            onSelectSuggestion={onSendMessage}
          />
        ) : (
          <div className="messages-inner">
            {messages.map((msg) => (
              <ChatMessage key={msg.id} message={msg} />
            ))}

            {isLoading && <LoadingIndicator language={language} />}

            <div ref={messagesEndRef} style={{ height: 1 }} aria-hidden="true" />
          </div>
        )}

        {/* When welcome screen is shown but loading or error, show messages end reference */}
        {!hasMessages && <div ref={messagesEndRef} style={{ height: 1 }} aria-hidden="true" />}
      </div>
    </div>
  );
}
