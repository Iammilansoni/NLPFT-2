/**
 * Dataset Generation Page
 * Complete workflow: Select template -> Configure -> Generate -> Download -> Embed
 */

'use client';

import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Sparkles,
  Download,
  Database,
  CheckCircle2,
  AlertCircle,
  Loader2,
  Play,
  Settings,
  FileText,
  Zap,
  TrendingUp,
  Clock,
  ChevronRight,
  RefreshCw,
} from 'lucide-react';
import { useTemplatesList } from '@/hooks/useTemplateManagement';
import {
  useGenerateDataset,
  useDatasetStatus,
  useEmbedDataset,
  useDownloadDataset,
} from '@/hooks/useDatasetManagement';

const LLM_MODELS = [
  { value: 'gpt-4', label: 'GPT-4 (Recommended)', description: 'Most accurate, slower' },
  { value: 'gpt-3.5-turbo', label: 'GPT-3.5 Turbo', description: 'Fast, good quality' },
  { value: 'claude-3-opus', label: 'Claude 3 Opus', description: 'High quality, creative' },
  { value: 'claude-3-sonnet', label: 'Claude 3 Sonnet', description: 'Balanced performance' },
  { value: 'demo', label: 'Demo (Mock Data)', description: 'For testing without API key' },
];

const EMBEDDING_MODELS = [
  { value: 'sentence-transformers/all-MiniLM-L6-v2', label: 'all-MiniLM-L6-v2 (Fast)', description: '384 dimensions' },
  { value: 'sentence-transformers/all-mpnet-base-v2', label: 'all-mpnet-base-v2', description: '768 dimensions' },
  { value: 'text-embedding-ada-002', label: 'OpenAI Ada-002', description: '1536 dimensions' },
];

