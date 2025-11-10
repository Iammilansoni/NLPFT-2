import { Metadata } from 'next'
import { Hero } from '@/components/landing/Hero'
import { HowItWorks } from '@/components/landing/HowItWorks'
import { FeatureHighlights } from '@/components/landing/FeatureHighlights'
import { MetricsProof } from '@/components/landing/MetricsProof'
import { PricingTeaser } from '@/components/landing/PricingTeaser'
import { FAQ } from '@/components/landing/FAQ'
import { CTABanner } from '@/components/landing/CTABanner'
import { LandingFooter } from '@/components/landing/LandingFooter'

export const metadata: Metadata = {
  title: 'NLPForge-Tester | Turn API Hints into Full Test Coverage',
  description: 'Paste a plain-English request. We handle dataset creation, embeddings, and validation—end-to-end. Built for teams in regulated environments.',
  openGraph: {
    title: 'NLPForge-Tester | AI-Powered API Testing',
    description: 'Turn one API hint into full test coverage with intelligent dataset generation and semantic validation.',
    type: 'website',
    images: ['/og-image.png'],
  },
  twitter: {
    card: 'summary_large_image',
    title: 'NLPForge-Tester | AI-Powered API Testing',
    description: 'Turn one API hint into full test coverage',
  },
}

export default function LandingPage() {
  return (
    <div className="flex flex-col">
      <Hero />
      <HowItWorks />
      <FeatureHighlights />
      <MetricsProof />
      <PricingTeaser />
      <FAQ />
      <CTABanner />
      <LandingFooter />
    </div>
  )
}
