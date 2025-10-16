# 🚀 Quick Start - NLPForge Frontend

Get up and running in 5 minutes!

## ⚡ Super Quick Start (Windows)

```cmd
cd Frontend
setup.bat
```

The script will automatically:
1. Check Node.js installation
2. Install all dependencies
3. Setup environment variables
4. Initialize Git hooks

Then run:
```cmd
npm run dev
```

Open http://localhost:3000 🎉

---

## 📋 Manual Setup

### 1. Prerequisites Check

```cmd
# Check Node.js (should be 18.x or 20.x)
node --version

# Check npm (should be 9.x+)
npm --version
```

Don't have Node.js? [Download here](https://nodejs.org/)

### 2. Install Dependencies

```cmd
cd Frontend
npm install
```

⏱️ **Time**: 2-3 minutes

### 3. Environment Setup

```cmd
# Copy environment template
copy .env.example .env.local
```

Edit `.env.local` if needed:
```env
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_ENABLE_3D=true
NEXT_PUBLIC_ENABLE_CUSTOM_CURSOR=true
```

### 4. Initialize Git Hooks

```cmd
npm run prepare
```

### 5. Start Development Server

```cmd
npm run dev
```

Open http://localhost:3000 in your browser.

---

## ✅ What You Should See

### ✨ Features to Test

1. **3D Hero Section** (Desktop only)
   - Rotating low-poly shape
   - Smooth animations
   - Theme-aware lighting

2. **Custom Cursor** (Desktop only)
   - Small dot with ring
   - Expands on hover over buttons/links
   - Hidden on touch devices

3. **Smooth Scrolling**
   - Locomotive-style easing
   - Natural momentum

4. **Theme Toggle**
   - Light/Dark mode
   - System preference detection
   - Persistent across sessions

5. **Microinteractions**
   - Buttons scale down on press (0.98)
   - Inputs show floating labels
   - Cards elevate on hover

---

## 🎨 Component Development (Storybook)

```cmd
npm run storybook
```

Open http://localhost:6006

### Available Stories

- **UI/Enhanced Button** - All variants and sizes
- **UI/Enhanced Card** - Hover and gradient effects
- **UI/Enhanced Input** - Float label demo
- More coming soon!

**Use the Accessibility tab** to check for violations.

---

## 🧪 Testing

### Run Tests

```cmd
# All tests
npm run test

# Watch mode
npm run test:watch

# With coverage
npm run test:ci
```

### Test Files

- `src/__tests__/` - Component tests
- `*.test.tsx` - Test files
- `jest.config.ts` - Configuration

---

## 🏗️ Production Build

```cmd
# Build for production
npm run build

# Start production server
npm run start
```

Open http://localhost:3000

**Check the build output** for bundle sizes.

---

## 🔧 Common Commands

| Command | Description |
|---------|-------------|
| `npm run dev` | Start development server |
| `npm run build` | Production build |
| `npm run start` | Start production server |
| `npm run lint` | Check for linting errors |
| `npm run lint:fix` | Auto-fix linting errors |
| `npm run format` | Format code with Prettier |
| `npm run test` | Run Jest tests |
| `npm run storybook` | Start Storybook |

---

## 🚨 Troubleshooting

### Issue: `npm install` fails

```cmd
# Clear cache and reinstall
rmdir /s /q node_modules
del package-lock.json
npm cache clean --force
npm install
```

### Issue: Port 3000 in use

```cmd
# Use different port
set PORT=3001 && npm run dev
```

### Issue: TypeScript errors

1. Restart VS Code
2. Press `Ctrl+Shift+P`
3. Type "TypeScript: Restart TS Server"
4. Press Enter

### Issue: 3D scene not showing

**Expected behavior**:
- 3D only shows on desktop (not mobile)
- Hidden if `prefers-reduced-motion` is enabled
- Fallback to gradient if GPU unavailable

Check console for detection logs.

### Issue: Custom cursor not showing

**Expected behavior**:
- Only shows on desktop (not touch devices)
- Hidden if `prefers-reduced-motion` is enabled

This is intentional for better UX.

---

## 📚 Learn More

- [FRONTEND_README.md](./FRONTEND_README.md) - Complete documentation
- [SETUP_GUIDE.md](./SETUP_GUIDE.md) - Detailed setup instructions
- [PERFORMANCE_RUNBOOK.md](./PERFORMANCE_RUNBOOK.md) - Performance guide
- [DESIGN_HANDOFF.md](./DESIGN_HANDOFF.md) - Design specifications

---

## 🎯 Next Steps

1. ✅ **Explore Components** - Check out Storybook
2. ✅ **Read Documentation** - Start with FRONTEND_README.md
3. ✅ **Write Tests** - Add unit tests for components
4. ✅ **Customize Theme** - Edit `src/styles/tokens.json`
5. ✅ **Deploy** - Push to Vercel

---

## 🆘 Need Help?

- **GitHub Issues**: [Report a bug](https://github.com/Iammilansoni/NLPForge-Tester/issues)
- **Documentation**: Check the docs folder
- **Discord**: #frontend-help

---

**Happy Coding! 🎉**
