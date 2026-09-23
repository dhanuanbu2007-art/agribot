import React from 'react';
import { Sprout } from 'lucide-react';

export default function LoadingIndicator() {
  return (
    <div className="loading-row" aria-live="polite" aria-label="AgriGuide is preparing advisory">
      <div className="assistant-avatar loading-avatar" aria-hidden="true">
        <Sprout size={18} strokeWidth={2.3} />
      </div>
      <div className="loading-bubble">
        <span className="loading-text">AgriGuide is reviewing agriculture sources</span>
        <div className="dots-container" aria-hidden="true">
          <span className="dot" />
          <span className="dot" />
          <span className="dot" />
        </div>
      </div>
    </div>
  );
}
