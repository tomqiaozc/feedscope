# 01 — Reference Project Analysis

## 1. Reference Project Overview

**X-Ray** is a multi-tenant Twitter/X content monitoring and insight system. A single operator deploys it; authenticated users (email-allowlisted) each get isolated workspaces.

### Core User Flow

1. Sign in with Google OAuth (email allowlist gate).
2. Configure a TweAPI key (third-party Twitter data API) in Settings.
3. Create **Watchlists** — add Twitter accounts to monitor; trigger a fetch that pulls recent tweets via SSE streaming, then batch-translate them with AI.
4. Browse, search, and analyze Twitter content: tweets, users, bookmarks, likes, DMs, lists, analytics.
5. Optionally expose data to external systems via **Webhook keys**.
6. Organize contacts into **Groups**, tag them, import from Twitter export files.

### Major Technical Pieces

| Layer | Technology | Role |
|-------|-----------|------|
| Runtime | Bun | JS/TS runtime (production + tests) |
| Framework | vinext (Vite + RSC) | Next.js-compatible web framework |
| Database | SQLite + Drizzle ORM | Embedded relational storage |
| Auth | NextAuth v5 + Google OAuth | Session management, JWT strategy |
| External API | TweAPI.io | Twitter data source (REST, API-key auth) |
| AI | Vercel AI SDK (Anthropic / OpenAI) | Tweet translation + editorial commentary |
| UI | Tailwind CSS v4 + shadcn/ui | Component library + design tokens |
| Testing | Bun test runner + Playwright | Unit/integration/E2E |
| Deployment | Docker → Railway | Container on PaaS with volume-mounted SQLite |

### Complexity Level

Medium-high for a single-developer project: 18 DB tables, 60+ API routes, SSE streaming, multi-tenant row-level security, AI integration with 5 providers, webhook auth system, and a 4-layer test pyramid.

---

## 2. Reference Architecture Breakdown

### Module Boundaries

```
┌─────────────────────────────────────────────────────────────────┐
│  Browser (React Client Components, "use client" everywhere)     │
│  └─ fetch() / SSE reader → /api/* routes                       │
├─────────────────────────────────────────────────────────────────┤
│  vinext Server                                                   │
│  ├─ proxy.ts (middleware: auth redirect, excludes /api/*)       │
│  ├─ /api/auth/*          → NextAuth handlers                    │
│  ├─ /api/explore/*       → session-auth → TwitterProvider       │
│  ├─ /api/twitter/*       → webhook-auth → TwitterProvider       │
│  ├─ /api/watchlists/*    → session-auth → ScopedDB              │
│  ├─ /api/groups/*        → session-auth → ScopedDB              │
│  ├─ /api/translate       → session-auth → AI service            │
│  ├─ /api/settings/*      → session-auth → ScopedDB (KV store)  │
│  └─ /api/webhooks/*      → session-auth → ScopedDB              │
├─────────────────────────────────────────────────────────────────┤
│  Data Layer                                                      │
│  ├─ ScopedDB(userId) → 13 domain repos with WHERE user_id = ?  │
│  ├─ ProfilesRepo (global, shared cache, no user scope)          │
│  └─ SQLite file (single file, volume-mounted in prod)           │
├─────────────────────────────────────────────────────────────────┤
│  External Services                                               │
│  ├─ TweAPI.io (Twitter data, 20 POST/GET endpoints)             │
│  ├─ AI providers (Anthropic, OpenAI-compat, 5 presets)          │
│  └─ zhe.to (bookmark integration, webhook push)                 │
└─────────────────────────────────────────────────────────────────┘
```

### Runtime Boundaries

- **Client**: All page components are `"use client"`. No RSC data fetching — everything goes through `/api/*`.
- **Server**: vinext serves both SSR (initial HTML) and API routes in the same Bun process.
- **Database**: In-process SQLite — no network hop. Dual-driver: `bun:sqlite` in Bun, `better-sqlite3` in Node.js dev workers.
- **No background workers**: Long operations (fetch, translate) are client-driven SSE streams. No job queue or scheduler in the web app.

### Data Flow

1. **Read path**: Client `useFetch()` → API route → `requireAuth()` → `ScopedDB` → Drizzle query → SQLite → JSON response.
2. **External data path**: API route → `TweAPIProvider` → TweAPI.io REST → `normalizer.ts` → internal types → JSON response.
3. **SSE write path**: Client opens SSE → API route loops over members → fetch from TweAPI → insert to SQLite → emit SSE event → client updates state.
4. **Webhook path**: External caller → `X-Webhook-Key` header → SHA256 lookup → resolve `userId` → same `TweAPIProvider` path as session-auth routes.

### External Dependencies

| Dependency | Criticality | Substitutable? |
|-----------|------------|----------------|
| TweAPI.io | Hard — all Twitter data flows through it | Yes, via `ITwitterProvider` interface |
| Google OAuth | Hard — only auth provider configured | Yes, NextAuth supports many providers |
| AI providers | Soft — translation is optional | Yes, 5 presets + custom endpoint |
| zhe.to | Soft — optional bookmark integration | Yes, generic webhook |

### Tightly Coupled Areas

- **vinext framework**: Middleware, route handlers, and font loading all have vinext-specific workarounds. Switching to standard Next.js would require reversing ~10 compatibility patches.
- **SQLite as sole data store**: No separation of auth store from business store. The `user` table is both NextAuth's identity table and the FK target for all business tables.
- **TweAPI response shapes**: The `normalizer.ts` module is tightly coupled to TweAPI's JSON format. A different Twitter API would require a full normalizer rewrite (but only that module).

---