export default function DatasetGenerationPage() {
  const userId = typeof window !== 'undefined' ? localStorage.getItem('userId') || 'demo-user' : 'demo-user';

  // Form state
  const [selectedTemplateId, setSelectedTemplateId] = useState('');
  const [rows, setRows] = useState(500);
  const [llmModel, setLlmModel] = useState('gpt-4');
  const [customPrompt, setCustomPrompt] = useState('');
  const [temperature, setTemperature] = useState(0.7);
  const [embeddingModel, setEmbeddingModel] = useState('sentence-transformers/all-MiniLM-L6-v2');

  // Generation state
  const [currentDatasetId, setCurrentDatasetId] = useState<string | null>(null);
  const [isPolling, setIsPolling] = useState(false);
  const [showSuccess, setShowSuccess] = useState(false);

  // Queries and mutations
  const { data: templatesData } = useTemplatesList({ status: 'approved' });
  const generateMutation = useGenerateDataset();
  const { data: statusData, isLoading: isLoadingStatus } = useDatasetStatus(
    currentDatasetId || '',
    isPolling
  );
  const embedMutation = useEmbedDataset();
  const downloadMutation = useDownloadDataset();

  const approvedTemplates = templatesData || [];
  const selectedTemplate = approvedTemplates.find(t => t.template_id === selectedTemplateId);

  // Auto-stop polling when complete
  useEffect(() => {
    if (statusData?.status === 'completed' || statusData?.status === 'failed') {
      setIsPolling(false);
      if (statusData.status === 'completed') {
        setShowSuccess(true);
        setTimeout(() => setShowSuccess(false), 5000);
      }
    }
  }, [statusData?.status]);

  const handleGenerate = async () => {
    if (!selectedTemplateId) {
      alert('Please select a template');
      return;
    }

    try {
      const response = await generateMutation.mutateAsync({
        user_id: userId,
        template_id: selectedTemplateId,
        rows,
        llm_model: llmModel,
        custom_prompt: customPrompt || undefined,
        temperature,
      });

      setCurrentDatasetId(response.dataset_id);
      setIsPolling(true);
    } catch (error: any) {
      alert(error.message || 'Failed to start generation');
    }
  };

  const handleDownload = () => {
    if (!currentDatasetId) return;
    downloadMutation.mutate({
      datasetId: currentDatasetId,
      filename: `dataset_${selectedTemplate?.api_name || 'export'}.csv`,
    });
  };

  const handleEmbed = async () => {
    if (!currentDatasetId) return;

    try {
      await embedMutation.mutateAsync({
        dataset_id: currentDatasetId,
        embedding_model: embeddingModel,
        vector_db_collection: 'api_templates',
      });
      alert('Dataset embedded successfully to Redis!');
    } catch (error: any) {
      alert(error.message || 'Failed to embed dataset');
    }
  };

  const isGenerating = generateMutation.isPending || (isPolling && statusData?.status === 'processing');
  const canDownload = statusData?.status === 'completed' && statusData.download_url;
  const canEmbed = statusData?.status === 'completed';

  return (
    <div className="min-h-screen bg-background">
      {/* Header */}
      <div className="bg-gradient-to-r from-primary/10 via-primary/5 to-transparent border-b">
        <div className="max-w-7xl mx-auto px-6 py-12">
          <div className="flex items-center gap-4 mb-4">
            <div className="p-3 bg-primary/10 rounded-xl">
              <Sparkles className="w-8 h-8 text-primary" />
            </div>
            <div>
              <h1 className="text-4xl font-bold">Dataset Generation</h1>
              <p className="text-muted-foreground mt-2">
                Generate AI-powered datasets from approved templates
              </p>
            </div>
          </div>

          {/* Status Cards */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mt-8">
            <div className="bg-card border rounded-xl p-4">
              <div className="flex items-center gap-3">
                <FileText className="w-5 h-5 text-primary" />
                <div>
                  <p className="text-sm text-muted-foreground">Templates Available</p>
                  <p className="text-2xl font-bold">{approvedTemplates.length}</p>
                </div>
              </div>
            </div>
            <div className="bg-card border rounded-xl p-4">
              <div className="flex items-center gap-3">
                <Zap className="w-5 h-5 text-warning" />
                <div>
                  <p className="text-sm text-muted-foreground">Generation Mode</p>
                  <p className="text-lg font-semibold">{LLM_MODELS.find(m => m.value === llmModel)?.label}</p>
                </div>
              </div>
            </div>
            <div className="bg-card border rounded-xl p-4">
              <div className="flex items-center gap-3">
                <TrendingUp className="w-5 h-5 text-success" />
                <div>
                  <p className="text-sm text-muted-foreground">Target Rows</p>
                  <p className="text-2xl font-bold">{rows}</p>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-6 py-8">
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Configuration Panel */}
          <div className="lg:col-span-2 space-y-6">
            {/* Step 1: Template Selection */}
            <div className="bg-card border rounded-xl p-6">
              <div className="flex items-center gap-3 mb-4">
                <div className="flex items-center justify-center w-8 h-8 rounded-full bg-primary text-white font-bold">
                  1
                </div>
                <h2 className="text-xl font-semibold">Select Template</h2>
              </div>

              <select
                value={selectedTemplateId}
                onChange={e => setSelectedTemplateId(e.target.value)}
                className="w-full px-4 py-3 bg-background border border-border rounded-lg focus:ring-2 focus:ring-primary"
                disabled={isGenerating}
              >
                <option value="">Choose a template...</option>
                {approvedTemplates.map(template => (
                  <option key={template.template_id} value={template.template_id}>
                    {template.api_name} ({template.method}) - {template.domain_tags.join(', ')}
                  </option>
                ))}
              </select>

              {selectedTemplate && (
                <motion.div
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  className="mt-4 p-4 bg-primary/5 border border-primary/20 rounded-lg"
                >
                  <p className="text-sm font-medium mb-2">{selectedTemplate.api_name}</p>
                  <p className="text-sm text-muted-foreground line-clamp-2">
                    {selectedTemplate.description}
                  </p>
                  <div className="flex gap-2 mt-3">
                    <span className="px-2 py-1 text-xs bg-primary/10 text-primary rounded">
                      {selectedTemplate.method}
                    </span>
                    {selectedTemplate.domain_tags.map(tag => (
                      <span key={tag} className="px-2 py-1 text-xs bg-muted rounded">
                        {tag}
                      </span>
                    ))}
                  </div>
                </motion.div>
              )}
            </div>

            {/* Step 2: Generation Settings */}
            <div className="bg-card border rounded-xl p-6">
              <div className="flex items-center gap-3 mb-4">
                <div className="flex items-center justify-center w-8 h-8 rounded-full bg-primary text-white font-bold">
                  2
                </div>
                <h2 className="text-xl font-semibold">Configure Generation</h2>
              </div>

              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium mb-2">Number of Rows</label>
                  <div className="flex items-center gap-4">
                    <input
                      type="range"
                      min="10"
                      max="10000"
                      step="10"
                      value={rows}
                      onChange={e => setRows(Number(e.target.value))}
                      disabled={isGenerating}
                      className="flex-1"
                    />
                    <input
                      type="number"
                      value={rows}
                      onChange={e => setRows(Number(e.target.value))}
                      disabled={isGenerating}
                      className="w-24 px-3 py-2 bg-background border border-border rounded-lg"
                    />
                  </div>
                  <p className="text-xs text-muted-foreground mt-1">
                    Estimated time: ~{Math.ceil(rows / 10)} seconds
                  </p>
                </div>

                <div>
                  <label className="block text-sm font-medium mb-2">LLM Model</label>
                  <select
                    value={llmModel}
                    onChange={e => setLlmModel(e.target.value)}
                    disabled={isGenerating}
                    className="w-full px-4 py-3 bg-background border border-border rounded-lg"
                  >
                    {LLM_MODELS.map(model => (
                      <option key={model.value} value={model.value}>
                        {model.label} - {model.description}
                      </option>
                    ))}
                  </select>
                </div>

                <div>
                  <label className="block text-sm font-medium mb-2">Temperature</label>
                  <input
                    type="range"
                    min="0"
                    max="2"
                    step="0.1"
                    value={temperature}
                    onChange={e => setTemperature(Number(e.target.value))}
                    disabled={isGenerating}
                    className="w-full"
                  />
                  <div className="flex justify-between text-xs text-muted-foreground mt-1">
                    <span>Deterministic (0.0)</span>
                    <span className="font-medium text-foreground">{temperature.toFixed(1)}</span>
                    <span>Creative (2.0)</span>
                  </div>
                </div>

                <div>
                  <label className="block text-sm font-medium mb-2">Custom Prompt (Optional)</label>
                  <textarea
                    value={customPrompt}
                    onChange={e => setCustomPrompt(e.target.value)}
                    disabled={isGenerating}
                    rows={3}
                    placeholder="Add custom instructions for data generation..."
                    className="w-full px-4 py-3 bg-background border border-border rounded-lg focus:ring-2 focus:ring-primary"
                  />
                </div>
              </div>

              <button
                onClick={handleGenerate}
                disabled={!selectedTemplateId || isGenerating}
                className="w-full mt-6 px-6 py-4 bg-primary text-white rounded-lg hover:bg-primary/90 disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2 font-semibold"
              >
                {isGenerating ? (
                  <>
                    <Loader2 className="w-5 h-5 animate-spin" />
                    Generating...
                  </>
                ) : (
                  <>
                    <Play className="w-5 h-5" />
                    Generate Dataset
                  </>
                )}
              </button>
            </div>

            {/* Step 3: Embed to Vector DB */}
            {canEmbed && (
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                className="bg-card border rounded-xl p-6"
              >
                <div className="flex items-center gap-3 mb-4">
                  <div className="flex items-center justify-center w-8 h-8 rounded-full bg-primary text-white font-bold">
                    3
                  </div>
                  <h2 className="text-xl font-semibold">Embed to Redis Vector Database</h2>
                </div>

                <div className="space-y-4">
                  <div>
                    <label className="block text-sm font-medium mb-2">Embedding Model</label>
                    <select
                      value={embeddingModel}
                      onChange={e => setEmbeddingModel(e.target.value)}
                      disabled={embedMutation.isPending}
                      className="w-full px-4 py-3 bg-background border border-border rounded-lg"
                    >
                      {EMBEDDING_MODELS.map(model => (
                        <option key={model.value} value={model.value}>
                          {model.label} - {model.description}
                        </option>
                      ))}
                    </select>
                  </div>

                  <div className="p-3 bg-primary/5 border border-primary/20 rounded-lg">
                    <p className="text-xs text-muted-foreground">
                      <strong>Redis Stack</strong> - Fast, scalable vector search with persistent storage
                    </p>
                  </div>

                  <button
                    onClick={handleEmbed}
                    disabled={embedMutation.isPending}
                    className="w-full px-6 py-3 bg-success text-white rounded-lg hover:bg-success/90 disabled:opacity-50 flex items-center justify-center gap-2"
                  >
                    {embedMutation.isPending ? (
                      <>
                        <Loader2 className="w-4 h-4 animate-spin" />
                        Embedding to Redis...
                      </>
                    ) : (
                      <>
                        <Database className="w-4 h-4" />
                        Embed to Redis
                      </>
                    )}
                  </button>
                </div>
              </motion.div>
            )}
          </div>

          {/* Status Panel */}
          <div className="lg:col-span-1">
            <div className="sticky top-4 space-y-4">
              {/* Generation Status */}
              {currentDatasetId && (
                <div className="bg-card border rounded-xl p-6">
                  <h3 className="font-semibold mb-4 flex items-center gap-2">
                    <Clock className="w-5 h-5" />
                    Generation Status
                  </h3>

                  {statusData ? (
                    <div className="space-y-4">
                      <div className="flex items-center justify-between">
                        <span className="text-sm text-muted-foreground">Status</span>
                        <span className={`px-2 py-1 text-xs rounded-full font-medium ${
                          statusData.status === 'completed' ? 'bg-success/10 text-success' :
                          statusData.status === 'failed' ? 'bg-destructive/10 text-destructive' :
                          statusData.status === 'processing' ? 'bg-warning/10 text-warning' :
                          'bg-muted text-muted-foreground'
                        }`}>
                          {statusData.status}
                        </span>
                      </div>

                      {statusData.status === 'processing' && (
                        <>
                          <div>
                            <div className="flex justify-between text-sm mb-2">
                              <span>Progress</span>
                              <span className="font-medium">{Math.round(statusData.progress * 100)}%</span>
                            </div>
                            <div className="w-full bg-muted rounded-full h-2 overflow-hidden">
                              <motion.div
                                initial={{ width: 0 }}
                                animate={{ width: `${statusData.progress * 100}%` }}
                                className="h-full bg-primary"
                              />
                            </div>
                          </div>

                          <div className="flex justify-between text-sm">
                            <span className="text-muted-foreground">Rows Generated</span>
                            <span className="font-medium">{statusData.rows_generated} / {statusData.total_rows}</span>
                          </div>
                        </>
                      )}

                      {statusData.status === 'completed' && (
                        <div className="space-y-3">
                          <div className="flex items-center gap-2 text-success">
                            <CheckCircle2 className="w-5 h-5" />
                            <span className="font-medium">Generation Complete!</span>
                          </div>
                          <div className="text-sm text-muted-foreground">
                            Generated {statusData.rows_generated} rows
                          </div>
                        </div>
                      )}

                      {statusData.status === 'failed' && (
                        <div className="flex items-center gap-2 text-destructive">
                          <AlertCircle className="w-5 h-5" />
                          <span className="text-sm">{statusData.error_message || 'Generation failed'}</span>
                        </div>
                      )}

                      {canDownload && (
                        <button
                          onClick={handleDownload}
                          disabled={downloadMutation.isPending}
                          className="w-full px-4 py-3 bg-primary text-white rounded-lg hover:bg-primary/90 disabled:opacity-50 flex items-center justify-center gap-2"
                        >
                          <Download className="w-4 h-4" />
                          Download CSV
                        </button>
                      )}
                    </div>
                  ) : (
                    <div className="flex items-center justify-center py-8">
                      <Loader2 className="w-6 h-6 animate-spin text-muted-foreground" />
                    </div>
                  )}
                </div>
              )}

              {/* Quick Stats */}
              <div className="bg-card border rounded-xl p-6">
                <h3 className="font-semibold mb-4">Quick Guide</h3>
                <div className="space-y-3 text-sm text-muted-foreground">
                  <div className="flex items-start gap-2">
                    <ChevronRight className="w-4 h-4 mt-0.5 flex-shrink-0" />
                    <span>Select an approved template</span>
                  </div>
                  <div className="flex items-start gap-2">
                    <ChevronRight className="w-4 h-4 mt-0.5 flex-shrink-0" />
                    <span>Configure rows and LLM model</span>
                  </div>
                  <div className="flex items-start gap-2">
                    <ChevronRight className="w-4 h-4 mt-0.5 flex-shrink-0" />
                    <span>Generate dataset with AI</span>
                  </div>
                  <div className="flex items-start gap-2">
                    <ChevronRight className="w-4 h-4 mt-0.5 flex-shrink-0" />
                    <span>Download CSV file</span>
                  </div>
                  <div className="flex items-start gap-2">
                    <ChevronRight className="w-4 h-4 mt-0.5 flex-shrink-0" />
                    <span>Embed into vector database</span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Success Toast */}
      <AnimatePresence>
        {showSuccess && (
          <motion.div
            initial={{ opacity: 0, y: 50 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: 50 }}
            className="fixed bottom-8 right-8 bg-success text-white px-6 py-4 rounded-xl shadow-2xl flex items-center gap-3 z-50"
          >
            <CheckCircle2 className="w-6 h-6" />
            <div>
              <p className="font-semibold">Dataset Generated!</p>
              <p className="text-sm opacity-90">Ready to download</p>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
