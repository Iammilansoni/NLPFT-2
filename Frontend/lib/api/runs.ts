/**
 * Test Runs API Service
 * Handle test run history and recent activity
 */

import { apiGet, apiPost, apiPatch, API_ENDPOINTS } from './client'
import type { TestRun, TestRunCreateRequest } from './types'

export const runsApi = {
  /**
   * Get recent test runs for dashboard
   */
  async getRecent(limit: number = 10, status?: string): Promise<TestRun[]> {
    const params: Record<string, any> = { limit }
    if (status) {
      params.status = status
    }
    // Backend returns { total: number, runs: TestRun[] }
    const response = await apiGet<{ runs: TestRun[], total: number }>(API_ENDPOINTS.runs.list, params)
    return response.runs || []
  },

  /**
   * Get a specific test run by ID
   */
  async get(id: number): Promise<TestRun> {
    return apiGet<TestRun>(API_ENDPOINTS.runs.get(id))
  },

  /**
   * Create a new test run
   */
  async create(testRun: TestRunCreateRequest): Promise<TestRun> {
    return apiPost<TestRun>(API_ENDPOINTS.runs.create, testRun)
  },

  /**
   * Update a test run
   */
  async update(
    id: number,
    updates: {
      status?: string
      error_message?: string
      tests_count?: number
    }
  ): Promise<TestRun> {
    return apiPatch<TestRun>(API_ENDPOINTS.runs.update(id), updates)
  },
}



