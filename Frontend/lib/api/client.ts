/**
 * API Client Configuration
 * Central configuration for all API requests
 */
import { getApiBase } from '../runtime-config';

// Helper to get API base dynamically (not at module load time)
function getApiBaseUrl(): string {
  return getApiBase().replace(/\/$/, '');
}

export const API_ENDPOINTS = {
  // Base - computed at runtime via getters
  get root() { return `${getApiBaseUrl()}/` },
  get datasetList() { return `${getApiBaseUrl()}/api/v1/dataset/list` },

  // Query Processing
  get query() { return `${getApiBaseUrl()}/api/v1/query` },
  get stats() { return `${getApiBaseUrl()}/api/v1/stats` },
  reindex: (intent: string) => `${getApiBaseUrl()}/api/v1/reindex/${intent}`,

  // Search
  get search() { return `${getApiBaseUrl()}/api/v1/search` },

  // Templates
  templates: {
    get list() { return `${getApiBaseUrl()}/api/v1/templates` },
    get: (intent: string) => `${getApiBaseUrl()}/api/v1/templates/${intent}`,
    get create() { return `${getApiBaseUrl()}/api/v1/templates` },
    update: (intent: string) => `${getApiBaseUrl()}/api/v1/templates/${intent}`,
    delete: (intent: string) => `${getApiBaseUrl()}/api/v1/templates/${intent}`,
    get sync() { return `${getApiBaseUrl()}/api/v1/templates/sync` },
    get reload() { return `${getApiBaseUrl()}/api/v1/templates/reload` },
    get stats() { return `${getApiBaseUrl()}/api/v1/templates/stats` },
  },

  // Datasets
  dataset: {
    get list() { return `${getApiBaseUrl()}/api/v1/dataset/list` },
    get upload() { return `${getApiBaseUrl()}/api/v1/dataset/upload` },
    get ingest() { return `${getApiBaseUrl()}/api/v1/dataset/ingest` },
    get generate() { return `${getApiBaseUrl()}/api/v1/dataset/generate` },
  },
}

/**
 * Custom error class for API errors
 */
export class ApiError extends Error {
  constructor(
    message: string,
    public status: number,
    public data?: any
  ) {
    super(message)
    this.name = 'ApiError'
  }
}

/**
 * Handle API response and errors
 */
async function handleResponse<T>(response: Response): Promise<T> {
  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}))
    const errorMessage = errorData.detail || errorData.error || `HTTP ${response.status}: ${response.statusText}`

    // Any 401 means the session is invalid or expired; redirect on status alone
    if (response.status === 401) {
      // Redirect to login — cookies will be cleared server-side on /logout
      if (typeof window !== 'undefined' && !window.location.pathname.startsWith('/auth')) {
        window.location.href = '/auth/login';
      }
    }

    throw new ApiError(
      errorMessage,
      response.status,
      errorData
    )
  }

  const contentType = response.headers.get('content-type')
  if (contentType?.includes('application/json')) {
    return response.json()
  }

  return response.text() as any
}

/**
 * Base fetch wrapper with error handling
 */
export async function apiFetch<T>(
  url: string,
  options: RequestInit = {}
): Promise<T> {
  try {
    const response = await fetch(url, {
      ...options,
      credentials: 'include',   // HttpOnly auth cookie sent automatically
      headers: {
        'Content-Type': 'application/json',
        ...options.headers,
      },
    })

    return handleResponse<T>(response)
  } catch (error) {
    if (error instanceof ApiError) {
      throw error
    }

    // Network or other errors
    throw new ApiError(
      error instanceof Error ? error.message : 'An unknown error occurred',
      0
    )
  }
}

/**
 * GET request
 */
export async function apiGet<T>(url: string, params?: Record<string, any>): Promise<T> {
  const urlWithParams = params
    ? `${url}?${new URLSearchParams(params as any)}`
    : url

  return apiFetch<T>(urlWithParams, { method: 'GET' })
}

/**
 * POST request
 */
export async function apiPost<T>(url: string, data?: any): Promise<T> {
  return apiFetch<T>(url, {
    method: 'POST',
    body: data ? JSON.stringify(data) : undefined,
  })
}

/**
 * PUT request
 */
export async function apiPut<T>(url: string, data?: any): Promise<T> {
  return apiFetch<T>(url, {
    method: 'PUT',
    body: data ? JSON.stringify(data) : undefined,
  })
}

/**
 * DELETE request
 */
export async function apiDelete<T>(url: string): Promise<T> {
  return apiFetch<T>(url, { method: 'DELETE' })
}

/**
 * PATCH request
 */
export async function apiPatch<T>(url: string, data?: any): Promise<T> {
  return apiFetch<T>(url, {
    method: 'PATCH',
    body: data ? JSON.stringify(data) : undefined,
  })
}
