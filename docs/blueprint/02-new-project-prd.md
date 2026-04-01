# 02 — New Project Definition & PRD Outline

## 5. New Project Definition

### Product Goal

Build a **multi-tenant social media intelligence platform** — a self-hosted or cloud-deployed web application that lets users monitor, aggregate, translate, and analyze content from external social platforms via third-party API providers.

The reference project (X-Ray) proves this product shape works for Twitter/X. The new project generalizes the architecture so it can target **any social platform** with an API provider, while keeping the same core workflow: watchlists → fetch → translate → analyze.

> The project is named **Feedscope**. `Confirmed`: product name. `Pending Confirmation`: domain, branding direction.

### Target Users

- **Individual power users** who monitor social media accounts for research, investment, journalism, or competitive intelligence.
- **Small teams** who need shared watchlists and group management with per-user data isolation.
- Same profile as the reference project's users, but not limited to a single social platform.

### Core Workflows

1. **Sign in** — OAuth (Google default, extensible). Email allowlist for access control.
2. **Connect a data source** — Configure API credentials for a social platform provider (e.g., TweAPI for Twitter).
3. **Create Watchlists** — Add accounts to monitor. Trigger fetch (SSE streaming). View aggregated posts.
4. **Translate & Analyze** — AI-powered translation with editorial commentary. Configurable AI providers.
5. **Explore** — Search posts, view user profiles, browse bookmarks/likes/lists/DMs from connected accounts.
6. **Organize** — Group contacts, tag them, import from platform exports.
7. **External API access** — Generate webhook keys for programmatic access.
8. **Settings** — Per-user credentials, AI provider config, retention policies, integration webhooks.

### Key Differentiators from Reference

| Aspect | Reference (X-Ray) | Feedscope |
|--------|-------------------|-------------|
| Platform | Twitter/X only | Platform-agnostic provider interface |
| Backend | Bun/TypeScript (vinext) | Python (FastAPI) |
| Database | SQLite (embedded) | PostgreSQL on Azure (scalable) |
| Deployment | Docker → Railway | Docker → Azure Container Apps |
| Frontend framework | vinext (non-standard) | Next.js 15 (standard) |
| Auth | NextAuth v5 (Google only) | NextAuth v5 (Google + extensible) |
| Background work | Client-driven SSE only | SSE + optional background tasks via Azure Queue |

### v1 Scope

- Full watchlist lifecycle: CRUD, member management, SSE fetch, SSE translate
- Twitter as the first (and only v1) platform provider via TweAPI
- Google OAuth with email allowlist
- AI translation with configurable providers (Anthropic, OpenAI-compatible)
- Explore module: search, user profiles, bookmarks, likes
- Groups with tagging and bulk import
- Webhook key system for external API access
- Settings: credentials, AI config, retention policies
- Dashboard with status overview
- Docker deployment to Azure Container Apps
- PostgreSQL on Azure for all persistence

### Later-Phase Scope (Not v1)

- Additional platform providers (Bluesky, Mastodon, Reddit)
- Background scheduled fetches (Azure Queue + worker)
- Team workspace with shared watchlists and RBAC
- Analytics dashboards with charts (Recharts)
- DM viewing and list browsing
- zhe.to or generic bookmark integrations
- Full-text search (Azure AI Search or PostgreSQL FTS)

---

## 6. Reference Reuse Strategy

### What to Reuse as Reference (study and adapt)

| Category | What | Why |
|----------|------|-----|
| Frontend patterns | Page organization, shell layout, sidebar, breadcrumbs, data fetching hooks, SSE client, Masonry grid, theme system | Proven interaction patterns; vinext quirks removed by switching to standard Next.js |
| UI design system | 3-tier luminance CSS tokens, fade-up animations, feedback components, Tailwind v4 setup | Visual polish with minimal code |
| API contract shape | `{ success, data, error }` envelope; session-auth vs webhook-auth split | Clean separation between internal UI routes and external API routes |
| Multi-tenancy pattern | ScopedDB — bind `userId` at construction, auto-inject `WHERE user_id = ?` | Row-level security "correct by construction" |
| Provider abstraction | `ITwitterProvider` interface + factory + mock | Enables platform-agnostic design and test mocks |
| Webhook auth | SHA256 hash, constant-time compare, prefix-only storage | Secure API key management |
| SSE protocol | Event types (progress, posts, done), pure parser, AbortController cleanup | Real-time UX for long-running operations |
| Test strategy | 4-layer pyramid, in-memory DB for unit tests, E2E auth bypass | Fast tests, no external dependencies |

### What to Re-implement Cleanly

| Category | What | Why |
|----------|------|-----|
| Backend API layer | All 60+ route handlers | Python (FastAPI), not TypeScript |
| Database schema | All 18 tables | PostgreSQL with Alembic migrations, not SQLite + ad-hoc ALTER TABLE |
| Auth adapter | NextAuth SQLite adapter | Replace with NextAuth PostgreSQL adapter or Python-native auth |
| AI translation service | Provider registry, prompt template, response parser | Python SDK equivalents (anthropic, openai) |
| Normalizer | TweAPI response → internal types | Python dataclasses/Pydantic models |

