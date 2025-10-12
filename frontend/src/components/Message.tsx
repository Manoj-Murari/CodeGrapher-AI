import { useState } from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { User, Bot, ChevronDown, Brain, Terminal, Copy, Check } from "lucide-react";
import DeerLoader from "./DeerLoader";

import Editor from 'react-simple-code-editor';
import { highlight, languages } from 'prismjs/components/prism-core';
import 'prismjs/components/prism-clike';
import 'prismjs/components/prism-javascript';
import 'prismjs/components/prism-python';
import 'prismjs/themes/prism-tomorrow.css';

interface MessageProps {
  role: "user" | "assistant";
  content: string;
  thoughts?: Array<{ type: string; content: string }>;
  createdAt?: number;
}

export default function Message({ role, content, thoughts, createdAt }: MessageProps) {
  const [showThoughts, setShowThoughts] = useState(false);
  const [copied, setCopied] = useState(false);
  const [copiedCode, setCopiedCode] = useState(false);

  const formattedTime = createdAt
    ? new Date(createdAt).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
    : undefined;

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(content);
      setCopied(true);
      setTimeout(() => setCopied(false), 1500);
    } catch (_) {}
  };

  return (
    <div className={`flex gap-3 py-5 md:gap-4 ${role === "user" ? "flex-row-reverse" : ""}`}>
      <div className={`h-8 w-8 flex-shrink-0 rounded-lg flex items-center justify-center ${
        role === "user" ? "bg-primary/10" : "bg-gradient-to-br from-primary to-primary-hover"
      }`}>
        {role === "user" ? <User className="h-5 w-5 text-primary" /> : <Bot className="h-5 w-5 text-primary-foreground" />}
      </div>

      <div className={`flex-1 space-y-2 ${role === "user" ? "text-right" : ""}`}>
        <div className={`relative inline-block w-full max-w-full rounded-2xl px-4 py-3 text-left ${
          role === "user" ? "bg-primary text-primary-foreground rounded-tr-sm" : "bg-surface border rounded-tl-sm"
        }`}>
          {/* Header row: timestamp and copy */}
          <div className={`mb-2 flex items-center ${role === 'user' ? 'justify-end' : 'justify-between'}`}>
            {role !== 'user' && (
              <span className="text-xs font-medium text-muted-foreground">Assistant</span>
            )}
            {formattedTime && (
              <span className={`text-xs ${role === 'user' ? 'text-primary-foreground/80' : 'text-muted-foreground'}`}>{formattedTime}</span>
            )}
          </div>

          {/* Copy button */}
          <button
            onClick={handleCopy}
            aria-label="Copy message"
            className={`absolute top-2 ${role === 'user' ? 'left-2' : 'right-2'} inline-flex items-center gap-1 rounded-md border px-2 py-1 text-xs backdrop-blur hover:bg-surface-alt`}
          >
            {copied ? <Check className="h-3.5 w-3.5" /> : <Copy className="h-3.5 w-3.5" />}
            <span className="hidden sm:inline">{copied ? 'Copied' : 'Copy'}</span>
          </button>

          {role === "user" ? (
            <p className="text-sm leading-relaxed whitespace-pre-wrap break-words">{content}</p>
          ) : (
            <div className="prose prose-sm dark:prose-invert max-w-none [&>*]:break-words prose-code:bg-surface-alt prose-code:text-foreground prose-code:font-normal prose-code:px-1.5 prose-code:py-0.5 prose-code:rounded-md">
              {(!content || content.trim().length === 0) ? (
                <div className="py-1"><DeerLoader /></div>
              ) : (
              <ReactMarkdown
                remarkPlugins={[remarkGfm]}
                components={{
                  code({ node, inline, className, children, ...props }: any) {
                    const match = /language-(\w+)/.exec(className || '');
                    const lang = match ? match[1] : 'clike';
                    const codeContent = String(children).replace(/\n$/, "");

                    // Treat short, single-line fenced blocks as inline code to avoid large code boxes
                    const isSingleLine = !codeContent.includes('\n');
                    const isShortSnippet = codeContent.trim().length <= 80;

                    if (inline || (isSingleLine && isShortSnippet)) {
                      return <code {...props}>{children}</code>;
                    }

                    return (
                      <div className="relative mt-3 mb-3">
                        {/* Language header */}
                        <div className="flex items-center justify-between rounded-t-lg border border-b-0 bg-surface-alt px-3 py-2 text-xs">
                          <span className="font-medium text-muted-foreground uppercase tracking-wide">
                            {lang === 'clike' ? 'Code' : lang}
                          </span>
                          <button
                            onClick={async () => {
                              try {
                                await navigator.clipboard.writeText(codeContent);
                                setCopiedCode(true);
                                setTimeout(() => setCopiedCode(false), 1200);
                              } catch (_) {}
                            }}
                            className="inline-flex items-center gap-1 rounded-md border bg-background/80 px-2 py-1 text-xs backdrop-blur hover:bg-surface"
                            aria-label="Copy code"
                          >
                            {copiedCode ? <Check className="h-3.5 w-3.5" /> : <Copy className="h-3.5 w-3.5" />}
                            <span className="hidden sm:inline">{copiedCode ? 'Copied' : 'Copy'}</span>
                          </button>
                        </div>
                        <Editor
                          value={codeContent}
                          onValueChange={() => {}} // Read-only
                          highlight={(code) => highlight(code, languages[lang] || languages.clike, lang)}
                          padding={10}
                          readOnly
                          style={{
                            fontFamily: '"Fira Code", "Fira Mono", monospace',
                            fontSize: 13.5,
                            backgroundColor: '#0b1220',
                            borderRadius: '0 0 8px 8px',
                            // spacing via wrapper margins
                            maxHeight: '600px',
                            overflowY: 'auto',
                          }}
                        />
                      </div>
                    );
                  },
                }}
              >
                {content}
              </ReactMarkdown>
              )}
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
              <div className="space-y-2 rounded-lg border bg-surface-alt p-4 text-left">
                <h4 className="text-xs font-semibold uppercase text-foreground">Agent's Thought Process</h4>
                <div className="space-y-2 pt-2">
                  {thoughts.map((thought, idx) => (
                    <div key={idx} className="flex items-start gap-2 text-xs text-muted-foreground">
                      <Terminal className="h-3 w-3 flex-shrink-0 mt-0.5 text-primary" />
                      <p className="whitespace-pre-wrap break-words">
                        {thought.content.replace('🤔', '').trim()}
                      </p>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}