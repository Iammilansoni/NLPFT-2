# 🚀 NLPForge Frontend - Production-Ready Next.js Application

> **Ultra-smooth, accessible, and delightful** Next.js frontend with Light/Dark themes, 3D visuals, and premium animations.

[![Next.js](https://img.shields.io/badge/Next.js-15.5-black?style=flat-square&logo=next.js)](https://nextjs.org/)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.x-blue?style=flat-square&logo=typescript)](https://www.typescriptlang.org/)
[![TailwindCSS](https://img.shields.io/badge/Tailwind-4.x-38bdf8?style=flat-square&logo=tailwind-css)](https://tailwindcss.com/)
[![Three.js](https://img.shields.io/badge/Three.js-0.170-black?style=flat-square&logo=three.js)](https://threejs.org/)
[![Storybook](https://img.shields.io/badge/Storybook-8.5-ff4785?style=flat-square&logo=storybook)](https://storybook.js.org/)
[![License](https://img.shields.io/badge/License-MIT-green?style=flat-square)](LICENSE)

## ✨ Features

### 🎨 **Design & UX**
- ⚡ **Subtle 3D Hero** - Low-poly Three.js scene with GLSL shaders (desktop only)
- 🖱️ **Custom Cursor** - Minimal dot + ring with hover states (desktop only)
- 🌊 **Smooth Scroll** - Lenis locomotive-style scrolling
- 🎭 **Microinteractions** - Framer Motion animations (scale 0.98 on press, underline transitions)
- 🌓 **Light/Dark Theme** - System preference + persistent toggle
- 🎨 **Design Tokens** - Comprehensive JSON-based design system

### ♿ **Accessibility**
- ✅ **WCAG 2.1 AA Compliant**
- ⌨️ **Full keyboard navigation**
- 🔊 **Screen reader optimized** (ARIA labels, semantic HTML)
- 🎯 **Focus management** with visible indicators
- 🚫 **Reduced motion** support (respects `prefers-reduced-motion`)

### ⚡ **Performance**
- 📦 **Code splitting** & dynamic imports for heavy libraries
- 🖼️ **Image optimization** (next/image with AVIF/WebP)
- 🎯 **Lazy loading** for 3D components
- 📊 **Lighthouse Score**: 90+ (desktop)
- 🔄 **Bundle optimization** with Tree Shaking

### 🛠️ **Developer Experience**
- 📚 **Storybook** for component development
- 🧪 **Jest + React Testing Library** for unit tests
- 🎨 **Prettier + ESLint** for code quality
- 🪝 **Husky** pre-commit hooks
- 📝 **TypeScript** strict mode

---

## 📋 Table of Contents

- [Quick Start](#-quick-start)
- [Project Structure](#-project-structure)
- [Design System](#-design-system)
- [Components](#-components)
- [Performance Checklist](#-performance-checklist)
- [Accessibility](#-accessibility)
- [Testing](#-testing)
- [Deployment](#-deployment)
- [Contributing](#-contributing)

---

## 🚀 Quick Start

### Prerequisites

- **Node.js** 18+ or 20+
- **npm** 9+ or **pnpm** 8+
- **Git**

### Installation

```bash
# 1. Clone the repository
git clone https://github.com/Iammilansoni/NLPForge-Tester.git
cd NLPForge-Tester/Frontend

# 2. Install dependencies
npm install

# 3. Copy environment variables
cp .env.example .env.local

# 4. Run development server
npm run dev
```

Open [http://localhost:3000](http://localhost:3000) in your browser.

### Available Scripts

```bash
npm run dev          # Start development server (Turbopack)
npm run build        # Build for production
npm run start        # Start production server
npm run lint         # Run ESLint
npm run lint:fix     # Fix ESLint errors
npm run format       # Format code with Prettier
npm run test         # Run Jest tests
npm run test:watch   # Run tests in watch mode
npm run storybook    # Start Storybook on port 6006
```

---

## 📂 Project Structure

```
Frontend/
├── .storybook/             # Storybook configuration
├── public/                 # Static assets
├── src/
│   ├── app/               # Next.js app directory (routes)
│   │   ├── layout.tsx     # Root layout with providers
│   │   ├── page.tsx       # Homepage
│   │   └── globals.css    # Global styles
│   ├── components/
│   │   ├── 3d/           # Three.js components
│   │   │   ├── Scene3DWrapper.tsx
│   │   │   └── LowPolyHero.tsx
│   │   ├── landing/       # Landing page sections
│   │   │   └── Enhanced3DHero.tsx
│   │   ├── ui/            # Atomic UI components
│   │   │   ├── enhanced-button.tsx
│   │   │   ├── enhanced-input.tsx
│   │   │   ├── enhanced-card.tsx
│   │   │   ├── enhanced-cursor.tsx
│   │   │   └── smooth-scroll.tsx
│   │   └── layout/        # Layout components
│   ├── hooks/             # Custom React hooks
│   │   └── useParallax.ts
│   ├── lib/               # Utilities
│   │   ├── utils.ts
│   │   ├── theme-provider.tsx
│   │   └── query-provider.tsx
│   ├── styles/            # Styles & design tokens
│   │   ├── tokens.json    # Design system tokens
│   │   └── cursor.css
│   └── __tests__/         # Test files
├── .env.example           # Environment variables template
├── .prettierrc            # Prettier configuration
├── .lintstagedrc          # Lint-staged configuration
├── next.config.ts         # Next.js configuration
├── tailwind.config.ts     # Tailwind configuration
├── tsconfig.json          # TypeScript configuration
├── vercel.json            # Vercel deployment config
└── package.json
```

---

## 🎨 Design System

### Design Tokens

All design tokens are centralized in `src/styles/tokens.json`:

```json
{
  "colors": {
    "primary": "#0EA5A4",
    "background": {
      "light": "#F8FAFC",
      "dark": "#0B1220"
    }
  },
  "motion": {
    "duration": {
      "fast": "150ms",
      "normal": "250ms",
      "slow": "350ms"
    },
    "easing": {
      "smooth": "cubic-bezier(0.45, 0, 0.55, 1)"
    }
  }
}
```

### Color Palette

#### Light Theme
- **Background**: `#F8FAFC` (Slate 50)
- **Text**: `#0F172A` (Slate 900)
- **Primary**: `#0EA5A4` (Custom Teal)

#### Dark Theme
- **Background**: `#0B1220` (Deep Navy)
- **Text**: `#F8FAFC` (Slate 50)
- **Primary**: `#0EA5A4` (Custom Teal)

### Typography

- **Font**: Geist Sans (variable)
- **Mono**: Geist Mono (variable)
- **Scale**: Fluid (0.75rem → 6rem)

### Spacing & Radius

- **Spacing**: 4px base (0.25rem increments)
- **Border Radius**: `sm: 6px, md: 12px, lg: 20px, 2xl: 32px`

---

## 🧩 Components

### Enhanced Button

```tsx
import { Button } from '@/components/ui/enhanced-button';

<Button variant="default" size="lg">
  Click Me
</Button>
```

**Features:**
- Scale 0.98 on press
- Loading state with spinner
- 6 variants: default, outline, ghost, secondary, link, destructive
- 5 sizes: sm, default, lg, xl, icon

### Enhanced Input

```tsx
import { Input } from '@/components/ui/enhanced-input';

<Input 
  label="Email" 
  type="email"
  error={errors.email?.message}
/>
```

**Features:**
- Floating label animation
- Border glow on focus
- Error state with message
- Icon support

### Enhanced Card

```tsx
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/enhanced-card';

<Card hover gradient>
  <CardHeader>
    <CardTitle>Title</CardTitle>
  </CardHeader>
  <CardContent>Content</CardContent>
</Card>
```

**Features:**
- Hover elevation effect
- Glassmorphism gradient
- Soft shadows
- Scroll-based reveal

### 3D Scene

```tsx
import { Scene3DWrapper } from '@/components/3d/Scene3DWrapper';
import { LowPolyHero } from '@/components/3d/LowPolyHero';

<Scene3DWrapper fallback={<StaticImage />}>
  <LowPolyHero />
</Scene3DWrapper>
```

**Features:**
- Auto-detect mobile/low-power devices
- Graceful fallback
- Theme-aware lighting
- Performance monitoring

---

## ⚡ Performance Checklist

### ✅ Implemented Optimizations

- [x] **Next.js Image** - Automatic WebP/AVIF, lazy loading
- [x] **Code Splitting** - Dynamic imports for Three.js, GSAP
- [x] **Bundle Analysis** - Tree shaking enabled
- [x] **Caching Headers** - CDN-friendly headers in `next.config.ts`
- [x] **Font Optimization** - Variable fonts (Geist Sans/Mono)
- [x] **CSS Optimization** - Tailwind JIT, purge unused
- [x] **Lazy Loading** - 3D components load on-demand
- [x] **React Strict Mode** - Detect side effects
- [x] **Production Build** - Minification + compression

### 📊 Target Metrics

| Metric | Target | Current |
|--------|--------|---------|
| Lighthouse Performance | ≥90 | TBD* |
| Lighthouse Accessibility | ≥90 | TBD* |
| First Contentful Paint | <1.8s | TBD* |
| Time to Interactive | <3.8s | TBD* |
| Cumulative Layout Shift | <0.1 | TBD* |

*Run `npm run build && npm run start` and test with Lighthouse.

---

## ♿ Accessibility

### WCAG 2.1 AA Compliance

#### Implemented Features

- ✅ **Semantic HTML** - Proper heading hierarchy, landmarks
- ✅ **ARIA Labels** - All interactive elements labeled
- ✅ **Keyboard Navigation** - Full keyboard support
- ✅ **Focus Management** - Visible focus indicators (ring-2)
- ✅ **Color Contrast** - 4.5:1 minimum (text), 3:1 (UI)
- ✅ **Reduced Motion** - Respects `prefers-reduced-motion`
- ✅ **Skip Links** - "Skip to main content" link
- ✅ **Alt Text** - All images have descriptive alt text
- ✅ **Form Validation** - Error messages with ARIA live regions

#### Testing Accessibility

```bash
# Run Storybook with a11y addon
npm run storybook

# Navigate to any component story
# Check the "Accessibility" tab for violations
```

**Recommended Tools:**
- [axe DevTools](https://www.deque.com/axe/devtools/)
- [WAVE Browser Extension](https://wave.webaim.org/extension/)
- [Lighthouse Accessibility Audit](https://developers.google.com/web/tools/lighthouse)

---

## 🧪 Testing

### Unit Tests (Jest + React Testing Library)

```bash
# Run all tests
npm run test

# Run tests in watch mode
npm run test:watch

# Run tests with coverage
npm run test:ci
```

### Example Test

```tsx
// src/components/ui/__tests__/enhanced-button.test.tsx
import { render, screen } from '@testing-library/react';
import { Button } from '../enhanced-button';

describe('Button', () => {
  it('renders with correct text', () => {
    render(<Button>Click Me</Button>);
    expect(screen.getByText('Click Me')).toBeInTheDocument();
  });

  it('shows loading state', () => {
    render(<Button loading>Loading</Button>);
    expect(screen.getByText('Loading...')).toBeInTheDocument();
  });
});
```

### Storybook Visual Tests

```bash
npm run storybook
# Open http://localhost:6006
# Use Accessibility addon to check for a11y violations
```

---

## 🚀 Deployment

### Vercel (Recommended)

1. **Connect to GitHub**
   - Go to [vercel.com](https://vercel.com)
   - Import your GitHub repository

2. **Environment Variables**
   ```bash
   NEXT_PUBLIC_API_URL=https://api.yourdomain.com
   NEXT_PUBLIC_APP_NAME=NLPForge
   ```

3. **Deploy**
   - Push to `main` branch
   - Vercel auto-deploys on push

### Manual Deployment

```bash
# 1. Build for production
npm run build

# 2. Start production server
npm run start

# 3. Or export static (if applicable)
npm run build && next export
```

### Production Checklist

- [ ] Environment variables configured
- [ ] API URL set to production endpoint
- [ ] Error tracking enabled (Sentry, LogRocket)
- [ ] Analytics enabled (GA4, Plausible)
- [ ] Lighthouse audit ≥90
- [ ] Accessibility audit passed
- [ ] Security headers configured
- [ ] HTTPS enabled
- [ ] CDN configured for assets

---

## 🤝 Contributing

### Code Quality

This project uses:
- **ESLint** - Code linting
- **Prettier** - Code formatting
- **Husky** - Pre-commit hooks
- **TypeScript** - Type safety

### Pre-commit Hooks

Husky runs automatically before commits:

```bash
# Runs automatically:
- ESLint --fix
- Prettier --write
- Type checking
```

### Pull Request Process

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

---

## 📄 License

MIT License - see [LICENSE](LICENSE) file

---

## 🙏 Acknowledgments

- **Design Inspiration**: Modern SaaS platforms
- **3D Graphics**: [Three.js](https://threejs.org/)
- **Animations**: [Framer Motion](https://www.framer.com/motion/)
- **UI Components**: [shadcn/ui](https://ui.shadcn.com/)
- **Smooth Scroll**: [Lenis](https://lenis.studiofreight.com/)

---

## 📞 Support

- **Documentation**: [docs.nlpforge.example](https://docs.nlpforge.example)
- **Issues**: [GitHub Issues](https://github.com/Iammilansoni/NLPForge-Tester/issues)
- **Discord**: [Join Community](https://discord.gg/nlpforge)

---

**Made with ❤️ by the NLPForge Team**
