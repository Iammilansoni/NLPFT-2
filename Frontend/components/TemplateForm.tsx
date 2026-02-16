/**
 * Template Form Component
 * Complete working version of Postman-style template builder
 * This file is intentionally long to keep all logic in one place for easier debugging
 */

'use client';

import React, { useState, useEffect, useCallback, useRef } from 'react';
import { useRouter } from 'next/navigation';
import {
  Plus,
  Trash2,
  AlertCircle,
  CheckCircle2,
  Save,
  Send,
  Check,
  X,
  Info,
  Lock,
  Globe,
  Shield,
  ShieldAlert,
  FileCode,
  ListChecks,
  Tag,
  RefreshCw,
} from 'lucide-react';

// ============================================================================
// LOCAL STORAGE DRAFT PERSISTENCE
// ============================================================================

interface DraftData {
  formData: any;
  parameters: any[];
  headerRows: { key: string; value: string }[];
  jsonSchemaString: string;
  sampleRequestStrings: { id: number; request: string; response: string }[];
  sampleIdCounter: number;
  expectedResponses: any[];
  activeTab: 'params' | 'headers' | 'body';
  savedAt: number;
}

const DRAFT_STORAGE_PREFIX = 'nlpforge_template_draft_';
const DRAFT_DEBOUNCE_MS = 500; // Save after 0.5 second of inactivity

// Standardized word counting function - matches backend behavior
function countWords(text: string): number {
  if (!text) return 0;
  return text.trim().split(/\s+/).filter(word => word.length > 0).length;
}

// Sanitize user input to prevent XSS
function sanitizeInput(input: string): string {
  if (!input) return '';
  return input
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#x27;');
}

function getDraftStorageKey(mode: 'create' | 'edit', templateId?: string, userId?: string): string {
  const userPrefix = userId ? `${userId}_` : '';
  if (mode === 'edit' && templateId) {
    return `${DRAFT_STORAGE_PREFIX}${userPrefix}edit_${templateId}`;
  }
  return `${DRAFT_STORAGE_PREFIX}${userPrefix}create`;
}

function saveDraftToStorage(key: string, data: DraftData): void {
  if (typeof window === 'undefined') return;
  try {
    localStorage.setItem(key, JSON.stringify(data));
  } catch (e) {
    console.warn('Failed to save draft to localStorage:', e);
  }
}

function loadDraftFromStorage(key: string): DraftData | null {
  if (typeof window === 'undefined') return null;
  try {
    const saved = localStorage.getItem(key);
    if (saved) {
      return JSON.parse(saved);
    }
  } catch (e) {
    console.warn('Failed to load draft from localStorage:', e);
  }
  return null;
}

function clearDraftFromStorage(key: string): void {
  if (typeof window === 'undefined') return;
  try {
    localStorage.removeItem(key);
  } catch (e) {
    console.warn('Failed to clear draft from localStorage:', e);
  }
}
import { JsonEditor } from './JsonEditor';
import {
  HttpMethod,
  TemplateStatus,
  UserRole,
  Parameter,
  ExpectedResponse,
  SampleRequest,
  CreateTemplateRequest,
} from '@/lib/template-api';
import {
  useCreateTemplate,
  useUpdateTemplate,
  useCreateDraftTemplate,
  useUpdateDraftTemplate,
  useCreateParameters,
  useCreateExpectedResponses,
  useCreateAuditLog,
  useApproveTemplate,
} from '@/hooks/useTemplateManagement';

// Types
interface TemplateFormProps {
  mode: 'create' | 'edit';
  initialData?: Partial<CreateTemplateRequest> & {
    template_id?: string;
    parameters?: Parameter[];
    expected_responses?: ExpectedResponse[];
  };
  userId: string;
  userRole: UserRole;
  onSuccess?: (templateId: string) => void;
}

const HTTP_METHODS: HttpMethod[] = ['GET', 'POST', 'PUT', 'PATCH', 'DELETE'];
const PARAMETER_TYPES = ['string', 'number', 'integer', 'boolean', 'array', 'object'];
const SUGGESTED_TAGS = ['telecom', 'fft', 'authentication', 'payment', 'webhook'];