### What to Replace

| Reference | Replacement | Reason |
|-----------|------------|--------|
| vinext (non-standard RSC framework) | Next.js 15 (standard) | Eliminates 10+ vinext-specific workarounds |
| SQLite (embedded) | Azure PostgreSQL Flexible Server | Scalable, concurrent writes, proper migrations |
| Railway (PaaS) | Azure Container Apps | User requirement: Azure-first |
| Bun runtime (backend) | Python 3.12+ / uvicorn | User requirement: Python backend |
| `bun:sqlite` / `better-sqlite3` dual driver | `asyncpg` or `sqlalchemy[asyncio]` | Single driver, async-native |
| Husky pre-commit (Bun tests) | pre-commit framework (Python linters + pytest) | Python ecosystem |

### What NOT to Carry Over

- X-Ray branding, product name, logo, and copy
- Chinese-language UI text and prompts (unless the user requests it)
- Twitter-specific hard-coded routes (generalize to provider interface)
- vinext compatibility workarounds (routerRef, null-prototype params, font shim)
- The `agent/` and `scripts/` directories (CLI tooling specific to the original project)
- SQLite-specific patterns (`initSchema`, `safeAddColumn`, `bunfig.toml` coverage config)

### What to Defer

- DM viewing, Twitter Lists browsing — low priority, high API complexity
- zhe.to integration — product-specific
- Recharts analytics dashboards — nice-to-have, not core
- Custom translation prompt editor — power-user feature, defer to v1.1

---

## 7. PRD Outline

### Problem Statement

Researchers, analysts, and power users need to systematically monitor social media accounts, aggregate their posts, and understand foreign-language content — all within a private, self-hosted environment that doesn't rely on the social platform's own notification system or algorithmic feed.

Existing solutions are either platform-locked SaaS products (no data ownership), command-line scripts (no UI), or enterprise tools (overpriced for individuals/small teams).

### Target Users

1. **Solo researchers** — track 10–100 accounts across topics, need translation and AI commentary.
2. **Small analysis teams** (2–5 people) — shared infrastructure, per-user data isolation.
3. **Developers** — programmatic access to aggregated social data via webhook API keys.

### Primary Use Cases

| # | Use Case | Actor |
|---|----------|-------|
| UC-1 | Create a watchlist, add accounts, fetch their recent posts | Researcher |
| UC-2 | Translate fetched posts with AI commentary | Researcher |
| UC-3 | Search for posts or users across the platform | Researcher |
| UC-4 | View a user's profile, timeline, followers, following | Researcher |
| UC-5 | Organize monitored accounts into groups with tags | Researcher |
| UC-6 | Import accounts from platform export files | Researcher |
| UC-7 | Access aggregated data via API using a webhook key | Developer |
| UC-8 | Configure AI provider, model, and custom prompt | Power user |
| UC-9 | Set retention policies and fetch intervals per watchlist | Power user |
| UC-10 | View personal bookmarks and likes from the connected account | Researcher |

### Core Features (v1)

1. **Authentication** — Google OAuth, email allowlist, JWT sessions.
2. **Dashboard** — Status cards showing credential health, recent activity, quick actions.
3. **Watchlists** — CRUD, member management with tags, SSE fetch, SSE translate, post browsing with filters.
4. **Groups** — CRUD, member management, bulk import, profile cache.
5. **Explore** — Post search, user profile viewer, bookmarks, likes.
6. **AI Translation** — Multi-provider (Anthropic, OpenAI-compatible), configurable model/prompt, batch translation with streaming progress.
7. **Webhook API** — Key generation/rotation, SHA256 auth, external Twitter data access.
8. **Settings** — Credentials, AI config, retention policies, integrations.
9. **Usage Tracking** — Per-endpoint call counts, daily aggregation.

### Non-Goals (v1)

- Multi-platform support (Bluesky, Mastodon, Reddit) — architecture supports it, but v1 ships with Twitter only.
- Background scheduled fetches — v1 uses client-triggered SSE; background workers are a later-phase feature.
- Team workspaces with RBAC — v1 is multi-tenant but each user is independent.
- Mobile-native app — responsive web only.
- Real-time push notifications — polling/manual refresh only.

### v1 Success Criteria

1. A user can sign in, configure TweAPI credentials, create a watchlist, add 10 accounts, fetch their posts, and translate them — all within 5 minutes.
2. All API routes enforce user isolation (multi-tenancy) — no cross-user data leakage.
3. AI translation works with at least 2 providers (Anthropic and one OpenAI-compatible).
4. Webhook API allows external scripts to pull user tweets and search results.
5. Deployed on Azure with PostgreSQL, accessible via HTTPS with custom domain.
6. Test coverage ≥ 80% on backend (pytest), frontend has Playwright E2E for critical paths.
