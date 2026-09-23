# NLPForge — Frontend

The Next.js 16 (App Router) client for NLPForge. See the [root README](../README.md) for the
product overview and how to run the full stack.

## Stack

Next.js 16 · React 18 · TypeScript · Tailwind CSS (token-based theme, light/dark) ·
TanStack Query · Radix UI primitives · lucide-react

## Pages

| Route | Purpose |
|---|---|
| `/` | Landing page |
| `/auth/*` | Sign in, register, verify e-mail, password reset (plus Google sign-in when configured) |
| `/dashboard` | Route a request: resolved endpoint, extracted body, per-stage outcomes |
| `/templates` | API catalogue: create, review, approve templates |
| `/datasets` | Generate utterance datasets with an LLM, upload CSVs, embed for routing |
| `/settings` | Profile, security, LLM provider keys, runtime pipeline configuration |
| `/docs`, `/help`, `/getting-started`, `/status` | Public documentation and service status |

## Talking to the API

The browser calls same-origin `/api/*`. `next.config.js` rewrites those requests to
`BACKEND_INTERNAL_URL`, so authentication uses HttpOnly cookies and never needs CORS. The rewrite
is resolved at **build time**, which is why `docker-compose.yml` passes `BACKEND_INTERNAL_URL` as a
build argument.

## Run without Docker

```bash
npm install
BACKEND_INTERNAL_URL=http://localhost:8000 NEXT_PUBLIC_DEMO_MODE=true npm run dev
```

| Variable | Default | Meaning |
|---|---|---|
| `BACKEND_INTERNAL_URL` | — | Where `/api/*` is proxied. Required for the proxy. |
| `NEXT_PUBLIC_API_URL` | empty | Set only to call the API cross-origin instead of through the proxy. |
| `NEXT_PUBLIC_DEMO_MODE` | `false` | Shows the one-click demo login. |
| `NEXT_PUBLIC_GOOGLE_CLIENT_ID` | empty | Enables Google sign-in. |

## Checks

```bash
npx tsc --noEmit   # types
npm run lint       # ESLint (next/core-web-vitals)
npm run build      # production build (also run in CI)
```

## Design system

Colours, radii, shadows and fonts are CSS variables in `styles/globals.css`, exposed through
`tailwind.config.ts` as semantic classes: `bg-primary`, `text-success`, `border-border`,
`rounded-xl`, `shadow-md`, `bg-brand-gradient`. Use these instead of raw palette classes or
hex values. Shared building blocks: `components/ui/page-header.tsx` (page headers and status
pills) and `components/dashboard/MetricCard.tsx` (KPI cards).
