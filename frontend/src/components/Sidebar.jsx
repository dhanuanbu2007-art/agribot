import React, { useMemo } from 'react';
import {
  Sprout,
  Plus,
  BookOpen,
  Bug,
  FlaskConical,
  FileText,
  MessageSquare,
  Trash2,
  X,
} from 'lucide-react';

const KNOWLEDGE_CATEGORIES = [
  { name: 'Agriculture Guidelines', icon: BookOpen },
  { name: 'Crop Guides', icon: Sprout },
  { name: 'Disease & Pest Management', icon: Bug },
  { name: 'Fertilizer & Nutrient Management', icon: FlaskConical },
  { name: 'Government Schemes', icon: FileText },
];

function groupConversations(conversations) {
  const groups = {
    today: [],
    yesterday: [],
    last7Days: [],
    older: [],
  };

  const now = new Date();
  const todayStart = new Date(now.getFullYear(), now.getMonth(), now.getDate()).getTime();
  const oneDay = 24 * 60 * 60 * 1000;
  const yesterdayStart = todayStart - oneDay;
  const sevenDaysAgoStart = todayStart - 7 * oneDay;

  conversations.forEach((conv) => {
    const time = new Date(conv.updatedAt || conv.createdAt).getTime();
    if (time >= todayStart) {
      groups.today.push(conv);
    } else if (time >= yesterdayStart) {
      groups.yesterday.push(conv);
    } else if (time >= sevenDaysAgoStart) {
      groups.last7Days.push(conv);
    } else {
      groups.older.push(conv);
    }
  });

  return groups;
}

export default function Sidebar({
  isOpen,
  onClose,
  onNewChat,
  conversations = [],
  activeConversationId,
  onSelectConversation,
  onDeleteConversation,
}) {
  const groups = useMemo(() => groupConversations(conversations), [conversations]);

  const hasHistory = conversations.length > 0;

  const renderGroup = (title, items) => {
    if (!items || items.length === 0) return null;

    return (
      <div className="history-group" key={title}>
        <div className="history-group-title">{title}</div>
        <ul className="history-list" role="list">
          {items.map((conv) => {
            const isActive = conv.id === activeConversationId;
            return (
              <li key={conv.id} className="history-list-item">
                <div className={`conversation-item-wrapper ${isActive ? 'active' : ''}`}>
                  <button
                    type="button"
                    className="conversation-select-btn"
                    onClick={() => onSelectConversation && onSelectConversation(conv.id)}
                    title={conv.title}
                    aria-current={isActive ? 'true' : undefined}
                  >
                    <MessageSquare size={15} className="conversation-icon" strokeWidth={1.8} />
                    <span className="conversation-title">{conv.title || 'New Conversation'}</span>
                  </button>
                  <button
                    type="button"
                    className="delete-conversation-btn"
                    onClick={(e) => {
                      e.stopPropagation();
                      if (onDeleteConversation) {
                        onDeleteConversation(conv.id);
                      }
                    }}
                    title="Delete conversation"
                    aria-label={`Delete ${conv.title}`}
                  >
                    <Trash2 size={13} strokeWidth={2} />
                  </button>
                </div>
              </li>
            );
          })}
        </ul>
      </div>
    );
  };

  return (
    <>
      {/* Mobile backdrop */}
      <div
        className={`sidebar-backdrop ${isOpen ? 'open' : ''}`}
        onClick={onClose}
        aria-hidden="true"
      />

      <aside className={`sidebar ${isOpen ? 'open' : ''}`} aria-label="Sidebar Navigation">
        {/* Header Branding */}
        <div className="sidebar-header">
          <div className="sidebar-logo-icon">
            <Sprout size={20} strokeWidth={2.4} />
          </div>
          <div className="sidebar-title-area">
            <span className="sidebar-title">AgriGuide</span>
            <span className="sidebar-subtitle">Agriculture AI Assistant</span>
          </div>
          <button
            type="button"
            className="sidebar-close-btn"
            onClick={onClose}
            aria-label="Close sidebar"
          >
            <X size={18} />
          </button>
        </div>

        {/* Primary Action Button: New Chat */}
        <div className="sidebar-action-area">
          <button
            type="button"
            className="new-chat-button"
            onClick={onNewChat}
            aria-label="Start a new chat conversation"
          >
            <Plus size={18} strokeWidth={2.5} />
            <span>New Chat</span>
          </button>
        </div>

        {/* Scrollable middle section: Chat History & Knowledge Base */}
        <div className="sidebar-content">
          {/* Chat History Section */}
          <div className="sidebar-section-container">
            <div className="sidebar-section-title">Chat History</div>
            {hasHistory ? (
              <div className="history-groups-wrapper">
                {renderGroup('Today', groups.today)}
                {renderGroup('Yesterday', groups.yesterday)}
                {renderGroup('Previous 7 Days', groups.last7Days)}
                {renderGroup('Older', groups.older)}
              </div>
            ) : (
              <div className="history-empty-state">
                <span>No saved conversations yet.</span>
              </div>
            )}
          </div>

          <div className="sidebar-divider" />

          {/* Knowledge Base Categories */}
          <div className="sidebar-section-container">
            <div className="sidebar-section-title">Knowledge Base</div>
            <ul className="categories-list" role="list">
              {KNOWLEDGE_CATEGORIES.map((cat, idx) => {
                const IconComponent = cat.icon;
                return (
                  <li key={idx} className="category-item" title={cat.name}>
                    <div className="category-icon-wrapper">
                      <IconComponent size={15} className="category-icon" strokeWidth={1.9} />
                    </div>
                    <span>{cat.name}</span>
                  </li>
                );
              })}
            </ul>
          </div>
        </div>

        {/* Footer info branding */}
        <div className="sidebar-footer">
          <div className="powered-by-label">Powered by</div>
          <div className="powered-by-stack">
            <span>BGE-M3</span>
            <span className="powered-by-dot">•</span>
            <span>Qdrant</span>
            <span className="powered-by-dot">•</span>
            <span>Gemini</span>
          </div>
        </div>
      </aside>
    </>
  );
}
