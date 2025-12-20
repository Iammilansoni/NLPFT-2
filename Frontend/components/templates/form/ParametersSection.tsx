/**
 * ParametersSection Component
 * Query parameters, headers, and request body tabs
 */

import { FileCode, Trash2 } from 'lucide-react';
import { Parameter } from '@/lib/template-api';
import { JsonEditor } from '@/components/JsonEditor';
import { PARAMETER_TYPES, HeaderRow, ValidationErrors } from './types';

interface ParametersSectionProps {
    activeTab: 'params' | 'headers' | 'body';
    setActiveTab: (tab: 'params' | 'headers' | 'body') => void;
    parameters: Parameter[];
    headerRows: HeaderRow[];
    jsonSchemaString: string;
    errors: ValidationErrors;
    userId: string;
    onAddParameter: () => void;
    onUpdateParameter: (index: number, field: keyof Parameter, value: any) => void;
    onRemoveParameter: (index: number) => void;
    onAddHeaderRow: () => void;
    onUpdateHeaderRow: (index: number, field: 'key' | 'value', value: string) => void;
    onRemoveHeaderRow: (index: number) => void;
    onJsonSchemaChange: (value: string) => void;
}

export function ParametersSection({
    activeTab,
    setActiveTab,
    parameters,
    headerRows,
    jsonSchemaString,
    errors,
    onAddParameter,
    onUpdateParameter,
    onRemoveParameter,
    onAddHeaderRow,
    onUpdateHeaderRow,
    onRemoveHeaderRow,
    onJsonSchemaChange,
}: ParametersSectionProps) {
    return (
        <div className="bg-card border border-border rounded-lg p-6 space-y-4">
            <h2 className="text-lg font-semibold flex items-center gap-2">
                <FileCode className="w-5 h-5" /> Request Details
            </h2>

            <div className="flex border-b border-border">
                {(['params', 'headers', 'body'] as const).map((tab) => (
                    <button
                        key={tab}
                        type="button"
                        onClick={() => setActiveTab(tab)}
                        className={`px-4 py-2 text-sm font-medium border-b-2 ${activeTab === tab
                                ? 'border-primary text-primary'
                                : 'border-transparent text-muted-foreground hover:text-foreground'
                            }`}
                    >
                        {tab.charAt(0).toUpperCase() + tab.slice(1)}
                    </button>
                ))}
            </div>

            <div className="pt-4">
                {activeTab === 'params' && (
                    <div className="space-y-4">
                        <div className="flex justify-between items-center">
                            <h3 className="text-sm font-medium">Query Parameters</h3>
                            <button
                                type="button"
                                onClick={onAddParameter}
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
                                            onChange={e => onUpdateParameter(idx, 'name', e.target.value)}
                                            placeholder="Key"
                                            className="w-28 px-3 py-2 text-sm bg-background border border-border rounded"
                                        />
                                        <select
                                            value={param.type}
                                            onChange={e => onUpdateParameter(idx, 'type', e.target.value)}
                                            className="w-24 px-3 py-2 text-sm bg-background border border-border rounded"
                                        >
                                            {PARAMETER_TYPES.map(t => <option key={t} value={t}>{t}</option>)}
                                        </select>
                                        <input
                                            type="text"
                                            value={(param as any).value || ''}
                                            onChange={e => onUpdateParameter(idx, 'value' as any, e.target.value)}
                                            placeholder="Value"
                                            className="w-28 px-3 py-2 text-sm bg-background border border-border rounded"
                                        />
                                        <input
                                            type="text"
                                            value={param.example || ''}
                                            onChange={e => onUpdateParameter(idx, 'example', e.target.value)}
                                            placeholder="Example"
                                            className="w-28 px-3 py-2 text-sm bg-background border border-border rounded"
                                        />
                                        <input
                                            type="text"
                                            value={param.description || ''}
                                            onChange={e => onUpdateParameter(idx, 'description', e.target.value)}
                                            placeholder="Description"
                                            className="flex-1 min-w-[120px] px-3 py-2 text-sm bg-background border border-border rounded"
                                        />
                                        <div className="flex items-center h-9 gap-1" title="Required">
                                            <input
                                                type="checkbox"
                                                checked={param.required}
                                                onChange={e => onUpdateParameter(idx, 'required', e.target.checked)}
                                                className="w-4 h-4"
                                                id={`req-${idx}`}
                                            />
                                            <label htmlFor={`req-${idx}`} className="text-xs text-muted-foreground">Req</label>
                                        </div>
                                        <button
                                            type="button"
                                            onClick={() => onRemoveParameter(idx)}
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
                                onClick={onAddHeaderRow}
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
                                            onChange={e => onUpdateHeaderRow(idx, 'key', e.target.value)}
                                            placeholder="Key"
                                            className="flex-1 px-3 py-2 text-sm bg-background border border-border rounded"
                                        />
                                        <input
                                            type="text"
                                            value={row.value}
                                            onChange={e => onUpdateHeaderRow(idx, 'value', e.target.value)}
                                            placeholder="Value"
                                            className="flex-1 px-3 py-2 text-sm bg-background border border-border rounded"
                                        />
                                        <button
                                            type="button"
                                            onClick={() => onRemoveHeaderRow(idx)}
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
                        onChange={onJsonSchemaChange}
                        validateAsSchema
                        height="300px"
                        label="Request Schema (JSON)"
                        required
                        error={errors.json_schema}
                    />
                )}
            </div>
        </div>
    );
}
