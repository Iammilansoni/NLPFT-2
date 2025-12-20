/**
 * SampleRequestsSection Component
 * Three sample request/response pairs required for dataset generation
 */

import { ListChecks, Plus, Trash2 } from 'lucide-react';
import { JsonEditor } from '@/components/JsonEditor';
import { SampleRequest } from '@/lib/template-api';
import { SampleRequestString, ValidationErrors } from './types';

interface SampleRequestsSectionProps {
    sampleRequestStrings: SampleRequestString[];
    sampleRequests: SampleRequest[] | undefined;
    errors: ValidationErrors;
    onAddSampleRequest: () => void;
    onUpdateSampleRequest: (index: number, field: keyof SampleRequest, value: any) => void;
    onRemoveSampleRequest: (index: number) => void;
    onSampleStringChange: (index: number, field: 'request' | 'response', value: string) => void;
}

export function SampleRequestsSection({
    sampleRequestStrings,
    sampleRequests,
    errors,
    onAddSampleRequest,
    onUpdateSampleRequest,
    onRemoveSampleRequest,
    onSampleStringChange,
}: SampleRequestsSectionProps) {
    return (
        <div className="bg-card border border-border rounded-lg p-6 space-y-4">
            <div className="flex justify-between items-center">
                <h2 className="text-lg font-semibold flex items-center gap-2">
                    <ListChecks className="w-5 h-5" /> Sample Requests
                    {errors.sample_requests && (
                        <span className="text-xs text-destructive">({errors.sample_requests})</span>
                    )}
                </h2>
                <button
                    type="button"
                    onClick={onAddSampleRequest}
                    disabled={(sampleRequests?.length || 0) >= 3}
                    className="px-4 py-2 bg-primary text-primary-foreground rounded-md disabled:opacity-50 flex items-center gap-2"
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
                            onClick={() => onRemoveSampleRequest(idx)}
                            className="text-destructive hover:bg-destructive/10 p-1 rounded"
                        >
                            <Trash2 className="w-4 h-4" />
                        </button>
                    </div>
                    <JsonEditor
                        value={sampleString.request}
                        onChange={v => {
                            onSampleStringChange(idx, 'request', v);
                            try {
                                onUpdateSampleRequest(idx, 'request', JSON.parse(v));
                            } catch { }
                        }}
                        height="150px"
                        label="Request"
                    />
                    <JsonEditor
                        value={sampleString.response}
                        onChange={v => {
                            onSampleStringChange(idx, 'response', v);
                            try {
                                onUpdateSampleRequest(idx, 'expected_response', JSON.parse(v));
                            } catch { }
                        }}
                        height="150px"
                        label="Expected Response"
                    />
                    <input
                        type="text"
                        value={sampleRequests?.[idx]?.note || ''}
                        onChange={e => onUpdateSampleRequest(idx, 'note', e.target.value)}
                        placeholder="Optional note..."
                        className="w-full px-3 py-2 text-sm bg-background border border-border rounded"
                    />
                </div>
            ))}
        </div>
    );
}
