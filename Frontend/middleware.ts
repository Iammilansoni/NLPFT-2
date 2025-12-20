import { NextResponse } from 'next/server'
import type { NextRequest } from 'next/server'

// Public routes that don't require authentication
const publicRoutes = [
  '/', // Landing page
  '/about', // About us page
  '/status', // Status page
  '/privacy', // Privacy policy
  '/terms', // Terms of service
  '/auth/login',
  '/auth/register',
  '/auth/verify-email',
  '/auth/forgot-password',
  '/auth/reset-password',
  '/api', // API routes are public (auth handled by backend)
]

// Check if route is public
function isPublicRoute(pathname: string): boolean {
  // CRITICAL: Check exact match for root FIRST to avoid prefix matching issues
  if (pathname === '/') {
    return true;
  }

  return publicRoutes.some(route => {
    // Skip root path (already checked above)
    if (route === '/') {
      return false;
    }
    // Prefix match for other routes
    return pathname.startsWith(route);
  });
}

export function middleware(request: NextRequest) {
  const { pathname } = request.nextUrl

  console.log('[Middleware] Check:', pathname);

  // Allow public routes
  if (isPublicRoute(pathname)) {
    console.log('[Middleware] Public route, allowing access');
    return NextResponse.next()
  }

  // Check for authentication token
  const token = request.cookies.get('nlpforge_access_token')?.value
  const allCookies = request.cookies.getAll();

  console.log('[Middleware] Cookies:', allCookies.map(c => c.name).join(', '));
  console.log('[Middleware] Token found:', !!token);

  // If no token and not on public route, redirect to login
  if (!token) {
    console.log('[Middleware] No token, redirecting to login');
    const loginUrl = new URL('/auth/login', request.url)
    loginUrl.searchParams.set('from', pathname)
    return NextResponse.redirect(loginUrl)
  }

  // Allow authenticated requests
  console.log('[Middleware] Token found, allowing access');
  return NextResponse.next()
}

// Configure which routes to run middleware on
export const config = {
  matcher: [
    /*
     * Match all request paths except:
     * - _next/static (static files)
     * - _next/image (image optimization files)
     * - favicon.ico (favicon file)
     * - public folder
     */
    '/((?!_next/static|_next/image|favicon.ico|.*\\.(?:svg|png|jpg|jpeg|gif|webp)$).*)',
  ],
}
