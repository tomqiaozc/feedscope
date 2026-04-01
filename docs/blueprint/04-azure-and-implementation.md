# 04 — Azure Mapping & Staged Implementation Plan

## 9. Azure Service Mapping

| # | Reference Dependency | Azure Replacement | Migration Impact | Difficulty | Notes |
|---|---------------------|-------------------|-----------------|------------|-------|
| 1 | Railway (PaaS hosting) | **Azure Container Apps** | High — new deployment target | Medium | Two containers: frontend (Next.js) + backend (FastAPI). Supports internal networking, auto-scale, custom domains. |
| 2 | SQLite (embedded DB) | **Azure Database for PostgreSQL Flexible Server** | High — schema rewrite, driver change | Medium | Burstable tier (B1ms) sufficient for start. Enables concurrent writes, proper migrations, connection pooling. |
| 3 | Docker (build) | **Azure Container Registry (ACR)** | Low — same Dockerfiles, new registry | Low | Push images to ACR, Container Apps pulls from it. |
| 4 | `.env` file (secrets) | **Azure Key Vault** | Medium — secret references in Container Apps | Low | Container Apps supports Key Vault secret references natively. |
| 5 | No CDN | **Azure Front Door** or **Container Apps built-in ingress** | Low | Low | Start with Container Apps ingress; add Front Door later for CDN + WAF. |
| 6 | No CI/CD | **GitHub Actions** → ACR → Container Apps | Medium — new pipeline | Medium | Build, test, push image, deploy. Separate jobs for frontend and backend. |
| 7 | No monitoring | **Azure Monitor** + **Application Insights** | Low — add SDK | Low | OpenTelemetry integration for both Next.js and FastAPI. |
| 8 | No queues (SSE only) | **Azure Queue Storage** (later-phase) | N/A for v1 | Low | For background scheduled fetches in later phases. |
| 9 | Volume-mounted SQLite | **Azure Blob Storage** (optional) | Low | Low | Only needed if caching media files. PostgreSQL handles all data. |
| 10 | Google OAuth (NextAuth) | **Google OAuth** (unchanged) + **Microsoft Entra ID** (optional) | Low | Low | Keep Google OAuth. Optionally add Entra ID for enterprise sign-in. `Pending Confirmation` |
| 11 | No DNS management | **Azure DNS** | Low | Low | Only needed for custom domain. `Pending Confirmation`: domain name |
| 12 | No email/notifications | **Azure Communication Services** (later-phase) | N/A for v1 | Medium | For alert notifications in later phases. |

### Azure Resource Group Layout

```
rg-feedscope-{env}/
├── aca-env-{env}                    # Container Apps Environment
│   ├── aca-frontend-{env}           # Next.js container
│   └── aca-backend-{env}            # FastAPI container
├── psql-feedscope-{env}             # PostgreSQL Flexible Server
├── acr-feedscope                    # Container Registry (shared across envs)
├── kv-feedscope-{env}               # Key Vault
├── log-feedscope-{env}              # Log Analytics Workspace
└── appi-feedscope-{env}             # Application Insights
```

`{env}` = `dev`, `staging`, `prod`. ACR is shared.

---

## 10. Staged Implementation Plan

### Phase 0 — Project Bootstrap (Days 1–2)

**Objective**: Runnable monorepo with both frontend and backend skeleton, local Docker Compose.

**Key Tasks**:
1. Initialize monorepo structure: `frontend/`, `backend/`, `docker-compose.yml`
2. **Frontend**: `npx create-next-app@latest` with TypeScript, Tailwind v4, App Router
3. **Backend**: `pyproject.toml` with FastAPI, uvicorn, SQLAlchemy, Alembic, httpx, pydantic-settings, ruff, pytest
4. Set up `docker-compose.yml`: PostgreSQL 16 + frontend (Node) + backend (Python)
5. Backend: Create `app/main.py` with health check endpoint
6. Frontend: Create `/api/proxy/[...path]/route.ts` reverse proxy stub
7. Verify: `docker compose up` → frontend on :3000, backend on :8000, PostgreSQL on :5432, health check responds
8. Initialize git, add `.gitignore`, initial commit

**Dependencies**: None
**Risks**: Docker Compose networking misconfiguration
**Deliverables**: Runnable empty monorepo
**Acceptance**: `curl localhost:8000/health` returns `{"status": "ok"}`

---

### Phase 1 — Auth + Database Foundation (Days 3–5)

