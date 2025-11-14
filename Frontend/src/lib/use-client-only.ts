'use client';

import { useEffect, useState } from 'react';

/**
 * Hook to prevent hydration mismatches by only rendering content after client-side hydration
 * @param serverFallback - What to render on the server/initial hydration
 * @param clientContent - What to render after hydration is complete
 */
export function useClientOnly<T>(serverFallback: T, clientContent: T): T {
  const [isClient, setIsClient] = useState(false);

  useEffect(() => {
    setIsClient(true);
  }, []);

  return isClient ? clientContent : serverFallback;
}

/**
 * Simple hook that returns true only after client-side hydration is complete
 */
export function useIsClient(): boolean {
  const [isClient, setIsClient] = useState(false);

  useEffect(() => {
    setIsClient(true);
  }, []);

  return isClient;
}