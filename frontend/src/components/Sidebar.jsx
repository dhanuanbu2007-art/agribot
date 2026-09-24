import React, { useMemo } from 'react';
import {
  Sprout,
  Plus,
  MessageSquare,
  Trash2,
  X,
  LogOut,
  User,
  Sparkles,
} from 'lucide-react';

function groupConversations(conversations) {
  const groups = { today: [], yesterday: [], last7Days: [], older: [] };
  const now = new Date();
  const todayStart = new Date(now.getFullYear(), now.getMonth(), now.getDate()).getTime();
  const oneDay = 24 * 60 * 60 * 1000;
  const yesterdayStart = todayStart - oneDay;
  const sevenDaysAgoStart = todayStart - 7 * oneDay;

  conversations.forEach((conv) => {
    const time = new Date(conv.updatedAt || conv.createdAt || Date.now()).getTime();
    if (time >= todayStart) groups.today.push(conv);
    else if (time >= yesterdayStart) groups.yesterday.push(conv);
    else if (time >= sevenDaysAgoStart) groups.last7Days.push(conv);
    else groups.older.push(conv);
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
  user,
  onLogout,
}) {
  const groups = useMemo(() => groupConversations(conversations), [conversations]);
  const hasHistory = conversations.length > 0;

  const renderGroup = (title, items) => {
    if (!items || items.length === 0) return null;
    return (
      <div className="sidebar-history-group" key={title}>
        <div className="sidebar-group-title">{title}</div>
        <ul className="sidebar-history-list" role="list">
          {items.map((conv) => {
            const isActive = conv.id === activeConversationId;
            return (
              <li key={conv.id} className="sidebar-history-item">
                <div className={`conversation-bubble ${isActive ? 'active' : ''}`}>
                  <button
                    type="button"
                    className="conversation-title-btn"
                    onClick={() => {
                      if (onSelectConversation) onSelectConversation(conv.id);
                      if (window.innerWidth <= 768 && onClose) onClose();
                    }}
                    title={conv.title}
                    aria-current={isActive ? 'true' : undefined}
                  >
                    <MessageSquare size={16} className="conv-icon" />
                    <span className="conv-text">{conv.title || 'New conversation'}</span>
                  </button>

                  <button
                    type="button"
                    className="conv-delete-btn"
                    onClick={(e) => {
                      e.stopPropagation();
                      if (onDeleteConversation) onDeleteConversation(e, conv.id);
                    }}
                    title="Delete conversation"
                    aria-label={`Delete ${conv.title}`}
                  >
                    <Trash2 size={14} />
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

      <aside className={`agriguide-sidebar ${isOpen ? 'open' : 'closed'}`} aria-label="Sidebar Navigation">
        {/* ── Brand Header ────────────────────────────────────────────── */}
        <div className="sidebar-header">
          <div className="sidebar-brand">
            <div className="sidebar-brand-icon">
              <Sprout size={22} strokeWidth={2.4} />
            </div>
            <div className="sidebar-brand-text">
              <span className="sidebar-brand-title">AgriGuide</span>
              <span className="sidebar-brand-subtitle">Smart Farming Assistant</span>
            </div>
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

        {/* ── New Conversation Button ──────────────────────────────────── */}
        <div className="sidebar-action-box">
          <button
            type="button"
            className="sidebar-new-chat-btn"
            onClick={() => {
              if (onNewChat) onNewChat();
              if (window.innerWidth <= 768 && onClose) onClose();
            }}
            aria-label="Start a new conversation"
          >
            <Plus size={18} strokeWidth={2.4} />
            <span>New Conversation</span>
          </button>
        </div>

        {/* ── Scrollable History ───────────────────────────────────────── */}
        <div className="sidebar-scroll-area">
          <div className="sidebar-section-header">
            <span>Conversations</span>
            <span className="sidebar-count-badge">{conversations.length}</span>
          </div>

          {hasHistory ? (
            <div className="sidebar-history-wrapper">
              {renderGroup('Today', groups.today)}
              {renderGroup('Yesterday', groups.yesterday)}
              {renderGroup('Previous 7 Days', groups.last7Days)}
              {renderGroup('Older', groups.older)}
            </div>
          ) : (
            <div className="sidebar-empty-state">
              <Sprout size={28} className="empty-icon" />
              <p>No conversations yet.</p>
              <span>Click "New Conversation" to start.</span>
            </div>
          )}
        </div>

        {/* ── Agricultural Graphic Accent ──────────────────────────────── */}
        <div className="sidebar-visual-accent">
          <div className="accent-inner">
            <Sparkles size={13} className="accent-sparkle" />
            <span>Knowledge Base: Paddy, Crops & Schemes</span>
          </div>
        </div>

        {/* ── Bottom: Farmer Info & Logout ─────────────────────────────── */}
        <div className="sidebar-bottom-panel">
          <div className="farmer-profile-card">
            <div className="farmer-avatar">
              <User size={18} />
            </div>
            <div className="farmer-info">
              <span className="farmer-name">
                {user?.displayName || "Farmer"}
              </span>
              <span className="farmer-email" title={user?.email || ""}>
                {user?.email || "Signed In"}
              </span>
            </div>
          </div>

          <button
            type="button"
            className="sidebar-logout-btn"
            onClick={onLogout}
            title="Logout"
            aria-label="Log out of AgriGuide"
          >
            <LogOut size={16} />
            <span>Logout</span>
          </button>
        </div>
      </aside>
    </>
  );
}
