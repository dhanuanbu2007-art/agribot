import { useEffect, useMemo, useRef, useState } from "react";
import { onAuthStateChanged, signOut } from "firebase/auth";
import { Leaf } from "lucide-react";

import { auth } from "./firebase";
import Auth from "./components/Auth";
import Header from "./components/Header";
import Sidebar from "./components/Sidebar";
import ChatWindow from "./components/ChatWindow";
import ChatInput from "./components/ChatInput";
import { sendChatMessage, checkHealth, getHistory, saveHistory, deleteConversation } from "./services/api";

import "./app.css";

// ─────────────────────────────────────────────────────────────────────────────
// Helpers
// ─────────────────────────────────────────────────────────────────────────────

function createNewConversation() {
  return {
    id: crypto.randomUUID(),
    title: "New conversation",
    messages: [],
    createdAt: Date.now(),
    updatedAt: Date.now(),
  };
}

function getTitle(question) {
  const q = question.trim();
  if (!q) return "New conversation";
  return q.length <= 36 ? q : `${q.slice(0, 36)}...`;
}

// ─────────────────────────────────────────────────────────────────────────────
// App Component
// ─────────────────────────────────────────────────────────────────────────────

export default function App() {
  // Auth
  const [user, setUser] = useState(null);
  const [authLoading, setAuthLoading] = useState(true);

  // Conversations
  const [conversations, setConversations] = useState([]);
  const [activeConversationId, setActiveConversationId] = useState(null);
  
  // Track if initial history load is complete
  const [historyLoaded, setHistoryLoaded] = useState(false);

  // UI state
  const [sidebarOpen, setSidebarOpen] = useState(window.innerWidth > 768);
  const [language, setLanguage] = useState("en");
  const [isSending, setIsSending] = useState(false);
  const [chatError, setChatError] = useState(null);

  // Backend
  const [backendStatus, setBackendStatus] = useState("checking");

  // ── Firebase Auth Listener ────────────────────────────────────────────────
  useEffect(() => {
    const unsubscribe = onAuthStateChanged(auth, async (currentUser) => {
      setHistoryLoaded(false);
      setUser(currentUser);
      
      if (currentUser) {
        try {
          const idToken = await currentUser.getIdToken();
          const history = await getHistory(idToken);
          
          if (Array.isArray(history) && history.length > 0) {
            setConversations(history);
            setActiveConversationId(history[0].id);
          } else {
            const newConv = createNewConversation();
            setConversations([newConv]);
            setActiveConversationId(newConv.id);
          }
          setHistoryLoaded(true);
        } catch (err) {
          console.error("[AgriGuide] Failed to load history from backend:", err);
          const newConv = createNewConversation();
          setConversations([newConv]);
          setActiveConversationId(newConv.id);
          // Keep historyLoaded false if backend fetch failed so we don't overwrite DB with blank state
          setHistoryLoaded(false);
        }
      } else {
        // Clear state on logout
        setConversations([]);
        setActiveConversationId(null);
        setHistoryLoaded(false);
      }
      
      setAuthLoading(false);
    });
    return unsubscribe;
  }, []);

  // ── Backend Health Check ──────────────────────────────────────────────────
  useEffect(() => {
    let mounted = true;
    const check = async () => {
      try {
        await checkHealth();
        if (mounted) setBackendStatus("online");
      } catch {
        if (mounted) setBackendStatus("offline");
      }
    };
    check();
    const interval = setInterval(check, 30000);
    return () => {
      mounted = false;
      clearInterval(interval);
    };
  }, []);

  // ── Responsive Sidebar ────────────────────────────────────────────────────
  useEffect(() => {
    const handleResize = () => {
      if (window.innerWidth <= 768) {
        setSidebarOpen(false);
      }
    };
    window.addEventListener("resize", handleResize);
    return () => window.removeEventListener("resize", handleResize);
  }, []);

  // ── Active Conversation ───────────────────────────────────────────────────
  const activeConversation = useMemo(
    () => conversations.find((c) => c.id === activeConversationId) || null,
    [conversations, activeConversationId]
  );

  // ── New Conversation ──────────────────────────────────────────────────────
  const handleNewConversation = () => {
    const newConv = createNewConversation();
    setConversations((prev) => [newConv, ...prev]);
    setActiveConversationId(newConv.id);
    setChatError(null);
  };

  // ── Select Conversation ───────────────────────────────────────────────────
  const handleSelectConversation = (id) => {
    setActiveConversationId(id);
    setChatError(null);
  };

  // ── Delete Conversation ───────────────────────────────────────────────────
  const handleDeleteConversation = async (event, conversationId) => {
    if (event) event.stopPropagation();

    const remaining = conversations.filter((c) => c.id !== conversationId);
    let nextActiveId = activeConversationId;
    if (conversationId === activeConversationId) {
      nextActiveId = remaining.length > 0 ? remaining[0].id : null;
    }
    if (remaining.length === 0) {
      const fresh = createNewConversation();
      setConversations([fresh]);
      setActiveConversationId(fresh.id);
    } else {
      setConversations(remaining);
      setActiveConversationId(nextActiveId);
    }

    if (user) {
      try {
        const idToken = await user.getIdToken();
        await deleteConversation(conversationId, idToken);
      } catch (err) {
        console.error("[AgriGuide] Failed to delete conversation on server:", err);
      }
    }
  };

  // ── Send Message ──────────────────────────────────────────────────────────
  const handleSendMessage = async (question) => {
    if (!question?.trim() || isSending) return;
    if (!user) return;

    setChatError(null);
    const trimmedQuestion = question.trim();

    // Ensure an active conversation exists
    let conversationId = activeConversationId;
    if (!conversationId) {
      const newConv = createNewConversation();
      conversationId = newConv.id;
      setConversations((prev) => [newConv, ...prev]);
      setActiveConversationId(conversationId);
    }

    const userMessageId = crypto.randomUUID();
    const userMessage = {
      id: userMessageId,
      role: "user",
      content: trimmedQuestion,
      timestamp: Date.now(),
    };

    // Immediately show user message
    setConversations((prev) =>
      prev.map((conv) => {
        if (conv.id !== conversationId) return conv;
        const isFirst = conv.messages.length === 0;
        return {
          ...conv,
          title: isFirst ? getTitle(trimmedQuestion) : conv.title,
          messages: [...conv.messages, userMessage],
          updatedAt: Date.now(),
        };
      })
    );

    setIsSending(true);

    try {
      const idToken = await user.getIdToken();
      const response = await sendChatMessage(
        trimmedQuestion,
        conversationId,
        idToken,
        userMessageId
      );

      const serverConv = response?.conversation;
      const assistantMessage = {
        id: serverConv?.messages?.slice(-1)[0]?.id || crypto.randomUUID(),
        role: "assistant",
        content:
          response?.answer ||
          "I couldn't generate a response. Please try again.",
        timestamp: Date.now(),
      };

      setConversations((prev) =>
        prev.map((conv) => {
          if (conv.id !== conversationId) return conv;
          return {
            ...conv,
            title: serverConv?.title || conv.title,
            messages: [...conv.messages, assistantMessage],
            updatedAt: Date.now(),
          };
        })
      );
    } catch (error) {
      console.error("[AgriGuide] Send message failed:", error);

      const errorMessage = {
        id: crypto.randomUUID(),
        role: "assistant",
        isError: true,
        content:
          error?.message ||
          "Something went wrong connecting to AgriGuide AI. Please check the backend and try again.",
        timestamp: Date.now(),
      };

      setConversations((prev) =>
        prev.map((conv) => {
          if (conv.id !== conversationId) return conv;
          return {
            ...conv,
            messages: [...conv.messages, errorMessage],
            updatedAt: Date.now(),
          };
        })
      );

      setChatError(
        error?.message || "Failed to contact AgriGuide AI. Is the backend running?"
      );
    } finally {
      setIsSending(false);
    }
  };

  // ── Logout ────────────────────────────────────────────────────────────────
  const handleLogout = async () => {
    try {
      await signOut(auth);
    } catch (error) {
      console.error("[AgriGuide] Logout failed:", error);
    }
  };

  // ─────────────────────────────────────────────────────────────────────────
  // RENDER: Auth Loading
  // ─────────────────────────────────────────────────────────────────────────

  if (authLoading) {
    return (
      <div className="app-auth-loading">
        <div className="auth-loading-card">
          <div className="loading-leaf-icon">
            <Leaf size={32} />
          </div>
          <h2 className="loading-brand-name">AgriGuide</h2>
          <p className="loading-text">Preparing your farming assistant...</p>
          <div className="loading-spinner-bar" />
        </div>
      </div>
    );
  }

  // ─────────────────────────────────────────────────────────────────────────
  // RENDER: Not Logged In → Show Auth
  // ─────────────────────────────────────────────────────────────────────────

  if (!user) {
    return <Auth onLogin={setUser} />;
  }

  // ─────────────────────────────────────────────────────────────────────────
  // RENDER: Main Application
  // ─────────────────────────────────────────────────────────────────────────

  return (
    <div className="agriguide-app-shell">
      {/* ── Sidebar ─────────────────────────────────────────────────── */}
      <Sidebar
        isOpen={sidebarOpen}
        onClose={() => setSidebarOpen(false)}
        onNewChat={handleNewConversation}
        conversations={conversations}
        activeConversationId={activeConversationId}
        onSelectConversation={handleSelectConversation}
        onDeleteConversation={handleDeleteConversation}
        user={user}
        onLogout={handleLogout}
      />

      {/* ── Main Content Area ────────────────────────────────────────── */}
      <div className="agriguide-main-area">
        {/* Header */}
        <Header
          onToggleSidebar={() => setSidebarOpen((prev) => !prev)}
          backendStatus={backendStatus}
          language={language}
          onLanguageChange={setLanguage}
        />

        {/* Chat Window (messages or welcome) */}
        <div className="agriguide-chat-section">
          <ChatWindow
            messages={activeConversation?.messages || []}
            isLoading={isSending}
            error={chatError}
            language={language}
            onSendMessage={handleSendMessage}
            onClearError={() => setChatError(null)}
          />
        </div>

        {/* Fixed Chat Input Area */}
        <div className="agriguide-input-area">
          <ChatInput
            onSendMessage={handleSendMessage}
            disabled={isSending || backendStatus === "offline"}
            language={language}
          />
          <p className="input-disclaimer">
            AgriGuide provides agricultural guidance based on your farming knowledge base. Always consult local agriculture experts for critical decisions.
          </p>
        </div>
      </div>
    </div>
  );
}