**Objective**: Users can sign in with Google OAuth, database schema exists, multi-tenancy works.

**Key Tasks**:
1. **Backend DB models**: Port all 18 tables to SQLAlchemy models in `app/db/models.py` (PostgreSQL types: `TIMESTAMPTZ`, `JSONB`, `BOOLEAN`, `SERIAL`)
2. **Alembic init**: `alembic init`, auto-generate first migration from models, verify `alembic upgrade head` works
3. **Frontend auth**: Install `next-auth@beta`, configure Google OAuth provider, email allowlist callback, JWT strategy
4. **NextAuth PostgreSQL adapter**: Use `@auth/pg-adapter` or `@auth/drizzle-adapter` with PostgreSQL
5. **Backend auth dependency**: `get_current_user()` reads `X-User-Id` header, `require_auth()` returns `ScopedDB`
6. **ScopedDB class**: Port from reference — `__init__(user_id, session)`, 13 repo stubs (empty methods for now)
7. **Frontend proxy**: `/api/proxy/[...path]/route.ts` — validate session, extract `userId`, forward to backend with `X-User-Id` header
8. **Login page**: Port the reference login page layout (Google sign-in button, branded card)
9. **E2E auth bypass**: `E2E_SKIP_AUTH` env var for backend, deterministic test user

**Dependencies**: Phase 0 complete, Google OAuth credentials (`Manual Action Required`)
**Risks**: NextAuth + PostgreSQL adapter compatibility; proxy session forwarding
**Deliverables**: Sign in → session cookie → proxy forwards authenticated requests to backend
**Acceptance**: Sign in with Google → backend logs `X-User-Id` on proxy request → DB `user` table has a row

---

### Phase 2 — Shell + Dashboard + Settings (Days 6–10)

**Objective**: Authenticated users see the app shell with sidebar, dashboard, and can configure credentials.

**Key Tasks**:
1. **AppShell**: Port from reference — collapsible sidebar, floating island content area, mobile responsive
2. **Sidebar**: Config-driven static groups + CSS Grid row animation collapse
3. **Breadcrumbs**: Port `useBreadcrumbs` context + hook pattern
4. **Theme system**: Port 3-tier luminance CSS tokens, FOUC prevention script, theme toggle
5. **Feedback components**: Port `LoadingSpinner`, `ErrorBanner`, `StatusMessage`, `EmptyState`, `SectionSkeleton`
6. **Dashboard page**: Status cards (credentials health, recent activity), fade-up stagger animation
7. **Settings page**: Credentials CRUD (TweAPI key, cookie) with display/edit toggle, masked display
8. **AI Settings page**: Provider selector, API key, model, base URL, SDK type, test connection
9. **Backend routes**: `GET/PUT/DELETE /api/v1/credentials`, `GET/PUT /api/v1/settings/ai`, `POST /api/v1/settings/ai/test`
10. **Backend ScopedDB repos**: Implement `CredentialsRepo`, `SettingsRepo` with full CRUD
11. **Data fetching hooks**: Port `useFetch`, `useSearch` from reference (adapt endpoint paths to `/api/proxy/...`)

**Dependencies**: Phase 1 complete
**Risks**: Tailwind v4 + shadcn/ui setup; CSS token mapping
**Deliverables**: Full shell with working settings, AI connection test succeeds
**Acceptance**: User can save TweAPI key, configure AI provider, test connection — all persisted to DB

---

### Phase 3 — Watchlists Core (Days 11–18)

**Objective**: Users can create watchlists, add members, fetch tweets via SSE, and view aggregated posts.

**Key Tasks**:
1. **Backend routes**: Full watchlist CRUD, member CRUD, posts CRUD, settings, logs
2. **Backend ScopedDB repos**: Implement `WatchlistRepo`, `MemberRepo`, `PostRepo`, `LogRepo`, `TagRepo`
3. **Backend SSE fetch**: `POST /{id}/fetch` → `StreamingResponse` async generator → loop over members → call `TweAPIProvider.fetch_user_tweets()` → insert posts → yield SSE events (`cleanup`, `progress`, `posts`, `done`)
4. **TweAPIProvider**: Implement full provider with all 20 TweAPI endpoints, `httpx.AsyncClient`, timeout handling, error hierarchy (`ProviderError`, `UpstreamError`, `AuthRequiredError`, `TimeoutError`)
5. **Normalizer**: Port `normalizer.ts` → `normalizer.py` — TweAPI raw response → internal `Post`/`Author` Pydantic models
6. **MockProvider**: Return fixture data for all methods
7. **Frontend watchlist list page**: Grid of `WatchlistCard` components, create/edit/delete dialogs, `?new=1` auto-open
8. **Frontend watchlist detail page**: Members tab + posts tab, tag filter pills, SSE fetch with progress UI, SSE client using `parseSSEBuffer` pattern
9. **Tags**: CRUD API + frontend tag management in member edit flow
10. **Post browsing**: Filtered by tag, sorted by date, "Load More" pagination
11. **PostCard component**: Platform-agnostic content card (text, metrics, media grid, translation display)

