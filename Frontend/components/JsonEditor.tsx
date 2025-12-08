/**
 * JSON Editor Component
 * Syntax-highlighted JSON editor with validation
 * Falls back to textarea if Monaco is unavailable
 */

'use client';

import React, { useState, useEffect } from 'react';
import { AlertCircle, CheckCircle2 } from 'lucide-react';

interface JsonEditorProps {
  value: string;
  onChange: (value: string) => void;
  onValidation?: (isValid: boolean, error?: string) => void;
  placeholder?: string;
  height?: string;
  validateAsSchema?: boolean;
  label?: string;
  helpText?: string;
  required?: boolean;
  error?: string;
}

export function JsonEditor({
  value,
  onChange,
  onValidation,
  placeholder = '{\n  "type": "object",\n  "properties": {}\n}',
  height = '300px',
  validateAsSchema = false,
  label,
  helpText,
  required = false,
  error: externalError,
}: JsonEditorProps) {
  const [internalError, setInternalError] = useState<string>('');
  const [isValid, setIsValid] = useState<boolean>(true);

  // Validate JSON and optionally check if it's a valid JSON Schema
  useEffect(() => {
    if (!value || value.trim() === '') {
      setInternalError(required ? 'This field is required' : '');
      setIsValid(!required);
      onValidation?.(!required, required ? 'Required' : undefined);
      return;
    }

    try {
      const parsed = JSON.parse(value);
      
      // Additional validation for JSON Schema
      if (validateAsSchema) {
        if (typeof parsed !== 'object' || parsed === null) {
          throw new Error('JSON Schema must be an object');
        }
        
        // Basic JSON Schema validation - check for essential keys
        const hasType = 'type' in parsed;
        const hasProperties = 'properties' in parsed;
        const hasOneOf = 'oneOf' in parsed;
        const hasAnyOf = 'anyOf' in parsed;
        const hasAllOf = 'allOf' in parsed;
        
        if (!hasType && !hasProperties && !hasOneOf && !hasAnyOf && !hasAllOf) {
          throw new Error(
            'Invalid JSON Schema: must contain at least one of: type, properties, oneOf, anyOf, allOf'
          );
        }
      }
      
      setInternalError('');
      setIsValid(true);
      onValidation?.(true);
    } catch (err: any) {
      const errorMsg = err.message || 'Invalid JSON';
      setInternalError(errorMsg);
      setIsValid(false);
      onValidation?.(false, errorMsg);
    }
  }, [value, validateAsSchema, required, onValidation]);

  const displayError = externalError || internalError;

  // Format JSON with proper indentation
  const formatJson = () => {
    try {
      const parsed = JSON.parse(value);
      const formatted = JSON.stringify(parsed, null, 2);
      onChange(formatted);
    } catch (err) {
      // If invalid, don't format
    }
  };

  return (
    <div className="space-y-2">
      {label && (
        <label className="block text-sm font-medium text-foreground">
          {label}
          {required && <span className="text-destructive ml-1">*</span>}
        </label>
      )}
      
      {helpText && (
        <p className="text-xs text-muted-foreground">{helpText}</p>
      )}

      <div className="relative">
        <textarea
          value={value}
          onChange={(e) => onChange(e.target.value)}
          placeholder={placeholder}
          className={`w-full px-4 py-3 font-mono text-sm bg-background border rounded-lg focus:outline-none focus:ring-2 resize-none ${
            displayError
              ? 'border-destructive focus:ring-destructive/50'
              : 'border-border focus:ring-primary/50'
          }`}
          style={{ height }}
          spellCheck={false}
        />
        
        {/* Validation indicator */}
        <div className="absolute top-2 right-2">
          {value && (
            isValid ? (
              <CheckCircle2 className="w-5 h-5 text-success" />
            ) : (
              <AlertCircle className="w-5 h-5 text-destructive" />
            )
          )}
        </div>
      </div>

      {/* Format button */}
      <div className="flex justify-between items-center">
        <button
          type="button"
          onClick={formatJson}
          disabled={!isValid}
          className="text-xs text-primary hover:underline disabled:text-muted-foreground disabled:no-underline"
        >
          Format JSON
        </button>
        
        {displayError && (
          <span className="text-xs text-destructive flex items-center gap-1">
            <AlertCircle className="w-3 h-3" />
            {displayError}
          </span>
        )}
      </div>
    </div>
  );
}

export default JsonEditor;
