// Runtime helpers to resolve API and WebSocket base URLs for dev and prod
export function getApiBase(): string {
  // Server-side (Next.js) should use internal backend URL when available
  if (typeof window === 'undefined') {
    return (
      process.env.BACKEND_INTERNAL_URL || process.env.NEXT_PUBLIC_API_URL || 'http://backend:8000'
    ).replace(/\/$/, '');
  }
  // Detect common hostnames used in development/host networking and map to backend
  const host = window.location.hostname;
  if (host === '10.0.0.1') {
    return 'http://10.0.0.1:8000';
  }
  if (host === 'host.docker.internal') {
    return 'http://host.docker.internal:8000';
  }
  if (host === 'localhost' || host === '127.0.0.1') {
    return 'http://localhost:8000';
  }

  // Fallback: check for explicit env var or use :8000 on current host
  const env = process.env.NEXT_PUBLIC_API_URL;
  if (env && !env.includes('backend:8000')) return env.replace(/\/$/, '');
  
  return `http://${host}:8000`;
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
    return `${proto}://localhost:8000`;
  }

  // Fallback: use :8000 on current host
  return `${proto}://${host}:8000`;
}
