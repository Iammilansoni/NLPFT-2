'use client';

import { LandingNav } from '@/components/landing/LandingNav';
import { HeroSection } from '@/components/hero/HeroSection';

/**
 * Landing Page - NLPForge
 * 
 * Enterprise-grade landing page following "Enterprise Calm" design direction:
 * - Clean navigation with accessible mobile menu
 * - Split hero layout with product preview
 * - No flashy animations or gradient backgrounds
 * - Professional, understated, high trust design
 */
export default function Home() {
  return (
    <div className="min-h-screen bg-background overflow-x-hidden">
      {/* Navigation */}
      <LandingNav />

      {/* Main Content */}
      <main>
        <HeroSection />
      </main>
    </div>
  );
}
