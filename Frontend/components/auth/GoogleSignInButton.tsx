/**
 * GoogleSignInButton — renders Google Identity Services' own "Sign In With
 * Google" button and exchanges the ID token it returns for a session via
 * POST /api/v1/auth/google (see AuthContext.loginWithGoogle).
 *
 * Falls back to a disabled placeholder when NEXT_PUBLIC_GOOGLE_CLIENT_ID
 * isn't set, rather than rendering a button that can never work.
 */
'use client';

import { useEffect, useRef, useState } from 'react';
import { useRouter } from 'next/navigation';
import { useAuth } from '@/contexts/AuthContext';

declare global {
  interface Window {
    google?: {
      accounts: {
        id: {
          initialize: (config: Record<string, unknown>) => void;
          renderButton: (el: HTMLElement, options: Record<string, unknown>) => void;
        };
      };
    };
  }
}

interface GoogleSignInButtonProps {
  onError?: (message: string) => void;
}

export default function GoogleSignInButton({ onError }: GoogleSignInButtonProps) {
  const { loginWithGoogle } = useAuth();
  const router = useRouter();
  const buttonRef = useRef<HTMLDivElement>(null);
  const [scriptLoaded, setScriptLoaded] = useState(false);
  const clientId = process.env.NEXT_PUBLIC_GOOGLE_CLIENT_ID;

  // Load the GIS script once (it's safe to share across pages/mounts).
  useEffect(() => {
    if (!clientId) return;
    if (window.google?.accounts?.id) {
      setScriptLoaded(true);
      return;
    }
    const existing = document.getElementById('google-identity-services');
    if (existing) {
      existing.addEventListener('load', () => setScriptLoaded(true), { once: true });
      return;
    }
    const script = document.createElement('script');
    script.id = 'google-identity-services';
    script.src = 'https://accounts.google.com/gsi/client';
    script.async = true;
    script.defer = true;
    script.onload = () => setScriptLoaded(true);
    document.body.appendChild(script);
  }, [clientId]);

  useEffect(() => {
    if (!scriptLoaded || !clientId || !buttonRef.current || !window.google) return;

    window.google.accounts.id.initialize({
      client_id: clientId,
      callback: async (response: { credential: string }) => {
        try {
          await loginWithGoogle(response.credential);
          const searchParams = new URLSearchParams(window.location.search);
          const from = searchParams.get('from');
          router.push(from || '/dashboard');
        } catch (err: any) {
          onError?.(
            err?.response?.data?.detail || 'Google sign-in failed. Please try again.'
          );
        }
      },
    });

    // Clear before rendering so re-runs (e.g. onError identity changing)
    // don't stack up duplicate Google-rendered buttons.
    buttonRef.current.innerHTML = '';
    window.google.accounts.id.renderButton(buttonRef.current, {
      theme: 'outline',
      size: 'large',
      shape: 'pill',
      text: 'continue_with',
      width: 360,
    });
    // loginWithGoogle/router/onError are stable enough in practice; the
    // real trigger for this effect is the script finishing load.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [scriptLoaded, clientId]);

  if (!clientId) {
    return (
      <button
        type="button"
        disabled
        title="Google sign-in is not configured on this deployment"
        aria-label="Continue with Google - not configured"
        className="w-full px-6 py-3.5 bg-background border border-border text-foreground font-medium rounded-lg flex items-center justify-center gap-3 opacity-50 cursor-not-allowed"
      >
        <GoogleGlyph />
        Continue with Google
        <span className="text-xs text-muted-foreground">(not configured)</span>
      </button>
    );
  }

  return <div ref={buttonRef} className="w-full flex justify-center" />;
}

function GoogleGlyph() {
  return (
    <svg className="w-5 h-5" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
      <path d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z" fill="#4285F4"/>
      <path d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z" fill="#34A853"/>
      <path d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z" fill="#FBBC05"/>
      <path d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z" fill="#EA4335"/>
    </svg>
  );
}
