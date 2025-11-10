import { useState, useCallback } from 'react';
import { copyToClipboard as copy } from '@/lib/utils-extended';

export function useCopyToClipboard() {
  const [isCopied, setIsCopied] = useState(false);
  const [error, setError] = useState<Error | null>(null);

  const copyToClipboard = useCallback(async (text: string) => {
    try {
      await copy(text);
      setIsCopied(true);
      setError(null);
      setTimeout(() => setIsCopied(false), 2000);
    } catch (err) {
      setError(err as Error);
      setIsCopied(false);
    }
  }, []);

  return { isCopied, error, copyToClipboard };
}
