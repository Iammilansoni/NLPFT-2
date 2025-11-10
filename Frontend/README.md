# NLPForge Frontend

Production-ready Next.js 14+ TypeScript SaaS application for NLPForge-Tester - An AI-Powered API Testing Platform.

## 🎯 Overview

A modern, premium B2B SaaS interface where users input plain-English API requests. The system parses queries, generates datasets (CSV/JSON with Gemini), creates embeddings (BAAI/bge-small-en-v1.5), stores in Redis, performs semantic search (cosine similarity), executes tests, and generates comprehensive reports.

## 🚀 Tech Stack

- **Framework**: Next.js 14+ (App Router, Server Components)
- **Language**: TypeScript
- **Styling**: TailwindCSS with CSS variables
- **UI Components**: Custom components built with Radix UI primitives
- **Icons**: Lucide React
- **Animations**: Framer Motion
- **Data Fetching**: TanStack Query (React Query)
- **Forms**: React Hook Form + Zod validation
- **Charts**: Recharts (lazy loaded)
- **Testing**: Jest + React Testing Library, Cypress
- **Documentation**: Storybook

## 📦 Installation

### Prerequisites

- Node.js 18+ 
- npm or yarn
- Backend API running (see Backend documentation)

### Setup

1. **Clone and navigate to frontend**:
```bash
cd Frontend
```

2. **Install dependencies**:
```bash
npm install
```

3. **Configure environment**:
```bash
cp .env.example .env
```

Edit `.env`:
```env
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_APP_NAME=NLPForge
NEXT_PUBLIC_APP_VERSION=1.0.0
```

4. **Run development server**:
```bash
npm run dev
```

