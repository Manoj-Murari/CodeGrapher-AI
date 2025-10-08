// frontend/src/components/Header.tsx

import { useState, useEffect } from "react";
import { FolderGit2, Plus, Loader2, AlertCircle, CheckCircle2 } from "lucide-react";

// Define the shape of the props this component will receive from its parent (App.tsx)
interface HeaderProps {
  onProjectChange: (projectId: string) => void;
  selectedProject: string;
  apiBaseUrl: string;
}

// Define the shape of the job status object we expect from the API
interface JobStatus {
  job_id: string;
  status: "queued" | "processing" | "completed" | "failed";
}

export default function Header({ onProjectChange, selectedProject, apiBaseUrl }: HeaderProps) {
  const [projects, setProjects] = useState<string[]>([]);
  const [gitUrl, setGitUrl] = useState("");
  const [isJobRunning, setIsJobRunning] = useState(false);
  const [jobStatus, setJobStatus] = useState<JobStatus | null>(null);
  const [statusMessage, setStatusMessage] = useState("");

  // This function fetches the list of available projects from the backend.
  const fetchProjects = async () => {
    try {
      const response = await fetch(`${apiBaseUrl}/projects`);
      if (!response.ok) throw new Error("Failed to fetch projects");
      const data: string[] = await response.json();
      setProjects(data);

      // If no project is selected yet, and we have projects, select the first one.
      if (data.length > 0 && !selectedProject) {
        onProjectChange(data[0]);
      }
    } catch (error) {
      console.error("Error loading projects:", error);
      setStatusMessage("Could not load projects.");
    }
  };

  // The `useEffect` hook runs this function once when the component first loads.
  useEffect(() => {
    fetchProjects();
  }, []);

  // This function polls the backend for the status of an indexing job.
  const pollJobStatus = (jobId: string) => {
    setIsJobRunning(true);
    const intervalId = setInterval(async () => {
      try {
        const response = await fetch(`${apiBaseUrl}/projects/status/${jobId}`);
        const data: JobStatus = await response.json();
        setJobStatus(data);
        setStatusMessage(`Status: ${data.status}...`);

        if (data.status === 'completed' || data.status === 'failed') {
          clearInterval(intervalId);
          setIsJobRunning(false);
          setJobStatus(data.status === 'completed' ? data : null);
          setStatusMessage(data.status === 'completed' ? 'Project indexed successfully!' : 'Indexing failed.');
          if (data.status === 'completed') {
            fetchProjects(); // Refresh the project list on completion
          }
          setTimeout(() => {
            setJobStatus(null);
            setStatusMessage("");
          }, 5000); // Clear the message after 5 seconds
        }
      } catch (error) {
        console.error("Error polling job status:", error);
        setStatusMessage('Error checking status.');
        clearInterval(intervalId);
        setIsJobRunning(false);
      }
    }, 3000); // Poll every 3 seconds
  };

  // This function handles the "Add Project" form submission.
  const handleAddProject = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!gitUrl.trim() || !gitUrl.endsWith('.git')) {
      setStatusMessage('Please enter a valid https Git URL ending in .git');
      return;
    }
    
    setJobStatus(null); // Clear previous status
    setStatusMessage('Submitting job...');
    
    try {
      const response = await fetch(`${apiBaseUrl}/projects`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ git_url: gitUrl }),
      });
      if (!response.ok) throw new Error("Failed to submit job");
      const data = await response.json();
      setGitUrl("");
      pollJobStatus(data.job_id);
    } catch (error) {
      console.error('Error adding project:', error);
      setStatusMessage('Failed to submit job.');
    }
  };

  return (
    <header className="sticky top-0 z-50 w-full border-b bg-surface/80 backdrop-blur-lg">
      <div className="container mx-auto flex h-16 items-center justify-between px-4">
        <div className="flex items-center gap-6">
          <div className="flex items-center gap-2">
            <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-gradient-to-br from-primary to-primary-hover">
              <FolderGit2 className="h-5 w-5 text-primary-foreground" />
            </div>
            <h1 className="text-lg font-semibold">CodeGrapher-AI</h1>
          </div>
          <div className="flex items-center gap-3">
            <select
              value={selectedProject}
              onChange={(e) => onProjectChange(e.target.value)}
              className="min-w-[180px] rounded-lg border bg-background px-3 py-1.5 text-sm focus:outline-none focus:ring-2 focus:ring-ring"
              disabled={isJobRunning || projects.length === 0}
            >
              <option value="">Select a project...</option>
              {projects.map((project) => (
                <option key={project} value={project}>{project}</option>
              ))}
            </select>
            {jobStatus && (
              <div className="flex items-center gap-2 whitespace-nowrap rounded-lg bg-surface-alt px-3 py-1.5 text-sm">
                {jobStatus.status === "completed" ? (
                  <CheckCircle2 className="h-4 w-4 text-success" />
                ) : jobStatus.status === "failed" ? (
                  <AlertCircle className="h-4 w-4 text-destructive" />
                ) : (
                  <Loader2 className="h-4 w-4 animate-spin text-primary" />
                )}
                <span className="text-muted-foreground">{statusMessage}</span>
              </div>
            )}
          </div>
        </div>

        <form onSubmit={handleAddProject} className="flex items-center gap-2">
          <input
            type="url"
            placeholder="Paste Git URL to index..."
            value={gitUrl}
            onChange={(e) => setGitUrl(e.target.value)}
            className="w-80 rounded-lg border bg-background px-3 py-1.5 text-sm focus:outline-none focus:ring-2 focus:ring-ring"
            disabled={isJobRunning}
          />
          <button
            type="submit"
            disabled={isJobRunning || !gitUrl.trim()}
            className="flex items-center gap-2 whitespace-nowrap rounded-lg bg-primary px-4 py-1.5 text-sm text-primary-foreground hover:bg-primary-hover disabled:cursor-not-allowed disabled:opacity-50"
          >
            {isJobRunning ? <Loader2 className="h-4 w-4 animate-spin" /> : <Plus className="h-4 w-4" />}
            Add Project
          </button>
        </form>
      </div>
    </header>
  );
}