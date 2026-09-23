import React from 'react';
import { BookOpen } from 'lucide-react';
import Markdown from 'react-markdown';
import remarkGfm from 'remark-gfm';

export default function SourceCard({ sourceContent }) {
  if (!sourceContent || !sourceContent.trim()) return null;

  return (
    <div className="sources-card" aria-label="Referenced Sources">
      <div className="sources-card-header">
        <div className="sources-icon-badge" aria-hidden="true">
          <BookOpen size={14} strokeWidth={2.2} />
        </div>
        <span className="sources-card-title">Verified Agriculture Sources</span>
      </div>
      <div className="sources-card-content markdown-body">
        <Markdown remarkPlugins={[remarkGfm]}>
          {sourceContent.trim()}
        </Markdown>
      </div>
    </div>
  );
}
