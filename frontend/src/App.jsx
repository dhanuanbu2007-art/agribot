import React, { useState, useEffect, useCallback, useRef } from 'react';
import Sidebar from './components/Sidebar';
import Header from './components/Header';
import ChatWindow from './components/ChatWindow';
import { checkBackendHealth, sendChatMessage } from './services/api';

// ─── localStorage helpers ─────────────────────────────────────────────────────

const STORAGE_KEY = 'agriguide_chats';

function loadFromStorage() {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (!raw) return { conversations: [], activeConversationId: null };
    return JSON.parse(raw);
  } catch {
    return { conversations: [], activeConversationId: null };
  }
}

function saveToStorage(conversations, activeConversationId) {
  try {
    localStorage.setItem(
      STORAGE_KEY,
      JSON.stringify({ conversations, activeConversationId })
    );
  } catch (e) {
    console.warn('[AgriGuide] Could not save chat history:', e);
  }
}

// ─── Utilities ────────────────────────────────────────────────────────────────

function generateId() {
  return `${Date.now()}-${Math.random().toString(36).slice(2, 9)}`;
}

/**
 * Generate a clean, short title from the first user message.
 * Strips filler words and trims to ≤35 characters.
 */
function generateTitle(firstUserMessage) {
  const fillers = [
    'i want to', 'i would like to', 'i need to', 'i am going to',
    'i plan to', 'can you', 'could you', 'please', 'help me',
    'tell me about', 'what is', 'what are', 'how to', 'how do i',
    'what should i do', 'how can i', 'naan', 'nan', 'en',
    'ennoda', 'epdi', 'eppadi', 'edhavadhu', 'edhuvadhu',
  ];

  let text = firstUserMessage.trim();

  // Remove punctuation at the end
  text = text.replace(/[?.!]+$/, '').trim();

  // Strip filler prefixes (case-insensitive)
  const lower = text.toLowerCase();
  for (const filler of fillers) {
    if (lower.startsWith(filler + ' ')) {
      text = text.slice(filler.length).trim();
      break;
    }
  }

  // Capitalize first letter
  if (text.length > 0) {
    text = text.charAt(0).toUpperCase() + text.slice(1);
  }

  // Truncate to 35 chars cleanly
  if (text.length > 35) {
    const truncated = text.slice(0, 35);
    const lastSpace = truncated.lastIndexOf(' ');
    text = lastSpace > 20 ? truncated.slice(0, lastSpace) : truncated;
    text += '…';
  }

  return text || 'Agriculture Question';
}

function createNewConversation() {
  return {
    id: generateId(),
    title: 'New Conversation',
    createdAt: new Date().toISOString(),
    updatedAt: new Date().toISOString(),
    messages: [],
  };
}

// ─── App ──────────────────────────────────────────────────────────────────────

