# 🚀 NLPForge - Quick Start Guide

## ⚠️ IMPORTANT: Start Backend First!

The frontend **requires** the backend to be running. You'll see connection errors if the backend is not started.

---

## 📋 Step-by-Step Startup

### Step 1: Start Backend Services

#### 1.1 Start PostgreSQL
```bash
# Windows (if using PostgreSQL service)
net start postgresql-x64-14

# Or check if it's running
psql -U nlpforge -d nlpforge
```

#### 1.2 Start Redis
```bash
# Windows (if using Redis service)
redis-server

# Or check if it's running
redis-cli ping
# Should return: PONG
```

#### 1.3 Start Backend API
```bash
# Open Terminal 1
cd Backend
python -m uvicorn app.main:app --reload
```

**Wait for this message:**
```
INFO:     Application startup complete.
INFO:     Uvicorn running on http://127.0.0.1:8000
```

#### 1.4 Verify Backend is Running
Open browser: http://localhost:8000

You should see:
```json
{
  "name": "NLPForge API",
  "version": "1.0.0",
  "status": "running",
  "docs": "/docs"
}
```

---

### Step 2: Start Frontend

#### 2.1 Install Dependencies (First Time Only)
```bash
# Open Terminal 2
cd Frontend
npm install
```

#### 2.2 Start Development Server
```bash
# Windows - Use the batch file
start.bat

# Or manually
npm run dev
```

**Wait for this message:**
```
✓ Ready in 3.2s
○ Local:   http://localhost:3000
```

---

### Step 3: Access Application

Open browser: **http://localhost:3000/dashboard**

You should see:
- ✅ Green "Backend Online" indicator in sidebar
- ✅ Real-time KPI cards with data
- ✅ No connection errors in console

---

## 🔍 Troubleshooting

### Problem: "Backend Offline" Alert

**Symptoms:**
- Red alert in bottom-right corner
- Console errors: `ERR_CONNECTION_REFUSED`
- Red status indicator in sidebar

**Solution:**
1. Check if backend is running:
   ```bash
   curl http://localhost:8000
   ```

2. If not running, start it:
   ```bash
   cd Backend
   python -m uvicorn app.main:app --reload
   ```

3. Check PostgreSQL:
   ```bash
   psql -U nlpforge -d nlpforge
   ```

4. Check Redis:
   ```bash
   redis-cli ping
   ```

---

### Problem: Hydration Warning

**Symptoms:**
```
Warning: Extra attributes from the server: fdprocessedidat
```

**Solution:**
This is a harmless warning caused by browser extensions (password managers, form fillers). It's already fixed in the code with `suppressHydrationWarning`.

To completely remove it:
1. Disable browser extensions temporarily
2. Use incognito mode
3. Or ignore it - it doesn't affect functionality

---

### Problem: Port Already in Use

**Backend (Port 8000):**
```bash
# Windows - Find and kill process
netstat -ano | findstr :8000
taskkill /PID <PID> /F
```

**Frontend (Port 3000):**
```bash
# Windows - Find and kill process
netstat -ano | findstr :3000
taskkill /PID <PID> /F
```

---

### Problem: Database Connection Error

**Symptoms:**
```
sqlalchemy.exc.OperationalError: could not connect to server
```

**Solution:**
1. Check PostgreSQL is running:
   ```bash
   pg_isready -U nlpforge
   ```

2. Check credentials in `Backend/.env`:
   ```env
   POSTGRES_HOST=localhost
   POSTGRES_PORT=5432
   POSTGRES_USER=nlpforge
   POSTGRES_PASSWORD=nlpforge_password
   POSTGRES_DB=nlpforge
   ```

3. Create database if needed:
   ```bash
   psql -U postgres
   CREATE DATABASE nlpforge;
   CREATE USER nlpforge WITH PASSWORD 'nlpforge_password';
   GRANT ALL PRIVILEGES ON DATABASE nlpforge TO nlpforge;
   ```

---

### Problem: Redis Connection Error

**Symptoms:**
```
redis.exceptions.ConnectionError: Error connecting to Redis
```

**Solution:**
1. Start Redis:
   ```bash
   redis-server
   ```

2. Check Redis is running:
   ```bash
   redis-cli ping
   # Should return: PONG
   ```

