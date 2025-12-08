/**
 * Main API Export
 * Central export point for all API services
 */

// Re-export types
export * from './types'
export * from './client'

// Re-export individual API modules
export { queryApi } from './query'
export { templateApi } from './templates'
export { searchApi } from './search'

// Default export with all services
import { queryApi } from './query'
import { templateApi } from './templates'
import { searchApi } from './search'

const api = {
  query: queryApi,
  templates: templateApi,
  search: searchApi,
}

export default api
