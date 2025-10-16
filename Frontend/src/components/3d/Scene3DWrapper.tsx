'use client';

import { Suspense, useEffect, useState } from 'react';
import { Canvas } from '@react-three/fiber';
import { OrbitControls, PerspectiveCamera } from '@react-three/drei';
import { useTheme } from 'next-themes';

interface Scene3DWrapperProps {
  children: React.ReactNode;
  className?: string;
  fallback?: React.ReactNode;
  enableControls?: boolean;
  cameraPosition?: [number, number, number];
  fov?: number;
}


export function Scene3DWrapper({
  children,
  className = '',
  fallback,
  enableControls = false,
  cameraPosition = [0, 0, 5],
  fov = 75,
}: Scene3DWrapperProps) {
  const { theme, systemTheme } = useTheme();
  const [shouldRender3D, setShouldRender3D] = useState(false);
  const [prefersReducedMotion, setPrefersReducedMotion] = useState(false);

  useEffect(() => {
    
    const mediaQuery = window.matchMedia('(prefers-reduced-motion: reduce)');
    setPrefersReducedMotion(mediaQuery.matches);

    const handleChange = (e: MediaQueryListEvent) => {
      setPrefersReducedMotion(e.matches);
    };

    mediaQuery.addEventListener('change', handleChange);

    
    const isMobile = /iPhone|iPad|iPod|Android/i.test(navigator.userAgent);
    const hasTouch = 'ontouchstart' in window;
    const isLowPower = navigator.hardwareConcurrency ? navigator.hardwareConcurrency < 4 : false;

    
    const canRender3D = !isMobile && !hasTouch && !isLowPower && !mediaQuery.matches;
    setShouldRender3D(canRender3D);

    return () => {
      mediaQuery.removeEventListener('change', handleChange);
    };
  }, []);

  
  if (!shouldRender3D || prefersReducedMotion) {
    return <>{fallback}</>;
  }

  const currentTheme = theme === 'system' ? systemTheme : theme;
  const isDark = currentTheme === 'dark';

  return (
    <div className={`relative w-full h-full ${className}`} aria-hidden="true">
      <Canvas
        className="w-full h-full"
        dpr={[1, 2]}
        performance={{ min: 0.5 }}
        gl={{
          antialias: true,
          alpha: true,
          powerPreference: 'high-performance',
        }}
      >
        <PerspectiveCamera makeDefault position={cameraPosition} fov={fov} />
        
        <ambientLight intensity={isDark ? 0.3 : 0.5} />
        <directionalLight
          position={[10, 10, 5]}
          intensity={isDark ? 0.5 : 1}
          castShadow
        />
        <pointLight position={[-10, -10, -5]} intensity={isDark ? 0.3 : 0.5} />

        <Suspense fallback={null}>
          {children}
        </Suspense>

        {enableControls && (
          <OrbitControls
            enableZoom={false}
            enablePan={false}
            maxPolarAngle={Math.PI / 2}
            minPolarAngle={Math.PI / 2}
          />
        )}
      </Canvas>
    </div>
  );
}
