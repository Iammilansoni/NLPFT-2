"use client";

import { useEffect, useState } from "react";
import { Progress } from "@/components/ui/progress";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Loader2, CheckCircle2, XCircle, Clock, Database } from "lucide-react";
import type { EmbeddingStatus } from "@/hooks/useEmbeddings";

interface EmbeddingProgressProps {
  /** Embedding status from polling */
  status: EmbeddingStatus | null;
  /** Whether currently polling for updates */
  isPolling?: boolean;
  /** Show as compact inline indicator */
  compact?: boolean;
}

/**
 * EmbeddingProgress - Displays real-time embedding progress
 * 
 * Shows:
 * - Progress bar (0-100%)
 * - Rows processed / total
 * - Current status (pending, in_progress, completed, failed)
 * - Estimated time remaining
 */
export function EmbeddingProgress({
  status,
  isPolling = false,
  compact = false,
}: EmbeddingProgressProps) {
  const [elapsedSeconds, setElapsedSeconds] = useState(0);
  
  // Update elapsed time
  useEffect(() => {
    if (status?.status === "in_progress" && status.started_at) {
      const startTime = new Date(status.started_at).getTime();
      
      const interval = setInterval(() => {
        const now = Date.now();
        setElapsedSeconds(Math.floor((now - startTime) / 1000));
      }, 1000);
      
      return () => clearInterval(interval);
    }
  }, [status?.status, status?.started_at]);
  
  if (!status) return null;
  
  // Status badge
  const getStatusBadge = () => {
    switch (status.status) {
      case "pending":
        return (
          <Badge variant="secondary" className="gap-1">
            <Clock className="h-3 w-3" />
            Pending
          </Badge>
        );
      case "in_progress":
        return (
          <Badge variant="default" className="gap-1 bg-blue-500">
            <Loader2 className="h-3 w-3 animate-spin" />
            Embedding...
          </Badge>
        );
      case "completed":
        return (
          <Badge variant="default" className="gap-1 bg-green-500">
            <CheckCircle2 className="h-3 w-3" />
            Completed
          </Badge>
        );
      case "failed":
        return (
          <Badge variant="destructive" className="gap-1">
            <XCircle className="h-3 w-3" />
            Failed
          </Badge>
        );
      default:
        return null;
    }
  };
  
  // Format time
  const formatTime = (seconds: number) => {
    if (seconds < 60) return `${seconds}s`;
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}m ${secs}s`;
  };
  
  // Calculate ETA
  const getETA = () => {
    if (status.status !== "in_progress" || status.progress === 0) return null;
    
    const estimatedTotal = elapsedSeconds / (status.progress / 100);
    const remaining = Math.max(0, estimatedTotal - elapsedSeconds);
    
    return formatTime(Math.round(remaining));
  };
  
  // Compact mode - inline indicator
  if (compact) {
    return (
      <div className="flex items-center gap-3">
        {getStatusBadge()}
        {status.status === "in_progress" && (
          <>
            <Progress value={status.progress} className="w-24 h-2" />
            <span className="text-xs text-muted-foreground">
              {status.progress}%
            </span>
          </>
        )}
      </div>
    );
  }
  
  // Full card mode
  return (
    <Card>
      <CardHeader className="pb-2">
        <div className="flex items-center justify-between">
          <CardTitle className="text-lg flex items-center gap-2">
            <Database className="h-5 w-5" />
            Embedding Progress
          </CardTitle>
          {getStatusBadge()}
        </div>
      </CardHeader>
      <CardContent className="space-y-4">
        {/* Progress Bar */}
        <div className="space-y-2">
          <div className="flex justify-between text-sm">
            <span className="text-muted-foreground">Progress</span>
            <span className="font-medium">{status.progress}%</span>
          </div>
          <Progress value={status.progress} className="h-3" />
        </div>
        
        {/* Stats */}
        <div className="grid grid-cols-2 gap-4 text-sm">
          <div>
            <p className="text-muted-foreground">Rows Embedded</p>
            <p className="font-medium">
              {status.embedded_rows.toLocaleString()} / {status.total_rows.toLocaleString()}
            </p>
          </div>
          
          {status.embedding_model && (
            <div>
              <p className="text-muted-foreground">Model</p>
              <p className="font-mono text-xs">{status.embedding_model}</p>
            </div>
          )}
          
          {status.status === "in_progress" && (
            <>
              <div>
                <p className="text-muted-foreground">Elapsed Time</p>
                <p className="font-medium">{formatTime(elapsedSeconds)}</p>
              </div>
              
              {getETA() && (
                <div>
                  <p className="text-muted-foreground">Est. Remaining</p>
                  <p className="font-medium">{getETA()}</p>
                </div>
              )}
            </>
          )}
          
          {status.status === "completed" && status.completed_at && (
            <div>
              <p className="text-muted-foreground">Completed At</p>
              <p className="font-medium">
                {new Date(status.completed_at).toLocaleTimeString()}
              </p>
            </div>
          )}
        </div>
        
        {/* Error Message */}
        {status.status === "failed" && status.error_message && (
          <div className="rounded-md bg-destructive/10 p-3">
            <p className="text-sm text-destructive">{status.error_message}</p>
          </div>
        )}
      </CardContent>
    </Card>
  );
}

export default EmbeddingProgress;
