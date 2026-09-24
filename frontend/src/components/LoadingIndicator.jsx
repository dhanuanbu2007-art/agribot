import React from 'react';
import { Sprout } from 'lucide-react';

export default function LoadingIndicator({ language = 'en' }) {
  return (
    <div
      className="agriguide-msg-row assistant-msg loading-msg"
      aria-live="polite"
      aria-label="AgriGuide is researching agricultural knowledge base"
      role="status"
    >
      <div className="msg-avatar-box assistant-avatar" aria-hidden="true">
        <Sprout size={16} strokeWidth={2.4} />
      </div>

      <div className="msg-content-wrapper">
        <div className="msg-header-info">
          <span className="msg-sender-name">AgriGuide</span>
          <span className="msg-role-tag">Searching knowledge base</span>
        </div>

        <div className="msg-bubble-box bubble-assistant loading-bubble">
          <span className="loading-text">
            {language === 'ta'
              ? 'விவசாய அறிவுத் தளத்தில் தேடுகிறது'
              : 'Consulting agricultural knowledge base'}
          </span>
          <div className="bouncing-dots" aria-hidden="true">
            <span className="dot" />
            <span className="dot" />
            <span className="dot" />
          </div>
        </div>
      </div>
    </div>
  );
}