**Dependencies**: Phase 2 complete, TweAPI key configured
**Risks**: SSE streaming through Next.js proxy (test early); TweAPI response shape changes; rate limiting
**Deliverables**: End-to-end watchlist flow works: create → add members → fetch → browse posts
**Acceptance**: Create watchlist, add 3 members, fetch → posts appear with real-time progress → posts persist after page reload

---

### Phase 4 — AI Translation (Days 19–22)

**Objective**: Posts can be translated with AI commentary, batch translation with streaming progress.

**Key Tasks**:
1. **Backend translation service**: Port `ai.ts` + `translation.ts` + `prompt-defaults.ts` to Python
2. **Provider registry**: Dict of `{ id: config }` for Anthropic, OpenAI-compatible, custom
3. **Prompt renderer**: Mustache-style template with conditional quoted-text blocks
4. **Response parser**: Split on `[翻译]`, `[引用翻译]`, `[锐评]` markers
5. **Batch translation SSE**: `POST /{id}/translate` → async generator with `asyncio.Semaphore(3)` for sliding-window concurrency → yield events (`start`, `translating`, `translated`, `error`, `done`)
6. **Single translation endpoint**: `POST /api/v1/translate` for one-off translation
7. **Frontend translate button**: Per-post translate action, batch translate all button
8. **Frontend translate progress**: SSE client showing per-post progress, success/failure counts
9. **Translation display**: Rendered in PostCard below original text (translated text + editorial comment)

**Dependencies**: Phase 3 complete, AI provider configured (Phase 2 settings)
**Risks**: AI provider rate limits; prompt compatibility across providers; response parsing fragility
**Deliverables**: Batch translate 10 posts with real-time progress
**Acceptance**: Translate 10 posts → 9+ succeed → translated text + commentary visible in PostCard

---

### Phase 5 — Explore + Groups (Days 23–28)

**Objective**: Users can search tweets, view user profiles, browse bookmarks/likes, and organize contacts into groups.

**Key Tasks**:
1. **Backend explore routes**: Search tweets, user info, user tweets/timeline/replies/highlights/followers/following, bookmarks, likes
2. **Backend group routes**: Full CRUD + members with batch add/delete, profile linking
3. **Backend ProfilesRepo**: Global shared cache (no user scope), upsert on fetch
4. **Frontend explore pages**: Search page with results grid, user profile page (info + tabs for tweets/followers/following), bookmarks page (Masonry grid), likes page (Masonry grid)
5. **Frontend group pages**: List page (same pattern as watchlist list), detail page with member management, bulk import from file
6. **MasonryGrid component**: Port from reference — shortest-column algorithm + `useColumns()` with matchMedia
7. **Profile cache**: `POST /api/v1/profiles/refresh` for batch profile updates with concurrency limit

**Dependencies**: Phase 3 complete (for provider), Phase 2 complete (for shell)
**Risks**: Masonry layout performance with large datasets; bookmarks/likes require Twitter cookie auth
**Deliverables**: Search works, user profiles display, groups with bulk import functional
**Acceptance**: Search a keyword → results display; view a user profile → timeline loads; create group → import 50 users from file

---

### Phase 6 — Webhook API + Usage (Days 29–32)

**Objective**: External callers can access data via webhook keys; usage is tracked.

**Key Tasks**:
1. **Backend webhook routes**: CRUD + key rotation, SHA256 hashing, constant-time comparison
2. **Backend webhook auth dependency**: `authenticate_webhook_key(key)` → user_id
3. **Backend twitter routes**: Mirror explore routes but with webhook auth instead of session auth
4. **Usage tracking**: Fire-and-forget per-endpoint call counter, daily aggregation
5. **Frontend webhook page**: Key list (prefix + dates only), generate new, rotate, delete
6. **Frontend usage page**: Table of endpoint call counts, date range filter
7. **Credits endpoints**: Proxy TweAPI credits/usage API

