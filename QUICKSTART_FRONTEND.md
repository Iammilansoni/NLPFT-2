# NLPForge-Tester - Quick Start Guide

Get the NLPForge-Tester frontend up and running in 5 minutes.

## Prerequisites

- Node.js 18+ installed
- Backend API running on `http://localhost:8000`

## Quick Setup

### 1. Navigate to Frontend
```bash
cd Frontend
```

### 2. Install Dependencies
```bash
npm install
```
⏱️ This takes 2-5 minutes depending on your internet speed.

### 3. Configure Environment
```bash
# Copy example environment file
cp .env.example .env
```

The default configuration connects to `http://localhost:8000` - this should work if your backend is running locally.

### 4. Start Development Server
```bash
npm run dev
```

### 5. Open in Browser
Navigate to: **http://localhost:3000**

## Verify Everything Works

### ✅ Check 1: Home Page
- Landing page loads
- Navigation is visible
- Feature cards are animated

### ✅ Check 2: Backend Connection
Go to: http://localhost:3000/health
- Should show "Backend Status: Healthy"
- Green checkmark visible

### ✅ Check 3: Search
Go to: http://localhost:3000/search
- Search interface loads
- Can type in search box

### ✅ Check 4: Templates
Go to: http://localhost:3000/templates
- Template list loads
- Templates are displayed

### ✅ Check 5: Dataset
Go to: http://localhost:3000/dataset
- Dataset tabs visible
- Interface is responsive

## Common Issues

### Issue: Port 3000 already in use
```bash
# Use a different port
npm run dev -- -p 3001
```

### Issue: API connection failed
1. Check backend is running: `curl http://localhost:8000/health`
2. If backend is on different port, update `.env`:
   ```
   NEXT_PUBLIC_API_URL=http://localhost:YOUR_PORT
   ```

### Issue: Dependencies fail to install
```bash
# Clear cache and retry
npm cache clean --force
rm -rf node_modules package-lock.json
npm install
```

## Available Routes

Once running, explore:

- `/` - Home page
- `/dashboard` - Statistics (needs directory creation)
- `/search` - Semantic search
- `/templates` - Template management
- `/dataset` - Dataset operations
- `/health` - Backend health check
- `/run/new` - New test run (needs directory creation)

## Development Scripts

```bash
npm run dev        # Start development server
npm run build      # Build for production
npm run start      # Start production server
npm run lint       # Run linter
npm test           # Run tests
```

## Project Structure

```
Frontend/
├── src/
│   ├── app/              # Pages (Next.js App Router)
│   ├── components/       # React components
│   ├── lib/             # Utilities, API client
│   ├── hooks/           # Custom hooks
│   └── styles/          # Global styles
├── package.json         # Dependencies
└── README.md           # Full documentation
```

## Next Steps

1. **Read Full Documentation**: See `Frontend/README.md`
2. **Setup Guide**: See `Frontend/SETUP_GUIDE.md`
3. **API Integration**: See `Frontend/BACKEND_INTEGRATION_GUIDE.md`
4. **Deployment**: See `Frontend/DEPLOYMENT_GUIDE.md`

## Getting Help

- **Frontend Issues**: Check browser console and network tab
- **API Issues**: Check `BACKEND_INTEGRATION_GUIDE.md`
- **Setup Issues**: Check `SETUP_GUIDE.md`

## What's Built

✅ Complete Next.js 14+ application
✅ TypeScript with full type safety
✅ TailwindCSS design system
✅ API client with React Query
✅ Form validation with Zod
✅ Animations with Framer Motion
✅ Light/Dark theme support
✅ Responsive design
✅ Accessibility features

## Production Build

To test production build locally:

```bash
npm run build
npm start
```

Then visit: http://localhost:3000

---

**You're ready to develop!** 🎉

For detailed instructions, see the documentation in the `Frontend/` directory.
