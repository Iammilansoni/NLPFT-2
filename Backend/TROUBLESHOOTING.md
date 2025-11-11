# Troubleshooting Internal Server Error

## Quick Checks

### 1. Is the Backend Running?
```bash
# Check if backend is running on port 8000
curl http://localhost:8000/docs
# or
curl http://localhost:8000/api/v1/dataset/list
```

### 2. Check Backend Logs
Look at your backend server console for error messages. Common issues:
- Import errors
- Database connection errors
- Redis connection errors
- Missing environment variables

### 3. Test the Endpoint Directly
```bash
# Test the list endpoint
curl http://localhost:8000/api/v1/dataset/list

# Should return: {"datasets": []}
```

### 4. Check Frontend Console
Open browser DevTools (F12) and check:
- Network tab: What request is failing?
- Console tab: Any JavaScript errors?
- What's the exact error message?

### 5. Common Issues

#### Backend Not Running
- Start backend: `cd Backend && uvicorn app.main:app --reload`

#### CORS Error
- Check `CORS_ORIGINS` environment variable
- Default allows `http://localhost:3000`

#### Port Conflicts
- Backend: Port 8000
- Frontend: Port 3000
- Redis: Port 6379
- PostgreSQL: Port 5432

#### Missing Dependencies
```bash
cd Backend
pip install -r requirements.txt
```

#### Redis/PostgreSQL Not Running
```bash
# Using Docker Compose
docker-compose up -d

# Or start services individually
```

## Debug Steps

1. **Check Backend Status**
   ```bash
   curl http://localhost:8000/health
   # or
   curl http://localhost:8000/docs
   ```

2. **Check Specific Endpoint**
   ```bash
   curl -v http://localhost:8000/api/v1/dataset/list
   ```

3. **Check Backend Logs**
   - Look for Python tracebacks
   - Check for import errors
   - Verify database connections

4. **Check Frontend Network Tab**
   - What URL is being called?
   - What's the response status code?
   - What's the response body?

## Recent Changes That Might Cause Issues

1. **Preview Endpoint** - Now maps CSV columns to frontend format
2. **List Endpoint** - Added error handling
3. **CORS Configuration** - Now uses environment variables

If you see a specific error message, share it and I can help debug further!





