/**
 * Where an expired / missing session should send the user.
 *
 * Only PROTECTED pages redirect to login on a 401. Public pages (landing,
 * about, docs, auth screens) legitimately make anonymous requests -- e.g. the
 * auth context probing /auth/me -- and must render for signed-out visitors.
 * Mirrors the public route list in middleware.ts.
 */
const PUBLIC_PREFIXES = ['/auth', '/about', '/status', '/privacy', '/terms', '/contact', '/docs', '/help', '/getting-started']

export function isPublicPath(pathname: string): boolean {
  return pathname === '/' || PUBLIC_PREFIXES.some((p) => pathname === p || pathname.startsWith(`${p}/`))
}

export function redirectToLogin(): void {
  if (typeof window === 'undefined') return
  const { pathname } = window.location
  if (isPublicPath(pathname)) return
  window.location.href = `/auth/login?from=${encodeURIComponent(pathname)}`
}
