/**
 * Structured Frontend Error Logger
 *
 * Provides consistent error logging with structured metadata
 * for easier debugging and future integration with external
 * error reporting services (e.g., Sentry, DataDog).
 */

export interface ErrorLogEntry {
  timestamp: string;
  level: 'error' | 'warn' | 'info';
  message: string;
  component?: string;
  action?: string;
  userId?: string;
  metadata?: Record<string, unknown>;
  stack?: string;
}

interface ErrorContext {
  component?: string;
  action?: string;
  userId?: string;
  metadata?: Record<string, unknown>;
}

function formatEntry(
  level: ErrorLogEntry['level'],
  error: unknown,
  context?: ErrorContext
): ErrorLogEntry {
  const entry: ErrorLogEntry = {
    timestamp: new Date().toISOString(),
    level,
    message: error instanceof Error ? error.message : String(error),
    component: context?.component,
    action: context?.action,
    userId: context?.userId,
    metadata: context?.metadata,
    stack: error instanceof Error ? error.stack : undefined,
  };
  return entry;
}

/**
 * Log an error with structured metadata.
 */
export function logError(error: unknown, context?: ErrorContext): void {
  const entry = formatEntry('error', error, context);
  console.error('[NLPForge Error]', JSON.stringify(entry, null, 2));
}

/**
 * Log a warning with structured metadata.
 */
export function logWarning(message: string, context?: ErrorContext): void {
  const entry = formatEntry('warn', message, context);
  console.warn('[NLPForge Warn]', JSON.stringify(entry, null, 2));
}
