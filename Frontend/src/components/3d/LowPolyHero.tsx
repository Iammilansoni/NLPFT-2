'use client';

// This component requires @react-three/fiber and three.js
// For now, it's a stub component that renders a placeholder
// Install with: npm install three @react-three/fiber @react-three/drei

interface LowPolyHeroProps {
  scale?: number;
  rotationSpeed?: number;
  color?: string;
}

/**
 * Placeholder 3D Hero component
 * To enable 3D rendering, install: npm install three @react-three/fiber @react-three/drei
 */
export function LowPolyHero({ 
  scale = 1, 
  rotationSpeed = 0.001,
  color = '#0EA5A4' 
}: LowPolyHeroProps) {
  return (
    <div 
      className="w-full h-full flex items-center justify-center bg-gradient-to-br from-cyan-500/10 to-teal-500/10 rounded-lg border border-cyan-500/20"
      style={{ minHeight: '400px' }}
    >
      <div className="text-center">
        <div className="text-6xl font-bold text-cyan-500/30 mb-4">🎯</div>
        <p className="text-muted-foreground">3D visualization (optional)</p>
        <p className="text-xs text-muted-foreground mt-2">Install three.js for 3D rendering</p>
      </div>
    </div>
  );
}

/**
 * Placeholder geometric particles component
 */
export function GeometricParticles({ count = 50 }: { count?: number }) {
  return (
    <div 
      className="w-full h-full flex items-center justify-center bg-gradient-to-br from-cyan-500/5 to-teal-500/5 rounded-lg border border-cyan-500/10"
      style={{ minHeight: '300px' }}
    >
      <div className="text-center">
        <p className="text-muted-foreground text-sm">Particle effects (optional)</p>
      </div>
    </div>
  );
}
