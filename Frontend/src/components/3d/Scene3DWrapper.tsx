'use client';

import { useState, useEffect } from 'react';

interface Scene3DWrapperProps {
  children: React.ReactNode;
  className?: string;
  fallback?: React.ReactNode;
  enableControls?: boolean;
  cameraPosition?: [number, number, number];
  fov?: number;
}

/**
 * Placeholder 3D Scene Wrapper
 * To enable 3D rendering, install: npm install three @react-three/fiber @react-three/drei
 */
export function Scene3DWrapper({
  children,
  className = '',
  fallback,
  enableControls = false,
  cameraPosition = [0, 0, 5],
  fov = 75,
}: Scene3DWrapperProps) {
  const [prefersReducedMotion, setPrefersReducedMotion] = useState(false);

  useEffect(() => {
    const mediaQuery = window.matchMedia('(prefers-reduced-motion: reduce)');
    setPrefersReducedMotion(mediaQuery.matches);

    const handleChange = (e: MediaQueryListEvent) => {
      setPrefersReducedMotion(e.matches);
    };

    mediaQuery.addEventListener('change', handleChange);
    return () => {
      mediaQuery.removeEventListener('change', handleChange);
    };
  }, []);

  // Return fallback or placeholder when 3D is not available
  return (
    <div 
      className={`relative w-full h-full bg-gradient-to-br from-cyan-500/5 to-teal-500/5 rounded-lg border border-cyan-500/10 flex items-center justify-center ${className}`}
      style={{ minHeight: '400px' }}
    >
      {fallback || (
        <div className="text-center">
          <div className="text-6xl font-bold text-cyan-500/30 mb-4">🎬</div>
          <p className="text-muted-foreground">3D Scene (optional)</p>
          <p className="text-xs text-muted-foreground mt-2">Install @react-three/fiber for 3D rendering</p>
        </div>
      )}
    </div>
  );
}
