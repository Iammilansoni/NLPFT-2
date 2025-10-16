'use client';

import { useEffect, useRef } from 'react';
import Lenis from '@studio-freight/lenis';

interface SmoothScrollProviderProps {
  children: React.ReactNode;
}


export function SmoothScrollProvider({ children }: SmoothScrollProviderProps) {
  const lenisRef = useRef<Lenis | null>(null);
  const rafRef = useRef<number | null>(null);

  useEffect(() => {
    
    const mediaQuery = window.matchMedia('(prefers-reduced-motion: reduce)');
    if (mediaQuery.matches) {
      return;
    }

    
    lenisRef.current = new Lenis({
      duration: 1.2,
      easing: (t) => Math.min(1, 1.001 - Math.pow(2, -10 * t)),
    });

    
    function raf(time: number) {
      lenisRef.current?.raf(time);
      rafRef.current = requestAnimationFrame(raf);
    }

    rafRef.current = requestAnimationFrame(raf);

    
    return () => {
      if (rafRef.current !== null) {
        cancelAnimationFrame(rafRef.current);
      }
      lenisRef.current?.destroy();
    };
  }, []);

  return <>{children}</>;
}


export function useLenis(): Lenis | null {
  const lenisRef = useRef<Lenis | null>(null);

  useEffect(() => {
    
    const checkLenis = () => {
      if (window.lenis) {
        lenisRef.current = window.lenis;
      }
    };

    checkLenis();
    
    
    const timeout = setTimeout(checkLenis, 100);

    return () => clearTimeout(timeout);
  }, []);

  return lenisRef.current;
}


declare global {
  interface Window {
    lenis?: Lenis;
  }
}
