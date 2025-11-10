# NLPForge Frontend - Deployment Guide

Complete guide for deploying the NLPForge frontend to production environments.

## Deployment Options

1. [Vercel (Recommended)](#vercel-deployment)
2. [Docker](#docker-deployment)
3. [Traditional Server](#traditional-server-deployment)
4. [AWS](#aws-deployment)

---

## Vercel Deployment

### Prerequisites
- GitHub account
- Vercel account (free tier available)
- Code pushed to GitHub repository

### Steps

#### 1. Prepare for Deployment

**a. Build locally to test**:
```bash
cd Frontend
npm run build
npm start
```

Verify the production build works correctly.

**b. Commit all changes**:
```bash
git add .
git commit -m "feat: production-ready frontend"
git push origin main
```

#### 2. Deploy to Vercel

**Option A: Using Vercel Dashboard**

1. Go to [vercel.com](https://vercel.com)
2. Click "New Project"
3. Import your GitHub repository
4. Configure project:
   - **Framework Preset**: Next.js
   - **Root Directory**: `Frontend`
   - **Build Command**: `npm run build`
   - **Output Directory**: `.next`

5. **Environment Variables**:
   ```
   NEXT_PUBLIC_API_URL=https://your-backend-api.com
   NEXT_PUBLIC_APP_NAME=NLPForge
   NEXT_PUBLIC_APP_VERSION=1.0.0
   ```

6. Click "Deploy"

**Option B: Using Vercel CLI**

```bash
# Install Vercel CLI
npm install -g vercel

# Login
vercel login

# Deploy from Frontend directory
cd Frontend
vercel

# Follow prompts:
# - Set up and deploy? Yes
# - Which scope? Your account/team
# - Link to existing project? No
# - Project name? nlpforge-frontend
# - Directory? ./
# - Override settings? No

# Deploy to production
vercel --prod
```

#### 3. Configure Custom Domain (Optional)

In Vercel Dashboard:
1. Go to Project Settings → Domains
2. Add your custom domain
3. Configure DNS records as instructed
4. Wait for SSL certificate provisioning

#### 4. Post-Deployment Checks

✅ Visit your deployment URL
✅ Check all routes work
✅ Verify API connection (check /health)
✅ Test theme toggle
✅ Try a query on /run/new
✅ Check responsive design on mobile

---

## Docker Deployment

### Create Dockerfile

Create `Dockerfile` in Frontend directory:

```dockerfile
# Frontend/Dockerfile
FROM node:18-alpine AS base

# Install dependencies only when needed
FROM base AS deps
RUN apk add --no-cache libc6-compat
WORKDIR /app

# Copy package files
COPY package.json package-lock.json* ./
RUN npm ci

# Rebuild the source code only when needed
FROM base AS builder
WORKDIR /app
COPY --from=deps /app/node_modules ./node_modules
COPY . .

# Set environment variables for build
ENV NEXT_TELEMETRY_DISABLED 1
ENV NEXT_PUBLIC_API_URL http://backend:8000

RUN npm run build

# Production image, copy all the files and run next
FROM base AS runner
WORKDIR /app

ENV NODE_ENV production
ENV NEXT_TELEMETRY_DISABLED 1

RUN addgroup --system --gid 1001 nodejs
RUN adduser --system --uid 1001 nextjs

COPY --from=builder /app/public ./public
COPY --from=builder --chown=nextjs:nodejs /app/.next/standalone ./
COPY --from=builder --chown=nextjs:nodejs /app/.next/static ./.next/static

USER nextjs

EXPOSE 3000

ENV PORT 3000
ENV HOSTNAME "0.0.0.0"

CMD ["node", "server.js"]
```

### Update next.config.js

```javascript
/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  swcMinify: true,
  output: 'standalone', // Add this for Docker
  experimental: {
    optimizePackageImports: ['lucide-react', 'recharts'],
  },
  async rewrites() {
    return [
      {
        source: '/api/:path*',
        destination: process.env.NEXT_PUBLIC_API_URL || 'http://backend:8000/api/:path*',
      },
    ];
  },
};

module.exports = nextConfig;
```

### Build and Run

```bash
# Build Docker image
docker build -t nlpforge-frontend:latest ./Frontend

# Run container
docker run -p 3000:3000 \
  -e NEXT_PUBLIC_API_URL=http://backend:8000 \
  nlpforge-frontend:latest
```

### Docker Compose (Full Stack)

Update root `docker-compose.yml`:

```yaml
version: '3.8'

services:
  frontend:
    build:
      context: ./Frontend
      dockerfile: Dockerfile
    ports:
      - "3000:3000"
    environment:
      - NEXT_PUBLIC_API_URL=http://backend:8000
    depends_on:
      - backend
    networks:
      - nlpforge-network

  backend:
    build: ./Backend
    ports:
      - "8000:8000"
    depends_on:
      - postgres
      - redis
    networks:
      - nlpforge-network

  postgres:
    image: postgres:15
    environment:
      POSTGRES_DB: nlpforge
      POSTGRES_USER: nlpforge
      POSTGRES_PASSWORD: your_password
    volumes:
      - postgres_data:/var/lib/postgresql/data
    networks:
      - nlpforge-network

  redis:
    image: redis/redis-stack:latest
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    networks:
      - nlpforge-network

volumes:
  postgres_data:
  redis_data:

networks:
  nlpforge-network:
    driver: bridge
```

Run full stack:
```bash
docker-compose up -d
```

---

## Traditional Server Deployment

### On Ubuntu/Debian Server

#### 1. Install Node.js

```bash
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt-get install -y nodejs
```

#### 2. Install PM2 (Process Manager)

```bash
sudo npm install -g pm2
```

#### 3. Deploy Application

```bash
# Clone repository
git clone https://github.com/your-org/nlpforge.git
cd nlpforge/Frontend

# Install dependencies
npm ci --production=false

# Build
npm run build

# Start with PM2
pm2 start npm --name "nlpforge-frontend" -- start

# Save PM2 configuration
pm2 save

# Setup PM2 to start on boot
pm2 startup
```

#### 4. Configure Nginx Reverse Proxy

```nginx
# /etc/nginx/sites-available/nlpforge
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://localhost:3000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
    }
}
```

Enable site:
```bash
sudo ln -s /etc/nginx/sites-available/nlpforge /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

#### 5. Setup SSL with Let's Encrypt

```bash
sudo apt-get install certbot python3-certbot-nginx
sudo certbot --nginx -d your-domain.com
```

---

## AWS Deployment

### Using AWS Amplify

1. Go to AWS Amplify Console
2. Connect your GitHub repository
3. Configure build settings:
   ```yaml
   version: 1
   frontend:
     phases:
       preBuild:
         commands:
           - cd Frontend
           - npm ci
       build:
         commands:
           - npm run build
     artifacts:
       baseDirectory: Frontend/.next
       files:
         - '**/*'
     cache:
       paths:
         - Frontend/node_modules/**/*
   ```
4. Set environment variables
5. Deploy

### Using EC2 + Load Balancer

1. Launch EC2 instance (Ubuntu 22.04)
2. Install Node.js and PM2
3. Clone and build application
4. Configure Application Load Balancer
5. Setup Auto Scaling Group
6. Configure CloudWatch monitoring

---

## Environment Variables for Production

Create `.env.production`:

```env
# API Configuration
NEXT_PUBLIC_API_URL=https://api.your-domain.com

# App Configuration
NEXT_PUBLIC_APP_NAME=NLPForge
NEXT_PUBLIC_APP_VERSION=1.0.0

# Analytics (Optional)
NEXT_PUBLIC_SENTRY_DSN=your_sentry_dsn
NEXT_PUBLIC_POSTHOG_KEY=your_posthog_key
NEXT_PUBLIC_POSTHOG_HOST=https://app.posthog.com

# Feature Flags (Optional)
NEXT_PUBLIC_ENABLE_ANALYTICS=true
NEXT_PUBLIC_ENABLE_STORYBOOK=false
```

---

## Performance Optimization

### Build Optimization

```bash
# Analyze bundle size
npm run build
# Check .next/analyze output

# Environment-specific builds
NODE_ENV=production npm run build
```

### CDN Configuration

Configure CDN for static assets:
- Next.js automatic static optimization
- Image optimization with Next/Image
- Font preloading
- Asset caching headers

---

## Monitoring and Logging

### Setup Sentry (Error Tracking)

```bash
npm install @sentry/nextjs
```

```javascript
// sentry.client.config.js
import * as Sentry from '@sentry/nextjs';

Sentry.init({
  dsn: process.env.NEXT_PUBLIC_SENTRY_DSN,
  tracesSampleRate: 1.0,
});
```

### Setup PostHog (Analytics)

```bash
npm install posthog-js
```

```typescript
// lib/analytics.ts
import posthog from 'posthog-js';

if (typeof window !== 'undefined') {
  posthog.init(process.env.NEXT_PUBLIC_POSTHOG_KEY!, {
    api_host: process.env.NEXT_PUBLIC_POSTHOG_HOST,
  });
}
```

---

## Health Checks

Create `/api/health` endpoint:

```typescript
// app/api/health/route.ts
export async function GET() {
  return Response.json({
    status: 'healthy',
    timestamp: new Date().toISOString(),
    version: process.env.NEXT_PUBLIC_APP_VERSION,
  });
}
```

---

## Rollback Strategy

### Vercel
- Click "Redeploy" on previous successful deployment
- Instant rollback

### Docker
```bash
# Tag versions
docker tag nlpforge-frontend:latest nlpforge-frontend:v1.0.0
docker tag nlpforge-frontend:latest nlpforge-frontend:v1.0.1

# Rollback
docker-compose down
docker-compose up -d nlpforge-frontend:v1.0.0
```

### PM2
```bash
# Save current version
pm2 save

# Rollback code
git checkout v1.0.0
npm run build
pm2 restart nlpforge-frontend
```

---

## Production Checklist

Before deploying:

- [ ] All tests pass: `npm test`
- [ ] Build succeeds: `npm run build`
- [ ] No console errors in production build
- [ ] Environment variables configured correctly
- [ ] Backend URL points to production API
- [ ] CORS configured on backend
- [ ] SSL/TLS certificates configured
- [ ] CDN configured for static assets
- [ ] Error tracking (Sentry) setup
- [ ] Analytics (PostHog) setup
- [ ] Health check endpoint working
- [ ] Monitoring and alerts configured
- [ ] Backup and rollback strategy in place
- [ ] Load testing completed
- [ ] Security headers configured
- [ ] Rate limiting implemented
- [ ] Documentation updated

---

## Post-Deployment

After deployment:

1. **Verify Deployment**
   - Check all routes work
   - Test core functionality
   - Verify API integration
   - Check error boundaries

2. **Monitor Metrics**
   - Response times
   - Error rates
   - User traffic
   - API call patterns

3. **Setup Alerts**
   - Error rate threshold
   - Response time threshold
   - Downtime alerts
   - Resource usage alerts

---

**Deployment Complete!** 🚀

Your NLPForge frontend is now live in production.
