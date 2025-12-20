/**
 * Template Form Types
 * Shared types for template form components
 */

import {
    HttpMethod,
    TemplateStatus,
    UserRole,
    Parameter,
    ExpectedResponse,
    SampleRequest,
    CreateTemplateRequest,
} from '@/lib/template-api';

export interface TemplateFormData extends Partial<CreateTemplateRequest> {
    template_id?: string;
    parameters?: Parameter[];
    expected_responses?: ExpectedResponse[];
}

export interface TemplateFormProps {
    mode: 'create' | 'edit';
    initialData?: TemplateFormData;
    userId: string;
    userRole: UserRole;
    onSuccess?: (templateId: string) => void;
}

export interface HeaderRow {
    key: string;
    value: string;
}

export interface SampleRequestString {
    id: number;
    request: string;
    response: string;
}

export interface DraftData {
    formData: any;
    parameters: any[];
    headerRows: HeaderRow[];
    jsonSchemaString: string;
    sampleRequestStrings: SampleRequestString[];
    sampleIdCounter: number;
    expectedResponses: any[];
    activeTab: 'params' | 'headers' | 'body';
    savedAt: number;
}

export interface ValidationErrors {
    api_name?: string;
    description?: string;
    base_url?: string;
    method?: string;
    json_schema?: string;
    sample_requests?: string;
    domain_tags?: string;
}

export const HTTP_METHODS: HttpMethod[] = ['GET', 'POST', 'PUT', 'PATCH', 'DELETE'];
export const PARAMETER_TYPES = ['string', 'number', 'integer', 'boolean', 'array', 'object'];
export const SUGGESTED_TAGS = ['telecom', 'fft', 'authentication', 'payment', 'webhook'];