## 3. Reference Development Workflow

### Local Setup

```bash
bun install                    # install deps (bun:sqlite + better-sqlite3)
cp .env.example .env           # configure OAuth + TweAPI keys
bun run db:push                # push Drizzle schema to SQLite
bun dev                        # vinext dev server on port 7007
```

### Run / Build / Test

| Command | Purpose |
|---------|---------|
| `bun dev` | Dev server with HMR (port 7007) |
| `bun run build` | Production build via vinext |
| `bun start` | Serve production build |
| `bun test` | Run all Bun tests (unit + integration) |
| `bun test src/__tests__/db/scoped.test.ts` | Single test file |
| `bun test --coverage` | Coverage report (90% threshold) |
| `bun run test:e2e:browser` | Playwright browser tests |
| `bun run lint` | ESLint strict check |

### Test Pyramid (4 layers)

| Layer | Trigger | Scope | Tool |
|-------|---------|-------|------|
| 1 — Unit + Integration | Pre-commit hook | `tests/` + `src/__tests__/{db,api,twitter,components,services,ui}/` | Bun test, `--coverage` |
| 2 — Lint | Pre-commit hook | All `src/` | ESLint |
| 3 — API E2E | Pre-push hook | `src/__tests__/e2e/` — starts server on port 17007, `E2E_SKIP_AUTH=true` | Bun test |
| 4 — Browser E2E | Manual (`bun run test:e2e:browser`) | `e2e/*.pw.ts` — vinext dev on port 27028, `MOCK_PROVIDER=true` | Playwright |

### Configuration Loading

- `.env` file loaded automatically by Bun.
- Settings (AI config, retention, intervals) stored in `settings(user_id, key, value)` KV table.
- Per-watchlist settings override global settings via `watchlist.{id}.{key}` namespace.

### Release Flow

```bash
bun run release              # patch bump (default)
bun run release -- minor     # minor bump
```

Automated script: bump `package.json` version → sync lockfile → generate CHANGELOG → git commit + tag + push → create GitHub release.

### Deployment Path

Docker build (3-stage) → push to Railway → Railway serves container with volume-mounted SQLite at `/data/xray.db`.

---

## 4. Git History Interpretation

*Based on analysis of 520 commits over 68 days (Jan 21 – Mar 30, 2026).*

### Major Development Phases

| Phase | Dates | Commits | What Happened |
|-------|-------|---------|---------------|
| 0 — CLI prototype | Jan 21–31 | ~42 | Tweet classification scripts, Express scheduler, AI analysis workflow. No web app. |
| 1 — Web scaffold | Feb 12–24 | ~68 | 3-week gap, then massive burst: Next.js + Drizzle + NextAuth + Docker + all initial pages in 2 days. |
| 2 — Feature sprint | Feb 25 – Mar 6 | ~362 | Peak intensity (38 commits/day avg). Watchlists, SSE, AI translation, groups, multi-tenancy, ScopedDB rewrite, Playwright tests. |
| 3 — Polish | Mar 7–15 | ~30 | Custom translation prompts, retention policies, test hardening, lint enforcement. |
| 4 — Maintenance | Mar 21–30 | ~21 | Release automation, auth bug fixes, UI spec compliance, port migration. |

### Implementation Order Worth Noting

1. **Scripts and data pipeline first** — the CLI prototype validated the data model before any web UI existed.
2. **Full web scaffold in 2 days** — auth, layout, all pages, Docker, deployment all landed simultaneously.
3. **Core feature (watchlists) on day 3** — built end-to-end (DB + API + SSE + UI) in a single day once the scaffold was stable.
4. **Multi-tenancy refactor on day 7** — `ScopedDB` + auth adapter rewrite touched 20+ files in one day. Identity bugs only surfaced after multi-session testing.
5. **Groups feature on day 9** — followed the same CRUD+members pattern as watchlists, built in a single day.
6. **Test formalization on day 8** — 4-layer test pyramid, coverage thresholds, and strict lint rules were added after the feature sprint, not before.

### Sequencing Worth Borrowing

- **Validate data model with scripts before building UI** — reduces schema churn during UI development.
- **Scaffold everything at once** (auth, shell, all page stubs, Docker) — provides a runnable app from day 1.
- **Build the hardest feature (watchlists + SSE) early** — it forces architectural decisions that benefit all later features.
- **Defer multi-tenancy hardening until real usage reveals bugs** — premature row-level security adds complexity before you know the access patterns.
- **Add test infrastructure after the first feature sprint** — testing empty shells wastes effort; testing real features catches real bugs.

### High-Churn Areas (Risk Signals)

| Area | Touches | Implication |
|------|---------|-------------|
| `src/db/index.ts` | 36 | Schema init and migration logic is the most volatile code. Plan for migration tooling. |
| `tweet-card.tsx` | 29 | Core leaf component. Rich media, translation, metrics — expect ongoing iteration. |
| `sidebar.tsx` | 25 | Every new feature adds a nav entry. Design the sidebar to be config-driven from day 1. |
| `schema.ts` | 16 | Continuous column additions. Use a proper migration tool in production. |
| vinext compat fixes | 3 rounds | Framework edge cases caused multi-day debugging. Budget time for framework quirks. |

### Planning Implications

- A skilled developer built this full-featured app in ~11 focused days. With Python backend + separate frontend, expect 3–4 weeks for equivalent functionality.
- The Hono server detour (built and deleted in 24h) shows the cost of premature architecture. Pick the API framework early and commit.
- The ScopedDB rewrite (1 day, 20+ files) shows that auth/identity bugs surface late. Build with multi-tenancy from the start.
