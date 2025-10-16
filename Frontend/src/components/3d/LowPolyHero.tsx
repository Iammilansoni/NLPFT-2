'use client';

import { useRef, useMemo } from 'react';
import { useFrame } from '@react-three/fiber';
import { Mesh, BufferGeometry, Material } from 'three';
import * as THREE from 'three';

interface LowPolyHeroProps {
  scale?: number;
  rotationSpeed?: number;
  color?: string;
}


export function LowPolyHero({ 
  scale = 1, 
  rotationSpeed = 0.001,
  color = '#0EA5A4' 
}: LowPolyHeroProps) {
  const meshRef = useRef<Mesh<BufferGeometry, Material | Material[]>>(null);

  
  const shaderMaterial = useMemo(
    () =>
      new THREE.ShaderMaterial({
        uniforms: {
          time: { value: 0 },
          colorA: { value: new THREE.Color(color) },
          colorB: { value: new THREE.Color('#4dd2d1') },
        },
        vertexShader: `
          uniform float time;
          varying vec2 vUv;
          varying vec3 vPosition;
          
          void main() {
            vUv = uv;
            vPosition = position;
            
            // Subtle wave animation
            vec3 pos = position;
            float wave = sin(position.x * 2.0 + time) * 0.1;
            pos.z += wave;
            
            gl_Position = projectionMatrix * modelViewMatrix * vec4(pos, 1.0);
          }
        `,
        fragmentShader: `
          uniform vec3 colorA;
          uniform vec3 colorB;
          varying vec2 vUv;
          varying vec3 vPosition;
          
          void main() {
            // Gradient based on position
            vec3 color = mix(colorA, colorB, vUv.y);
            gl_FragColor = vec4(color, 0.9);
          }
        `,
        transparent: true,
        side: THREE.DoubleSide,
      }),
    [color]
  );

  
  useFrame((state) => {
    if (meshRef.current) {
      
      meshRef.current.rotation.x += rotationSpeed;
      meshRef.current.rotation.y += rotationSpeed * 1.5;
      
      
      if (shaderMaterial.uniforms.time) {
        shaderMaterial.uniforms.time.value = state.clock.elapsedTime;
      }
    }
  });

  return (
    <mesh ref={meshRef} scale={scale} material={shaderMaterial}>
      <icosahedronGeometry args={[1, 0]} />
    </mesh>
  );
}


export function GeometricParticles({ count = 50 }: { count?: number }) {
  const particlesRef = useRef<THREE.Points>(null);

  const particles = useMemo(() => {
    const positions = new Float32Array(count * 3);
    
    for (let i = 0; i < count; i++) {
      positions[i * 3] = (Math.random() - 0.5) * 10;
      positions[i * 3 + 1] = (Math.random() - 0.5) * 10;
      positions[i * 3 + 2] = (Math.random() - 0.5) * 10;
    }
    
    return positions;
  }, [count]);

  useFrame(() => {
    if (particlesRef.current) {
      particlesRef.current.rotation.y += 0.0005;
    }
  });

  return (
    <points ref={particlesRef}>
      <bufferGeometry>
        <bufferAttribute
          attach="attributes-position"
          count={particles.length / 3}
          array={particles}
          itemSize={3}
        />
      </bufferGeometry>
      <pointsMaterial
        size={0.02}
        color="#0EA5A4"
        transparent
        opacity={0.6}
        sizeAttenuation
      />
    </points>
  );
}
