import { FolderGit2, Plus, ArrowUp } from "lucide-react";

interface EmptyStateProps {
  onAddProject: () => void;
}

export default function EmptyState({ onAddProject }: EmptyStateProps) {
  return (
    <div className="flex h-full items-center justify-center p-4 md:p-8">
      <div className="w-full max-w-2xl space-y-6 text-center md:space-y-8">
        <div className="space-y-3 md:space-y-4">
          <div className="mx-auto flex h-16 w-16 items-center justify-center rounded-full bg-surface-alt">
            <FolderGit2 className="h-8 w-8 text-muted-foreground" />
          </div>
          <h2 className="text-2xl font-bold md:text-3xl">Welcome to CodeGrapher-AI</h2>
          <p className="mx-auto max-w-xl px-4 text-base text-muted-foreground md:text-lg">
            Get started by adding your first project. We'll analyze your codebase and help you understand, test, and improve your code.
          </p>
        </div>

        <div className="mx-auto w-full max-w-lg space-y-4">
          <div className="rounded-lg border bg-surface p-4 text-left text-sm text-muted-foreground">
            <h3 className="mb-2 font-medium text-foreground">How to get started:</h3>
            <ol className="list-decimal pl-5 space-y-1">
              <li>Paste a Git repository URL in the input field above</li>
              <li>Wait for the project to be indexed (this may take a few minutes)</li>
              <li>Start asking questions about your codebase</li>
            </ol>
          </div>

          <button
            onClick={onAddProject}
            className="group mx-auto flex w-full max-w-sm items-center justify-center gap-3 rounded-lg border-2 border-dashed border-primary/30 bg-primary/5 px-6 py-4 text-primary transition-all hover:border-primary/50 hover:bg-primary/10 focus:outline-none focus:ring-2 focus:ring-ring"
          >
            <Plus className="h-5 w-5" />
            <span className="font-medium">Add Your First Project</span>
            <ArrowUp className="h-4 w-4 opacity-60" />
          </button>

          <p className="text-xs text-muted-foreground">
            Supported: GitHub, GitLab, Bitbucket, and other Git repositories
          </p>
        </div>
      </div>
    </div>
  );
}
