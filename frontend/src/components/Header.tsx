// frontend/src/components/Header.tsx

import { useState, useEffect, useCallback, useRef } from "react";
import { FolderGit2, Plus, Loader2, AlertCircle, CheckCircle2, Trash2 } from "lucide-react";

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
  // Hovered state not needed with explicit delete button visibility in each row
  const [isProjectMenuOpen, setIsProjectMenuOpen] = useState(false);
  const projectMenuRef = useRef<HTMLDivElement | null>(null);

  // This function fetches the list of available projects from the backend.
  const fetchProjects = useCallback(async () => {
    try {
      const response = await fetch(`${apiBaseUrl}/projects`);
      if (!response.ok) throw new Error("Failed to fetch projects");
      const data: string[] = await response.json();
      console.log('Fetched projects:', data);
      console.log('Current projects state before update:', projects);
      setProjects(data);
      console.log('Projects state updated to:', data);

      // If no project is selected yet, and we have projects, select the first one.
      if (data.length > 0 && !selectedProject) {
        onProjectChange(data[0]);
      }
    } catch (error) {
      console.error("Error loading projects:", error);
      setStatusMessage("Could not load projects.");
    }
  }, [apiBaseUrl, selectedProject, onProjectChange]);

  // Function to delete a project
  const handleDeleteProject = async (projectName: string) => {
    if (!window.confirm(`Are you sure you want to delete the project "${projectName}"? This will remove all indexed data and cannot be undone.`)) {
      return;
    }

    try {
      const response = await fetch(`${apiBaseUrl}/projects/${encodeURIComponent(projectName)}`, {
        method: 'DELETE',
      });
      
      if (!response.ok) {
        throw new Error('Failed to delete project');
      }
      
      // Optimistically remove from local list for immediate UI feedback
      setProjects((prev) => prev.filter((p) => p !== projectName));
      
      // If the deleted project was selected, switch to another or clear selection
      if (selectedProject === projectName) {
        const remaining = projects.filter((p) => p !== projectName);
        onProjectChange(remaining[0] || "");
      }
      
      // Also refresh from backend to stay in sync
      await fetchProjects();
      
      setStatusMessage(`Project "${projectName}" deleted successfully.`);
      setTimeout(() => setStatusMessage(""), 3000);
    } catch (error) {
      console.error('Error deleting project:', error);
      setStatusMessage('Failed to delete project.');
      setTimeout(() => setStatusMessage(""), 3000);
    }
  };

  // The `useEffect` hook runs this function once when the component first loads.
  useEffect(() => {
    fetchProjects();
  }, [fetchProjects]);

  // Close custom dropdown on outside click
  useEffect(() => {
    const onClickOutside = (e: MouseEvent) => {
      if (!projectMenuRef.current) return;
      if (!projectMenuRef.current.contains(e.target as Node)) {
        setIsProjectMenuOpen(false);
      }
    };
    if (isProjectMenuOpen) {
      document.addEventListener('mousedown', onClickOutside);
    }
    return () => document.removeEventListener('mousedown', onClickOutside);
  }, [isProjectMenuOpen]);

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
            // Add a small delay to ensure the backend has fully processed the project
            setTimeout(() => {
              console.log('Project completed, refreshing project list...');
              fetchProjects(); // Refresh the project list on completion
            }, 1000);
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
            <div className="relative" ref={projectMenuRef}>
              <button
                type="button"
                disabled={isJobRunning || projects.length === 0}
                onClick={() => setIsProjectMenuOpen((v) => !v)}
                className="min-w-[200px] inline-flex items-center justify-between gap-2 rounded-lg border bg-background px-3 py-1.5 text-sm focus:outline-none focus:ring-2 focus:ring-ring disabled:opacity-60"
                title={selectedProject || 'Select a project...'}
              >
                <span className="truncate text-left flex-1">{selectedProject || 'Select a project...'}</span>
                <svg className="h-4 w-4 opacity-70" viewBox="0 0 20 20" fill="currentColor" aria-hidden="true"><path fillRule="evenodd" d="M5.23 7.21a.75.75 0 011.06.02L10 10.94l3.71-3.71a.75.75 0 111.08 1.04l-4.25 4.25a.75.75 0 01-1.06 0L5.21 8.27a.75.75 0 01.02-1.06z" clipRule="evenodd" /></svg>
              </button>

              {isProjectMenuOpen && (
                <div className="absolute z-50 mt-1 w-[260px] overflow-hidden rounded-lg border bg-background shadow-lg">
                  <div className="max-h-64 overflow-auto p-1">
                    {projects.length === 0 ? (
                      <div className="px-3 py-2 text-sm text-muted-foreground">No projects</div>
                    ) : (
                      projects.map((project) => {
                        const isActive = project === selectedProject;
                        return (
                          <div
                            key={project}
                            className={`group flex items-center gap-2 rounded-md px-2 py-1.5 text-sm hover:bg-surface-alt ${isActive ? 'bg-primary/10 text-primary' : ''}`}
                          >
                            <button
                              type="button"
                              className="min-w-0 flex-1 truncate text-left"
                              onClick={() => {
                                onProjectChange(project);
                                setIsProjectMenuOpen(false);
                              }}
                            >
                              {project}
                            </button>
                            <button
                              type="button"
                              className="rounded p-1 text-destructive opacity-0 transition-opacity hover:bg-destructive/10 group-hover:opacity-100"
                              title={`Delete ${project}`}
                              onClick={(e) => {
                                e.stopPropagation();
                                handleDeleteProject(project).then(() => {
                                  // If the list becomes empty or current project removed, close menu
                                  setIsProjectMenuOpen(false);
                                });
                              }}
                            >
                              <Trash2 className="h-4 w-4" />
                            </button>
                          </div>
                        );
                      })
                    )}
                  </div>
                </div>
              )}
            </div>
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