"use client";

import { useState } from "react";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { AlertTriangle, RefreshCw, Settings, ArrowRight, Loader2 } from "lucide-react";
import api from "@/lib/api";

/**
 * MODEL_MISMATCH error structure from backend
 */
export interface ModelMismatchError {
  error: "MODEL_MISMATCH";
  message: string;
  dataset_id: string;
  embedded_with_model: string;
  embedded_with_dimension: number;
  current_model: string;
  current_dimension: number;
  embedded_rows: number;
  actions: {
    use_previous: string;
    reembed: string;
  };
  reembed_endpoint: string;
}

interface ModelMismatchModalProps {
  /** Whether the modal is open */
  open: boolean;
  /** Close handler */
  onClose: () => void;
  /** The MODEL_MISMATCH error data */
  error: ModelMismatchError | null;
  /** Callback when user chooses to use the previous model */
  onUsePreviousModel?: (model: string) => void;
  /** Callback when user chooses to re-embed */
  onReembed?: (datasetId: string, taskId: string) => void;
}

/**
 * ModelMismatchModal - Displays when user tries to search with a different model
 * 
 * Shows:
 * - Warning message explaining the mismatch
 * - Current model vs embedded model comparison
 * - Two action buttons:
 *   1. "Use Previous Model" - Switch user's model setting
 *   2. "Re-Embed Dataset" - Start re-embedding with current model
 */
export function ModelMismatchModal({
  open,
  onClose,
  error,
  onUsePreviousModel,
  onReembed,
}: ModelMismatchModalProps) {
  const [isReembedding, setIsReembedding] = useState(false);
  const [isSwitching, setIsSwitching] = useState(false);

  if (!error) return null;

  const handleUsePreviousModel = async () => {
    try {
      setIsSwitching(true);
      
      // Update user's embedding model setting
      await api.post("/api/v1/datasets/settings/embedding-model", {
        model_name: error.embedded_with_model,
      });
      
      // Callback to parent
      if (onUsePreviousModel) {
        onUsePreviousModel(error.embedded_with_model);
      }
      
      onClose();
    } catch (err) {
      console.error("Failed to switch model:", err);
    } finally {
      setIsSwitching(false);
    }
  };

  const handleReembed = async () => {
    try {
      setIsReembedding(true);
      
      // Trigger re-embedding
      const response = await api.reembedDataset(error.dataset_id, {
        model: error.current_model,
        force: true,
        chunk_size: 100,
      });
      
      const taskId = response.celery_task_id;
      
      // Callback to parent with task ID for progress tracking
      if (onReembed) {
        onReembed(error.dataset_id, taskId);
      }
      
      onClose();
    } catch (err) {
      console.error("Failed to start re-embedding:", err);
    } finally {
      setIsReembedding(false);
    }
  };

  return (
    <Dialog open={open} onOpenChange={(open) => !open && onClose()}>
      <DialogContent className="sm:max-w-lg">
        <DialogHeader>
          <div className="flex items-center gap-3">
            <div className="flex h-10 w-10 items-center justify-center rounded-full bg-amber-100 dark:bg-amber-900/30">
              <AlertTriangle className="h-5 w-5 text-amber-600 dark:text-amber-400" />
            </div>
            <DialogTitle className="text-xl">Embedding Model Mismatch</DialogTitle>
          </div>
          <DialogDescription className="mt-2 text-base">
            {error.message}
          </DialogDescription>
        </DialogHeader>

        {/* Model Comparison */}
        <div className="mt-4 rounded-lg border bg-muted/50 p-4">
          <div className="flex items-center justify-between">
            {/* Embedded Model */}
            <div className="flex flex-col items-center gap-2">
              <span className="text-xs font-medium uppercase text-muted-foreground">
                Dataset Embedded With
              </span>
              <Badge variant="secondary" className="text-sm font-mono">
                {error.embedded_with_model}
              </Badge>
              <span className="text-xs text-muted-foreground">
                Dimension: {error.embedded_with_dimension}
              </span>
            </div>

            {/* Arrow */}
            <div className="flex flex-col items-center">
              <span className="text-xs text-red-500 font-medium">≠</span>
              <ArrowRight className="h-4 w-4 text-muted-foreground" />
            </div>

            {/* Current Model */}
            <div className="flex flex-col items-center gap-2">
              <span className="text-xs font-medium uppercase text-muted-foreground">
                Your Current Model
              </span>
              <Badge variant="outline" className="text-sm font-mono border-amber-500">
                {error.current_model}
              </Badge>
              <span className="text-xs text-muted-foreground">
                Dimension: {error.current_dimension}
              </span>
            </div>
          </div>
        </div>

        {/* Stats */}
        <div className="mt-4 flex items-center justify-center gap-4 text-sm text-muted-foreground">
          <span>
            <strong className="text-foreground">{error.embedded_rows.toLocaleString()}</strong> rows embedded
          </span>
        </div>

        {/* Actions Explanation */}
        <div className="mt-4 space-y-2 text-sm">
          <div className="flex items-start gap-2">
            <Settings className="h-4 w-4 mt-0.5 text-blue-500" />
            <p>
              <strong>Use Previous Model:</strong> Switch your model settings to{" "}
              <code className="bg-muted px-1 rounded">{error.embedded_with_model}</code> and retry search.
            </p>
          </div>
          <div className="flex items-start gap-2">
            <RefreshCw className="h-4 w-4 mt-0.5 text-green-500" />
            <p>
              <strong>Re-Embed Dataset:</strong> Delete existing embeddings and re-embed all{" "}
              {error.embedded_rows} rows with{" "}
              <code className="bg-muted px-1 rounded">{error.current_model}</code>.
              This may take several minutes.
            </p>
          </div>
        </div>

        <DialogFooter className="mt-6 flex gap-3 sm:gap-3">
          <Button
            variant="outline"
            onClick={handleUsePreviousModel}
            disabled={isSwitching || isReembedding}
            className="flex-1"
          >
            {isSwitching ? (
              <>
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                Switching...
              </>
            ) : (
              <>
                <Settings className="mr-2 h-4 w-4" />
                Use Previous Model
              </>
            )}
          </Button>
          <Button
            onClick={handleReembed}
            disabled={isSwitching || isReembedding}
            className="flex-1"
          >
            {isReembedding ? (
              <>
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                Starting...
              </>
            ) : (
              <>
                <RefreshCw className="mr-2 h-4 w-4" />
                Re-Embed Dataset
              </>
            )}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}

export default ModelMismatchModal;
