import { useState } from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { User, Bot, ChevronDown, Brain } from "lucide-react";

// --- NEW IMPORTS ---
import Editor from 'react-simple-code-editor';
import { highlight, languages } from 'prismjs/components/prism-core';
import 'prismjs/components/prism-clike';
import 'prismjs/components/prism-javascript';
import 'prismjs/components/prism-python';
import 'prismjs/themes/prism-tomorrow.css'; // Or another theme

interface MessageProps {
  role: "user" | "assistant";
  content: string;
  thoughts?: Array<{ type: string; content: string }>;
}

export default function Message({ role, content, thoughts }: MessageProps) {
  const [showThoughts, setShowThoughts] = useState(false);

  return (
    <div className={`flex gap-3 py-6 md:gap-4 ${role === "user" ? "flex-row-reverse" : ""}`}>
      <div className={`h-8 w-8 flex-shrink-0 rounded-lg flex items-center justify-center ${
        role === "user" ? "bg-primary/10" : "bg-gradient-to-br from-primary to-primary-hover"
      }`}>
        {role === "user" ? <User className="h-5 w-5 text-primary" /> : <Bot className="h-5 w-5 text-primary-foreground" />}
      </div>

      <div className={`flex-1 space-y-3 ${role === "user" ? "text-right" : ""}`}>
        <div className={`inline-block w-full max-w-full rounded-2xl px-4 py-3 text-left ${
          role === "user" ? "bg-primary text-primary-foreground rounded-tr-sm" : "bg-surface border rounded-tl-sm"
        }`}>
          {role === "user" ? (
            <p className="text-sm leading-relaxed whitespace-pre-wrap break-words">{content}</p>
          ) : (
            <div className="prose prose-sm dark:prose-invert max-w-none [&>*]:break-words">
              <ReactMarkdown
                remarkPlugins={[remarkGfm]}
                components={{
                  code({ node, inline, className, children, ...props }: any) {
                    const match = /language-(\w+)/.exec(className || '');
                    const lang = match ? match[1] : 'clike';
                    const codeContent = String(children).replace(/\n$/, "");

                    return !inline ? (
                      <div className="code-editor-container">
                        <Editor
                          value={codeContent}
                          onValueChange={() => {}} // Read-only
                          highlight={(code) => highlight(code, languages[lang] || languages.clike, lang)}
                          padding={10}
                          readOnly
                          style={{
                            fontFamily: '"Fira Code", "Fira Mono", monospace',
                            fontSize: 14,
                            backgroundColor: '#2d2d2e',
                            borderRadius: '8px',
                            marginTop: '1em',
                            marginBottom: '1em',
                          }}
                        />
                      </div>
                    ) : (
                      <code className="text-sm font-semibold bg-surface-alt px-1 py-0.5 rounded" {...props}>{children}</code>
                    );
                  },
                }}
              >
                {content || "..."}
              </ReactMarkdown>
            </div>
          )}
        </div>

        {role === "assistant" && thoughts && thoughts.length > 0 && (
          <div className="space-y-2">
            <button
              onClick={() => setShowThoughts(!showThoughts)}
              className="inline-flex items-center gap-2 text-sm text-muted-foreground transition-colors hover:text-foreground"
            >
              <Brain className="h-4 w-4" />
              <span>Show Work</span>
              <ChevronDown className={`h-4 w-4 transition-transform ${showThoughts ? "rotate-180" : ""}`} />
            </button>

            {showThoughts && (
              <div className="space-y-2 rounded-lg border bg-surface-alt p-3 text-left">
                {thoughts.map((thought, idx) => (
                  <div key={idx} className="text-xs text-muted-foreground">
                    <p className="whitespace-pre-wrap break-words font-medium">{thought.content}</p>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}