# NLPForge Frontend - Complete Setup Guide

This guide will help you set up, configure, and run the NLPForge frontend application.

## Prerequisites

Before you begin, ensure you have the following installed:

- **Node.js** 18.x or higher ([Download](https://nodejs.org/))
- **npm** 9.x or higher (comes with Node.js)
- **Git** (for version control)
- **Backend API** running on `http://localhost:8000` (see Backend documentation)

Check your installations:
```bash
node --version  # Should be v18.x or higher
npm --version   # Should be 9.x or higher
```

## Installation Steps

### 1. Navigate to Frontend Directory

```bash
cd Frontend
```

### 2. Install Dependencies

```bash
npm install
```

This will install all required packages:
- Next.js 14+
- React 18
- TypeScript
- TailwindCSS
- TanStack Query
- Framer Motion
- Radix UI components
- And more...

Installation should take 2-5 minutes depending on your internet connection.

### 3. Configure Environment Variables

Create a `.env` file in the Frontend directory:

```bash
cp .env.example .env
```

Edit `.env` with your configuration:

```env
# Backend API URL
NEXT_PUBLIC_API_URL=http://localhost:8000

# App Configuration
NEXT_PUBLIC_APP_NAME=NLPForge
NEXT_PUBLIC_APP_VERSION=1.0.0
```

**Important**: Make sure the backend is running before starting the frontend.

### 4. Verify Backend Connection

Ensure the backend API is running and accessible:

```bash
curl http://localhost:8000/health
```

You should see a health check response with status "healthy".

### 5. Start Development Server

```bash
npm run dev
```

The application will start on **http://localhost:3000**

You should see:
```
✓ Ready in Xms
○ Local:        http://localhost:3000
○ Network:      http://192.168.x.x:3000
```

### 6. Open in Browser

Navigate to **http://localhost:3000** in your web browser.

You should see the NLPForge landing page with:
- Header navigation
- Hero section
- Feature cards (Search, Templates, Datasets)
- Footer

## Verifying the Setup

### Test 1: Check Home Page
- ✅ Page loads without errors
- ✅ Navigation links are visible
- ✅ Feature cards animate on load
- ✅ Theme toggle works (light/dark mode)

### Test 2: Check Dashboard
Navigate to `/dashboard`
- ✅ KPI cards display statistics
- ✅ Intent distribution chart renders
- ✅ "New Run" button is clickable

### Test 3: Check Backend Integration
Navigate to `/health`
- ✅ Backend status shows "healthy"
- ✅ Database connection is active
- ✅ System metrics are displayed

### Test 4: Try a Query
1. Go to `/run/new`
2. Enter: "Login with username admin and password test123"
3. Click "Run Test"
4. ✅ Query processes successfully
5. ✅ Results are displayed with confidence score

## Project Structure Overview

```
Frontend/
├── src/
│   ├── app/                 # Next.js App Router pages
│   │   ├── page.tsx         # Home page (/)
│   │   ├── dashboard/       # Dashboard (/dashboard)
│   │   ├── run/new/         # New run (/run/new)
│   │   ├── search/          # Search (/search)
│   │   ├── templates/       # Templates (/templates)
│   │   └── dataset/         # Datasets (/dataset)
│   │
│   ├── components/          # Reusable components
│   │   ├── ui/              # Base UI components
│   │   ├── dashboard/       # Dashboard components
│   │   └── ...
│   │
│   ├── lib/                 # Utilities and configurations
│   │   ├── api.ts           # API client
│   │   ├── api-types.ts     # TypeScript types
│   │   ├── utils.ts         # Utility functions
│   │   └── constants.ts     # App constants
│   │
│   ├── hooks/               # Custom React hooks
│   ├── styles/              # Global styles
│   └── __tests__/           # Test files
│
├── public/                  # Static assets
├── package.json             # Dependencies
├── tsconfig.json            # TypeScript config
├── tailwind.config.ts       # Tailwind config
└── next.config.js           # Next.js config
```

## Available Scripts

### Development
```bash
npm run dev          # Start development server
npm run lint         # Run ESLint
npm run build        # Build for production
npm run start        # Start production server
```

### Testing
```bash
npm test             # Run unit tests
npm run test:watch   # Run tests in watch mode
npm run test:e2e     # Run Cypress E2E tests
```

### Documentation
```bash
npm run storybook    # Start Storybook (component docs)
```

## Common Issues and Solutions

### Issue 1: Port 3000 Already in Use

**Error**: `Port 3000 is already in use`

**Solution**:
```bash
# Option 1: Kill the process using port 3000
# Windows
netstat -ano | findstr :3000
taskkill /PID <PID> /F

# Option 2: Use a different port
npm run dev -- -p 3001
```

### Issue 2: API Connection Failed

**Error**: `Failed to fetch`, `Network error`

**Solutions**:
1. Check backend is running: `curl http://localhost:8000/health`
2. Verify `NEXT_PUBLIC_API_URL` in `.env`
3. Check CORS configuration in backend
4. Ensure no firewall blocking localhost connections

### Issue 3: Module Not Found

**Error**: `Module not found: Can't resolve...`

**Solution**:
```bash
# Clear cache and reinstall
rm -rf node_modules package-lock.json
npm install
```

### Issue 4: TypeScript Errors

**Error**: `Type error: ...`

**Solution**:
```bash
# Rebuild TypeScript
npm run build
```

### Issue 5: Styling Not Applied

**Error**: Styles not loading, components unstyled

**Solution**:
1. Check `tailwind.config.ts` is present
2. Verify `globals.css` is imported in root layout
3. Clear `.next` cache:
```bash
rm -rf .next
npm run dev
```

## Development Workflow

### 1. Start Backend
```bash
cd Backend
python app/main.py
```

### 2. Start Frontend
```bash
cd Frontend
npm run dev
```

### 3. Make Changes
- Edit files in `src/`
- Changes hot-reload automatically
- Check browser console for errors

### 4. Test Your Changes
- Manual testing in browser
- Run unit tests: `npm test`
- Check TypeScript: `npm run lint`

### 5. Build for Production
```bash
npm run build
npm start
```

## Integration with Backend

The frontend communicates with the backend API through:

1. **API Client** (`src/lib/api-client.ts`)
   - Axios-based HTTP client
   - Error handling
   - Request/response interceptors

2. **API Methods** (`src/lib/api.ts`)
   - Type-safe API functions
   - Query processing
   - Template management
   - Dataset operations
   - Search functionality

3. **React Query** (`src/lib/query-provider.tsx`)
   - Data fetching and caching
   - Optimistic updates
   - Automatic retries

See `BACKEND_INTEGRATION_GUIDE.md` for detailed API documentation.

## Performance Optimization

The app is optimized for production:

- ✅ **Code Splitting**: Automatic route-based splitting
- ✅ **Lazy Loading**: Heavy components loaded on demand
- ✅ **Image Optimization**: Next.js Image component
- ✅ **Font Optimization**: Variable fonts, preloading
- ✅ **Bundle Analysis**: Check with `npm run build`
- ✅ **Caching**: React Query with smart cache invalidation
- ✅ **Virtualization**: Large lists use TanStack Virtual

## Deployment

### Deploy to Vercel (Recommended)

1. Push code to GitHub
2. Import project to Vercel
3. Configure environment variables:
   - `NEXT_PUBLIC_API_URL`: Your backend URL
4. Deploy

### Manual Deployment

```bash
# Build
npm run build

# The output is in `.next/`
# Deploy this folder to your hosting provider

# Start production server
npm start
```

## Getting Help

- **Frontend Issues**: Check browser console and network tab
- **API Issues**: See `BACKEND_INTEGRATION_GUIDE.md`
- **Component Docs**: Run `npm run storybook`
- **Type Errors**: Check `src/lib/api-types.ts`

## Next Steps

After setup, explore:

1. **Dashboard** (`/dashboard`) - View platform statistics
2. **New Run** (`/run/new`) - Test natural language queries
3. **Search** (`/search`) - Semantic search through embeddings
4. **Templates** (`/templates`) - Manage API templates
5. **Datasets** (`/dataset`) - Generate and manage test data

## Production Checklist

Before deploying to production:

- [ ] Environment variables configured
- [ ] Backend URL points to production API
- [ ] Build succeeds without errors: `npm run build`
- [ ] Tests pass: `npm test`
- [ ] Lighthouse score ≥95
- [ ] Error boundaries in place
- [ ] Security: No secrets in code
- [ ] Performance: Bundle size optimized
- [ ] Accessibility: Keyboard navigation works
- [ ] SEO: Metadata configured

---

**Setup Complete!** 🎉

You now have a fully functional NLPForge frontend ready for development.

For additional help, refer to:
- `README.md` - Project overview
- `BACKEND_INTEGRATION_GUIDE.md` - API integration
- Component Storybook - UI documentation
