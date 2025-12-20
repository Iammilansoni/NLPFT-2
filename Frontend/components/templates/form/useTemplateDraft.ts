/**
 * useTemplateDraft Hook
 * Handles local storage draft persistence for template forms
 */

import { useEffect, useRef, useState, useCallback } from 'react';
import { DraftData, SampleRequestString, HeaderRow } from './types';

const DRAFT_STORAGE_PREFIX = 'nlpforge_template_draft_';
const DRAFT_DEBOUNCE_MS = 500;

export function getDraftStorageKey(
    mode: 'create' | 'edit',
    templateId?: string,
    userId?: string
): string {
    if (mode === 'edit' && templateId) {
        return `${DRAFT_STORAGE_PREFIX}edit_${templateId}`;
    }
    return `${DRAFT_STORAGE_PREFIX}create_${userId || 'anonymous'}`;
}

export function saveDraftToStorage(key: string, data: DraftData): void {
    try {
        localStorage.setItem(key, JSON.stringify(data));
    } catch (error) {
        console.warn('Failed to save draft to localStorage:', error);
    }
}

export function loadDraftFromStorage(key: string): DraftData | null {
    try {
        const stored = localStorage.getItem(key);
        if (stored) {
            return JSON.parse(stored) as DraftData;
        }
    } catch (error) {
        console.warn('Failed to load draft from localStorage:', error);
    }
    return null;
}

export function clearDraftFromStorage(key: string): void {
    try {
        localStorage.removeItem(key);
    } catch (error) {
        console.warn('Failed to clear draft from localStorage:', error);
    }
}

interface UseTemplateDraftOptions {
    mode: 'create' | 'edit';
    templateId?: string;
    userId: string;
    formData: any;
    parameters: any[];
    headerRows: HeaderRow[];
    jsonSchemaString: string;
    sampleRequestStrings: SampleRequestString[];
    sampleIdCounter: number;
    expectedResponses: any[];
    activeTab: 'params' | 'headers' | 'body';
}

export function useTemplateDraft(options: UseTemplateDraftOptions) {
    const {
        mode,
        templateId,
        userId,
        formData,
        parameters,
        headerRows,
        jsonSchemaString,
        sampleRequestStrings,
        sampleIdCounter,
        expectedResponses,
        activeTab,
    } = options;

    const [lastSaved, setLastSaved] = useState<Date | null>(null);
    const [hasDraft, setHasDraft] = useState(false);
    const saveTimeoutRef = useRef<NodeJS.Timeout | null>(null);

    const draftKey = getDraftStorageKey(mode, templateId, userId);

    const saveCurrentState = useCallback(() => {
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
        setLastSaved(new Date());
    }, [
        draftKey,
        formData,
        parameters,
        headerRows,
        jsonSchemaString,
        sampleRequestStrings,
        sampleIdCounter,
        expectedResponses,
        activeTab,
    ]);

    // Debounced auto-save
    const debouncedSave = useCallback(() => {
        if (saveTimeoutRef.current) {
            clearTimeout(saveTimeoutRef.current);
        }
        saveTimeoutRef.current = setTimeout(() => {
            saveCurrentState();
        }, DRAFT_DEBOUNCE_MS);
    }, [saveCurrentState]);

    // Load draft on mount
    const loadDraft = useCallback((): DraftData | null => {
        const draft = loadDraftFromStorage(draftKey);
        if (draft) {
            setHasDraft(true);
            setLastSaved(new Date(draft.savedAt));
        }
        return draft;
    }, [draftKey]);

    // Clear draft
    const clearDraft = useCallback(() => {
        clearDraftFromStorage(draftKey);
        setHasDraft(false);
        setLastSaved(null);
    }, [draftKey]);

    // Save on visibility change and page hide
    useEffect(() => {
        const handleBeforeUnload = (e: BeforeUnloadEvent) => {
            saveCurrentState();
        };

        const handleVisibilityChange = () => {
            if (document.visibilityState === 'hidden') {
                saveCurrentState();
            }
        };

        const handlePageHide = () => {
            saveCurrentState();
        };

        window.addEventListener('beforeunload', handleBeforeUnload);
        document.addEventListener('visibilitychange', handleVisibilityChange);
        window.addEventListener('pagehide', handlePageHide);

        return () => {
            if (saveTimeoutRef.current) {
                clearTimeout(saveTimeoutRef.current);
            }
            window.removeEventListener('beforeunload', handleBeforeUnload);
            document.removeEventListener('visibilitychange', handleVisibilityChange);
            window.removeEventListener('pagehide', handlePageHide);
        };
    }, [saveCurrentState]);

    return {
        draftKey,
        lastSaved,
        hasDraft,
        setHasDraft,
        saveCurrentState,
        debouncedSave,
        loadDraft,
        clearDraft,
    };
}
