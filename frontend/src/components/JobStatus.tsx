import { useState, useEffect } from "react";
import { Clock, CheckCircle2, AlertCircle, Loader2, GitBranch, Database, Network } from "lucide-react";
import { Popover, PopoverContent, PopoverTrigger } from "@/components/ui/popover";
import { Tooltip, TooltipContent, TooltipTrigger } from "@/components/ui/tooltip";

interface JobStatus {
  job_id: string;
  status: "queued" | "processing" | "completed" | "failed";
  detailed_status?: string;
  message?: string;
  result?: string;
}

interface JobStatusProps {
  jobId: string | null;
  apiBaseUrl: string;
  projectName?: string;
}

export default function JobStatus({ jobId, apiBaseUrl, projectName }: JobStatusProps) {
  const [jobStatus, setJobStatus] = useState<JobStatus | null>(null);
  const [isOpen, setIsOpen] = useState(false);

  useEffect(() => {
    if (!jobId) {
      setJobStatus(null);
      return;
    }

    const pollJobStatus = () => {
      fetch(`${apiBaseUrl}/projects/status/${jobId}`)
        .then(response => response.json())
        .then((data: JobStatus) => {
          setJobStatus(data);
          
          // Auto-close popover when job completes
          if (data.status === 'completed' || data.status === 'failed') {
            setTimeout(() => setIsOpen(false), 3000);
          }
        })
        .catch(error => {
          console.error("Error polling job status:", error);
        });
    };

    // Poll immediately
    pollJobStatus();

    // Set up polling interval
    const interval = setInterval(pollJobStatus, 2000);

    return () => clearInterval(interval);
  }, [jobId, apiBaseUrl]);

  if (!jobStatus) return null;

  const getStatusIcon = () => {
    switch (jobStatus.detailed_status || jobStatus.status) {
      case "queued":
        return <Clock className="h-4 w-4 text-muted-foreground" />;
      case "cloning":
        return <GitBranch className="h-4 w-4 text-blue-500 animate-pulse" />;
      case "indexing":
        return <Database className="h-4 w-4 text-yellow-500 animate-pulse" />;
      case "graphing":
        return <Network className="h-4 w-4 text-purple-500 animate-pulse" />;
      case "completed":
        return <CheckCircle2 className="h-4 w-4 text-green-500" />;
      case "failed":
        return <AlertCircle className="h-4 w-4 text-red-500" />;
      default:
        return <Loader2 className="h-4 w-4 text-primary animate-spin" />;
    }
  };

  const getStatusColor = () => {
    switch (jobStatus.detailed_status || jobStatus.status) {
      case "queued":
        return "text-muted-foreground";
      case "cloning":
        return "text-blue-500";
      case "indexing":
        return "text-yellow-500";
      case "graphing":
        return "text-purple-500";
      case "completed":
        return "text-green-500";
      case "failed":
        return "text-red-500";
      default:
        return "text-primary";
    }
  };

  const getStatusLabel = () => {
    switch (jobStatus.detailed_status || jobStatus.status) {
      case "queued":
        return "Queued";
      case "cloning":
        return "Cloning";
      case "indexing":
        return "Indexing";
      case "graphing":
        return "Building Graph";
      case "completed":
        return "Completed";
      case "failed":
        return "Failed";
      default:
        return "Processing";
    }
  };

  return (
    <Popover open={isOpen} onOpenChange={setIsOpen}>
      <Tooltip>
        <TooltipTrigger asChild>
          <PopoverTrigger asChild>
            <button
              className="flex items-center gap-2 rounded-lg border bg-background px-3 py-1.5 text-sm hover:bg-surface-alt transition-colors"
            >
              {getStatusIcon()}
              <span className={getStatusColor()}>{getStatusLabel()}</span>
            </button>
          </PopoverTrigger>
        </TooltipTrigger>
        <TooltipContent side="bottom">
          <p>View indexing progress</p>
        </TooltipContent>
      </Tooltip>
      
      <PopoverContent className="w-80">
        <div className="space-y-3">
          <div className="flex items-center gap-2">
            {getStatusIcon()}
            <h3 className="font-semibold text-sm">Indexing Progress</h3>
          </div>
          
          {projectName && (
            <div className="text-xs text-muted-foreground">
              Project: <span className="font-medium">{projectName}</span>
            </div>
          )}
          
          <div className="space-y-2">
            <div className="flex items-center justify-between text-sm">
              <span className="font-medium">Status:</span>
              <span className={getStatusColor()}>{getStatusLabel()}</span>
            </div>
            
            {jobStatus.message && (
              <div className="text-xs text-muted-foreground">
                {jobStatus.message}
              </div>
            )}
            
            {jobStatus.status === "completed" && (
              <div className="text-xs text-green-600 bg-green-50 dark:bg-green-900/20 p-2 rounded">
                ✅ Project indexed successfully! You can now ask questions about the codebase.
              </div>
            )}
            
            {jobStatus.status === "failed" && (
              <div className="text-xs text-red-600 bg-red-50 dark:bg-red-900/20 p-2 rounded">
                ❌ Indexing failed. Please check the repository URL and try again.
              </div>
            )}
          </div>
        </div>
      </PopoverContent>
    </Popover>
  );
}
