/**
 * BasicInfoSection Component
 * API name, description, base URL, and method fields
 */

import { Info } from 'lucide-react';
import { CreateTemplateRequest, HttpMethod } from '@/lib/template-api';
import { HTTP_METHODS, ValidationErrors } from './types';

interface BasicInfoSectionProps {
    formData: Partial<CreateTemplateRequest>;
    errors: ValidationErrors;
    onFieldChange: (field: keyof CreateTemplateRequest, value: any) => void;
}

// Standardized word counting function - matches backend behavior
function countWords(text: string): number {
    if (!text) return 0;
    return text.trim().split(/\s+/).filter(word => word.length > 0).length;
}

export function BasicInfoSection({
    formData,
    errors,
    onFieldChange,
}: BasicInfoSectionProps) {
    const wordCount = countWords(formData.description || '');

    return (
        <div className="bg-card border border-border rounded-lg p-6 space-y-4">
            <h2 className="text-lg font-semibold flex items-center gap-2">
                <Info className="w-5 h-5" /> Basic Information
            </h2>

            <div>
                <label className="block text-sm font-medium mb-1.5">
                    API Name <span className="text-destructive">*</span>
                </label>
                <input
                    type="text"
                    value={formData.api_name || ''}
                    onChange={e => onFieldChange('api_name', e.target.value)}
                    maxLength={120}
                    className="w-full px-3 py-2 bg-background border border-border rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-primary/50"
                    placeholder="Create_fft_with_no_pilot_signal"
                />
                <div className="flex justify-between text-xs mt-1">
                    <span className="text-muted-foreground">{(formData.api_name || '').length}/120</span>
                    {errors.api_name && <span className="text-destructive">{errors.api_name}</span>}
                </div>
            </div>

            <div>
                <label className="block text-sm font-medium mb-1.5">
                    Description <span className="text-destructive">*</span>
                </label>
                <textarea
                    value={formData.description || ''}
                    onChange={e => onFieldChange('description', e.target.value)}
                    rows={6}
                    className="w-full px-3 py-2 bg-background border border-border rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-primary/50"
                    placeholder="Detailed description (min 500 words). Include: purpose, use cases, technical context, integration details..."
                />
                <div className="flex justify-between text-xs mt-1">
                    <span className={wordCount < 500 ? 'text-destructive' : 'text-muted-foreground'}>
                        {wordCount}/500 words minimum
                    </span>
                    {errors.description && <span className="text-destructive">{errors.description}</span>}
                </div>
            </div>

            <div className="grid grid-cols-3 gap-4">
                <div className="col-span-2">
                    <label className="block text-sm font-medium mb-1.5">
                        Base URL <span className="text-destructive">*</span>
                    </label>
                    <input
                        type="url"
                        value={formData.base_url || ''}
                        onChange={e => onFieldChange('base_url', e.target.value)}
                        className="w-full px-3 py-2 bg-background border border-border rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-primary/50"
                        placeholder="https://api.example.com/v1"
                    />
                    {errors.base_url && <span className="text-xs text-destructive">{errors.base_url}</span>}
                </div>
                <div>
                    <label className="block text-sm font-medium mb-1.5">
                        Method <span className="text-destructive">*</span>
                    </label>
                    <select
                        value={formData.method || 'GET'}
                        onChange={e => onFieldChange('method', e.target.value as HttpMethod)}
                        className="w-full px-3 py-2 bg-background border border-border rounded-md text-sm"
                    >
                        {HTTP_METHODS.map(m => <option key={m} value={m}>{m}</option>)}
                    </select>
                </div>
            </div>
        </div>
    );
}
