"use client";

import React, { useState, useEffect } from 'react';
import { Download, RefreshCw, Database, FileJson, FileText, Sparkles, Loader2, CheckCircle, XCircle, Clock, Zap, ChevronLeft, ChevronRight, ChevronsLeft, ChevronsRight } from 'lucide-react';

interface DatasetRecord {
  api: string;
  endpoint: string;
  nl_input: string;
  definition_of_api: string;
  paraphrase_type: string;
  embedding_model: string;
}

interface DatasetStatistics {
  total_apis: number;
  total_nl_variations: number;
  avg_variations_per_api: number;
  redis_stored_count?: number;
  redis_status?: string;
}

interface GenerationTask {
  task_id: string;
  dataset_id?: string;
  status: string;
  message: string;
  created_at?: string;
  completed_at?: string;
  statistics?: DatasetStatistics;
  files?: {
    json: string;
    jsonl: string;
    csv: string;
    summary: string;
  };
}

interface DatasetPreview {
  task_id: string;
  dataset_id?: string;
  total_records: number;
  showing: number;
  offset: number;
  limit: number;
  has_more: boolean;
  records: DatasetRecord[];
}

export default function DatasetGeneratorPage() {
  const [isGenerating, setIsGenerating] = useState(false);
  const [currentTask, setCurrentTask] = useState<GenerationTask | null>(null);
  const [previewData, setPreviewData] = useState<DatasetPreview | null>(null);
  const [allTasks, setAllTasks] = useState<GenerationTask[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [currentPage, setCurrentPage] = useState(0);
  const [pageSize] = useState(100);
  
  
  const formatError = (err: unknown): string => {
    if (typeof err === 'string') return err;
    if (err && typeof err === 'object') {
      const errorObj = err as Record<string, unknown>;
      
      if (errorObj.detail) {
        if (Array.isArray(errorObj.detail)) {
          return errorObj.detail.map((e: Record<string, unknown>) => 
            (e.msg as string) || JSON.stringify(e)
          ).join(', ');
        }
        return typeof errorObj.detail === 'string' ? errorObj.detail : JSON.stringify(errorObj.detail);
      }
      return JSON.stringify(err);
    }
    return 'An unexpected error occurred';
  };

  
  const [apiCount, setApiCount] = useState(10);
  const [nlVariations, setNlVariations] = useState(20);
  const [useLLM, setUseLLM] = useState(true); // Default to LLM (recommended)
  const [clearExistingEmbeddings, setClearExistingEmbeddings] = useState(false);
  const [apiContext, setApiContext] = useState("");

  const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

  
  useEffect(() => {
    fetchAllTasks();
  }, []);

  
  useEffect(() => {
    if (currentTask && currentTask.status === 'running') {
      const interval = setInterval(() => {
        fetchTaskStatus(currentTask.task_id);
      }, 2000);

      return () => clearInterval(interval);
    }
  }, [currentTask]);

  const fetchAllTasks = async () => {
    try {
      const response = await fetch(`${API_BASE}/api/v1/dataset/list`);
      const data = await response.json();
      setAllTasks(data.datasets || []);
    } catch (err) {
      console.error('Error fetching tasks:', err);
    }
  };

  const fetchTaskStatus = async (taskId: string) => {
    try {
      const response = await fetch(`${API_BASE}/api/v1/dataset/status/${taskId}`);
      const data = await response.json();
      setCurrentTask(data);

      if (data.status === 'completed') {
        setIsGenerating(false);
        fetchPreview(taskId);
        fetchAllTasks();
      } else if (data.status === 'failed') {
        setIsGenerating(false);
        setError(formatError(data.message || data));
      }
    } catch (err) {
      console.error('Error fetching task status:', err);
      setError(formatError(err));
    }
  };

  const fetchPreview = async (taskId: string, limit: number = 100, offset: number = 0) => {
    try {
      const response = await fetch(`${API_BASE}/api/v1/dataset/preview/${taskId}?limit=${limit}&offset=${offset}`);
      const data = await response.json();
      setPreviewData(data);
      setCurrentPage(Math.floor(offset / pageSize));
    } catch (err) {
      console.error('Error fetching preview:', err);
      setError(formatError(err));
    }
  };

  const handleNextPage = () => {
    if (previewData && currentTask && previewData.has_more) {
      const nextOffset = previewData.offset + pageSize;
      fetchPreview(currentTask.task_id, pageSize, nextOffset);
    }
  };

  const handlePrevPage = () => {
    if (previewData && currentTask && previewData.offset > 0) {
      const prevOffset = Math.max(0, previewData.offset - pageSize);
      fetchPreview(currentTask.task_id, pageSize, prevOffset);
    }
  };

  const handleFirstPage = () => {
    if (previewData && currentTask) {
      fetchPreview(currentTask.task_id, pageSize, 0);
    }
  };

  const handleLastPage = () => {
    if (previewData && currentTask) {
      const lastOffset = Math.floor((previewData.total_records - 1) / pageSize) * pageSize;
      fetchPreview(currentTask.task_id, pageSize, lastOffset);
    }
  };

  const handleGenerate = async () => {
    setIsGenerating(true);
    setError(null);
    setCurrentTask(null);
    setPreviewData(null);

    try {
      const response = await fetch(`${API_BASE}/api/v1/dataset/generate`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          api_count: apiCount,
          nl_variations_per_api: nlVariations,
          use_llm: useLLM,
          embedding_model: 'sentence-transformers/all-MiniLM-L6-v2',
          llm_model: 'microsoft/Phi-3-mini-4k-instruct',
          redis_host: 'redis', // Use Docker service name for backend container
          redis_port: 6379,
          clear_existing_embeddings: clearExistingEmbeddings,
          api_context: apiContext,
        }),
      });

      const data = await response.json();

      if (response.ok) {
        setCurrentTask(data);
        
        fetchTaskStatus(data.task_id);
      } else {
        setError(formatError(data));
        setIsGenerating(false);
      }
    } catch (err) {
      setError(formatError(err));
      setIsGenerating(false);
      console.error('Error generating dataset:', err);
    }
  };

  const handleDownload = async (taskId: string, format: string) => {
    try {
      const response = await fetch(`${API_BASE}/api/v1/dataset/download/${taskId}/${format}`);
      
      if (response.ok) {
        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `api_dataset_${taskId}.${format}`;
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
        document.body.removeChild(a);
      } else {
        setError(formatError('Failed to download file'));
      }
    } catch (err) {
      console.error('Error downloading file:', err);
      setError(formatError(err));
    }
  };

  const handleDownloadFormattedDocs = async (taskId: string) => {
    try {
      const response = await fetch(`${API_BASE}/api/v1/dataset/format-api-docs/${taskId}`);
      
      if (response.ok) {
        const data = await response.json();
        const documentation = data.documentation;
        
        // Create blob and download
        const blob = new Blob([documentation], { type: 'text/plain' });
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `api_docs_${taskId}.txt`;
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
        document.body.removeChild(a);
      } else {
        setError(formatError('Failed to generate formatted documentation'));
      }
    } catch (err) {
      console.error('Error generating formatted docs:', err);
      setError(formatError(err));
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'completed':
        return <CheckCircle className="w-5 h-5 text-green-500" />;
      case 'failed':
        return <XCircle className="w-5 h-5 text-red-500" />;
      case 'running':
        return <Loader2 className="w-5 h-5 text-blue-500 animate-spin" />;
      default:
        return <Clock className="w-5 h-5 text-gray-500" />;
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-50 to-gray-100 dark:from-gray-900 dark:to-gray-800 p-8">
      <div className="max-w-7xl mx-auto space-y-8">
        <div className="text-center space-y-4">
          <div className="flex justify-center">
            <div className="bg-gradient-to-r from-blue-500 to-purple-600 p-4 rounded-2xl">
              <Database className="w-12 h-12 text-white" />
            </div>
          </div>
          <h1 className="text-4xl font-bold text-gray-900 dark:text-white">
            API Dataset Generator
          </h1>
          <p className="text-lg text-gray-600 dark:text-gray-300 max-w-2xl mx-auto">
            Generate structured datasets for REST API documentation with NLP augmentation,
            embedding-based synthesis, and natural language variations.
          </p>
        </div>

        <div className="bg-white dark:bg-gray-800 rounded-2xl shadow-xl p-8 space-y-6">
          <h2 className="text-2xl font-semibold text-gray-900 dark:text-white flex items-center gap-2">
            <Sparkles className="w-6 h-6 text-purple-500" />
            Dataset Configuration
          </h2>

          {/* API Context Input - Optional */}
          <div className="mb-6">
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
              API Context (Optional) 🎯
            </label>
            <textarea
              value={apiContext}
              onChange={(e) => setApiContext(e.target.value)}
              placeholder="Describe the domain or type of APIs you want to generate (e.g., 'e-commerce system', 'hotel booking platform', 'healthcare management'). Leave blank for general-purpose APIs."
              rows={3}
              className="w-full px-4 py-3 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white placeholder-gray-400 dark:placeholder-gray-500 focus:ring-2 focus:ring-purple-500 focus:border-transparent resize-none"
              disabled={isGenerating}
            />
            <p className="mt-2 text-xs text-gray-500 dark:text-gray-400">
              💡 <strong>Tip:</strong> Providing context will generate domain-specific APIs using AI. For example:
              &quot;restaurant management&quot; → (create-order, update-menu, manage-reservations).
              Leave blank to use default authentication/profile APIs.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                Number of APIs
              </label>
              <input
                type="number"
                min="1"
                max="50"
                value={apiCount}
                onChange={(e) => setApiCount(parseInt(e.target.value))}
                className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-purple-500 focus:border-transparent"
                disabled={isGenerating}
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                NL Variations per API
              </label>
              <input
                type="number"
                min="5"
                max="100"
                value={nlVariations}
                onChange={(e) => setNlVariations(parseInt(e.target.value))}
                className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-purple-500 focus:border-transparent"
                disabled={isGenerating}
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                Paraphrase Method
              </label>
              <select
                value={useLLM ? 'llm' : 'rule'}
                onChange={(e) => setUseLLM(e.target.value === 'llm')}
                className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-purple-500 focus:border-transparent"
                disabled={isGenerating}
              >
                <option value="llm">LLM-based (Recommended) ⭐</option>
                <option value="rule">Rule-based (Basic, Offline Only)</option>
              </select>
              <p className="mt-2 text-sm text-gray-500 dark:text-gray-400">
                {useLLM ? (
                  <span className="flex items-center gap-1">
                    <Sparkles className="w-4 h-4 text-purple-500" />
                    High-quality natural variations using AI
                  </span>
                ) : (
                  <span className="flex items-center gap-1">
                    <Zap className="w-4 h-4 text-yellow-500" />
                    Fast but basic variations for offline use
                  </span>
                )}
              </p>
            </div>
          </div>

          {/* Redis Cleanup Option */}
          <div className="mt-4 p-4 bg-gray-50 dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700">
            <label className="flex items-start gap-3 cursor-pointer">
              <input
                type="checkbox"
                checked={clearExistingEmbeddings}
                onChange={(e) => setClearExistingEmbeddings(e.target.checked)}
                disabled={isGenerating}
                className="mt-1 w-4 h-4 text-purple-600 bg-gray-100 border-gray-300 rounded focus:ring-purple-500 dark:focus:ring-purple-600 dark:ring-offset-gray-800 focus:ring-2 dark:bg-gray-700 dark:border-gray-600 cursor-pointer"
              />
              <div className="flex-1">
                <span className="text-sm font-medium text-gray-900 dark:text-gray-100">
                  Clear existing Redis embeddings before generation
                </span>
                <p className="mt-1 text-xs text-gray-600 dark:text-gray-400">
                  🧹 When enabled, this will remove all previous embeddings from Redis before storing new ones. 
                  Use this to avoid duplicates when regenerating the same dataset. 
                  Note: Each generation creates new variations (even for the same APIs), and Redis stores them with timestamp-based unique IDs.
                </p>
              </div>
            </label>
          </div>

          <button
            onClick={handleGenerate}
            disabled={isGenerating}
            className="w-full bg-gradient-to-r from-blue-500 to-purple-600 hover:from-blue-600 hover:to-purple-700 text-white font-semibold py-3 px-6 rounded-lg transition-all duration-200 flex items-center justify-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {isGenerating ? (
              <>
                <Loader2 className="w-5 h-5 animate-spin" />
                Generating Dataset...
              </>
            ) : (
              <>
                <Sparkles className="w-5 h-5" />
                Generate Dataset
              </>
            )}
          </button>

          {error && (
            <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg p-4">
              <p className="text-red-800 dark:text-red-200">{error}</p>
            </div>
          )}
        </div>

        {currentTask && (
          <div className="bg-white dark:bg-gray-800 rounded-2xl shadow-xl p-8 space-y-4">
            <div className="flex items-center justify-between">
              <h2 className="text-2xl font-semibold text-gray-900 dark:text-white flex items-center gap-2">
                {getStatusIcon(currentTask.status)}
                Task Status
              </h2>
              <span className="text-sm text-gray-500 dark:text-gray-400">
                Task ID: {currentTask.task_id}
              </span>
            </div>

            <div className="space-y-2">
              <p className="text-gray-600 dark:text-gray-300">{currentTask.message}</p>
              
              {currentTask.statistics && (
                <>
                  <div className="grid grid-cols-3 gap-4 mt-4">
                    <div className="bg-blue-50 dark:bg-blue-900/20 rounded-lg p-4">
                      <p className="text-sm text-gray-600 dark:text-gray-400">Total APIs</p>
                      <p className="text-2xl font-bold text-blue-600 dark:text-blue-400">
                        {currentTask.statistics.total_apis}
                      </p>
                    </div>
                    <div className="bg-purple-50 dark:bg-purple-900/20 rounded-lg p-4">
                      <p className="text-sm text-gray-600 dark:text-gray-400">NL Variations</p>
                      <p className="text-2xl font-bold text-purple-600 dark:text-purple-400">
                        {currentTask.statistics.total_nl_variations}
                      </p>
                    </div>
                    <div className="bg-green-50 dark:bg-green-900/20 rounded-lg p-4">
                      <p className="text-sm text-gray-600 dark:text-gray-400">Avg per API</p>
                      <p className="text-2xl font-bold text-green-600 dark:text-green-400">
                        {currentTask.statistics.avg_variations_per_api.toFixed(1)}
                      </p>
                    </div>
                  </div>
                  
                  {/* Redis Storage Status */}
                  {currentTask.statistics.redis_status && (
                    <div className={`mt-4 p-4 rounded-lg border-2 ${
                      currentTask.statistics.redis_status === 'success' 
                        ? 'bg-emerald-50 dark:bg-emerald-900/20 border-emerald-300 dark:border-emerald-700' 
                        : currentTask.statistics.redis_status === 'configured_but_failed'
                        ? 'bg-amber-50 dark:bg-amber-900/20 border-amber-300 dark:border-amber-700'
                        : 'bg-gray-50 dark:bg-gray-800 border-gray-300 dark:border-gray-700'
                    }`}>
                      <div className="flex items-center gap-2">
                        {currentTask.statistics.redis_status === 'success' ? (
                          <>
                            <span className="text-2xl">🎉</span>
                            <div>
                              <p className="font-semibold text-emerald-800 dark:text-emerald-300">
                                Redis Vector Storage Success!
                              </p>
                              <p className="text-sm text-emerald-700 dark:text-emerald-400">
                                Successfully stored {currentTask.statistics.redis_stored_count} embeddings in Redis vector database
                              </p>
                            </div>
                          </>
                        ) : currentTask.statistics.redis_status === 'configured_but_failed' ? (
                          <>
                            <span className="text-2xl">⚠️</span>
                            <div>
                              <p className="font-semibold text-amber-800 dark:text-amber-300">
                                Redis Storage Failed
                              </p>
                              <p className="text-sm text-amber-700 dark:text-amber-400">
                                Redis is configured but no embeddings were stored. Check your Redis connection.
                              </p>
                            </div>
                          </>
                        ) : (
                          <>
                            <span className="text-2xl">ℹ️</span>
                            <div>
                              <p className="font-semibold text-gray-700 dark:text-gray-300">
                                Redis Storage Skipped
                              </p>
                              <p className="text-sm text-gray-600 dark:text-gray-400">
                                Redis is not configured. Vector search features unavailable.
                              </p>
                            </div>
                          </>
                        )}
                      </div>
                    </div>
                  )}
                </>
              )}

              {currentTask.status === 'completed' && currentTask.files && (
                <div className="flex flex-wrap gap-3 mt-4">
                  <button
                    onClick={() => handleDownload(currentTask.task_id, 'json')}
                    className="flex items-center gap-2 px-4 py-2 bg-blue-500 hover:bg-blue-600 text-white rounded-lg transition-colors"
                  >
                    <FileJson className="w-4 h-4" />
                    Download JSON
                  </button>
                  <button
                    onClick={() => handleDownload(currentTask.task_id, 'csv')}
                    className="flex items-center gap-2 px-4 py-2 bg-green-500 hover:bg-green-600 text-white rounded-lg transition-colors"
                  >
                    <FileText className="w-4 h-4" />
                    Download CSV
                  </button>
                  <button
                    onClick={() => handleDownloadFormattedDocs(currentTask.task_id)}
                    className="flex items-center gap-2 px-4 py-2 bg-orange-500 hover:bg-orange-600 text-white rounded-lg transition-colors"
                  >
                    <FileText className="w-4 h-4" />
                    Download API Docs
                  </button>
                </div>
              )}
            </div>
          </div>
        )}

        {previewData && (
          <div className="bg-white dark:bg-gray-800 rounded-2xl shadow-xl p-8 space-y-4">
            <div className="flex items-center justify-between">
              <h2 className="text-2xl font-semibold text-gray-900 dark:text-white">
                Dataset Preview
              </h2>
              <span className="text-sm text-gray-500 dark:text-gray-400">
                Showing {previewData.showing} of {previewData.total_records} records
              </span>
            </div>

            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead className="bg-gray-50 dark:bg-gray-700">
                  <tr>
                    <th className="px-4 py-3 text-left text-gray-700 dark:text-gray-300 font-medium">API</th>
                    <th className="px-4 py-3 text-left text-gray-700 dark:text-gray-300 font-medium">Natural Language Input</th>
                    <th className="px-4 py-3 text-left text-gray-700 dark:text-gray-300 font-medium">Definition of API</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-200 dark:divide-gray-700">
                  {previewData.records.map((record, index) => (
                    <tr key={index} className="hover:bg-gray-50 dark:hover:bg-gray-700/50">
                      <td className="px-4 py-3 text-gray-900 dark:text-white font-mono text-xs">
                        {record.api}
                      </td>
                      <td className="px-4 py-3 text-gray-700 dark:text-gray-300">
                        {record.nl_input}
                      </td>
                      <td className="px-4 py-3 text-gray-600 dark:text-gray-400 text-xs">
                        {record.definition_of_api.substring(0, 100)}...
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            {/* Pagination Controls */}
            <div className="flex items-center justify-between pt-4 border-t border-gray-200 dark:border-gray-700">
              <div className="text-sm text-gray-600 dark:text-gray-400">
                Showing {previewData.offset + 1} - {previewData.offset + previewData.showing} of {previewData.total_records} records
              </div>
              
              <div className="flex items-center gap-2">
                {/* First Page */}
                <button
                  onClick={handleFirstPage}
                  disabled={previewData.offset === 0}
                  className="p-2 rounded-lg bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 hover:bg-gray-200 dark:hover:bg-gray-600 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                  title="First page"
                >
                  <ChevronsLeft className="w-5 h-5" />
                </button>

                {/* Previous Page */}
                <button
                  onClick={handlePrevPage}
                  disabled={previewData.offset === 0}
                  className="p-2 rounded-lg bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 hover:bg-gray-200 dark:hover:bg-gray-600 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                  title="Previous page"
                >
                  <ChevronLeft className="w-5 h-5" />
                </button>

                {/* Page Info */}
                <span className="px-4 py-2 text-sm font-medium text-gray-700 dark:text-gray-300">
                  Page {currentPage + 1} of {Math.ceil(previewData.total_records / pageSize)}
                </span>

                {/* Next Page */}
                <button
                  onClick={handleNextPage}
                  disabled={!previewData.has_more}
                  className="p-2 rounded-lg bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 hover:bg-gray-200 dark:hover:bg-gray-600 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                  title="Next page"
                >
                  <ChevronRight className="w-5 h-5" />
                </button>

                {/* Last Page */}
                <button
                  onClick={handleLastPage}
                  disabled={!previewData.has_more}
                  className="p-2 rounded-lg bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 hover:bg-gray-200 dark:hover:bg-gray-600 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                  title="Last page"
                >
                  <ChevronsRight className="w-5 h-5" />
                </button>
              </div>
            </div>
          </div>
        )}

        {allTasks.length > 0 && (
          <div className="bg-white dark:bg-gray-800 rounded-2xl shadow-xl p-8 space-y-4">
            <div className="flex items-center justify-between">
              <h2 className="text-2xl font-semibold text-gray-900 dark:text-white">
                Previous Generations
              </h2>
              <button
                onClick={fetchAllTasks}
                className="flex items-center gap-2 px-4 py-2 text-gray-600 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg transition-colors"
              >
                <RefreshCw className="w-4 h-4" />
                Refresh
              </button>
            </div>

            <div className="space-y-3">
              {allTasks.slice(0, 5).map((task) => (
                <div
                  key={task.task_id}
                  className="border border-gray-200 dark:border-gray-700 rounded-lg p-4 hover:bg-gray-50 dark:hover:bg-gray-700/50 transition-colors"
                >
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-3">
                      {getStatusIcon(task.status)}
                      <div>
                        <p className="font-medium text-gray-900 dark:text-white">
                          Dataset {task.dataset_id || task.task_id}
                        </p>
                        <p className="text-sm text-gray-500 dark:text-gray-400">
                          {task.created_at ? new Date(task.created_at).toLocaleString() : 'N/A'}
                        </p>
                      </div>
                    </div>

                    {task.status === 'completed' && (
                      <div className="flex gap-2">
                        <button
                          onClick={() => {
                            setCurrentTask(task);
                            fetchPreview(task.task_id);
                          }}
                          className="px-3 py-1 text-sm bg-blue-500 hover:bg-blue-600 text-white rounded transition-colors"
                        >
                          View
                        </button>
                        <button
                          onClick={() => handleDownload(task.task_id, 'csv')}
                          className="px-3 py-1 text-sm bg-green-500 hover:bg-green-600 text-white rounded transition-colors"
                        >
                          <Download className="w-4 h-4" />
                        </button>
                      </div>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