3. Check credentials in `Backend/.env`:
   ```env
   REDIS_HOST=localhost
   REDIS_PORT=6379
   REDIS_PASSWORD=your_password
   ```

---

## 🎯 Quick Test Checklist

After starting both backend and frontend:

### Backend Health Check
- [ ] http://localhost:8000 returns JSON
- [ ] http://localhost:8000/docs shows API documentation
- [ ] http://localhost:8000/api/v1/stats returns statistics
- [ ] http://localhost:8000/api/v1/templates/ returns templates

### Frontend Health Check
- [ ] http://localhost:3000/dashboard loads
- [ ] Green "Backend Online" in sidebar
- [ ] KPI cards show real numbers (not 0)
- [ ] No console errors
- [ ] Query input works
- [ ] Navigation works

---

## 📊 Testing Features

### 1. Test Query Processing
1. Go to Dashboard or Query page
2. Enter: `Login with username admin and password secret123`
3. Click "Run Query"
4. Should see:
   - Intent: `login`
   - Extracted parameters: `username: admin`, `password: secret123`
   - Confidence score
   - Best matches

### 2. Test Templates
1. Go to Templates page
2. Should see list of API templates
3. Try creating a new template
4. Try editing existing template

### 3. Test Analytics
1. Go to Analytics page
2. Should see:
   - Performance metrics
   - Query trend chart
   - Intent distribution
   - System statistics

### 4. Test Search
1. Go to Search page
2. Enter: `authentication`
3. Should see semantic search results

### 5. Test Datasets
1. Go to Datasets page
2. Try uploading a CSV file
3. Try generating a dataset

---

## 🔧 Development Commands

### Backend
```bash
cd Backend

# Start server
python -m uvicorn app.main:app --reload

# Run tests
pytest

# Check logs
tail -f logs/app.log
```

### Frontend
```bash
cd Frontend

# Development
npm run dev

# Build for production
npm run build

# Start production server
npm start

# Type check
npm run type-check

# Lint
npm run lint
```

---

## 📝 Environment Variables

### Backend (.env)
```env
# PostgreSQL
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_USER=nlpforge
POSTGRES_PASSWORD=nlpforge_password
POSTGRES_DB=nlpforge

# Redis
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_PASSWORD=your_password

# API Settings
TOP_K=5
CONFIDENCE_THRESHOLD=0.7
DEBUG=True
```

### Frontend (.env.local)
```env
# Backend URL
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000

# Disable mock data
NEXT_PUBLIC_ENABLE_MOCK_DATA=false
```

---

## 🎉 Success Indicators

When everything is working correctly, you should see:

### Backend Terminal
```
INFO:     Application startup complete.
INFO:     Uvicorn running on http://127.0.0.1:8000
✅ Loaded 12 API templates
PostgreSQL: Main brain connected
```

### Frontend Terminal
```
✓ Ready in 3.2s
○ Local:   http://localhost:3000
```

### Browser
- ✅ Green "Backend Online" indicator
- ✅ Real-time data in KPI cards
- ✅ No console errors
- ✅ All pages load correctly
- ✅ Query processing works
- ✅ Templates load
- ✅ Analytics show charts

---

## 📞 Still Having Issues?

1. **Check logs:**
   - Backend: `Backend/logs/app.log`
   - Frontend: Browser DevTools Console (F12)

2. **Verify services:**
   ```bash
   # PostgreSQL
   psql -U nlpforge -d nlpforge -c "SELECT 1;"
   
   # Redis
   redis-cli ping
   
   # Backend
   curl http://localhost:8000
   ```

3. **Restart everything:**
   ```bash
   # Stop all services
   # Ctrl+C in all terminals
   
   # Start fresh
   # Follow Step 1 and Step 2 again
   ```

4. **Check documentation:**
   - `FRONTEND_SETUP_GUIDE.md`
   - `DEPLOYMENT_GUIDE.md`
   - `Frontend/CORPORATE_UI_README.md`

---

## 🚀 Ready to Go!

Once you see the green "Backend Online" indicator and no errors, you're ready to use NLPForge!

**Next Steps:**
1. Explore the dashboard
2. Try processing queries
3. View analytics
4. Manage templates
5. Upload datasets

**Happy Testing! 🎯**