export function TemplateForm({
  mode,
  initialData,
  userId,
  userRole,
  onSuccess,
}: TemplateFormProps) {
  const router = useRouter();

  // Draft persistence - include userId to prevent key collisions between users
  const draftKey = getDraftStorageKey(mode, initialData?.template_id, userId);
  const [hasDraft, setHasDraft] = useState(false);
  const [lastSaved, setLastSaved] = useState<Date | null>(null);
  const [isInitialized, setIsInitialized] = useState(false);
  const saveTimeoutRef = useRef<NodeJS.Timeout | null>(null);

  // Save mutex to prevent race conditions between auto-save and manual save
  const isSavingRef = useRef(false);
  const saveQueueRef = useRef<Promise<void>>(Promise.resolve());

  // Form state
  const [formData, setFormData] = useState<CreateTemplateRequest>({
    user_id: userId,
    api_name: initialData?.api_name || '',
    description: initialData?.description || '',
    base_url: initialData?.base_url || '',
    method: initialData?.method || 'POST',
    headers: initialData?.headers || {},
    json_schema: initialData?.json_schema || {},
    sample_requests: initialData?.sample_requests || [],
    side_effects: initialData?.side_effects || '',
    domain_tags: initialData?.domain_tags || [],
    status: initialData?.status || 'draft',
    reviewer_notes: initialData?.reviewer_notes || '',
  });

  // Initialize parameters from initialData for edit mode
  const [parameters, setParameters] = useState<Omit<Parameter, 'parameter_id'>[]>(
    (initialData?.parameters || []).map(p => ({
      user_id: userId,
      template_id: initialData?.template_id || '',
      name: p.name || '',
      type: p.type || 'string',
      description: p.description || '',
      example: p.example || '',
      required: p.required || false,
    }))
  );
  const [headerRows, setHeaderRows] = useState<{ key: string; value: string }[]>(
    Object.entries(initialData?.headers || {}).map(([key, value]) => ({ key, value }))
  );
  const [activeTab, setActiveTab] = useState<'params' | 'headers' | 'body'>('params');
  const [expectedResponses, setExpectedResponses] = useState<Omit<ExpectedResponse, 'response_id'>[]>([]);
  const [jsonSchemaString, setJsonSchemaString] = useState(JSON.stringify(initialData?.json_schema || {}, null, 2));
  const [tagInput, setTagInput] = useState('');
  const [errors, setErrors] = useState<Record<string, string>>({});
  const [showApprovalModal, setShowApprovalModal] = useState(false);
  const [showDatasetWarning, setShowDatasetWarning] = useState(false);

  // Counter for unique sample request IDs
  const [sampleIdCounter, setSampleIdCounter] = useState(
    (initialData?.sample_requests?.length || 0) + 1
  );

  // Local state for sample request strings (to allow editing invalid JSON)
  // Each entry has a unique ID to avoid key collisions
  const [sampleRequestStrings, setSampleRequestStrings] = useState<{ id: number; request: string; response: string }[]>(
    (initialData?.sample_requests || []).map((s, i) => ({
      id: i + 1,
      request: JSON.stringify(s.request || {}, null, 2),
      response: JSON.stringify(s.expected_response || {}, null, 2)
    }))
  );

  // Load draft from localStorage on mount
  useEffect(() => {
    const savedDraft = loadDraftFromStorage(draftKey);
    if (savedDraft) {
      // For both create and edit mode, restore draft if it exists and is recent
      let shouldRestore = false;

      if (mode === 'create') {
        // In create mode, always restore any saved draft
        shouldRestore = true;
      } else if (mode === 'edit' && initialData?.template_id) {
        // In edit mode, auto-restore if draft is recent (within 24 hours)
        // This ensures user's unsaved work is preserved when they navigate away and return
        const draftAge = Date.now() - savedDraft.savedAt;
        const maxDraftAge = 24 * 60 * 60 * 1000; // 24 hours

        if (draftAge < maxDraftAge) {
          // Auto-restore in edit mode - user expects their work to be saved
          shouldRestore = true;
        }
      }

      if (shouldRestore) {
        setFormData(savedDraft.formData);
        setParameters(savedDraft.parameters || []);
        setHeaderRows(savedDraft.headerRows || []);
        setJsonSchemaString(savedDraft.jsonSchemaString || '{}');
        setSampleRequestStrings(savedDraft.sampleRequestStrings || []);
        setSampleIdCounter(savedDraft.sampleIdCounter || 1);
        setExpectedResponses(savedDraft.expectedResponses || []);
        if (savedDraft.activeTab) setActiveTab(savedDraft.activeTab);
        setHasDraft(true);
        setLastSaved(new Date(savedDraft.savedAt));
      }
    }
    setIsInitialized(true);
  }, [draftKey, mode, initialData?.template_id]);

  // Auto-save draft with debounce
  const saveDraft = useCallback(() => {
    if (!isInitialized) return;

    const draftData: DraftData = {
      formData,
      parameters,
      headerRows,
      jsonSchemaString,
      sampleRequestStrings,
      sampleIdCounter,
      expectedResponses,
      activeTab,
      savedAt: Date.now(),
    };

    saveDraftToStorage(draftKey, draftData);
    setHasDraft(true);
    setLastSaved(new Date());
  }, [formData, parameters, headerRows, jsonSchemaString, sampleRequestStrings, sampleIdCounter, expectedResponses, activeTab, draftKey, isInitialized]);

  // Debounced save effect
  useEffect(() => {
    if (!isInitialized) return;

    if (saveTimeoutRef.current) {
      clearTimeout(saveTimeoutRef.current);
    }

    saveTimeoutRef.current = setTimeout(() => {
      saveDraft();
    }, DRAFT_DEBOUNCE_MS);

    return () => {
      if (saveTimeoutRef.current) {
        clearTimeout(saveTimeoutRef.current);
      }
    };
  }, [formData, parameters, headerRows, jsonSchemaString, sampleRequestStrings, sampleIdCounter, expectedResponses, activeTab, saveDraft, isInitialized]);

  // Save immediately before page unload (refresh, close, navigate away)
  useEffect(() => {
    if (!isInitialized) return;

    const saveCurrentState = () => {
      // Save draft immediately
      const draftData: DraftData = {
        formData,
        parameters,
        headerRows,
        jsonSchemaString,
        sampleRequestStrings,
        sampleIdCounter,
        expectedResponses,
        activeTab,
        savedAt: Date.now(),
      };
      saveDraftToStorage(draftKey, draftData);
    };

    const handleBeforeUnload = (e: BeforeUnloadEvent) => {
      saveCurrentState();

      // Show browser warning if there's unsaved content
      if (formData.api_name || formData.description || formData.base_url || parameters.length > 0) {
        e.preventDefault();
        e.returnValue = '';
        return '';
      }
    };

    // Handle visibility change (tab switch, minimize)
    const handleVisibilityChange = () => {
      if (document.visibilityState === 'hidden') {
        saveCurrentState();
      }
    };

    // Handle page hide (more reliable for mobile and some browsers)
    const handlePageHide = () => {
      saveCurrentState();
    };

    window.addEventListener('beforeunload', handleBeforeUnload);
    document.addEventListener('visibilitychange', handleVisibilityChange);
    window.addEventListener('pagehide', handlePageHide);

    return () => {
      window.removeEventListener('beforeunload', handleBeforeUnload);
      document.removeEventListener('visibilitychange', handleVisibilityChange);
      window.removeEventListener('pagehide', handlePageHide);
    };
  }, [formData, parameters, headerRows, jsonSchemaString, sampleRequestStrings, sampleIdCounter, expectedResponses, activeTab, draftKey, isInitialized]);

  // Save and navigate back - ensures draft is saved before leaving
  const handleNavigateBack = useCallback(() => {
    // Save current state to localStorage immediately before navigating
    const draftData: DraftData = {
      formData,
      parameters,
      headerRows,
      jsonSchemaString,
      sampleRequestStrings,
      sampleIdCounter,
      expectedResponses,
      activeTab,
      savedAt: Date.now(),
    };
    saveDraftToStorage(draftKey, draftData);
    router.back();
  }, [formData, parameters, headerRows, jsonSchemaString, sampleRequestStrings, sampleIdCounter, expectedResponses, activeTab, draftKey, router]);

  // Clear draft function
  const clearDraft = useCallback(() => {
    clearDraftFromStorage(draftKey);
    setHasDraft(false);
    setLastSaved(null);

    // Reset to initial data or empty state
    setFormData({
      user_id: userId,
      api_name: initialData?.api_name || '',
      description: initialData?.description || '',
      base_url: initialData?.base_url || '',
      method: initialData?.method || 'POST',
      headers: initialData?.headers || {},
      json_schema: initialData?.json_schema || {},
      sample_requests: initialData?.sample_requests || [],
      side_effects: initialData?.side_effects || '',
      domain_tags: initialData?.domain_tags || [],
      status: initialData?.status || 'draft',
      reviewer_notes: initialData?.reviewer_notes || '',
    });
    setParameters((initialData?.parameters || []).map(p => ({
      user_id: userId,
      template_id: initialData?.template_id || '',
      name: p.name || '',
      type: p.type || 'string',
      description: p.description || '',
      example: p.example || '',
      required: p.required || false,
    })));
    setHeaderRows(Object.entries(initialData?.headers || {}).map(([key, value]) => ({ key, value })));
    setJsonSchemaString(JSON.stringify(initialData?.json_schema || {}, null, 2));
    setSampleRequestStrings(
      (initialData?.sample_requests || []).map((s, i) => ({
        id: i + 1,
        request: JSON.stringify(s.request || {}, null, 2),
        response: JSON.stringify(s.expected_response || {}, null, 2)
      }))
    );
    setSampleIdCounter((initialData?.sample_requests?.length || 0) + 1);
    setExpectedResponses([]);
    setActiveTab('params');
  }, [draftKey, initialData, userId]);

  // Mutations
  const createTemplate = useCreateTemplate();
  const updateTemplate = useUpdateTemplate();
  const createDraftTemplate = useCreateDraftTemplate();
  const updateDraftTemplate = useUpdateDraftTemplate();
  const createParametersMutation = useCreateParameters();
  const createExpectedResponsesMutation = useCreateExpectedResponses();
  const createAuditLog = useCreateAuditLog();
  const approveTemplateMutation = useApproveTemplate();

  const isLoading = createTemplate.isPending || updateTemplate.isPending || createDraftTemplate.isPending || updateDraftTemplate.isPending || approveTemplateMutation.isPending;

  // Validation
  const validate = (): boolean => {
    const newErrors: Record<string, string> = {};

    if (!formData.api_name || formData.api_name.length === 0) newErrors.api_name = 'Required';
    else if (formData.api_name.length > 120) newErrors.api_name = 'Max 120 chars';

    // Backend requires 500 words minimum - use standardized word counting
    const wordCount = countWords(formData.description || '');
    if (wordCount < 500) {
      newErrors.description = `Min 500 words (${wordCount}/500)`;
    }

    if (!formData.base_url) newErrors.base_url = 'Required';
    else {
      try {
        new URL(formData.base_url);
      } catch {
        newErrors.base_url = 'Invalid URL';
      }
    }

    try {
      const schema = JSON.parse(jsonSchemaString);
      if (!schema.type && !schema.properties) newErrors.json_schema = 'Invalid schema';
    } catch {
      newErrors.json_schema = 'Invalid JSON';
    }

    if (formData.sample_requests?.length !== 3) {
      newErrors.sample_requests = `Need 3 samples (${formData.sample_requests?.length || 0}/3)`;
    }

    if (formData.domain_tags?.length === 0) newErrors.domain_tags = 'Need at least 1 tag';

    if (parameters.length === 0) newErrors.parameters = 'Need at least 1 parameter';

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  // Handlers
  const handleFieldChange = (field: keyof CreateTemplateRequest, value: any) => {
    setFormData(prev => ({ ...prev, [field]: value }));
  };

  const addSampleRequest = () => {
    if ((formData.sample_requests?.length || 0) >= 3) return;
    const newSampleRequests = [...(formData.sample_requests || []), { request: {}, expected_response: {}, note: '' }];
    handleFieldChange('sample_requests', newSampleRequests);
    // Add new entry with unique ID
    const newId = sampleIdCounter;
    setSampleIdCounter(prev => prev + 1);
    setSampleRequestStrings(prev => [...prev, { id: newId, request: '{\n  \n}', response: '{\n  \n}' }]);
  };

  const updateSampleRequest = (index: number, field: keyof SampleRequest, value: any) => {
    const updated = formData.sample_requests?.map((s, i) =>
      i === index ? { ...s, [field]: value } : s
    );
    handleFieldChange('sample_requests', updated);
  };

  const removeSampleRequest = (index: number) => {
    handleFieldChange('sample_requests', formData.sample_requests?.filter((_, i) => i !== index));
    setSampleRequestStrings(prev => prev.filter((_, i) => i !== index));
  };

  const addTag = (tag: string) => {
    const trimmed = tag.trim();
    if (trimmed && !formData.domain_tags.includes(trimmed)) {
      handleFieldChange('domain_tags', [...formData.domain_tags, trimmed]);
      setTagInput('');
    }
  };

  const removeTag = (tag: string) => {
    handleFieldChange('domain_tags', formData.domain_tags.filter(t => t !== tag));
  };

  const updateHeaderRow = (index: number, field: 'key' | 'value', value: string) => {
    const newRows = [...headerRows];
    newRows[index][field] = value;
    setHeaderRows(newRows);

    // Update formData
    const headersObj = newRows.reduce((acc, row) => {
      if (row.key) acc[row.key] = row.value;
      return acc;
    }, {} as Record<string, string>);
    handleFieldChange('headers', headersObj);
  };

  const addHeaderRow = () => {
    setHeaderRows([...headerRows, { key: '', value: '' }]);
  };

  const removeHeaderRow = (index: number) => {
    const newRows = headerRows.filter((_, i) => i !== index);
    setHeaderRows(newRows);

    // Update formData
    const headersObj = newRows.reduce((acc, row) => {
      if (row.key) acc[row.key] = row.value;
      return acc;
    }, {} as Record<string, string>);
    handleFieldChange('headers', headersObj);
  };

  const addParameter = () => {
    setParameters([...parameters, {
      user_id: userId,
      template_id: '',
      name: '',
      type: 'string',
      description: '',
      example: '',
      required: false,
    }]);
  };

  const updateParameter = (index: number, field: keyof Parameter, value: any) => {
    setParameters(parameters.map((p, i) => i === index ? { ...p, [field]: value } : p));
  };

  const removeParameter = (index: number) => {
    setParameters(parameters.filter((_, i) => i !== index));
  };

  const addExpectedResponse = () => {
    setExpectedResponses([...expectedResponses, {
      user_id: userId,
      template_id: '',
      status: 200,
      fields: {},
    }]);
  };

  const updateExpectedResponse = (index: number, field: keyof ExpectedResponse, value: any) => {
    setExpectedResponses(expectedResponses.map((r, i) => i === index ? { ...r, [field]: value } : r));
  };

  const removeExpectedResponse = (index: number) => {
    setExpectedResponses(expectedResponses.filter((_, i) => i !== index));
  };

  // Submit handlers
  const handleSaveDraft = async () => {
    // No validation required for saving draft - allow saving incomplete templates

    try {
      // Parse JSON schema from string - use empty object if invalid
      let parsedJsonSchema = {};
      try {
        parsedJsonSchema = JSON.parse(jsonSchemaString);
      } catch {
        // Keep empty object if JSON is invalid
      }

      const dataToSubmit = {
        ...formData,
        json_schema: parsedJsonSchema,
        status: 'draft' as TemplateStatus
      };

      // Convert parameters to the format backend expects
      const parameterSchemas = parameters.map(p => ({
        name: p.name,
        type: p.type,
        description: p.description,
        example: p.example,
        required: p.required,
      }));

      if (mode === 'create') {
        const result = await createTemplate.mutateAsync({ data: dataToSubmit, parameters: parameterSchemas });
        // Clear local draft on successful save
        clearDraftFromStorage(draftKey);
        onSuccess?.(result.template_id);
        router.push('/templates');
      } else if (initialData?.template_id) {
        await updateTemplate.mutateAsync({ templateId: initialData.template_id, data: dataToSubmit, parameters: parameterSchemas });
        // Clear local draft on successful save
        clearDraftFromStorage(draftKey);
        onSuccess?.(initialData.template_id);
        router.push('/templates');
      }
    } catch (error: any) {
      alert(error.message || 'Failed to save');
    }
  };

  const handleSubmitForReview = async () => {
    // Save as draft immediately - no validation required
    // This allows users to save incomplete templates and return later

    try {
      // Parse JSON schema from string - use empty object if invalid
      let parsedJsonSchema = {};
      try {
        parsedJsonSchema = JSON.parse(jsonSchemaString);
      } catch {
        // Keep empty object if JSON is invalid
      }

      // Always save as draft first - user can submit for review from the templates list
      const dataToSubmit = {
        ...formData,
        json_schema: parsedJsonSchema,
        status: 'draft' as TemplateStatus
      };
      let templateId: string;

      // Convert parameters to the format backend expects
      const parameterSchemas = parameters.map(p => ({
        name: p.name,
        type: p.type,
        description: p.description,
        example: p.example,
        required: p.required,
      }));

      if (mode === 'create') {
        // Use draft endpoint which has relaxed validation
        const result = await createDraftTemplate.mutateAsync({ data: dataToSubmit, parameters: parameterSchemas });
        templateId = result.template_id;
      } else {
        templateId = initialData?.template_id!;
        // Use draft endpoint which has relaxed validation
        await updateDraftTemplate.mutateAsync({ templateId, data: dataToSubmit, parameters: parameterSchemas });
      }

      // Clear local draft on successful save to backend
      clearDraftFromStorage(draftKey);

      // Audit log is handled automatically by the backend
      try {
        await createAuditLog.mutateAsync({
          action: 'save_template_draft',
          user_id: userId,
          template_id: templateId,
        });
      } catch (auditError) {
        console.log('Audit log handled by backend');
      }

      onSuccess?.(templateId);
      // Redirect directly to templates list instead of preview page
      router.push('/templates');
    } catch (error: any) {
      // Parse validation errors from backend
      const detail = error?.detail
      let errorMessage = 'Failed to save template'

      if (typeof detail === 'object' && detail.errors) {
        const errorList = Array.isArray(detail.errors) ? detail.errors.join('\n') : detail.errors
        errorMessage = `${detail.message || 'Validation failed'}:\n\n${errorList}`
      } else if (typeof detail === 'string') {
        errorMessage = detail
      } else if (error?.message) {
        errorMessage = error.message
      }

      alert(errorMessage);
    }
  };

  const handleApprove = async () => {
    if (!initialData?.template_id) return;
    try {
      await approveTemplateMutation.mutateAsync(initialData.template_id);
      // Audit log is handled automatically by the backend
      try {
        await createAuditLog.mutateAsync({
          action: 'approve_template',
          user_id: userId,
          template_id: initialData.template_id,
        });
      } catch (auditError) {
        console.log('Audit log handled by backend');
      }
      setShowApprovalModal(false);
      onSuccess?.(initialData.template_id);
    } catch (error: any) {
      alert(error.message || 'Failed to approve');
    }
  };

  const canApprove = userRole === 'admin' || userRole === 'reviewer';

  // Validation summary
  const validationIssues = React.useMemo(() => {
    const issues: string[] = [];
    if (!formData.api_name) issues.push('API name missing');
    const wordCount = countWords(formData.description || '');
    if (wordCount < 500) issues.push(`Description (${wordCount}/500 words)`);
    if (!formData.base_url) issues.push('Base URL missing');
    try {
      const schema = JSON.parse(jsonSchemaString);
      if (!schema.properties && !schema.type) issues.push('JSON Schema incomplete');
    } catch {
      issues.push('JSON Schema invalid');
    }
    if (formData.sample_requests?.length !== 3) issues.push(`Samples (${formData.sample_requests?.length || 0}/3)`);
    if (formData.domain_tags?.length === 0) issues.push('No tags');
    if (parameters.length === 0) issues.push('No parameters');
    return issues;
  }, [formData, jsonSchemaString, parameters]);

  return (
    <div className="min-h-screen bg-background py-8">
      <div className="max-w-7xl mx-auto px-4">
        <div className="grid grid-cols-1 lg:grid-cols-4 gap-8">
          {/* Main Form */}
          <div className="lg:col-span-3 space-y-6">
            <div>
              <h1 className="text-3xl font-bold">{mode === 'create' ? 'Create Template' : 'Edit Template'}</h1>
              <p className="text-muted-foreground">Define your API template</p>

              {/* Auto-save Status Indicator */}
              {lastSaved && (
                <div className="mt-3 flex items-center justify-between bg-green-500/10 border border-green-500/30 rounded-lg px-4 py-2">
                  <div className="flex items-center gap-2 text-green-600 dark:text-green-400">
                    <Save className="w-4 h-4" />
                    <span className="text-sm">
                      {hasDraft ? (
                        <>Local draft restored &amp; auto-saving (last: {lastSaved.toLocaleTimeString()})</>
                      ) : (
                        <>Auto-saved locally at {lastSaved.toLocaleTimeString()}</>
                      )}
                    </span>
                  </div>
                  {hasDraft && (
                    <button
                      type="button"
                      onClick={clearDraft}
                      className="flex items-center gap-1 text-sm text-muted-foreground hover:text-foreground transition-colors"
                    >
                      <RefreshCw className="w-3 h-3" />
                      {mode === 'edit' ? 'Reload from Server' : 'Start Fresh'}
                    </button>
                  )}
                </div>
              )}
            </div>

            {/* Basic Info */}
            <div className="bg-card border rounded-xl p-6 space-y-4">
              <h2 className="text-xl font-semibold flex items-center gap-2">
                <Info className="w-5 h-5" /> Basic Information
              </h2>

              <div>
                <label className="block text-sm font-medium mb-2">
                  API Name <span className="text-destructive">*</span>
                </label>
                <input
                  type="text"
                  value={formData.api_name}
                  onChange={e => handleFieldChange('api_name', e.target.value)}
                  maxLength={120}
                  className="w-full px-4 py-3 bg-background border border-border rounded-lg focus:ring-2 focus:ring-primary"
                  placeholder="Create_fft_with_no_pilot_signal"
                />
                <div className="flex justify-between text-xs mt-1">
                  <span className="text-muted-foreground">{formData.api_name.length}/120</span>
                  {errors.api_name && <span className="text-destructive">{errors.api_name}</span>}
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium mb-2">
                  Description <span className="text-destructive">*</span>
                </label>
                <textarea
                  value={formData.description}
                  onChange={e => handleFieldChange('description', e.target.value)}
                  rows={6}
                  className="w-full px-4 py-3 bg-background border border-border rounded-lg focus:ring-2 focus:ring-primary"
                  placeholder="Detailed description (min 500 words). Include: purpose, use cases, technical context, integration details, security considerations, architecture overview, error handling, performance characteristics..."
                />
                <div className="flex justify-between text-xs mt-1">
                  <span className={countWords(formData.description || '') < 500 ? 'text-destructive' : 'text-muted-foreground'}>
                    {countWords(formData.description || '')}/500 words minimum
                  </span>
                  {errors.description && <span className="text-destructive">{errors.description}</span>}
                </div>
              </div>

              <div className="grid grid-cols-3 gap-4">
                <div className="col-span-2">
                  <label className="block text-sm font-medium mb-2">
                    Base URL <span className="text-destructive">*</span>
                  </label>
                  <input
                    type="url"
                    value={formData.base_url}
                    onChange={e => handleFieldChange('base_url', e.target.value)}
                    className="w-full px-4 py-3 bg-background border border-border rounded-lg focus:ring-2 focus:ring-primary"
                    placeholder="https://api.example.com/v1"
                  />
                  {errors.base_url && <span className="text-xs text-destructive">{errors.base_url}</span>}
                </div>
                <div>
                  <label className="block text-sm font-medium mb-2">Method <span className="text-destructive">*</span></label>
                  <select
                    value={formData.method}
                    onChange={e => handleFieldChange('method', e.target.value as HttpMethod)}
                    className="w-full px-4 py-3 bg-background border border-border rounded-lg"
                  >
                    {HTTP_METHODS.map(m => <option key={m} value={m}>{m}</option>)}
                  </select>
                </div>
              </div>
            </div>

            {/* JSON Schema */}
            <div className="bg-card border rounded-xl p-6 space-y-4">
              <h2 className="text-xl font-semibold flex items-center gap-2">
                <FileCode className="w-5 h-5" /> Request Details
              </h2>

              <div className="flex border-b">
                <button
                  type="button"
                  onClick={() => setActiveTab('params')}
                  className={`px-4 py-2 text-sm font-medium border-b-2 transition-colors ${activeTab === 'params' ? 'border-primary text-primary' : 'border-transparent text-muted-foreground hover:text-foreground'
                    }`}
                >
                  Params
                </button>
                <button
                  type="button"
                  onClick={() => setActiveTab('headers')}
                  className={`px-4 py-2 text-sm font-medium border-b-2 transition-colors ${activeTab === 'headers' ? 'border-primary text-primary' : 'border-transparent text-muted-foreground hover:text-foreground'
                    }`}
                >
                  Headers
                </button>
                <button
                  type="button"
                  onClick={() => setActiveTab('body')}
                  className={`px-4 py-2 text-sm font-medium border-b-2 transition-colors ${activeTab === 'body' ? 'border-primary text-primary' : 'border-transparent text-muted-foreground hover:text-foreground'
                    }`}
                >
                  Body
                </button>
              </div>

              <div className="pt-4">
                {activeTab === 'params' && (
                  <div className="space-y-4">
                    <div className="flex justify-between items-center">
                      <h3 className="text-sm font-medium">Query Parameters</h3>
                      <button
                        type="button"
                        onClick={addParameter}
                        className="text-xs px-2 py-1 bg-primary/10 text-primary rounded hover:bg-primary/20"
                      >
                        + Add Param
                      </button>
                    </div>
                    {parameters.length === 0 ? (
                      <p className="text-sm text-muted-foreground italic">No parameters defined.</p>
                    ) : (
                      <div className="space-y-2">
                        {parameters.map((param, idx) => (
                          <div key={idx} className="flex flex-wrap gap-2 items-start p-2 bg-muted/30 rounded-lg">
                            <input
                              type="text"
                              value={param.name}
                              onChange={e => updateParameter(idx, 'name', e.target.value)}
                              placeholder="Key"
                              className="w-28 px-3 py-2 text-sm bg-background border border-border rounded"
                            />
                            <select
                              value={param.type}
                              onChange={e => updateParameter(idx, 'type', e.target.value)}
                              className="w-24 px-3 py-2 text-sm bg-background border border-border rounded"
                            >
                              {PARAMETER_TYPES.map(t => <option key={t} value={t}>{t}</option>)}
                            </select>
                            <input
                              type="text"
                              value={param.value || ''}
                              onChange={e => updateParameter(idx, 'value', e.target.value)}
                              placeholder="Value"
                              className="w-28 px-3 py-2 text-sm bg-background border border-border rounded"
                            />
                            <input
                              type="text"
                              value={param.example || ''}
                              onChange={e => updateParameter(idx, 'example', e.target.value)}
                              placeholder="Example"
                              className="w-28 px-3 py-2 text-sm bg-background border border-border rounded"
                            />
                            <input
                              type="text"
                              value={param.description || ''}
                              onChange={e => updateParameter(idx, 'description', e.target.value)}
                              placeholder="Description"
                              className="flex-1 min-w-[120px] px-3 py-2 text-sm bg-background border border-border rounded"
                            />
                            <div className="flex items-center h-9 gap-1" title="Required">
                              <input
                                type="checkbox"
                                checked={param.required}
                                onChange={e => updateParameter(idx, 'required', e.target.checked)}
                                className="w-4 h-4"
                                id={`req-${idx}`}
                              />
                              <label htmlFor={`req-${idx}`} className="text-xs text-muted-foreground">Req</label>
                            </div>
                            <button
                              type="button"
                              onClick={() => removeParameter(idx)}
                              className="p-2 text-destructive hover:bg-destructive/10 rounded"
                            >
                              <Trash2 className="w-4 h-4" />
                            </button>
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                )}

                {activeTab === 'headers' && (
                  <div className="space-y-4">
                    <div className="flex justify-between items-center">
                      <h3 className="text-sm font-medium">Request Headers</h3>
                      <button
                        type="button"
                        onClick={addHeaderRow}
                        className="text-xs px-2 py-1 bg-primary/10 text-primary rounded hover:bg-primary/20"
                      >
                        + Add Header
                      </button>
                    </div>
                    {headerRows.length === 0 ? (
                      <p className="text-sm text-muted-foreground italic">No headers defined.</p>
                    ) : (
                      <div className="space-y-2">
                        {headerRows.map((row, idx) => (
                          <div key={idx} className="flex gap-2 items-start">
                            <input
                              type="text"
                              value={row.key}
                              onChange={e => updateHeaderRow(idx, 'key', e.target.value)}
                              placeholder="Key"
                              className="flex-1 px-3 py-2 text-sm bg-background border border-border rounded"
                            />
                            <input
                              type="text"
                              value={row.value}
                              onChange={e => updateHeaderRow(idx, 'value', e.target.value)}
                              placeholder="Value"
                              className="flex-1 px-3 py-2 text-sm bg-background border border-border rounded"
                            />
                            <button
                              type="button"
                              onClick={() => removeHeaderRow(idx)}
                              className="p-2 text-destructive hover:bg-destructive/10 rounded"
                            >
                              <Trash2 className="w-4 h-4" />
                            </button>
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                )}

                {activeTab === 'body' && (
                  <JsonEditor
                    value={jsonSchemaString}
                    onChange={setJsonSchemaString}
                    validateAsSchema
                    height="300px"
                    label="Request Schema (JSON)"
                    required
                    error={errors.json_schema}
                  />
                )}
              </div>
            </div>

            {/* Sample Requests - CRITICAL: Must be exactly 3 */}
            <div className="bg-card border rounded-xl p-6 space-y-4">
              <div className="flex justify-between items-center">
                <h2 className="text-xl font-semibold flex items-center gap-2">
                  <ListChecks className="w-5 h-5" /> Sample Requests {errors.sample_requests && <span className="text-xs text-destructive">({errors.sample_requests})</span>}
                </h2>
                <button
                  type="button"
                  onClick={addSampleRequest}
                  disabled={(formData.sample_requests?.length || 0) >= 3}
                  className="px-4 py-2 bg-primary text-white rounded-lg disabled:opacity-50 flex items-center gap-2"
                >
                  <Plus className="w-4 h-4" /> Add Sample
                </button>
              </div>

              <p className="text-sm text-muted-foreground">
                Add exactly 3 sample requests. Required before generating datasets.
              </p>

              {sampleRequestStrings.map((sampleString, idx) => (
                <div key={sampleString.id} className="p-4 border border-border rounded-lg space-y-3">
                  <div className="flex justify-between items-center">
                    <h3 className="font-medium">Sample #{idx + 1}</h3>
                    <button
                      type="button"
                      onClick={() => removeSampleRequest(idx)}
                      className="text-destructive hover:bg-destructive/10 p-1 rounded"
                    >
                      <Trash2 className="w-4 h-4" />
                    </button>
                  </div>
                  <JsonEditor
                    value={sampleString.request}
                    onChange={v => {
                      setSampleRequestStrings(prev =>
                        prev.map((s, i) => i === idx ? { ...s, request: v } : s)
                      );
                      try {
                        updateSampleRequest(idx, 'request', JSON.parse(v));
                      } catch { }
                    }}
                    height="150px"
                    label="Request"
                  />
                  <JsonEditor
                    value={sampleString.response}
                    onChange={v => {
                      setSampleRequestStrings(prev =>
                        prev.map((s, i) => i === idx ? { ...s, response: v } : s)
                      );
                      try {
                        updateSampleRequest(idx, 'expected_response', JSON.parse(v));
                      } catch { }
                    }}
                    height="150px"
                    label="Expected Response"
                  />
                  <input
                    type="text"
                    value={formData.sample_requests?.[idx]?.note || ''}
                    onChange={e => updateSampleRequest(idx, 'note', e.target.value)}
                    placeholder="Optional note..."
                    className="w-full px-3 py-2 text-sm bg-background border border-border rounded"
                  />
                </div>
              ))}
            </div>

            {/* Domain Tags */}
            <div className="bg-card border rounded-xl p-6 space-y-4">
              <h2 className="text-xl font-semibold flex items-center gap-2">
                <Tag className="w-5 h-5" /> Domain Tags
              </h2>

              <div>
                <label className="block text-sm font-medium mb-2">
                  Domain Tags <span className="text-destructive">*</span> {errors.domain_tags && <span className="text-xs text-destructive">({errors.domain_tags})</span>}
                </label>
                <div className="flex gap-2 mb-2">
                  <input
                    type="text"
                    value={tagInput}
                    onChange={e => setTagInput(e.target.value)}
                    onKeyDown={e => e.key === 'Enter' && (e.preventDefault(), addTag(tagInput))}
                    placeholder="Type and press Enter"
                    className="flex-1 px-3 py-2 bg-background border border-border rounded-lg"
                  />
                  <button type="button" onClick={() => addTag(tagInput)} className="px-4 py-2 bg-primary text-white rounded-lg">Add</button>
                </div>
                <div className="flex flex-wrap gap-2 mb-2">
                  {formData.domain_tags.map(tag => (
                    <span key={tag} className="px-3 py-1 bg-primary/10 text-primary rounded-full text-sm flex items-center gap-2">
                      {tag}
                      <button type="button" onClick={() => removeTag(tag)}><X className="w-3 h-3" /></button>
                    </span>
                  ))}
                </div>
                <div className="flex flex-wrap gap-2">
                  {SUGGESTED_TAGS.map(tag => (
                    !formData.domain_tags.includes(tag) && (
                      <button
                        key={tag}
                        type="button"
                        onClick={() => addTag(tag)}
                        className="px-2 py-1 text-xs bg-muted hover:bg-muted/80 rounded"
                      >
                        + {tag}
                      </button>
                    )
                  ))}
                </div>
              </div>

              {(formData.status === 'review' || formData.status === 'approved') && (
                <div>
                  <label className="block text-sm font-medium mb-2">Reviewer Notes</label>
                  <textarea
                    value={formData.reviewer_notes || ''}
                    onChange={e => handleFieldChange('reviewer_notes', e.target.value)}
                    rows={3}
                    className="w-full px-4 py-3 bg-background border border-border rounded-lg"
                    disabled={!canApprove}
                  />
                </div>
              )}
            </div>
          </div>

          {/* Validation Panel (Sticky Right Column) */}
          <div className="lg:col-span-1">
            <div className="sticky top-4 bg-card border rounded-xl p-6 space-y-4">
              <h3 className="font-semibold flex items-center gap-2">
                {validationIssues.length === 0 ? (
                  <><CheckCircle2 className="w-5 h-5 text-success" /> All Valid</>
                ) : (
                  <><AlertCircle className="w-5 h-5 text-warning" /> {validationIssues.length} Issues</>
                )}
              </h3>

              {validationIssues.length > 0 ? (
                <ul className="space-y-2">
                  {validationIssues.map((issue, i) => (
                    <li key={i} className="text-sm text-muted-foreground flex items-start gap-2">
                      <X className="w-4 h-4 text-destructive flex-shrink-0 mt-0.5" />
                      {issue}
                    </li>
                  ))}
                </ul>
              ) : (
                <p className="text-sm text-success">Ready to submit!</p>
              )}

              <div className="pt-4 border-t space-y-2">
                <p className="text-xs text-muted-foreground">Status: <span className="font-medium">{formData.status}</span></p>
              </div>
            </div>
          </div>
        </div>

        {/* Action Buttons */}
        <div className="mt-8 flex justify-between items-center bg-card border rounded-xl p-6">
          <button
            type="button"
            onClick={handleNavigateBack}
            className="px-6 py-3 border border-border rounded-lg hover:bg-muted"
          >
            Cancel
          </button>

          <div className="flex flex-col items-end gap-2">
            <button
              type="button"
              onClick={handleSubmitForReview}
              disabled={isLoading}
              className="px-6 py-3 bg-primary text-white hover:bg-primary/90 rounded-lg flex items-center gap-2 disabled:opacity-50"
              title="Save draft to database and go to templates list"
            >
              <Save className="w-4 h-4" /> Save Draft
            </button>
            <p className="text-xs text-muted-foreground">
              Auto-saved locally (survives refresh). Click &quot;Save Draft&quot; to save to database &amp; access from Templates page.
            </p>
          </div>
        </div>

        {/* Approval Modal */}
        {showApprovalModal && (
          <div
            className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4"
            onClick={() => setShowApprovalModal(false)}
          >
            <div
              className="bg-card border border-border rounded-lg p-6 max-w-md w-full"
              onClick={e => e.stopPropagation()}
            >
              <h3 className="text-xl font-semibold mb-4">Approve Template?</h3>
              <p className="text-muted-foreground mb-6">
                This will mark the template as approved and allow dataset generation.
              </p>
              <div className="flex justify-end gap-3">
                <button
                  onClick={() => setShowApprovalModal(false)}
                  className="px-4 py-2 border border-border rounded-md hover:bg-muted"
                >
                  Cancel
                </button>
                <button
                  onClick={handleApprove}
                  disabled={isLoading}
                  className="px-4 py-2 bg-green-600 text-white rounded-md hover:bg-green-700 disabled:opacity-50"
                >
                  Approve
                </button>
              </div>
            </div>
          </div>
        )}

        {/* Dataset Warning Modal */}
        {showDatasetWarning && (
          <div
            className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4"
            onClick={() => setShowDatasetWarning(false)}
          >
            <div
              className="bg-card border border-border rounded-lg p-6 max-w-md w-full"
              onClick={e => e.stopPropagation()}
            >
              <h3 className="text-xl font-semibold mb-4 flex items-center gap-2">
                <AlertCircle className="w-6 h-6 text-amber-500" />
                Template Needs Approval
              </h3>
              <p className="text-muted-foreground mb-6">
                Template needs to be approved before dataset generation. Submit for review?
              </p>
              <div className="flex justify-end gap-3">
                <button
                  onClick={() => setShowDatasetWarning(false)}
                  className="px-4 py-2 border border-border rounded-md hover:bg-muted"
                >
                  Cancel
                </button>
                <button
                  onClick={() => {
                    setShowDatasetWarning(false);
                    handleSubmitForReview();
                  }}
                  disabled={isLoading}
                  className="px-4 py-2 bg-primary text-primary-foreground rounded-md hover:bg-primary/90 disabled:opacity-50"
                >
                  Submit for Review
                </button>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
