# NLPForge-Tester Landing Page

## Overview

Production-grade B2B SaaS landing page built with Next.js 14 App Router, TypeScript, TailwindCSS, shadcn/ui, Framer Motion, and lucide-react.

## Features

### ✨ Design & UX
- **Modern Clean SaaS Design** - Professional, hand-crafted look (not AI-template)
- **Responsive Layout** - Mobile-first, works perfectly on all devices
- **Light/Dark Themes** - First-class theme support with next-themes
- **Smooth Animations** - Tasteful micro-interactions with Framer Motion
- **Accessibility** - WCAG AA compliant with semantic HTML and ARIA labels

### 🎨 Visual Elements
- **Teal Primary Color** (#06B6D4) - Used sparingly for impact
- **Soft Radius** (12-16px) - Modern, approachable feel
- **Layered Shadows** - Subtle depth and hierarchy
- **Gradient Accents** - Strategic use for CTAs and highlights
- **Custom Design Tokens** - CSS variables for consistent theming

### 📄 Page Sections

1. **Hero Section**
   - Compelling headline and value proposition
   - Live demo card with animated query processing
   - Primary and secondary CTAs
   - Trust badges (ISO/SOC compliance)

2. **How It Works** (4 Steps)
   - Understand Query (NER + QA)
   - Generate Dataset (Gemini AI)
   - Embed & Search (Redis Vector)
   - Run & Report (Testing)

3. **Feature Highlights**
   - Auto-templates & versioning
   - Incremental dataset enrichment
   - Redis vector + filters
   - Confidence scoring & explainability
   - Code snippets for technical credibility

4. **Metrics & Social Proof**
   - Animated stat counters (50k+ tests/day, 45ms latency, 94.2% pass rate)
   - Customer testimonials with avatars
   - Real-world use cases

5. **Pricing Teaser**
   - Starter, Team, Enterprise tiers
   - Feature comparison
   - Contact sales dialog for Enterprise

6. **FAQ Accordion**
   - 6 common questions (security, rate limits, multi-tenant, export, support, on-premise)
   - Smooth expand/collapse animations

7. **CTA Banner**
   - Final conversion opportunity
   - Gradient background with decorative elements

8. **Footer**
   - Product, Company, Resources, Legal links
   - Social media icons
   - Theme toggle
   - Copyright notice

### 🚀 Performance

- **Lighthouse Score Target**: 95+ on all metrics
- **Image Optimization**: next/image for all images
- **Font Optimization**: next/font (Inter + Manrope)
- **Code Splitting**: Dynamic imports for heavy components
- **Reduced Motion**: Respects prefers-reduced-motion

### ♿ Accessibility

- Semantic HTML5 landmarks
- Keyboard navigation support
- ARIA labels and descriptions
- Visible focus indicators
- Alt text for all images
- Color contrast meets WCAG AA

## File Structure

```
Frontend/
├── src/
│   ├── app/
│   │   ├── landing/
│   │   │   ├── layout.tsx          # Landing-specific layout with LandingNav
│   │   │   └── page.tsx            # Main landing page composition
│   │   ├── dashboard/
│   │   │   ├── layout.tsx          # Dashboard layout with Navigation
│   │   │   └── page.tsx
│   │   ├── layout.tsx              # Root layout with theme provider
│   │   └── page.tsx                # Redirects to /landing
│   ├── components/
│   │   ├── landing/
│   │   │   ├── Hero.tsx            # Hero section with badge and CTAs
│   │   │   ├── HeroDemo.tsx        # Animated demo card
│   │   │   ├── HowItWorks.tsx      # 4-step process
│   │   │   ├── FeatureHighlights.tsx # Feature grid with code snippets
│   │   │   ├── MetricsProof.tsx    # Stats and testimonials
│   │   │   ├── PricingTeaser.tsx   # Pricing cards
│   │   │   ├── FAQ.tsx             # Accordion FAQ
│   │   │   ├── CTABanner.tsx       # Final CTA section
│   │   │   ├── LandingFooter.tsx   # Footer with links
│   │   │   └── LandingNav.tsx      # Sticky navigation
│   │   ├── ui/
│   │   │   ├── accordion.tsx       # Radix UI accordion
│   │   │   ├── badge.tsx
│   │   │   ├── button.tsx
│   │   │   ├── card.tsx
│   │   │   ├── dialog.tsx
│   │   │   └── ...
│   │   └── ThemeToggle.tsx         # Theme switcher
│   ├── lib/
│   │   ├── seo.ts                  # SEO metadata helpers
│   │   └── utils.ts
│   └── styles/
│       └── globals.css             # Enhanced design tokens
└── tailwind.config.ts              # Extended with animations
```

## Usage

### Development

```bash
cd Frontend
npm run dev
```

Visit `http://localhost:3000/landing` to see the landing page.

### Routes

- `/` - Redirects to `/landing`
- `/landing` - Main landing page
- `/dashboard` - Application dashboard (requires auth)
- `/search`, `/templates`, `/datasets` - App features

### Customization

#### Colors

Edit `Frontend/src/styles/globals.css`:

```css
:root {
  --primary: 188 94% 43%; /* Teal #06B6D4 */
  --accent: 188 94% 43%;
  /* ... */
}
```

#### Content

Edit component files in `Frontend/src/components/landing/`:
- Update headlines, descriptions, and CTAs
- Modify feature lists and pricing tiers
- Change testimonials and stats

#### Animations

Adjust timing in component files:
```tsx
transition={{ duration: 0.5, delay: 0.2 }}
```

Or disable for reduced motion users (automatically handled).

## SEO

### Metadata

Configured in `Frontend/src/app/landing/page.tsx`:
- Title, description, keywords
- Open Graph tags for social sharing
- Twitter Card metadata

### Best Practices

- Semantic HTML structure
- Descriptive alt text
- Internal linking
- Fast page load times
- Mobile-friendly design

## Deployment

### Vercel (Recommended)

```bash
npm run build
vercel deploy
```

### Environment Variables

None required for landing page. For full app functionality:
- `NEXT_PUBLIC_API_URL` - Backend API endpoint

## Browser Support

- Chrome/Edge (latest 2 versions)
- Firefox (latest 2 versions)
- Safari (latest 2 versions)
- Mobile browsers (iOS Safari, Chrome Mobile)

## License

Proprietary - NLPForge-Tester

## Support

For questions or issues:
- Email: hello@nlpforge.com
- Docs: /docs
- Community: /community
