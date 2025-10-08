import { useState, useRef, useEffect } from "react";
import { Send, Loader2 } from "lucide-react";
import Message from "./Message";
import WelcomeScreen from "./WelcomeScreen";

interface ChatMessage {
  role: "user" | "assistant";
  content: string;
  thoughts?: Array<{ type: string; content: string }>;
}

interface ChatWindowProps {
  selectedProject: string;
  apiBaseUrl: string;
}

export default function ChatWindow({ selectedProject, apiBaseUrl }: ChatWindowProps) {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState("");
  const [isStreaming, setIsStreaming] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const handleSend = async (inputText: string = input) => {
    if (!inputText.trim() || !selectedProject || isStreaming) return;

    const userMessage: ChatMessage = { role: "user", content: inputText.trim() };
    setMessages((prev) => [...prev, userMessage]);
    setInput("");
    setIsStreaming(true);

    let assistantMessageContent = "";
    const thoughts: Array<{ type: string; content: string }> = [];

    try {
      const response = await fetch(`${apiBaseUrl}/query`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          question: inputText.trim(),
          project_id: selectedProject,
        }),
      });

      if (!response.ok || !response.body) throw new Error("Failed to start stream");
      
      setMessages((prev) => [...prev, { role: "assistant", content: "" }]);
      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let buffer = "";

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const events = buffer.split("\n\n");
        buffer = events.pop() || "";

        for (const eventStr of events) {
          if (eventStr.startsWith("data: ")) {
            const jsonStr = eventStr.slice(6).trim();
            if (jsonStr === "[DONE]") continue;

            try {
              const parsed = JSON.parse(jsonStr);
              if (parsed.type === "chunk" && parsed.content) {
                assistantMessageContent += parsed.content;
              } else if (parsed.type === "thought" && parsed.content) {
                thoughts.push({ type: parsed.type, content: parsed.content });
              }
              
              setMessages((prev) => {
                const newMessages = [...prev];
                newMessages[newMessages.length - 1] = {
                  role: "assistant",
                  content: assistantMessageContent,
                  thoughts: thoughts.length > 0 ? thoughts : undefined,
                };
                return newMessages;
              });

            } catch (e) {
              console.error("Failed to parse SSE JSON:", e);
            }
          }
        }
      }
    } catch (error) {
      console.error("Error streaming response:", error);
      setMessages((prev) => [
        ...prev,
        { role: "assistant", content: "Sorry, I encountered an error. Please check the server logs." },
      ]);
    } finally {
      setIsStreaming(false);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  return (
    <div className="flex h-[calc(100vh-8.5rem)] flex-col">
      <div className="flex-1 overflow-y-auto">
        <div className="container mx-auto max-w-4xl">
          {messages.length === 0 ? (
            <WelcomeScreen onExampleClick={(prompt) => handleSend(prompt)} />
          ) : (
            <div className="px-4">
              {messages.map((msg, idx) => (
                <Message key={idx} role={msg.role} content={msg.content} thoughts={msg.thoughts} />
              ))}
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
              placeholder={selectedProject ? "Ask anything about the codebase..." : "Select a project to begin..."}
              disabled={!selectedProject || isStreaming}
              rows={1}
              className="flex-1 resize-none rounded-xl border bg-background px-4 py-3 pr-12 text-sm focus:outline-none focus:ring-2 focus:ring-ring disabled:cursor-not-allowed disabled:opacity-50"
              style={{ minHeight: "52px", maxHeight: "200px" }}
            />
            <button
              onClick={() => handleSend()}
              disabled={!selectedProject || isStreaming || !input.trim()}
              className="absolute bottom-2 right-2 rounded-lg bg-primary p-2 text-primary-foreground hover:bg-primary-hover disabled:cursor-not-allowed disabled:opacity-50"
            >
              {isStreaming ? (
                <Loader2 className="h-5 w-5 animate-spin" />
              ) : (
                <Send className="h-5 w-5" />
              )}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}