'use client';



import { useEffect } from 'react';

export function HydrationWarningSuppress() {
  useEffect(() => {
    const originalError = console.error;
    
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    console.error = (...args: any[]) => {
      
      if (
        typeof args[0] === 'string' &&
        (
          args[0].includes('Hydration failed') ||
          args[0].includes('hydrated but some attributes') ||
          args[0].includes('did not match') ||
          args[0].includes('fdprocessedid') ||
          args[0].includes('data-new-gr-c-s-check-loaded') ||
          args[0].includes('data-gr-ext-installed')
        )
      ) {
        
        return;
      }
      
      
      originalError.call(console, ...args);
    };

    return () => {
      console.error = originalError;
    };
  }, []);

  return null;
}


if (typeof window !== 'undefined') {
  const originalError = console.error;
  
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  console.error = (...args: any[]) => {
    if (
      typeof args[0] === 'string' &&
      (
        args[0].includes('Hydration failed') ||
        args[0].includes('hydrated but some attributes') ||
        args[0].includes('did not match') ||
        args[0].includes('fdprocessedid') ||
        args[0].includes('data-new-gr-c-s-check-loaded') ||
        args[0].includes('data-gr-ext-installed')
      )
    ) {
      return;
    }
    originalError.call(console, ...args);
  };
}
