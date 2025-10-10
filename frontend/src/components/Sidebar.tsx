import { useMemo, useState, useRef, useEffect } from "react";
import { Plus, Search, MessageSquare, MoreVertical, Trash2, Archive, ArchiveRestore, Share2, Pencil, ChevronLeft, ChevronRight, Info, Settings } from "lucide-react";

type Message = { role: "user" | "assistant"; content: string; createdAt?: number };
type Session = { id: string; title: string; updatedAt: number; archived?: boolean };

interface SidebarProps {
  collapsed: boolean;
  onToggleCollapsed: () => void;
  sessions: Session[];
  activeSessionId: string | null;
  onNewSession: () => void;
  onSelectSession: (id: string) => void;
  onRenameSession: (id: string, title: string) => void;
  onDeleteSession: (id: string) => void;
  onArchiveSession: (id: string, archived: boolean) => void;
  onShareSession: (id: string) => void;
  messagesBySession: Record<string, Message[]>;
}

function formatTimestamp(ts: number) {
  try {
    const d = new Date(ts);
    return d.toLocaleString();
  } catch {
    return "";
  }
}

export default function Sidebar({ collapsed, onToggleCollapsed, sessions, activeSessionId, onNewSession, onSelectSession, onRenameSession, onDeleteSession, onArchiveSession, onShareSession, messagesBySession }: SidebarProps) {
  const [query, setQuery] = useState("");
  const [activeDropdown, setActiveDropdown] = useState<string | null>(null);
  const [showDetails, setShowDetails] = useState<string | null>(null);
  const dropdownRef = useRef<HTMLDivElement>(null);

  const { activeList, archivedList } = useMemo(() => {
    const active = sessions.filter(s => !s.archived);
    const archived = sessions.filter(s => s.archived);
    return { activeList: active, archivedList: archived };
  }, [sessions]);

  // Close dropdown when clicking outside
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setActiveDropdown(null);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  // Close details modal when clicking outside
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (showDetails && !(event.target as Element).closest('.details-modal')) {
        setShowDetails(null);
      }
    };

    if (showDetails) {
      document.addEventListener('mousedown', handleClickOutside);
      return () => document.removeEventListener('mousedown', handleClickOutside);
    }
  }, [showDetails]);

  const filterFn = (s: Session) => {
    const q = query.trim().toLowerCase();
    if (!q) return true;
    const titleMatch = (s.title || "").toLowerCase().includes(q);
    const last = (messagesBySession[s.id] || []);
    const lastMsg = last.length ? last[last.length - 1].content : "";
    const messageMatch = (lastMsg || "").toLowerCase().includes(q);
    return titleMatch || messageMatch;
  };

  const renderRow = (s: Session) => {
    const isActive = s.id === activeSessionId;
    const msgs = messagesBySession[s.id] || [];
    const lastMsg = msgs.length ? msgs[msgs.length - 1] : undefined;
    const preview = lastMsg?.content ? lastMsg.content.slice(0, 60) + (lastMsg.content.length > 60 ? "…" : "") : "";

    if (collapsed) {
      return (
        <button
          key={s.id}
          onClick={() => onSelectSession(s.id)}
          className={`group flex w-full items-center justify-center rounded-md p-2 text-left ${isActive ? "bg-primary/10 text-primary" : "hover:bg-surface-alt"}`}
          title={s.title}
        >
          <MessageSquare className="h-4 w-4" />
        </button>
      );
    }

    return (
      <div
        key={s.id}
        className={`group relative rounded-md px-2 py-2 ${isActive ? "bg-primary/10 text-primary" : "hover:bg-surface-alt"}`}
      >
        <div className="flex items-start gap-2">
          <button onClick={() => onSelectSession(s.id)} className="flex min-w-0 flex-1 items-start gap-2 text-left">
            <MessageSquare className="mt-0.5 h-4 w-4 flex-shrink-0 text-muted-foreground group-hover:text-foreground" />
            <div className="min-w-0 flex-1">
              <div className="line-clamp-1 text-sm font-medium">{s.title || "Untitled"}</div>
              {preview && <div className="line-clamp-1 text-xs text-muted-foreground">{preview}</div>}
            </div>
          </button>
          <div className="opacity-0 transition-opacity group-hover:opacity-100">
            <button
              className="rounded p-1 hover:bg-surface"
              title="More options"
              onClick={(e) => {
                e.stopPropagation();
                setActiveDropdown(activeDropdown === s.id ? null : s.id);
              }}
            >
              <MoreVertical className="h-4 w-4" />
            </button>
          </div>
        </div>
        
        {/* Dropdown Menu */}
        {activeDropdown === s.id && (
          <div 
            ref={dropdownRef}
            className="absolute right-2 top-12 z-50 min-w-[180px] rounded-lg border bg-background p-1 shadow-lg"
          >
            <button
              className="flex w-full items-center gap-3 rounded-md px-3 py-2 text-left text-sm hover:bg-surface-alt"
              onClick={() => {
                const next = prompt("Rename chat", s.title || "Untitled");
                if (next && next.trim()) onRenameSession(s.id, next.trim());
                setActiveDropdown(null);
              }}
            >
              <Pencil className="h-4 w-4" />
              Rename
            </button>
            <button
              className="flex w-full items-center gap-3 rounded-md px-3 py-2 text-left text-sm hover:bg-surface-alt"
              onClick={() => {
                setShowDetails(s.id);
                setActiveDropdown(null);
              }}
            >
              <Info className="h-4 w-4" />
              Details
            </button>
            <button
              className="flex w-full items-center gap-3 rounded-md px-3 py-2 text-left text-sm hover:bg-surface-alt"
              onClick={() => {
                onShareSession(s.id);
                setActiveDropdown(null);
              }}
            >
              <Share2 className="h-4 w-4" />
              Share
            </button>
            {s.archived ? (
              <button
                className="flex w-full items-center gap-3 rounded-md px-3 py-2 text-left text-sm hover:bg-surface-alt"
                onClick={() => {
                  onArchiveSession(s.id, false);
                  setActiveDropdown(null);
                }}
              >
                <ArchiveRestore className="h-4 w-4" />
                Unarchive
              </button>
            ) : (
              <button
                className="flex w-full items-center gap-3 rounded-md px-3 py-2 text-left text-sm hover:bg-surface-alt"
                onClick={() => {
                  onArchiveSession(s.id, true);
                  setActiveDropdown(null);
                }}
              >
                <Archive className="h-4 w-4" />
                Archive
              </button>
            )}
            <div className="my-1 h-px bg-border" />
            <button
              className="flex w-full items-center gap-3 rounded-md px-3 py-2 text-left text-sm text-destructive hover:bg-destructive/10"
              onClick={() => {
                if (window.confirm("Delete this chat? This cannot be undone.")) {
                  onDeleteSession(s.id);
                }
                setActiveDropdown(null);
              }}
            >
              <Trash2 className="h-4 w-4" />
              Delete
            </button>
          </div>
        )}
      </div>
    );
  };

  return (
    <div className={`flex h-[calc(100vh-4rem)] ${collapsed ? "w-14" : "w-64"} flex-col border-r bg-surface transition-all duration-300`}>
      <div className={`flex items-center gap-2 p-3 ${collapsed ? "flex-col" : "flex-row"}`}>
        <button
          onClick={onNewSession}
          className={`flex items-center justify-center gap-2 rounded-lg bg-primary px-3 py-2 text-sm font-medium text-primary-foreground hover:bg-primary-hover ${collapsed ? "w-full" : "flex-1"}`}
          title="New Chat"
        >
          <Plus className="h-4 w-4" />
          {!collapsed && <span>New Chat</span>}
        </button>
        <button
          onClick={(e) => {
            e.preventDefault();
            e.stopPropagation();
            console.log('Sidebar toggle clicked, collapsed:', collapsed);
            onToggleCollapsed();
          }}
          className="rounded-lg border bg-background p-2 hover:bg-surface-alt"
          title={collapsed ? "Expand" : "Collapse"}
        >
          {collapsed ? <ChevronRight className="h-4 w-4" /> : <ChevronLeft className="h-4 w-4" />}
        </button>
      </div>

      {!collapsed && (
        <div className="px-3 pb-3">
          <div className="relative">
            <Search className="pointer-events-none absolute left-2 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
            <input
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="Search chats..."
              className="w-full rounded-lg border bg-background py-2 pl-8 pr-3 text-sm focus:outline-none focus:ring-2 focus:ring-ring"
            />
          </div>
        </div>
      )}

      <div className="flex-1 overflow-y-auto px-2 pb-2">
        {!collapsed && activeList.filter(filterFn).length > 0 && (
          <div className="px-2 pb-1 text-xs font-semibold uppercase text-muted-foreground">Recent</div>
        )}
        <div className="space-y-1">
          {activeList.filter(filterFn).length === 0 ? (
            !collapsed && <div className="px-2 py-8 text-center text-sm text-muted-foreground">No chats — start a new one!</div>
          ) : (
            activeList.filter(filterFn).map(renderRow)
          )}
        </div>

        {archivedList.filter(filterFn).length > 0 && !collapsed && (
          <div className="mt-4">
            <div className="px-2 pb-1 text-xs font-semibold uppercase text-muted-foreground">Archived</div>
            <div className="space-y-1">{archivedList.filter(filterFn).map(renderRow)}</div>
          </div>
        )}
      </div>

      {/* Settings Section */}
      <div className="border-t p-3">
        <button
          className={`flex w-full items-center gap-3 rounded-lg px-3 py-2 text-left text-sm transition-colors hover:bg-surface-alt ${
            collapsed ? "justify-center" : ""
          }`}
          title="Settings"
        >
          <Settings className="h-4 w-4 flex-shrink-0" />
          {!collapsed && <span>Settings</span>}
        </button>
      </div>

      {/* Details Modal */}
      {showDetails && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
          <div className="details-modal relative w-full max-w-md rounded-lg border bg-background p-6 shadow-lg">
            <button
              onClick={() => setShowDetails(null)}
              className="absolute right-4 top-4 text-muted-foreground hover:text-foreground"
            >
              ×
            </button>
            <h3 className="mb-4 text-lg font-semibold">Chat Details</h3>
            {(() => {
              const session = sessions.find(s => s.id === showDetails);
              const messages = messagesBySession[showDetails || ""] || [];
              if (!session) return null;
              
              return (
                <div className="space-y-4">
                  <div>
                    <label className="text-sm font-medium text-muted-foreground">Title</label>
                    <p className="text-sm">{session.title || "Untitled"}</p>
                  </div>
                  <div>
                    <label className="text-sm font-medium text-muted-foreground">Created</label>
                    <p className="text-sm">{formatTimestamp(session.updatedAt)}</p>
                  </div>
                  <div>
                    <label className="text-sm font-medium text-muted-foreground">Messages</label>
                    <p className="text-sm">{messages.length} message{messages.length !== 1 ? 's' : ''}</p>
                  </div>
                  <div>
                    <label className="text-sm font-medium text-muted-foreground">Status</label>
                    <p className="text-sm">{session.archived ? "Archived" : "Active"}</p>
                  </div>
                </div>
              );
            })()}
          </div>
        </div>
      )}
    </div>
  );
}

