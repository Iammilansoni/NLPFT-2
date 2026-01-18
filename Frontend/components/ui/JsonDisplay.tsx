'use client';

import React, { useState, useMemo, useCallback } from 'react';
import { Check, Copy, ChevronDown, ChevronRight } from 'lucide-react';
import { cn } from '@/lib/utils';

interface JsonDisplayProps {
  data: unknown;
  maxHeight?: string;
  showCopyButton?: boolean;
  showLineNumbers?: boolean;
  collapsible?: boolean;
  className?: string;
  title?: string;
}

// Syntax highlighting colors - Professional subdued palette
const TOKEN_COLORS = {
  key: 'text-blue-600 dark:text-blue-400',
  string: 'text-green-600 dark:text-green-500',
  number: 'text-orange-600 dark:text-orange-400',
  boolean: 'text-violet-600 dark:text-violet-400',
  null: 'text-slate-500 dark:text-slate-400',
  bracket: 'text-slate-600 dark:text-slate-400',
  punctuation: 'text-slate-500 dark:text-slate-500',
};

/**
 * Premium JSON Display Component
 * Features:
 * - Syntax highlighting with semantic colors
 * - Line numbers (optional)
 * - Copy to clipboard with feedback
 * - Collapsible nested objects (optional)
 * - Proper 14px+ font sizing for readability
 */
export function JsonDisplay({
  data,
  maxHeight = '24rem',
  showCopyButton = true,
  showLineNumbers = false,
  collapsible = false,
  className,
  title,
}: JsonDisplayProps) {
  const [copied, setCopied] = useState(false);
  const [collapsed, setCollapsed] = useState(false);

  const jsonString = useMemo(() => {
    try {
      return JSON.stringify(data, null, 2);
    } catch {
      return String(data);
    }
  }, [data]);

  const handleCopy = useCallback(async () => {
    try {
      await navigator.clipboard.writeText(jsonString);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch (err) {
      console.error('Failed to copy:', err);
    }
  }, [jsonString]);

  // Tokenize and highlight JSON
  const highlightedLines = useMemo(() => {
    const lines = jsonString.split('\n');
    return lines.map((line, index) => highlightLine(line, index));
  }, [jsonString]);

  return (
    <div
      className={cn(
        'relative rounded-lg border border-border bg-muted/30 overflow-hidden',
        className
      )}
    >
      {/* Header */}
      {(title || showCopyButton || collapsible) && (
        <div className="flex items-center justify-between px-4 py-2.5 border-b border-border/50 bg-muted/20">
          <div className="flex items-center gap-2">
            {collapsible && (
              <button
                onClick={() => setCollapsed(!collapsed)}
                className="p-0.5 hover:bg-accent rounded transition-colors"
                aria-label={collapsed ? 'Expand' : 'Collapse'}
              >
                {collapsed ? (
                  <ChevronRight className="w-4 h-4 text-muted-foreground" />
                ) : (
                  <ChevronDown className="w-4 h-4 text-muted-foreground" />
                )}
              </button>
            )}
            {title && (
              <span className="text-sm font-medium text-foreground">{title}</span>
            )}
          </div>
          {showCopyButton && (
            <button
              onClick={handleCopy}
              className={cn(
                'flex items-center gap-1.5 px-2.5 py-1 rounded-md text-xs font-medium transition-all',
                copied
                  ? 'bg-emerald-500/10 text-emerald-600 dark:text-emerald-400'
                  : 'bg-muted hover:bg-accent text-muted-foreground hover:text-foreground'
              )}
            >
              {copied ? (
                <>
                  <Check className="w-3.5 h-3.5" />
                  Copied!
                </>
              ) : (
                <>
                  <Copy className="w-3.5 h-3.5" />
                  Copy
                </>
              )}
            </button>
          )}
        </div>
      )}

      {/* Content */}
      {!collapsed && (
        <div
          className="overflow-auto scrollbar-cc"
          style={{ maxHeight }}
        >
          <pre className="json-display p-4 text-sm font-mono leading-relaxed">
            <code className="block">
              {highlightedLines.map((line, index) => (
                <div key={index} className="flex">
                  {showLineNumbers && (
                    <span className="select-none pr-4 text-muted-foreground/50 text-right min-w-[2.5rem]">
                      {index + 1}
                    </span>
                  )}
                  <span className="flex-1">{line}</span>
                </div>
              ))}
            </code>
          </pre>
        </div>
      )}

      {collapsed && (
        <div className="px-4 py-3 text-sm text-muted-foreground">
          <span className="font-mono">{'{...}'}</span>
          <span className="ml-2 text-xs">
            {typeof data === 'object' && data !== null
              ? `${Object.keys(data).length} keys`
              : ''}
          </span>
        </div>
      )}
    </div>
  );
}

// Highlight a single line of JSON
function highlightLine(line: string, _lineIndex: number): React.ReactNode {
  const tokens: React.ReactNode[] = [];
  let i = 0;

  // Leading whitespace
  const leadingMatch = line.match(/^(\s*)/);
  if (leadingMatch && leadingMatch[1]) {
    tokens.push(<span key={`ws-${i}`}>{leadingMatch[1]}</span>);
    i = leadingMatch[1].length;
  }

  while (i < line.length) {
    const remaining = line.slice(i);

    // Key (quoted string followed by colon)
    const keyMatch = remaining.match(/^"([^"\\]|\\.)*"(?=\s*:)/);
    if (keyMatch) {
      tokens.push(
        <span key={`key-${i}`} className={TOKEN_COLORS.key}>
          {keyMatch[0]}
        </span>
      );
      i += keyMatch[0].length;
      continue;
    }

    // String value
    const stringMatch = remaining.match(/^"([^"\\]|\\.)*"/);
    if (stringMatch) {
      tokens.push(
        <span key={`str-${i}`} className={TOKEN_COLORS.string}>
          {stringMatch[0]}
        </span>
      );
      i += stringMatch[0].length;
      continue;
    }

    // Number
    const numMatch = remaining.match(/^-?\d+\.?\d*([eE][+-]?\d+)?/);
    if (numMatch) {
      tokens.push(
        <span key={`num-${i}`} className={TOKEN_COLORS.number}>
          {numMatch[0]}
        </span>
      );
      i += numMatch[0].length;
      continue;
    }

    // Boolean
    const boolMatch = remaining.match(/^(true|false)/);
    if (boolMatch) {
      tokens.push(
        <span key={`bool-${i}`} className={TOKEN_COLORS.boolean}>
          {boolMatch[0]}
        </span>
      );
      i += boolMatch[0].length;
      continue;
    }

    // Null
    if (remaining.startsWith('null')) {
      tokens.push(
        <span key={`null-${i}`} className={TOKEN_COLORS.null}>
          null
        </span>
      );
      i += 4;
      continue;
    }

    // Brackets
    if (/^[\[\]{}]/.test(remaining)) {
      tokens.push(
        <span key={`bracket-${i}`} className={TOKEN_COLORS.bracket}>
          {remaining[0]}
        </span>
      );
      i += 1;
      continue;
    }

    // Punctuation (colon, comma)
    if (/^[,:]/.test(remaining)) {
      tokens.push(
        <span key={`punct-${i}`} className={TOKEN_COLORS.punctuation}>
          {remaining[0]}
        </span>
      );
      i += 1;
      continue;
    }

    // Whitespace and other
    tokens.push(<span key={`other-${i}`}>{remaining[0]}</span>);
    i += 1;
  }

  return <>{tokens}</>;
}

export default JsonDisplay;
