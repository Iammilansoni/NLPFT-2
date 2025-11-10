# NLPForge Frontend - Quick Commands

## Windows Command Prompt / PowerShell

### Initial Setup (Run Once)
```cmd
cd Frontend
setup.bat
```

### Start Development Server
```cmd
cd Frontend
start.bat
```

Or manually:
```cmd
cd Frontend
npm run dev
```

### Other Commands
```cmd
# Build for production
npm run build

# Start production server
npm start

# Run tests
npm test

# Run linter
npm run lint

# Open Storybook
npm run storybook
```

## Verification Checklist

After running setup.bat and start.bat:

1. ✅ Open http://localhost:3000
2. ✅ Check home page loads
3. ✅ Navigate to /search
4. ✅ Navigate to /templates
5. ✅ Navigate to /dataset
6. ✅ Navigate to /health
7. ✅ Toggle theme (light/dark)
8. ✅ Check browser console (no errors)

## Troubleshooting

### Issue: "Node.js is not installed"
**Solution**: Install Node.js 18+ from https://nodejs.org/

### Issue: "npm install" fails
**Solution**: 
```cmd
npm cache clean --force
del /s /q node_modules package-lock.json
npm install
```

### Issue: Port 3000 already in use
**Solution**:
```cmd
# Find process using port 3000
netstat -ano | findstr :3000

# Kill the process (replace PID with actual process ID)
taskkill /PID <PID> /F

# Or use a different port
npm run dev -- -p 3001
```

### Issue: Backend connection failed
**Solution**:
1. Check backend is running: http://localhost:8000/health
2. Update .env file if backend is on different port
3. Check NEXT_PUBLIC_API_URL in .env

## Next Steps

After verification:
1. Review Frontend/SETUP_GUIDE.md
2. Read Frontend/BACKEND_INTEGRATION_GUIDE.md
3. Follow DEVELOPMENT_CHECKLIST.md
4. Start implementing missing pages

## Need Help?

- Setup issues: See Frontend/SETUP_GUIDE.md
- API integration: See Frontend/BACKEND_INTEGRATION_GUIDE.md
- Development: See DEVELOPMENT_CHECKLIST.md
- Deployment: See Frontend/DEPLOYMENT_GUIDE.md
