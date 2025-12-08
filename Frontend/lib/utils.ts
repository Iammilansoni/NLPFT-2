import { type ClassValue, clsx } from "clsx"
import { twMerge } from "tailwind-merge"

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}

// ============================================================================
// CENTRALIZED ERROR HANDLING
// ============================================================================

export interface ApiError {
  message: string;
  detail?: string | { message?: string; errors?: string[] };
  status?: number;
}

/**
 * Parse API error response and return a user-friendly message
 */
export function parseApiError(error: unknown, fallbackMessage: string = 'An error occurred'): string {
  if (!error) return fallbackMessage;
  
  if (error instanceof Error) {
    // Check if it's an API error with detail
    const apiError = error as any;
    if (apiError.detail) {
      if (typeof apiError.detail === 'string') {
        return apiError.detail;
      }
      if (typeof apiError.detail === 'object') {
        if (apiError.detail.errors && Array.isArray(apiError.detail.errors)) {
          return `${apiError.detail.message || 'Error'}: ${apiError.detail.errors.slice(0, 3).join(' | ')}`;
        }
        return apiError.detail.message || fallbackMessage;
      }
    }
    return error.message || fallbackMessage;
  }
  
  if (typeof error === 'string') return error;
  
  return fallbackMessage;
}

/**
 * Log error to console with consistent formatting
 */
export function logError(context: string, error: unknown): void {
  console.error(`[${context}]`, error);
}

// ============================================================================
// INPUT SANITIZATION
// ============================================================================

/**
 * Sanitize user input to prevent XSS attacks
 */
export function sanitizeHtml(input: string): string {
  if (!input) return '';
  return input
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#x27;');
}

/**
 * Standardized word counting - matches backend behavior
 */
export function countWords(text: string): number {
  if (!text) return 0;
  return text.trim().split(/\s+/).filter(word => word.length > 0).length;
}

// ============================================================================
// UUID VALIDATION
// ============================================================================

const UUID_REGEX = /^[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i;

/**
 * Validate if a string is a valid UUID
 */
export function isValidUUID(str: string): boolean {
  return UUID_REGEX.test(str);
}

// ============================================================================
// DATE FORMATTING
// ============================================================================

export function formatDate(date: string | Date): string {
  const d = typeof date === 'string' ? new Date(date) : date
  return new Intl.DateTimeFormat('en-US', {
    month: 'short',
    day: 'numeric',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  }).format(d)
}

export function formatRelativeTime(date: string | Date): string {
  const d = typeof date === 'string' ? new Date(date) : date
  const now = new Date()
  const diffInSeconds = Math.floor((now.getTime() - d.getTime()) / 1000)

  if (diffInSeconds < 60) return 'just now'
  if (diffInSeconds < 3600) return `${Math.floor(diffInSeconds / 60)}m ago`
  if (diffInSeconds < 86400) return `${Math.floor(diffInSeconds / 3600)}h ago`
  if (diffInSeconds < 604800) return `${Math.floor(diffInSeconds / 86400)}d ago`
  return formatDate(d)
}

export function formatBytes(bytes: number, decimals = 2): string {
  if (bytes === 0) return '0 Bytes'
  const k = 1024
  const dm = decimals < 0 ? 0 : decimals
  const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return parseFloat((bytes / Math.pow(k, i)).toFixed(dm)) + ' ' + sizes[i]
}

export function debounce<T extends (...args: any[]) => any>(
  func: T,
  wait: number
): (...args: Parameters<T>) => void {
  let timeout: NodeJS.Timeout | null = null
  return function executedFunction(...args: Parameters<T>) {
    const later = () => {
      timeout = null
      func(...args)
    }
    if (timeout) clearTimeout(timeout)
    timeout = setTimeout(later, wait)
  }
}

export function truncate(str: string, length: number): string {
  if (str.length <= length) return str
  return str.slice(0, length) + '...'
}

export function toTitleCase(str: string): string {
  return str
    .split(/[-_\s]/)
    .map(word => word.charAt(0).toUpperCase() + word.slice(1).toLowerCase())
    .join(' ')
}

export function getColorValue(color: string): { h: number; s: number; l: number } {
  const colors: Record<string, { h: number; s: number; l: number }> = {
    blue: { h: 221, s: 83, l: 53 },
    purple: { h: 271, s: 81, l: 56 },
    green: { h: 142, s: 76, l: 36 },
    orange: { h: 25, s: 95, l: 53 },
    pink: { h: 330, s: 81, l: 60 },
    red: { h: 0, s: 84, l: 60 },
  }
  return colors[color] || colors.blue
}
