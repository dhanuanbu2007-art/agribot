import React, { useMemo } from 'react';
import { Sprout, User, AlertTriangle } from 'lucide-react';
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

export default function ChatMessage({ message }) {
  const isUser = message.role === 'user';
  const rawText = message.content || message.text || '';
  const isError = Boolean(message.isError);

  const { body, sources } = useMemo(() => {
    if (isUser) return { body: rawText, sources: null };
    return parseMessageContent(rawText);
  }, [isUser, rawText]);

  const time = formatTimestamp(message.timestamp);

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