export default function App() {
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);
  const [isOnline, setIsOnline] = useState(false);
  const [isCheckingHealth, setIsCheckingHealth] = useState(true);
  const [language, setLanguage] = useState('en');

  // ── Conversation state loaded from localStorage ──
  const [conversations, setConversations] = useState(() => {
    const stored = loadFromStorage();
    return stored.conversations;
  });

  const [activeConversationId, setActiveConversationId] = useState(() => {
    const stored = loadFromStorage();
    return stored.activeConversationId;
  });

  // Derived: active conversation object
  const activeConversation = conversations.find(c => c.id === activeConversationId) || null;
  const messages = activeConversation ? activeConversation.messages : [];

  // Ref to track if we need to persist (avoid double-persist on mount)
  const didMountRef = useRef(false);

  // Persist whenever conversations or activeId changes (not on initial mount)
  useEffect(() => {
    if (!didMountRef.current) {
      didMountRef.current = true;
      return;
    }
    saveToStorage(conversations, activeConversationId);
  }, [conversations, activeConversationId]);

  // ── Health polling ──────────────────────────────────────────────────────────
  const checkHealth = useCallback(async () => {
    const res = await checkBackendHealth();
    setIsOnline(res.online);
    setIsCheckingHealth(false);
  }, []);

  useEffect(() => {
    checkHealth();
    const id = setInterval(checkHealth, 30000);
    return () => clearInterval(id);
  }, [checkHealth]);

  // ── Conversation CRUD ───────────────────────────────────────────────────────

  /** Update a conversation's data immutably */
  const updateConversation = useCallback((convId, updater) => {
    setConversations(prev =>
      prev.map(c => (c.id === convId ? { ...c, ...updater(c) } : c))
    );
  }, []);

  /** Create a brand-new conversation and make it active */
  const handleNewChat = useCallback(() => {
    const newConv = createNewConversation();
    setConversations(prev => [newConv, ...prev]);
    setActiveConversationId(newConv.id);
    setError(null);
    if (window.innerWidth < 768) setSidebarOpen(false);
  }, []);

  /** Switch to an existing conversation */
  const handleSelectConversation = useCallback((convId) => {
    setActiveConversationId(convId);
    setError(null);
    if (window.innerWidth < 768) setSidebarOpen(false);
  }, []);

  /** Delete a conversation */
  const handleDeleteConversation = useCallback((convId) => {
    setConversations(prev => {
      const updated = prev.filter(c => c.id !== convId);
      // If deleted the active one, switch to the next available
      if (convId === activeConversationId) {
        const newActive = updated.length > 0 ? updated[0].id : null;
        setActiveConversationId(newActive);
      }
      return updated;
    });
  }, [activeConversationId]);

  // ── Send Message ────────────────────────────────────────────────────────────

  const handleSendMessage = useCallback(async (questionText) => {
    if (!questionText || !questionText.trim() || isLoading) return;

    const trimmed = questionText.trim();

    // If no active conversation, create one automatically
    let currentConvId = activeConversationId;
    if (!currentConvId) {
      const newConv = createNewConversation();
      setConversations(prev => [newConv, ...prev]);
      setActiveConversationId(newConv.id);
      currentConvId = newConv.id;
    }

    const userMsgId = `user-${generateId()}`;
    const now = new Date().toISOString();

    // Append user message immediately
    setConversations(prev =>
      prev.map(c => {
        if (c.id !== currentConvId) return c;
        const newMessages = [
          ...c.messages,
          { id: userMsgId, role: 'user', text: trimmed, timestamp: now },
        ];
        // Auto-title from first user message
        const isFirstUserMsg = c.messages.every(m => m.role !== 'user');
        return {
          ...c,
          messages: newMessages,
          title: isFirstUserMsg ? generateTitle(trimmed) : c.title,
          updatedAt: now,
        };
      })
    );

    setIsLoading(true);
    setError(null);

    try {
      const response = await sendChatMessage(trimmed);

      const assistantMsgId = `assistant-${generateId()}`;
      const answerTime = new Date().toISOString();

      setConversations(prev =>
        prev.map(c => {
          if (c.id !== currentConvId) return c;
          return {
            ...c,
            messages: [
              ...c.messages,
              {
                id: assistantMsgId,
                role: 'assistant',
                text: response.answer,
                timestamp: answerTime,
              },
            ],
            updatedAt: answerTime,
          };
        })
      );

      setIsOnline(true);
    } catch (err) {
      console.error('[App] Failed to get response:', err);
      let msg = 'Something went wrong. Please try again.';
      if (
        err.message.includes("couldn't connect") ||
        err.message.includes('Failed to fetch') ||
        err.message.includes('NetworkError')
      ) {
        msg = "AgriGuide couldn't connect to the server. Please make sure the backend is running.";
        setIsOnline(false);
      }
      setError(msg);
    } finally {
      setIsLoading(false);
    }
  }, [activeConversationId, isLoading]);

  // ─────────────────────────────────────────────────────────────────────────────

  return (
    <div className="app-container">
      <Sidebar
        isOpen={sidebarOpen}
        onClose={() => setSidebarOpen(false)}
        onNewChat={handleNewChat}
        conversations={conversations}
        activeConversationId={activeConversationId}
        onSelectConversation={handleSelectConversation}
        onDeleteConversation={handleDeleteConversation}
      />

      <div className="main-wrapper">
        <Header
          onToggleSidebar={() => setSidebarOpen(prev => !prev)}
          isOnline={isOnline}
          isCheckingHealth={isCheckingHealth}
          language={language}
          onLanguageChange={setLanguage}
        />

        <ChatWindow
          messages={messages}
          isLoading={isLoading}
          error={error}
          language={language}
          onSendMessage={handleSendMessage}
          onClearError={() => setError(null)}
        />
      </div>
    </div>
  );
}
