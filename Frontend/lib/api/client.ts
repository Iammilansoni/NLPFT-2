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

    // Check for invalid token format error
    if (response.status === 401 && errorMessage.includes('Token format invalid')) {
      // Clear invalid token from storage
      if (typeof window !== 'undefined') {
        localStorage.removeItem('token')
        localStorage.removeItem('user')
        console.warn('🔄 Invalid token detected and cleared. Please log in again.')
        // Redirect to login page
        window.location.href = '/login'
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
    // Get auth token from localStorage
    const token = typeof window !== 'undefined' ? localStorage.getItem('nlpforge_access_token') : null

    const response = await fetch(url, {
      ...options,
      headers: {
        'Content-Type': 'application/json',
        ...(token ? { 'Authorization': `Bearer ${token}` } : {}),
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
