/**
 * Template API Service
 * Manage API templates (CRUD operations)
 */

import { apiGet, apiPost, apiPut, apiDelete, API_ENDPOINTS } from './client'
import type {
  Template,
  TemplateCreateRequest,
  TemplateUpdateRequest,
  SyncResponse,
  ReloadResponse,
  TemplateStatsResponse,
} from './types'

export const templateApi = {
  /**
   * List all API templates
   */
  async list(): Promise<Template[]> {
    return apiGet<Template[]>(API_ENDPOINTS.templates.list)
  },

  /**
   * Get a specific template by intent
   */
  async get(intent: string): Promise<Template> {
    return apiGet<Template>(API_ENDPOINTS.templates.get(intent))
  },

  /**
   * Create a new template
   */
  async create(template: TemplateCreateRequest): Promise<Template> {
    return apiPost<Template>(API_ENDPOINTS.templates.create, template)
  },

  /**
   * Update an existing template
   */
  async update(intent: string, updates: TemplateUpdateRequest): Promise<Template> {
    return apiPut<Template>(API_ENDPOINTS.templates.update(intent), updates)
  },

  /**
   * Delete a template
   */
  async delete(intent: string): Promise<void> {
    return apiDelete<void>(API_ENDPOINTS.templates.delete(intent))
  },

  /**
   * Sync templates from JSON file to database
   */
  async sync(): Promise<SyncResponse> {
    return apiPost<SyncResponse>(API_ENDPOINTS.templates.sync)
  },

  /**
   * Hot reload all services without server restart
   */
  async reload(): Promise<ReloadResponse> {
    return apiPost<ReloadResponse>(API_ENDPOINTS.templates.reload)
  },

  /**
   * Get template statistics
   */
  async getStats(): Promise<TemplateStatsResponse> {
    return apiGet<TemplateStatsResponse>(API_ENDPOINTS.templates.stats)
  },
}
