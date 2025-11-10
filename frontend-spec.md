You are a senior frontend architect. Build a production-ready Next.js 14+ (App Router) TypeScript SaaS for NLPForge-Tester, deeply integrated with the existing backend.

Read and use the repository docs/code, especially:

BACKEND_INTEGRATION_GUIDE.md — the single source of truth for endpoints, request/response examples, component architecture, and the implementation checklist.

Any generated OpenAPI schema (or server routes) to derive exact types.

🎯 Product in one line

A B2B SaaS where users type a plain-English API request, and the system parses → generates datasets (CSV/JSON, Gemini) → embeds (BAAI/bge-small-en-v1.5) → stores (Redis) → searches (cosine) → executes tests → reports. The UI must be clean, premium, fast, and human-crafted (no “AI template” vibes).

🧰 Tech Stack & Libraries (strict)

Next.js 14+ (App Router, Server Components), TypeScript

TailwindCSS with CSS variables + fluid type; next-themes for light/dark

shadcn/ui primitives (Radix under the hood) + lucide-react icons

Framer Motion for tasteful micro-interactions; respect prefers-reduced-motion

TanStack Query (React Query) for data fetching, caching, optimistic updates

react-hook-form + zod for forms + runtime validation

react-virtualized/@tanstack/react-virtual for big tables

Recharts for confidence/metrics charts (dynamic import)

SWR or SSE/WebSocket for live run updates (choose best fit per backend)

Jest + RTL for unit tests, Cypress for E2E, Storybook for UI docs

Optional (production readiness): Sentry (errors), PostHog (product analytics), Axe/lighthouse CI (a11y/perf).

🎨 Design System (no “AI look”)

Tone: modern, confident, human. No neon blobs, no heavy gradients.

Colors:

Background: #FFFFFF (light) / #0B1220 (dark)

Foreground: #0F172A (light) / #E5E7EB (dark)

Primary: teal #06B6D4 or violet #7C3AED (pick one family)

Success #10B981, Danger #EF4444, Warning #F59E0B

Typography: Inter for UI; Manrope/Satoshi for headings (variable fonts).

Radius: 12–16px cards; inputs 6–8px. Shadows: soft, layered.

Animations: 160–260ms, subtle easing, stagger (30–60ms). All motion must feel intentional.

Microcopy: friendly, concise, engineering tone (“Run Tests”, “Replay Failed”). Mask secrets by default; explicit reveal w/ confirmation.

🗺️ App Structure & Navigation

Primary routes (post-auth):

/dashboard — KPIs, recent runs, quick “New Run”

/run/new — primary query runner (NL input → progress → redirect to report)

/runs & /runs/:id — run list + detailed report (Cases, Logs, Metrics)

/search — semantic search (intent filters, similarity range, confidence)

/templates & /templates/:id — CRUD, auto-discover, sync from JSON, hot reload

/datasets — Browse / Generate / Upload tabs

/settings — Org, API Keys, Models, Rate Limits, Webhooks, Theme

/billing — plan teaser + portal link

/docs, /changelog — MDX docs

Top nav: Dashboard · Runs · Search · Templates · Datasets · Settings (+ “New Run” button, Theme toggle)

🧩 Pages — exact requirements
1) Dashboard (/dashboard)

KPI cards: Runs today, Pass rate, Avg latency, Active templates (click → filtered runs)

Recent Runs (virtualized), quick New Run input

Live Metrics + Trend chart (deferred load)

Empty states with one-click sample actions

Motion: staggered section entrance, hover lift on cards, confidence gauge sweep.

2) New Run (/run/new)

Large QueryInput with example chips (Login, Signup, Update, Delete)

Options drawer: tenant, model, dry run, rate limit

On submit: Progress Drawer (Queued → Generating Dataset → Embedding → Executing → Summarizing)

Upon completion: redirect to /runs/:id

Endpoints: from BACKEND_INTEGRATION_GUIDE.md (POST /api/v1/query, status, results).
Live updates: SSE/WebSocket if available; else poll + optimistic UI.

3) Runs (/runs, /runs/:id)

/runs: filters (status, date, intent, template), infinite list

/runs/:id:

Summary header: intent, confidence (0–100%), pass/fail, latency

Tabs:

Cases: table (virtualized) → expand row for masked req/resp JSON + diff viewer

Logs: live stream (tail), copy actions

Metrics: small charts (latency, distribution)

Actions: Replay, Download CSV/JSON, Create ticket

Motion: row expand height animation + fade, gentle progress ticks for live.

4) Search (/search)

Semantic search box (debounced) + chips for sample queries

Filters: intent multi-select, min similarity slider, date range, template version

Results: list/table with SimilarityBar, ConfidenceBadge, intent, template, actions

Right side slide-over (on row click): original query, matched case, request/expected JSON (masked), replay

