// Runtime helpers to resolve API and WebSocket base URLs for dev and prod
export function getApiBase(): string {
  // Server-side (Next.js) should use internal backend URL when available
  if (typeof window === 'undefined') {
    return (
      process.env.BACKEND_INTERNAL_URL || process.env.NEXT_PUBLIC_API_URL || 'http://backend:8000'
    ).replace(/\/$/, '');
  }
  // Client-side: prefer an explicit env var unless it's the Docker-internal hostname
  const env = process.env.NEXT_PUBLIC_API_URL;
  if (env && !env.includes('backend:8000')) return env.replace(/\/$/, '');

  // Detect common hostnames used in development/host networking and map to backend
  const host = window.location.hostname;
  if (host === '10.0.0.1') {
    return 'http://10.0.0.1:8000';
  }
  if (host === 'host.docker.internal') {
    return 'http://host.docker.internal:8000';
  }
  if (host === 'localhost' || host === '127.0.0.1') {
    return (process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000').replace(/\/$/, '');
  }

  // Fallback: use NEXT_PUBLIC_API_URL or same origin
  return (process.env.NEXT_PUBLIC_API_URL || window.location.origin).replace(/\/$/, '');
}

export function getWsUrl(): string {
  if (typeof window === 'undefined') {
    return process.env.NEXT_PUBLIC_WS_URL || 'ws://backend:8000';
  }
  const env = process.env.NEXT_PUBLIC_WS_URL;
  if (env && !env.includes('backend:8000')) return env.replace(/\/$/, '');

  const proto = window.location.protocol === 'https:' ? 'wss' : 'ws';
  const host = window.location.hostname;

  // Map common development hostnames to the backend websocket port
  if (host === '10.0.0.1') {
    return `${proto}://10.0.0.1:8000`;
  }
  if (host === 'host.docker.internal') {
    return `${proto}://host.docker.internal:8000`;
  }
  if (host === 'localhost' || host === '127.0.0.1') {
    return (process.env.NEXT_PUBLIC_WS_URL || `${proto}://localhost:8000`).replace(/\/$/, '');
  }

  // Fallback: use NEXT_PUBLIC_WS_URL or same host (keeps port/host from browser)
  return (process.env.NEXT_PUBLIC_WS_URL || `${proto}://${window.location.host}`).replace(/\/$/, '');
}