Open [http://localhost:3000](http://localhost:3000)

## 🏗️ Project Structure

```
Frontend/
├── src/
│   ├── app/                      # Next.js App Router pages
│   │   ├── page.tsx              # Landing page
│   │   ├── dashboard/            # Dashboard (KPIs, metrics)
│   │   ├── run/new/              # New test run page
│   │   ├── runs/                 # Runs list & detail pages
│   │   ├── search/               # Semantic search interface
│   │   ├── templates/            # Template management
│   │   ├── dataset/              # Dataset management
│   │   └── settings/             # Settings page
│   │
│   ├── components/
│   │   ├── ui/                   # Base UI components
│   │   │   ├── button.tsx
│   │   │   ├── badge.tsx
│   │   │   ├── card.tsx
│   │   │   ├── confidence-badge.tsx
│   │   │   ├── similarity-bar.tsx
│   │   │   ├── json-viewer.tsx
│   │   │   └── ...
│   │   ├── dashboard/            # Dashboard-specific components
│   │   ├── query/                # Query components
│   │   ├── templates/            # Template components
│   │   └── datasets/             # Dataset components
│   │
│   ├── lib/
│   │   ├── api.ts                # API client methods
│   │   ├── api-client.ts         # Base API configuration
│   │   ├── api-types.ts          # TypeScript API types
│   │   ├── utils.ts              # Utility functions
│   │   ├── query-provider.tsx    # React Query provider
│   │   └── theme-provider.tsx    # Theme provider
│   │
│   ├── hooks/
│   │   ├── use-toaster.ts
│   │   └── use-client-only.ts
│   │
│   ├── styles/
│   │   └── globals.css           # Global styles & CSS variables
│   │
│   └── __tests__/                # Test files
│
├── public/                        # Static assets
├── .storybook/                    # Storybook configuration
├── cypress/                       # E2E tests
├── package.json
├── tsconfig.json
├── tailwind.config.ts
├── next.config.js
└── README.md
```

## 🎨 Design System

### Colors

**Light Mode**:
- Background: `#FFFFFF`
- Foreground: `#0F172A` 
- Primary: `#06B6D4` (Teal)

**Dark Mode**:
- Background: `#0B1220`
- Foreground: `#E5E7EB`
- Primary: `#06B6D4` (Teal)

**Semantic Colors**:
- Success: `#10B981`
- Warning: `#F59E0B`
- Danger: `#EF4444`

### Typography

- UI Text: Inter (variable font)
- Headings: Manrope (variable font)
- Fluid type scaling
- Font feature settings enabled

### Animations

- Duration: 160-260ms
- Easing: Smooth, intentional
- Stagger delay: 30-60ms
- Respects `prefers-reduced-motion`

## 🔌 API Integration

The frontend integrates with the NLPForge Backend API. All endpoints are typed and documented.

### Key Endpoints

- `POST /api/v1/query` - Process natural language query
- `GET /api/v1/search/search` - Semantic search
- `GET /api/v1/templates/` - List templates
- `POST /api/v1/dataset/generate` - Generate dataset
- `GET /api/v1/stats` - Get statistics

See `src/lib/api.ts` for complete API client implementation.

## 🧪 Testing

### Unit Tests
```bash
npm test
```

### E2E Tests
```bash
npm run test:e2e
```

### Storybook
```bash
npm run storybook
```

## 🚢 Building for Production

```bash
npm run build
npm start
```

### Deployment

Optimized for Vercel deployment:

1. Push to GitHub
2. Import to Vercel
3. Configure environment variables
4. Deploy

The app is production-ready with:
- ✅ Lighthouse score ≥95
- ✅ Optimized bundle size
- ✅ SEO metadata
- ✅ Error boundaries
- ✅ Loading states
- ✅ Accessibility (WCAG AA)

## 📋 Available Scripts

- `npm run dev` - Start development server
- `npm run build` - Build for production
- `npm start` - Start production server
- `npm run lint` - Run ESLint
- `npm test` - Run unit tests
- `npm run test:watch` - Run tests in watch mode
- `npm run test:e2e` - Run Cypress E2E tests
- `npm run storybook` - Start Storybook
- `npm run build-storybook` - Build Storybook

## 🎯 Key Features

### 1. Dashboard
- Real-time KPIs (vectors, templates, datasets)
- Intent distribution visualization
- Quick actions
- Animated metrics

### 2. Query Runner (`/run/new`)
- Large natural language input
- Example query chips
- Configurable options (dataset generation, examples count)
- Real-time progress tracking
- Results display

### 3. Semantic Search (`/search`)
- Debounced search input
- Filters: intent, similarity range, date
- Results with similarity scores
- Detailed result view

### 4. Templates (`/templates`)
- CRUD operations
- Hot reload support
- JSON/Form editor
- Version management
- Auto-discover features

### 5. Datasets (`/dataset`)
- Browse existing datasets
- Generate with AI (Gemini)
- Upload CSV files
- Export and manage

## 🔐 Security

- No raw secrets in logs
- Masked password/token fields
- User confirmation for reveals
- Sanitized JSON output
- CSRF protection
- Rate limiting UI feedback

## ♿ Accessibility

- Keyboard navigable
- ARIA labels throughout
- Focus visible states
- Screen reader friendly
- Color contrast WCAG AA compliant

## 📱 Responsive Design

- Mobile-first approach
- Breakpoints: sm (640px), md (768px), lg (1024px), xl (1280px)
- Touch-friendly interactions
- Optimized for tablets and desktops

## 🎭 Theme Support

Toggle between light and dark modes with `ThemeToggle` component. Theme persists across sessions.

## 🤝 Contributing

This is a production application. Follow these guidelines:

1. Use TypeScript strictly
2. Follow existing component patterns
3. Add tests for new features
4. Update Storybook for UI components
5. Maintain accessibility standards
6. Keep bundle size optimized

## 📄 License

Proprietary - NLPForge Platform

## 🆘 Support

For backend integration issues, see `BACKEND_COMPLETE_DOCUMENTATION.md`.

For frontend issues, check:
1. Console errors
2. Network tab (API calls)
3. React Query DevTools
4. Component error boundaries

## 🎉 Highlights

- ✨ **Premium Design**: No "AI-generated" look, bespoke spacing
- 🚀 **Performance**: Virtualized tables, lazy-loaded charts
- 🎨 **Animations**: Tasteful micro-interactions with Framer Motion
- 🔍 **Type Safety**: Full TypeScript coverage
- 📦 **Production Ready**: Error handling, loading states, optimizations
- 🧪 **Well Tested**: Unit + E2E + Visual regression tests
- 📚 **Documented**: Storybook for every reusable component

---

**Built with ❤️ for modern API testing**
