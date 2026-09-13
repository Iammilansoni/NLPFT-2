// Runtime helpers to resolve API and WebSocket base URLs for dev and prod
export function getApiBase(): string {
  // Server-side (Next.js) should use internal backend URL when available
  if (typeof window === 'undefined') {
    return (
      process.env.BACKEND_INTERNAL_URL || process.env.NEXT_PUBLIC_API_URL || 'http://backend:8000'
    ).replace(/\/$/, '');
  }
  // Prefer explicit public API URL when provided
  const env = process.env.NEXT_PUBLIC_API_URL;
  if (env && !env.includes('backend:8000')) return env.replace(/\/$/, '');

  // No explicit URL (the docker-compose default): return a relative base so
  // requests hit the browser's own origin and are proxied server-side by
  // next.config.js's rewrites() to BACKEND_INTERNAL_URL. Guessing an absolute
  // `http://<host>:<port>` here previously pointed at port 19000, which
  // nothing in this stack listens on -- every request failed with
  // ERR_CONNECTION_REFUSED and login/query surfaced as a generic
  // "Invalid email or password" / request failure regardless of backend
  // health or credentials correctness.
  return '';
}

export function getWsUrl(): string {
  if (typeof window === 'undefined') {
    return process.env.NEXT_PUBLIC_WS_URL || 'ws://backend:8000';
  }
  const env = process.env.NEXT_PUBLIC_WS_URL;
  if (env && !env.includes('backend:8000')) return env.replace(/\/$/, '');

  const proto = window.location.protocol === 'https:' ? 'wss' : 'ws';
  const host = window.location.hostname;

  // WebSocket upgrades aren't proxied by next.config.js's rewrites() (HTTP
  // only), so this one genuinely needs the backend's real port -- 8000
  // everywhere else in this stack (docker-compose.yml, the SSR branch above),
  // not 19000.
  return `${proto}://${host}:8000`;
}