**Dependencies**: Phase 3 complete (provider infrastructure)
**Risks**: Webhook key security (constant-time compare, no plaintext storage)
**Deliverables**: External script can fetch tweets via webhook key
**Acceptance**: Generate key → `curl` with `X-Webhook-Key` header → tweets returned → usage incremented

---

### Phase 7 — Testing + CI/CD (Days 33–37)

**Objective**: Comprehensive test suite, GitHub Actions CI/CD, deployment pipeline.

**Key Tasks**:
1. **Backend unit tests**: All repos, normalizer, crypto, translation parser (pytest, test DB with transactions rolled back)
2. **Backend integration tests**: All API routes with `TestClient`, mock provider, test DB
3. **Backend E2E tests**: Full server with `E2E_SKIP_AUTH`, real DB operations
4. **Frontend Playwright tests**: Smoke tests (login, navigate all pages), functional tests (create watchlist, fetch, translate)
5. **Coverage enforcement**: Backend ≥ 80% (pytest-cov), frontend lint clean
6. **GitHub Actions CI**: On PR — lint (ruff + ESLint) → backend tests → frontend build → Playwright
7. **GitHub Actions CD**: On merge to main — build images → push to ACR → deploy to Azure Container Apps
8. **Pre-commit hooks**: ruff check + mypy (backend), ESLint (frontend)

**Dependencies**: All functional phases complete
**Risks**: Test DB setup in CI (use testcontainers or GitHub Actions PostgreSQL service)
**Deliverables**: Green CI pipeline, automated deployment
**Acceptance**: Push to main → CI passes → images deployed to Azure → health check green

---

### Phase 8 — Azure Deployment + Launch Hardening (Days 38–42)

**Objective**: Production deployment on Azure, custom domain, HTTPS, monitoring.

**Key Tasks**:
1. **Azure resource provisioning**: Resource group, Container Apps Environment, PostgreSQL, ACR, Key Vault, Log Analytics (`Manual Action Required`)
2. **Dockerfiles**: Optimize both frontend and backend images (multi-stage builds)
3. **Container Apps configuration**: Two containers (frontend + backend), internal networking (backend not publicly accessible), environment variables from Key Vault
4. **PostgreSQL setup**: Create database, run Alembic migrations, configure connection pooling
5. **Custom domain + HTTPS**: Configure in Container Apps (`Manual Action Required`: DNS records)
6. **Google OAuth callback URL**: Update to production domain (`Manual Action Required`)
7. **Application Insights**: Add OpenTelemetry SDK to both frontend and backend
8. **Health checks**: Liveness + readiness probes on both containers
9. **Secrets rotation plan**: Document Key Vault secret rotation procedure
10. **Load test**: Verify SSE streaming works through Azure ingress under moderate load

**Dependencies**: Phase 7 CI/CD pipeline working, Azure subscription provisioned
**Risks**: SSE streaming through Azure Container Apps ingress (test early); PostgreSQL connection limits; cold start latency
**Deliverables**: Production URL accessible, all features working on Azure
**Acceptance**: End-to-end smoke test on production URL — sign in, create watchlist, fetch, translate, verify persistence

---

### Phase Summary

| Phase | Days | Objective | Key Risk |
|-------|------|-----------|----------|
| 0 | 1–2 | Runnable empty monorepo | Docker networking |
| 1 | 3–5 | Auth + database + multi-tenancy | NextAuth + PostgreSQL adapter |
| 2 | 6–10 | Shell + dashboard + settings | Tailwind + shadcn setup |
| 3 | 11–18 | Watchlists + SSE fetch | SSE through proxy; TweAPI compat |
| 4 | 19–22 | AI translation | Provider rate limits; prompt parsing |
| 5 | 23–28 | Explore + groups | Masonry performance; cookie auth |
| 6 | 29–32 | Webhook API + usage | Key security |
| 7 | 33–37 | Testing + CI/CD | Test DB in CI |
| 8 | 38–42 | Azure deployment + hardening | SSE through Azure ingress |

**Total estimated duration**: ~42 working days (8–9 weeks) for a solo developer. Can compress to 5–6 weeks with two developers (frontend + backend in parallel from Phase 2 onward).
