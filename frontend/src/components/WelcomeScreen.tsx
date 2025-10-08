import { Code2, FileSearch, Sparkles } from "lucide-react";

interface WelcomeScreenProps {
  onExampleClick: (prompt: string) => void;
}

const examplePrompts = [
  {
    icon: Code2,
    title: "Explain a Function",
    prompt: "Explain the `create_app` function in `conduit/app.py`",
  },
  {
    icon: FileSearch,
    title: "Generate Unit Tests",
    prompt: "Generate unit tests for the `set_password` function in the `conduit/user/models.py` file.",
  },
  {
    icon: Sparkles,
    title: "Refactor Code",
    prompt: "In `conduit/user/models.py`, find the `set_password` function and extract the password hashing into a new function called `_hash_password`.",
  },
];

export default function WelcomeScreen({ onExampleClick }: WelcomeScreenProps) {
  return (
    <div className="flex h-full items-center justify-center p-4 md:p-8">
      <div className="w-full max-w-3xl space-y-6 text-center md:space-y-8">
        <div className="space-y-3 md:space-y-4">
          <h2 className="text-2xl font-bold md:text-3xl">Ready to Analyze</h2>
          <p className="mx-auto max-w-2xl px-4 text-base text-muted-foreground md:text-lg">
            Select an indexed project and ask a question to begin.
          </p>
        </div>

        <div className="mt-8 grid grid-cols-1 gap-3 md:mt-12 md:grid-cols-3 md:gap-4">
          {examplePrompts.map((example) => (
            <button
              key={example.title}
              onClick={() => onExampleClick(example.prompt)}
              className="group rounded-xl border bg-surface p-4 text-left transition-all hover:border-primary/50 hover:shadow-md md:p-6"
            >
              <div className="flex items-start gap-3 md:gap-4">
                <div className="flex-shrink-0 rounded-lg bg-surface-alt p-1.5 transition-colors group-hover:bg-primary/10 md:p-2">
                  <example.icon className="h-4 w-4 text-muted-foreground transition-colors group-hover:text-primary md:h-5 md:w-5" />
                </div>
                <div className="min-w-0 flex-1 space-y-1">
                  <h3 className="text-sm font-medium md:text-base">{example.title}</h3>
                  <p className="line-clamp-2 text-xs text-muted-foreground md:text-sm">{example.prompt}</p>
                </div>
              </div>
            </button>
          ))}
        </div>
      </div>
    </div>
  );
}