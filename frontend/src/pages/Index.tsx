import { useState, useEffect, useRef, useMemo } from "react";
import Header from "@/components/Header";
import Sidebar from "@/components/Sidebar";
import ChatWindow, { ChatMessage } from "@/components/ChatWindow";

// IMPORTANT: Update this URL to point to your Flask backend
const API_BASE_URL = "http://127.0.0.1:5000";

type Session = { id: string; title: string; updatedAt: number; archived?: boolean };

export default function Index() {
  const [selectedProject, setSelectedProject] = useState("");
  const [sessions, setSessions] = useState<Array<Session>>(() => {
    try {
      const raw = localStorage.getItem('cg_sessions');
      const parsed: Array<any> = raw ? JSON.parse(raw) : [];
      return parsed.map((s) => ({ ...s, archived: Boolean(s.archived) }));
    } catch { return []; }
  });
  const [activeSessionId, setActiveSessionId] = useState<string | null>(() => {
    try {
      return localStorage.getItem('cg_active_session');
    } catch { return null; }
  });
  const [isSidebarCollapsed, setIsSidebarCollapsed] = useState<boolean>(() => {
    try { return localStorage.getItem('cg_sidebar_collapsed') === '1'; } catch { return false; }
  });
  // Stabilize the very first session id during async state updates
  const pendingSessionIdRef = useRef<string | null>(null);
  
  const [messagesBySession, setMessagesBySession] = useState<Record<string, ChatMessage[]>>(() => {
    try {
      const raw = localStorage.getItem('cg_session_msgs');
      const parsed = raw ? JSON.parse(raw) : {};
      // Clean up any sessions with incomplete loading states
      const cleaned: Record<string, ChatMessage[]> = {};
      for (const [sessionId, messages] of Object.entries(parsed)) {
        if (Array.isArray(messages) && messages.length > 0) {
          // Remove any incomplete assistant messages (empty content)
          const cleanedMessages = messages.filter((msg: ChatMessage, index: number) => {
            if (msg.role === "assistant" && !msg.content && index === messages.length - 1) {
              return false; // Remove incomplete assistant message
            }
            return true;
          });
          if (cleanedMessages.length > 0) {
            cleaned[sessionId] = cleanedMessages;
          }
        }
      }
      return cleaned;
    } catch { return {}; }
  });

  const handleNewSession = () => {
    const id = crypto.randomUUID();
    const title = selectedProject ? `Chat - ${selectedProject}` : "New Chat";
    const newSession: Session = { id, title, updatedAt: Date.now(), archived: false };
    setSessions((prev) => [newSession, ...prev]);
    setActiveSessionId(id);
    // Clear any pending session ref when creating a new session
    pendingSessionIdRef.current = null;
  };

  const handleSelectSession = (id: string) => {
    setActiveSessionId(id);
  };

  const handleRenameSession = (id: string, title: string) => {
    setSessions((prev) => prev.map(s => s.id === id ? { ...s, title, updatedAt: Date.now() } : s));
  };

  const handleDeleteSession = (id: string) => {
    setSessions((prev) => prev.filter(s => s.id !== id));
    if (activeSessionId === id) setActiveSessionId(null);
    setMessagesBySession((prev) => {
      const copy = { ...prev };
      delete copy[id];
      return copy;
    });
  };

  const handleArchiveSession = (id: string, archived: boolean) => {
    setSessions((prev) => prev.map(s => s.id === id ? { ...s, archived, updatedAt: Date.now() } : s));
    if (archived && activeSessionId === id) setActiveSessionId(null);
  };

  const handleShareSession = async (id: string) => {
    const target = sessions.find(s => s.id === id);
    const payload = {
      id,
      title: target?.title || "",
      updatedAt: target?.updatedAt || Date.now(),
      messages: messagesBySession[id] || [],
    };
    const text = JSON.stringify(payload, null, 2);
    try {
      await navigator.clipboard.writeText(text);
      alert('Chat JSON copied to clipboard.');
    } catch {
      const blob = new Blob([text], { type: 'application/json' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `${payload.title || 'chat'}.json`;
      a.click();
      URL.revokeObjectURL(url);
    }
  };

  // persist sessions and active id
  useEffect(() => {
    try { localStorage.setItem('cg_sessions', JSON.stringify(sessions)); } catch {}
  }, [sessions]);
  useEffect(() => {
    try {
      if (activeSessionId) localStorage.setItem('cg_active_session', activeSessionId);
      else localStorage.removeItem('cg_active_session');
    } catch {}
  }, [activeSessionId]);
  useEffect(() => {
    try { localStorage.setItem('cg_session_msgs', JSON.stringify(messagesBySession)); } catch {}
  }, [messagesBySession]);
  useEffect(() => {
    try { localStorage.setItem('cg_sidebar_collapsed', isSidebarCollapsed ? '1' : '0'); } catch {}
  }, [isSidebarCollapsed]);

  const activeMessages: ChatMessage[] = activeSessionId ? (messagesBySession[activeSessionId] || []) : [];

  const sessionsSorted = useMemo(() => {
    return [...sessions].sort((a, b) => b.updatedAt - a.updatedAt);
  }, [sessions]);

  const ensureSession = (initialTitle?: string): string => {
    if (activeSessionId) {
      console.log('ensureSession: returning existing activeSessionId:', activeSessionId);
      return activeSessionId;
    }
    if (pendingSessionIdRef.current) {
      console.log('ensureSession: returning pending session ID:', pendingSessionIdRef.current);
      return pendingSessionIdRef.current;
    }
    
    const id = crypto.randomUUID();
    console.log('ensureSession: creating new session with ID:', id);
    pendingSessionIdRef.current = id;
    const titleBase = initialTitle || (selectedProject ? `Chat - ${selectedProject}` : "New Chat");
    const newSession = { id, title: titleBase, updatedAt: Date.now() };
    
    // Use functional updates to prevent race conditions
    setSessions((prev) => {
      // Check if session already exists to prevent duplicates
      if (prev.some(s => s.id === id)) return prev;
      return [newSession, ...prev];
    });
    setActiveSessionId(id);
    return id;
  };

  // Clear pending ref when activeSessionId commits
  useEffect(() => {
    if (activeSessionId) {
      pendingSessionIdRef.current = null;
    }
  }, [activeSessionId]);

  // Ensure we have a session when component mounts
  useEffect(() => {
    if (!activeSessionId && sessions.length === 0) {
      ensureSession();
    }
  }, [activeSessionId, sessions.length]);

  const setActiveMessages = (msgs: ChatMessage[]) => {
    // Only ensure session if we don't have an active session
    const id = activeSessionId || ensureSession();
    console.log('setActiveMessages called with activeSessionId:', activeSessionId, 'using id:', id);
    setMessagesBySession((prev) => ({ ...prev, [id]: msgs }));
    setSessions((prev) => prev.map(s => s.id === id ? { ...s, updatedAt: Date.now() } : s));
  };

  const handleFirstUserMessage = (text: string) => {
    // Only ensure session if we don't have an active session
    const id = activeSessionId || ensureSession();
    const firstLine = text.split('\n')[0].trim();
    const title = firstLine.length > 48 ? firstLine.slice(0, 45) + '…' : firstLine;
    setSessions((prev) => prev.map(s => s.id === id ? { ...s, title } : s));
  };

  return (
    <div className="min-h-screen bg-background">
      <Header
        onProjectChange={setSelectedProject}
        selectedProject={selectedProject}
        apiBaseUrl={API_BASE_URL}
      />
      <div className="flex">
        <aside className={`${isSidebarCollapsed ? "w-14" : "w-64"} transition-all duration-300`}>
          <Sidebar
            collapsed={isSidebarCollapsed}
            onToggleCollapsed={() => {
              console.log('Toggling sidebar, current state:', isSidebarCollapsed);
              setIsSidebarCollapsed(v => !v);
            }}
            sessions={sessionsSorted}
            activeSessionId={activeSessionId}
            onNewSession={handleNewSession}
            onSelectSession={handleSelectSession}
            onRenameSession={handleRenameSession}
            onDeleteSession={handleDeleteSession}
            onArchiveSession={handleArchiveSession}
            onShareSession={handleShareSession}
            messagesBySession={messagesBySession}
          />
        </aside>
        <main className="flex-1">
        <ChatWindow
          selectedProject={selectedProject}
          apiBaseUrl={API_BASE_URL}
          messages={activeMessages}
          onMessagesChange={setActiveMessages}
          onFirstUserMessage={handleFirstUserMessage}
          sessionId={activeSessionId}
        />
        </main>
      </div>
    </div>
  );
}