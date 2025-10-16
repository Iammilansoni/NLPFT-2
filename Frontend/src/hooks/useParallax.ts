'use client';

import { useEffect, useState, useCallback, useRef } from 'react';

interface ParallaxOptions {
  strength?: number;
  throttle?: number;
  disabled?: boolean;
}

interface ParallaxState {
  x: number;
  y: number;
}


export function useParallax({
  strength = 10,
  throttle = 16,
  disabled = false,
}: ParallaxOptions = {}): ParallaxState {
  const [position, setPosition] = useState<ParallaxState>({ x: 0, y: 0 });
  const rafRef = useRef<number | null>(null);
  const lastUpdate = useRef<number>(0);

  const handleMouseMove = useCallback(
    (e: MouseEvent) => {
      const now = Date.now();
      
      
      if (now - lastUpdate.current < throttle) {
        return;
      }

      lastUpdate.current = now;

      
      if (rafRef.current !== null) {
        cancelAnimationFrame(rafRef.current);
      }

      
      rafRef.current = requestAnimationFrame(() => {
        const { clientX, clientY } = e;
        const { innerWidth, innerHeight } = window;

        
        const normalizedX = (clientX / innerWidth - 0.5) * 2;
        const normalizedY = (clientY / innerHeight - 0.5) * 2;

        
        setPosition({
          x: normalizedX * strength,
          y: normalizedY * strength,
        });
      });
    },
    [strength, throttle]
  );

  useEffect(() => {
    
    const isTouchDevice = 'ontouchstart' in window;
    if (disabled || isTouchDevice) {
      return;
    }

    
    const mediaQuery = window.matchMedia('(prefers-reduced-motion: reduce)');
    if (mediaQuery.matches) {
      return;
    }

    window.addEventListener('mousemove', handleMouseMove, { passive: true });

    return () => {
      window.removeEventListener('mousemove', handleMouseMove);
      
      
      if (rafRef.current !== null) {
        cancelAnimationFrame(rafRef.current);
      }
    };
  }, [handleMouseMove, disabled]);

  return position;
}


export function useScrollParallax(speed: number = 0.5): number {
  const [offset, setOffset] = useState(0);
  const rafRef = useRef<number | null>(null);

  useEffect(() => {
    
    const mediaQuery = window.matchMedia('(prefers-reduced-motion: reduce)');
    if (mediaQuery.matches) {
      return;
    }

    const handleScroll = () => {
      if (rafRef.current !== null) {
        cancelAnimationFrame(rafRef.current);
      }

      rafRef.current = requestAnimationFrame(() => {
        setOffset(window.scrollY * speed);
      });
    };

    window.addEventListener('scroll', handleScroll, { passive: true });
    
    return () => {
      window.removeEventListener('scroll', handleScroll);
      if (rafRef.current !== null) {
        cancelAnimationFrame(rafRef.current);
      }
    };
  }, [speed]);

  return offset;
}
