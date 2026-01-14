# ============================
# Base image
# ============================
FROM node:20-alpine AS base

# ============================
# Dependencies stage
# ============================
FROM base AS deps
WORKDIR /app

ENV NPM_CONFIG_LOGLEVEL=warn \
    NPM_CONFIG_PREFER_OFFLINE=false \
    NPM_CONFIG_FETCH_RETRIES=5 \
    NPM_CONFIG_FETCH_RETRY_MINTIMEOUT=20000 \
    NPM_CONFIG_FETCH_RETRY_MAXTIMEOUT=120000 \
    NPM_CONFIG_IGNORE_SCRIPTS=true

COPY package.json package-lock.json* ./

# Install dependencies with script execution disabled
RUN npm ci --legacy-peer-deps --ignore-scripts || npm install --legacy-peer-deps --ignore-scripts

# Run npm audit to detect vulnerabilities
RUN npm audit --audit-level=moderate || true

# Clean npm cache to prevent post-install hooks
RUN npm cache clean --force && rm -rf /root/.npm

# ============================
# Build stage
# ============================
FROM base AS builder
WORKDIR /app

ENV NODE_ENV=production
ENV NEXT_TELEMETRY_DISABLED=1
ENV NPM_CONFIG_IGNORE_SCRIPTS=true

COPY --from=deps /app/node_modules ./node_modules
COPY . .

# Remove any potential malicious post-install scripts from node_modules
RUN find node_modules -path "*/.bin" -prune -o -type f -name "postinstall.js" -delete

ARG NEXT_PUBLIC_API_URL
ARG NEXT_PUBLIC_API_BASE_URL
ARG NEXT_PUBLIC_WS_URL

ENV NEXT_PUBLIC_API_URL=$NEXT_PUBLIC_API_URL
ENV NEXT_PUBLIC_API_BASE_URL=$NEXT_PUBLIC_API_BASE_URL
ENV NEXT_PUBLIC_WS_URL=$NEXT_PUBLIC_WS_URL

RUN npm run build

# ============================
# Runtime stage (FINAL & CORRECT)
# ============================
FROM node:20-alpine AS runner
WORKDIR /app

ENV NODE_ENV=production
ENV NEXT_TELEMETRY_DISABLED=1
ENV PORT=3000
ENV HOSTNAME=0.0.0.0
ENV NPM_CONFIG_IGNORE_SCRIPTS=true

RUN addgroup --system --gid 1001 nodejs \
 && adduser --system --uid 1001 nextjs

# Copy from builder stage
COPY --from=builder /app/node_modules ./node_modules
COPY --from=builder /app/.next ./.next
COPY --from=builder /app/public ./public
COPY --from=builder /app/package.json ./package.json

# Remove potential malicious artifacts
RUN rm -rf node_modules/.bin/* && \
    find node_modules -type f -name "*.sh" -not -path "*/*/bin/*" -delete && \
    find node_modules -type f -name "postinstall.js" -delete

USER nextjs
EXPOSE 3000

# Official, supported entrypoint - prevents shell injection
CMD ["node", "node_modules/next/dist/bin/next", "start", "-p", "3000"]