Endpoint: GET /api/v1/search?text=...&intent=...&minSim=... (cosine similarity).

5) Templates (/templates, /templates/:id)

Grid/list of templates (name, version, status, confidence, updated)

Actions: New, Auto-Discover (OpenAPI/Heuristic/LLM), Sync from JSON, Hot Reload

Editor (split view): AutoForm (zod schema → dynamic fields) + JSON editor (validation, diff on save)

Promote/Demote version, “Test probe” (dry-run), change history rail

Endpoints: GET/POST/PUT /api/v1/templates, /templates/autodiscover, /templates/sync, /templates/hot-reload.

6) Datasets (/datasets)

Tabs:

Browse: filters (intent/version), search by hash_id, table with expand → masked JSON + mini diff; bulk: export, re-embed, prune

Generate: prompt → steps (Parsing → LLM expand (Gemini) → Validate → Write CSV/JSON → Embed → Done) → link to Browse

Upload: CSV dropzone, schema validation, “also embed” checkbox

Endpoints: /datasets (GET), /datasets/generate (POST), /datasets/upload (POST), /embeddings/reindex (POST), datasets/export.

7) Settings (/settings)

Tabs: Profile, Organization, API Keys (masked, reveal w/ confirm), Models, Rate Limits, Webhooks

Theme + language + timezone

Audit log list (basic)

🧱 Reusable Components (build well, Storybook each)

KpiCard, ConfidenceGauge, SimilarityBar

ProgressDrawer (stepper + log tail)

DataTable (virtualized, selectable, sortable)

JSONViewer(masked) + copy & redact toggles

UploadDropzone(CSV) with preview/validation

TemplateCard, TemplateEditor(Form+JSON)

CodeBlock (copy), ConfirmDialog, ToastProvider, EmptyState

ThemeToggle, Breadcrumbs, ErrorBoundary

Motion patterns: scale 1.02 on hover for cards; 160–240ms; stagger by 40ms; no distracting looping animations. Respect prefers-reduced-motion.

🔌 Data Layer & Types

Generate or hand-write typed clients for all endpoints in BACKEND_INTEGRATION_GUIDE.md.

Centralize fetchers in lib/api.ts (TanStack Query).

Put shared response types in types.ts; validate with zod when parsing unknown JSON.

Global error boundary + route-level error UI with recovery actions.

🔐 Security & Privacy (front-end)

Never log raw secrets; mask password/token fields by default.

Reveal requires user confirmation (log the event client-side).

CSRF safe calls (per backend guidance), strict CORS.

Sanitize/escape all user-visible JSON.

Rate-limit UI buttons with cooldowns where sensible.

⚙️ Performance, A11y, SEO

Lighthouse ≥95 on Perf/A11y/Best Practices/SEO.

Dynamic import heavy widgets (charts, visualizers).

Optimize LCP (hero content first), preload fonts.

Keyboard navigable dialogs/menus/tables; ARIA everywhere; focus rings visible.

Metadata/OG tags; /sitemap.xml, /robots.txt.

🧪 Testing & QA

Unit tests for core components with RTL.

E2E happy path: new run → report → replay; template CRUD; dataset generate/upload; search filter & export.

Visual regression (critical pages).

Mock server for Storybook (MSW).

📦 File Structure (starter)
app/
  layout.tsx
  page.tsx                 # landing (already)
  dashboard/page.tsx
  run/new/page.tsx
  runs/page.tsx
  runs/[id]/page.tsx
  search/page.tsx
  templates/page.tsx
  templates/[id]/page.tsx
  datasets/page.tsx
  settings/page.tsx
components/
  dashboard/*  query/*  test-suite/*  templates/*  datasets/*
  ui/*  charts/*  common/*
lib/
  api.ts  fetch.ts  utils.ts  motion.ts  constants.ts
  validators/ (zod)
hooks/
  use-toaster.ts  use-progress.ts  use-live-logs.ts
types/
  index.ts  api.ts  templates.ts  runs.ts  datasets.ts
styles/
  globals.css  tokens.css

✅ Acceptance Criteria (definition of “done”)

All pages implemented, wired to backend per BACKEND_INTEGRATION_GUIDE.md

Beautiful light/dark themes; no “AI-generated” look; bespoke spacing & microcopy

Smooth, tasteful micro-interactions; motion respects user preferences

Virtualized big tables; charts lazy-loaded; no jank on mid-range laptops

Secrets masked, confirmations for reveals, downloadable CSV/JSON

Storybook for every reusable component + basic docs

Unit + E2E tests pass; Lighthouse ≥95; deploy-ready on Vercel

Clean, documented code with clear TODOs only where the backend lacks features

Now: read BACKEND_INTEGRATION_GUIDE.md and backend code, infer exact types, scaffold the routes & components above, and implement the full UI with premium polish, best-in-class micro-interactions, and production hardening.
