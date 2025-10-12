import { useState, useRef, useEffect } from "react";
import { Send, Bot, Square } from "lucide-react";
import Message from "./Message";
import WelcomeScreen from "./WelcomeScreen";
import EmptyState from "./EmptyState";
import { ConfirmationDialog } from "@/components/ui/confirmation-dialog";
import { Tooltip, TooltipContent, TooltipTrigger } from "@/components/ui/tooltip";

export interface ChatMessage {
  role: "user" | "assistant";
  content: string;
  thoughts?: Array<{ 
    type: string; 
    content: string; 
    icon?: string; 
    label?: string; 
    tool_name?: string; 
  }>;
  createdAt?: number;
}

interface ChatWindowProps {
  selectedProject: string;
  apiBaseUrl: string;
  messages: ChatMessage[];
  onMessagesChange: (messages: ChatMessage[]) => void;
  onFirstUserMessage?: (text: string) => void;
  sessionId?: string | null;
  projects: string[];
  onAddProject: () => void;
}

export default function ChatWindow({ selectedProject, apiBaseUrl, messages, onMessagesChange, onFirstUserMessage, sessionId, projects, onAddProject }: ChatWindowProps) {
  const [input, setInput] = useState("");
  const [isStreaming, setIsStreaming] = useState(false);
  // --- UPGRADE: State to hold live thoughts for the in-progress response ---
  const [currentThoughts, setCurrentThoughts] = useState<string[]>([]);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const messagesRef = useRef<ChatMessage[]>(messages);
  const abortControllerRef = useRef<AbortController | null>(null);
  const [clearDialogOpen, setClearDialogOpen] = useState(false);

  useEffect(() => { messagesRef.current = messages; }, [messages]);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, currentThoughts]); // Also scroll when new thoughts appear

  const handleSend = async (inputText: string = input) => {
    if (!inputText.trim() || !selectedProject || isStreaming) return;
    
    // Ensure we have a session ID before proceeding
    if (!sessionId) {
      console.error('No session ID available, cannot send message');
      return;
    }

    const userMessage: ChatMessage = { role: "user", content: inputText.trim(), createdAt: Date.now() };
    // Build next messages array synchronously with user + placeholder assistant
    const next: ChatMessage[] = [
      ...messagesRef.current,
      userMessage,
      { role: "assistant", content: "", createdAt: Date.now() },
    ];
    messagesRef.current = next;
    // IMPORTANT: Fire first-message callback BEFORE persisting messages
    // so the parent can create/select a session once, avoiding duplicates.
    if (next.length === 2 && onFirstUserMessage) {
      onFirstUserMessage(inputText.trim());
    }
    onMessagesChange(next);
    setInput("");
    setIsStreaming(true);
    // --- UPGRADE: Clear previous live thoughts ---
    setCurrentThoughts([]);

    let assistantMessageContent = "";
    const thoughts: Array<{ 
      type: string; 
      content: string; 
      icon?: string; 
      label?: string; 
      tool_name?: string; 
    }> = [];

    try {
      const controller = new AbortController();
      abortControllerRef.current = controller;
      console.log('Sending request with session ID:', sessionId);
      const response = await fetch(`${apiBaseUrl}/query`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          question: inputText.trim(),
          project_id: selectedProject,
          session_id: sessionId || undefined,
        }),
        signal: controller.signal,
      });

      if (!response.ok || !response.body) throw new Error("Failed to start stream");
      
      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let buffer = "";

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        // Support both \n\n and \r\n\r\n separators
        const events = buffer.split(/\r?\n\r?\n/);
        buffer = events.pop() || "";

        for (const eventStr of events) {
          // Collect all data: lines within the event block, join with \n
          const lines = eventStr.split(/\r?\n/);
          const dataLines: string[] = [];
          for (const line of lines) {
            if (line.startsWith("data:")) {
              dataLines.push(line.slice(5).trimStart()); // supports both "data:" and "data: "
            }
          }
          if (dataLines.length === 0) continue;
          const payload = dataLines.join("\n").trim();
          if (!payload || payload === "[DONE]") continue;

          try {
            const parsed = JSON.parse(payload);
            if (parsed.type === "chunk" && parsed.content) {
              assistantMessageContent += parsed.content;
            } else if (parsed.type === "thought" && parsed.content) {
              // Legacy thought format - keep for backward compatibility
              thoughts.push({ type: parsed.type, content: parsed.content });
              setCurrentThoughts((prev) => [...prev, parsed.content]);
            } else if (parsed.type === "agent_thought" && parsed.content) {
              // New structured agent thought
              const thoughtContent = `${parsed.icon} ${parsed.content}`;
              thoughts.push({ type: parsed.type, content: thoughtContent, icon: parsed.icon, label: parsed.label });
              setCurrentThoughts((prev) => [...prev, thoughtContent]);
            } else if (parsed.type === "tool_start" && parsed.content) {
              // Tool start event
              const toolContent = `${parsed.icon} ${parsed.content}`;
              thoughts.push({ type: parsed.type, content: toolContent, icon: parsed.icon, label: parsed.label, tool_name: parsed.tool_name });
              setCurrentThoughts((prev) => [...prev, toolContent]);
            } else if (parsed.type === "tool_result" && parsed.content) {
              // Tool result event
              const resultContent = `${parsed.icon} ${parsed.content}`;
              thoughts.push({ type: parsed.type, content: resultContent, icon: parsed.icon, label: parsed.label, tool_name: parsed.tool_name });
              setCurrentThoughts((prev) => [...prev, resultContent]);
            } else if (parsed.type === "error" && parsed.content) {
              // Handle error events from the backend
              const errUpdated = [...messagesRef.current];
              const lastIndex = errUpdated.length - 1;
              if (lastIndex >= 0 && errUpdated[lastIndex].role === "assistant") {
                errUpdated[lastIndex] = { ...errUpdated[lastIndex], content: parsed.content };
              } else {
                errUpdated.push({ role: "assistant", content: parsed.content, createdAt: Date.now() });
              }
              messagesRef.current = errUpdated;
              onMessagesChange(errUpdated);
              return; // Exit early on error
            }

            const updated = [...messagesRef.current];
            const lastIndex = updated.length - 1;
            if (lastIndex >= 0 && updated[lastIndex].role === "assistant") {
              updated[lastIndex] = {
                ...updated[lastIndex],
                content: assistantMessageContent,
                thoughts: thoughts.length > 0 ? thoughts : undefined,
              };
              messagesRef.current = updated;
              onMessagesChange(updated);
            }
          } catch (e) {
            console.error("Failed to parse SSE JSON:", e);
          }
        }
      }
    } catch (error) {
      console.error("Error streaming response:", error);
      const errUpdated = [...messagesRef.current];
      // If there's no assistant placeholder yet, add one; else replace content
      const lastIndex = errUpdated.length - 1;
      if (lastIndex >= 0 && errUpdated[lastIndex].role === "assistant") {
        errUpdated[lastIndex] = { ...errUpdated[lastIndex], content: "Something went wrong while processing your request. Please try again or contact support if the issue persists." };
      } else {
        errUpdated.push({ role: "assistant", content: "Something went wrong while processing your request. Please try again or contact support if the issue persists.", createdAt: Date.now() });
      }
      messagesRef.current = errUpdated;
      onMessagesChange(errUpdated);
    } finally {
      setIsStreaming(false);
      // --- UPGRADE: Clear the live thoughts display on completion ---
      setCurrentThoughts([]);
      abortControllerRef.current = null;
    }
  };

  const handleStop = () => {
    if (!isStreaming) return;
    try {
      abortControllerRef.current?.abort();
    } catch {}
    setIsStreaming(false);
    setCurrentThoughts([]);
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  // Clear conversation handler (exposed via custom event for now)
  useEffect(() => {
    const onClear = () => {
      if (!messagesRef.current.length) return;
      setClearDialogOpen(true);
    };
    (window as any).__cgClearConversation = onClear;
    return () => { delete (window as any).__cgClearConversation; };
  }, []);

  const handleConfirmClear = () => {
    onMessagesChange([]);
    setClearDialogOpen(false);
  };

  // Keyboard shortcut: Cmd/Ctrl+K to focus input
  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      const isMac = navigator.platform.toUpperCase().indexOf('MAC') >= 0;
      const modKey = isMac ? e.metaKey : e.ctrlKey;
      if (modKey && (e.key === 'k' || e.key === 'K')) {
        e.preventDefault();
        textareaRef.current?.focus();
      }
    };
    window.addEventListener('keydown', onKey);
    return () => window.removeEventListener('keydown', onKey);
  }, []);

  return (
    <div className="flex h-[calc(100vh-8.5rem)] flex-col">
      <div className="flex-1 overflow-y-auto">
        <div className="container mx-auto max-w-4xl">
          {projects.length === 0 ? (
              <EmptyState onAddProject={onAddProject} />
            ) : messages.length === 0 ? (
              <WelcomeScreen onExampleClick={(prompt) => handleSend(prompt)} />
            ) : (
            <div className="px-4">
              {messages.map((msg, idx) => (
                <Message key={idx} role={msg.role} content={msg.content} thoughts={msg.thoughts} createdAt={msg.createdAt} />
              ))}

              {/* --- ENHANCED: Live "Working on it..." display with structured events --- */}
              {isStreaming && currentThoughts.length > 0 && (
                <div className="flex gap-3 py-6 md:gap-4">
                  <div className="h-8 w-8 flex-shrink-0 rounded-lg flex items-center justify-center bg-gradient-to-br from-primary to-primary-hover">
                    <Bot className="h-5 w-5 text-primary-foreground" />
                  </div>
                  <div className="flex-1 space-y-2">
                    <div className="rounded-lg border bg-surface-alt p-3 text-left">
                      <p className="mb-3 text-sm font-semibold text-foreground">Working on it...</p>
                      <div className="space-y-2">
                        {currentThoughts.map((thought, idx) => {
                          // Extract icon and content from the thought string
                          const iconMatch = thought.match(/^([^\s]+)\s(.+)$/);
                          const icon = iconMatch ? iconMatch[1] : "🤔";
                          const content = iconMatch ? iconMatch[2] : thought;
                          
                          return (
                            <div key={idx} className="flex items-start gap-2 text-xs">
                              <span className="text-base flex-shrink-0 mt-0.5">{icon}</span>
                              <div className="flex-1 min-w-0">
                                <span className="text-muted-foreground whitespace-pre-wrap break-words">
                                  {content}
                                </span>
                              </div>
                            </div>
                          );
                        })}
                      </div>
                    </div>
                  </div>
                </div>
              )}
              {/* --- End of Enhanced Display --- */}
              
              <div ref={messagesEndRef} />
            </div>
            )}
        </div>
      </div>

      <div className="border-t bg-surface/80 backdrop-blur-lg">
        <div className="container mx-auto max-w-4xl px-4 py-4">
          <div className="relative flex items-end gap-3">
            <textarea
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={handleKeyDown}
              ref={textareaRef}
              placeholder={selectedProject ? "Ask anything about the codebase..." : "Select a project to begin..."}
              disabled={!selectedProject}
              rows={1}
              className="flex-1 resize-none rounded-2xl border bg-background px-4 py-3 pr-12 text-sm focus:outline-none focus:ring-2 focus:ring-ring disabled:cursor-not-allowed disabled:opacity-50"
              style={{ minHeight: "52px", maxHeight: "200px" }}
            />
            <Tooltip>
              <TooltipTrigger asChild>
                <button
                  onClick={() => (isStreaming ? handleStop() : handleSend())}
                  disabled={!selectedProject || (!input.trim() && !isStreaming)}
                  className="absolute bottom-2 right-2 rounded-lg bg-primary p-2 text-primary-foreground hover:bg-primary-hover disabled:cursor-not-allowed disabled:opacity-50"
                >
                  {isStreaming ? (
                    <Square className="h-5 w-5" />
                  ) : (
                    <Send className="h-5 w-5" />
                  )}
                </button>
              </TooltipTrigger>
              <TooltipContent side="top">
                <p>{isStreaming ? "Stop" : "Send"}</p>
              </TooltipContent>
            </Tooltip>
          </div>
        </div>
      </div>
      
      <ConfirmationDialog
        open={clearDialogOpen}
        onOpenChange={setClearDialogOpen}
        title="Clear Conversation"
        description="Clear this conversation? This cannot be undone."
        confirmText="Clear"
        cancelText="Cancel"
        onConfirm={handleConfirmClear}
        variant="destructive"
      />
    </div>
  );
}