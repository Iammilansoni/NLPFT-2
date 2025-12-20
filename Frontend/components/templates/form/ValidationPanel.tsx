/**
 * ValidationPanel Component
 * Sticky sidebar showing validation status
 */

import { CheckCircle2, AlertCircle, X } from 'lucide-react';
import { TemplateStatus } from '@/lib/template-api';

interface ValidationPanelProps {
    validationIssues: string[];
    status: TemplateStatus;
}

export function ValidationPanel({
    validationIssues,
    status,
}: ValidationPanelProps) {
    return (
        <div className="sticky top-4 bg-card border border-border rounded-lg p-6 space-y-4">
            <h3 className="font-semibold flex items-center gap-2">
                {validationIssues.length === 0 ? (
                    <>
                        <CheckCircle2 className="w-5 h-5 text-green-500" /> All Valid
                    </>
                ) : (
                    <>
                        <AlertCircle className="w-5 h-5 text-amber-500" /> {validationIssues.length} Issues
                    </>
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
                <p className="text-sm text-green-500">Ready to submit!</p>
            )}

            <div className="pt-4 border-t border-border space-y-2">
                <p className="text-xs text-muted-foreground">
                    Status: <span className="font-medium">{status}</span>
                </p>
            </div>
        </div>
    );
}
