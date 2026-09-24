import { useMemo } from 'react'
import { useQuery } from '@tanstack/react-query'
import { apiClient } from '@/lib/api'
import type { ProviderInfo } from '@/lib/api-types'

/**
 * The backend's provider registry, with how the current user can reach each
 * provider. The single source for provider names, key links and capabilities:
 * nothing about providers is hard-coded in the frontend.
 */
export function useProviders() {
  const query = useQuery({
    queryKey: ['providers'],
    queryFn: () => apiClient.getProviders(),
    staleTime: 60 * 1000,
  })
  const providers = useMemo(() => query.data?.providers ?? [], [query.data])
  const byId = useMemo(() => new Map(providers.map(p => [p.id, p])), [providers])
  return {
    ...query,
    providers,
    getProvider: (id: string): ProviderInfo | undefined => byId.get(id),
  }
}

/** Short status for a provider's access, in plain words. */
export function describeAccess(provider: Pick<ProviderInfo, 'access' | 'requires_key'>): string {
  switch (provider.access) {
    case 'connection':
      return 'Connected'
    case 'deployment':
      return 'Uses the deployment key'
    case 'none-needed':
      return 'No key needed'
    default:
      return provider.requires_key ? 'Needs your API key' : 'Not set up'
  }
}
