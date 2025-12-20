/**
 * TagsSection Component
 * Domain tags and reviewer notes
 */

import { Tag, X } from 'lucide-react';
import { TemplateStatus, UserRole } from '@/lib/template-api';
import { SUGGESTED_TAGS, ValidationErrors } from './types';

interface TagsSectionProps {
    domainTags: string[];
    tagInput: string;
    setTagInput: (value: string) => void;
    status: TemplateStatus;
    reviewerNotes: string | undefined;
    userRole: UserRole;
    errors: ValidationErrors;
    onAddTag: (tag: string) => void;
    onRemoveTag: (tag: string) => void;
    onReviewerNotesChange: (notes: string) => void;
}

export function TagsSection({
    domainTags,
    tagInput,
    setTagInput,
    status,
    reviewerNotes,
    userRole,
    errors,
    onAddTag,
    onRemoveTag,
    onReviewerNotesChange,
}: TagsSectionProps) {
    const canApprove = userRole === 'admin' || userRole === 'reviewer';

    return (
        <div className="bg-card border border-border rounded-lg p-6 space-y-4">
            <h2 className="text-lg font-semibold flex items-center gap-2">
                <Tag className="w-5 h-5" /> Domain Tags
            </h2>

            <div>
                <label className="block text-sm font-medium mb-1.5">
                    Domain Tags <span className="text-destructive">*</span>
                    {errors.domain_tags && (
                        <span className="text-xs text-destructive ml-2">({errors.domain_tags})</span>
                    )}
                </label>
                <div className="flex gap-2 mb-2">
                    <input
                        type="text"
                        value={tagInput}
                        onChange={e => setTagInput(e.target.value)}
                        onKeyDown={e => e.key === 'Enter' && (e.preventDefault(), onAddTag(tagInput))}
                        placeholder="Type and press Enter"
                        className="flex-1 px-3 py-2 bg-background border border-border rounded-md"
                    />
                    <button
                        type="button"
                        onClick={() => onAddTag(tagInput)}
                        className="px-4 py-2 bg-primary text-primary-foreground rounded-md"
                    >
                        Add
                    </button>
                </div>
                <div className="flex flex-wrap gap-2 mb-2">
                    {domainTags.map(tag => (
                        <span key={tag} className="px-3 py-1 bg-primary/10 text-primary rounded-full text-sm flex items-center gap-2">
                            {tag}
                            <button type="button" onClick={() => onRemoveTag(tag)}>
                                <X className="w-3 h-3" />
                            </button>
                        </span>
                    ))}
                </div>
                <div className="flex flex-wrap gap-2">
                    {SUGGESTED_TAGS.map(tag => (
                        !domainTags.includes(tag) && (
                            <button
                                key={tag}
                                type="button"
                                onClick={() => onAddTag(tag)}
                                className="px-2 py-1 text-xs bg-muted hover:bg-muted/80 rounded"
                            >
                                + {tag}
                            </button>
                        )
                    ))}
                </div>
            </div>

            {(status === 'review' || status === 'approved') && (
                <div>
                    <label className="block text-sm font-medium mb-1.5">Reviewer Notes</label>
                    <textarea
                        value={reviewerNotes || ''}
                        onChange={e => onReviewerNotesChange(e.target.value)}
                        rows={3}
                        className="w-full px-3 py-2 bg-background border border-border rounded-md"
                        disabled={!canApprove}
                    />
                </div>
            )}
        </div>
    );
}
