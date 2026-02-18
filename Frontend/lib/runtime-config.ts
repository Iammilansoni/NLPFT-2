// Runtime helpers to resolve API and WebSocket base URLs for dev and prod
export function getApiBase(): string {
  // Server-side (Next.js) should use internal backend URL when available
  if (typeof window === 'undefined') {
    return (
      process.env.BACKEND_INTERNAL_URL || process.env.NEXT_PUBLIC_API_URL || 'http://backend:8000'
    ).replace(/\/$/, '');
  }
  const host = window.location.hostname;

  // Prefer explicit public API URL when provided
  const env = process.env.NEXT_PUBLIC_API_URL;
  if (env && !env.includes('backend:8000')) return env.replace(/\/$/, '');
  
  // Fallback: use backend port on current host without hard-targeting a specific IP
  return `http://${host}:19000`;
}

export function getWsUrl(): string {
  if (typeof window === 'undefined') {
    return process.env.NEXT_PUBLIC_WS_URL || 'ws://backend:8000';
  }
  const env = process.env.NEXT_PUBLIC_WS_URL;
  if (env && !env.includes('backend:8000')) return env.replace(/\/$/, '');

  const proto = window.location.protocol === 'https:' ? 'wss' : 'ws';
  const host = window.location.hostname;

  // Fallback: use backend port on current host without hard-targeting a specific IP
  return `${proto}://${host}:19000`;
}
