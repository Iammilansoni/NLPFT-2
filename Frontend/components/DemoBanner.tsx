/**
 * DemoBanner - recruiter-facing notice for the public demo deployment.
 *
 * Renders nothing unless DEMO_MODE is on (NEXT_PUBLIC_DEMO_MODE=true), so it
 * is a no-op in local/dev and in any deployment that didn't opt in. Dismiss
 * state lives in sessionStorage so it reappears on the next visit/tab rather
 * than being gone for good after one click.
 */

'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import { X, Sparkles } from 'lucide-react';
import { DEMO_MODE, DEMO_CREDENTIALS } from '@/lib/constants';

const DISMISS_KEY = 'nlpforge-demo-banner-dismissed';

export default function DemoBanner() {
  const [dismissed, setDismissed] = useState(true); // default hidden until mount check runs

  useEffect(() => {
    if (!DEMO_MODE) return;
    try {
      setDismissed(sessionStorage.getItem(DISMISS_KEY) === '1');
    } catch {
      // sessionStorage unavailable (private mode, etc.) — just show the banner
      setDismissed(false);
    }
  }, []);

  if (!DEMO_MODE || dismissed) return null;

  const handleDismiss = () => {
    setDismissed(true);
    try {
      sessionStorage.setItem(DISMISS_KEY, '1');
    } catch {
      // ignore — worst case the banner comes back on next navigation
    }
  };

  return (
    <div className="relative z-50 flex flex-wrap items-center justify-center gap-x-3 gap-y-1 bg-primary px-4 py-2 text-center text-sm font-medium text-primary-foreground">
      <span className="inline-flex items-center gap-1.5">
        <Sparkles className="h-4 w-4 shrink-0" aria-hidden="true" />
        Live demo — seeded data, some actions are rate-limited.
      </span>
      <Link
        href="/auth/login?demo=1"
        className="inline-flex items-center rounded-md bg-primary-foreground/15 px-2.5 py-0.5 underline underline-offset-2 hover:bg-primary-foreground/25"
      >
        Try it with the demo login →
      </Link>
      <span className="hidden text-primary-foreground/80 sm:inline">
        ({DEMO_CREDENTIALS.email})
      </span>
      <button
        type="button"
        onClick={handleDismiss}
        aria-label="Dismiss demo banner"
        className="absolute right-2 top-1/2 -translate-y-1/2 rounded-md p-1 text-primary-foreground/80 hover:bg-primary-foreground/15 hover:text-primary-foreground"
      >
        <X className="h-4 w-4" />
      </button>
    </div>
  );
}
