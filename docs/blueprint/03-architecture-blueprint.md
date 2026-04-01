# 03 — Architecture Blueprint

## 8. Architecture Blueprint

### System Topology

```
┌─────────────────────────────────────────────────────────────────────┐
│  Browser                                                             │
│  Next.js 15 App (React Client Components)                           │
│  └─ fetch() / SSE reader                                            │
│     ├─ /api/auth/* → NextAuth (runs inside Next.js)                 │
│     └─ /api/proxy/* → reverse-proxy to Python backend               │
├─────────────────────────────────────────────────────────────────────┤
│  Next.js Server (Node.js, Azure Container Apps — "frontend")        │
│  ├─ SSR / static serving                                             │
│  ├─ /api/auth/* (NextAuth with PostgreSQL adapter)                  │
│  └─ /api/proxy/* (reverse proxy to backend, forwards session token) │
├─────────────────────────────────────────────────────────────────────┤
│  Python Backend (FastAPI, Azure Container Apps — "backend")          │
│  ├─ /api/v1/watchlists/*     session-auth                           │
│  ├─ /api/v1/groups/*         session-auth                           │
│  ├─ /api/v1/explore/*        session-auth                           │
│  ├─ /api/v1/settings/*       session-auth                           │
│  ├─ /api/v1/translate        session-auth                           │
│  ├─ /api/v1/webhooks/*       session-auth                           │
│  ├─ /api/v1/twitter/*        webhook-key-auth                       │
│  ├─ /api/v1/credits          session-auth                           │
│  ├─ /api/v1/usage            session-auth                           │
│  └─ /health                  public                                  │
├─────────────────────────────────────────────────────────────────────┤
│  Data Layer                                                          │
│  ├─ Azure Database for PostgreSQL Flexible Server                    │
│  ├─ Azure Key Vault (secrets)                                        │
│  └─ Azure Blob Storage (optional: media cache)                       │
├─────────────────────────────────────────────────────────────────────┤
│  External Services                                                   │
│  ├─ TweAPI.io (Twitter data, API-key auth)                          │
│  ├─ AI providers (Anthropic, OpenAI-compatible)                     │
│  └─ Google OAuth (identity provider)                                 │
└─────────────────────────────────────────────────────────────────────┘
```

### Recommended Repository Structure

Monorepo with two deployable units:

```
feedscope/
├── frontend/                          # Next.js 15 application
│   ├── src/
│   │   ├── app/
│   │   │   ├── layout.tsx             # Root layout: fonts, providers, FOUC script
│   │   │   ├── (dashboard)/
│   │   │   │   ├── layout.tsx         # AppShell wrapper
│   │   │   │   ├── page.tsx           # Dashboard
│   │   │   │   ├── watchlist/
│   │   │   │   │   ├── page.tsx       # Watchlist list
│   │   │   │   │   └── [id]/
│   │   │   │   │       ├── page.tsx   # Watchlist detail
│   │   │   │   │       ├── _lib/      # SSE parser, helpers
│   │   │   │   │       └── _components/  # SlidePanel, etc.
│   │   │   │   ├── groups/
│   │   │   │   ├── explore/
│   │   │   │   ├── settings/
│   │   │   │   ├── ai-settings/
│   │   │   │   ├── webhooks/
│   │   │   │   └── usage/
│   │   │   ├── login/
│   │   │   └── api/
│   │   │       ├── auth/[...nextauth]/  # NextAuth handlers
│   │   │       └── proxy/[...path]/     # Reverse proxy to backend
│   │   ├── components/
│   │   │   ├── layout/                # AppShell, Sidebar, Breadcrumbs, ThemeToggle
│   │   │   ├── domain/               # Platform-agnostic content cards
│   │   │   └── ui/                    # shadcn/ui + feedback components
│   │   ├── hooks/                     # useFetch, useSearch, useColumns, useMobile
│   │   ├── lib/                       # utils, palette, auth helpers
│   │   └── styles/
│   │       └── globals.css            # Tailwind v4 + design tokens
│   ├── next.config.ts
│   ├── tailwind.config.ts
│   ├── tsconfig.json
│   ├── package.json
│   └── Dockerfile
│
├── backend/                           # Python FastAPI application
│   ├── app/
│   │   ├── main.py                    # FastAPI app creation, middleware, lifespan
│   │   ├── config.py                  # Settings via pydantic-settings
│   │   ├── auth/
│   │   │   ├── dependencies.py        # get_current_user, require_auth
│   │   │   └── webhook.py             # webhook key auth
│   │   ├── db/
│   │   │   ├── engine.py              # async engine + session factory
│   │   │   ├── models.py              # SQLAlchemy ORM models (all tables)
│   │   │   └── scoped.py              # ScopedDB class (port of reference pattern)
│   │   ├── providers/
│   │   │   ├── base.py                # ISocialProvider protocol
│   │   │   ├── tweapi/
│   │   │   │   ├── provider.py        # TweAPIProvider
│   │   │   │   ├── normalizer.py      # Raw response → internal models
│   │   │   │   └── types.py           # TweAPI response Pydantic models
│   │   │   ├── mock.py                # MockProvider for tests
│   │   │   └── factory.py             # create_provider_for_user()
│   │   ├── services/
│   │   │   ├── ai.py                  # AI provider registry + translation
│   │   │   ├── translation.py         # Prompt rendering, response parsing
│   │   │   └── crypto.py              # Webhook key generation, hashing
│   │   ├── routes/
│   │   │   ├── watchlists.py          # Watchlist CRUD + members + fetch + translate
│   │   │   ├── groups.py              # Group CRUD + members
│   │   │   ├── explore.py             # Search, user profiles, bookmarks, likes
│   │   │   ├── twitter.py             # External webhook-auth API
│   │   │   ├── settings.py            # Credentials, AI config
│   │   │   ├── webhooks.py            # Webhook CRUD + rotate
│   │   │   ├── translate.py           # Single translation endpoint
│   │   │   ├── credits.py             # TweAPI credits
│   │   │   ├── usage.py               # Usage stats
│   │   │   └── health.py              # Health check
│   │   ├── schemas/                   # Pydantic request/response models
│   │   └── shared/
│   │       └── types.py               # Platform-agnostic types (Post, Author, etc.)
│   ├── alembic/                       # Database migrations
│   │   ├── env.py
│   │   └── versions/
│   ├── tests/
│   │   ├── conftest.py                # Fixtures: test DB, test client, mock provider
│   │   ├── test_watchlists.py
│   │   ├── test_groups.py
│   │   ├── test_explore.py
│   │   ├── test_auth.py
│   │   └── test_translation.py
│   ├── alembic.ini
│   ├── pyproject.toml                 # Dependencies, pytest config, ruff config
│   ├── Dockerfile
│   └── .env.example
│
├── shared/                            # Shared type definitions (TypeScript ↔ Python contract)
│   └── api-contract.md               # API endpoint documentation
│
├── docker-compose.yml                 # Local dev: frontend + backend + PostgreSQL
├── .github/
│   └── workflows/
│       ├── ci.yml                     # Lint + test (both frontend and backend)
│       └── deploy.yml                 # Build + push + deploy to Azure
└── README.md
```

### Runtime Boundaries

| Boundary | Technology | Deployment |
|----------|-----------|------------|
| Frontend server | Next.js 15 on Node.js 20+ | Azure Container Apps (container) |
| Backend server | FastAPI on Python 3.12+ / uvicorn | Azure Container Apps (container) |
| Database | PostgreSQL 16 | Azure Database for PostgreSQL Flexible Server |
| Reverse proxy | Azure Container Apps ingress (built-in) | Managed |
| Secrets | Azure Key Vault | Managed |
| Container registry | Azure Container Registry | Managed |

### Communication Between Frontend and Backend

The Next.js app handles auth (NextAuth) and proxies all data requests to the Python backend:

1. **Auth flow**: NextAuth runs in Next.js → stores JWT session cookie → Next.js proxy extracts `userId` from session and forwards it to the backend as `X-User-Id` header (trusted internal communication).
2. **Data flow**: Client `fetch("/api/proxy/watchlists")` → Next.js `/api/proxy/[...path]/route.ts` validates session → forwards to `http://backend:8000/api/v1/watchlists` with `X-User-Id` header.
3. **SSE flow**: Next.js proxy streams the SSE response from the backend through to the client (passthrough).
4. **Webhook flow**: External callers hit the backend directly (or via a separate Azure ingress) with `X-Webhook-Key` — no Next.js involvement.

> **Alternative**: `Pending Confirmation` — If the user prefers, auth can be handled entirely in the Python backend (e.g., using `authlib` or `python-jose`), eliminating the Next.js proxy layer. This simplifies deployment to a single frontend static export + a single backend container.

---

## Frontend Reference

*What to borrow from the reference project's frontend, adapted for standard Next.js 15.*

### Page Organization (Borrow)

- **Route group `(dashboard)/`** wrapping all authenticated pages with a shared `AppShell` layout. Login page sits outside this group.
- **Private folders** `_components/` and `_lib/` colocated with route segments for feature-specific code.
- **Dynamic routes** `[id]/` for detail pages (watchlist detail, group detail).
- All pages are `"use client"` — no RSC data fetching. This keeps the architecture simple and avoids RSC serialization edge cases.

### Shell & Layout Components (Borrow)

- **AppShell**: Desktop sidebar (collapsible, 68px ↔ 260px) + mobile sidebar (fixed overlay with backdrop). Floating island content area (`rounded-[16px] bg-card`).
- **Sidebar**: Config-driven static groups (`TOP_GROUPS`, `BOTTOM_GROUPS`) + data-driven dynamic groups (watchlists, groups fetch their own data). CSS Grid row animation for collapse (`gridTemplateRows: "1fr" ↔ "0fr"`).
- **Breadcrumbs**: Context + hook pattern. Pages call `useBreadcrumbs([...items])` at component top. Shell header consumes the value. No prop drilling.
- **Theme toggle**: `useSyncExternalStore` + custom `"theme-change"` event. FOUC prevention via blocking inline `<script>` in `<head>`.

### Design System (Borrow)

- **3-tier luminance**: `bg-background` (L0, page body) → `bg-card` (L1, panels) → `bg-secondary` (L2, inner cards). Creates depth without borders.
- **Custom tokens**: `--radius-card: 14px`, `--radius-widget: 10px`, mapped to `rounded-card` / `rounded-widget`.
- **Fade-up stagger**: `@keyframes fade-up` (opacity 0→1, translateY 12px→0, 400ms ease-out) with `fade-up-stagger-{1..5}` delay utilities.
- **Feedback components**: `LoadingSpinner`, `ErrorBanner`, `StatusMessage`, `EmptyState`, `SectionSkeleton` — the five gap components every project needs.

### Data Fetching Hooks (Borrow, adapt endpoint paths)

- **`useFetch<T>(endpoint)`**: Auto-fetches on mount, returns `{ data, loading, error, refetch }`. Includes `didMount` ref to prevent StrictMode double-invoke.
- **`useSearch<T>()`**: Returns `{ data, loading, error, searched, execute, reset }`. The `searched` boolean distinguishes "idle" from "searched, zero results".
- **SSE client pattern**: `fetch()` → `response.body.getReader()` → loop with `parseSSEBuffer()` pure function → dispatch events to React state → `AbortController` on unmount.

### Responsive Patterns (Borrow)

- **`useColumns()`**: Uses `matchMedia` change listeners (not ResizeObserver) for discrete column counts. More efficient — fires only on breakpoint crossings.
- **`MasonryGrid<T>`**: Generic component with shortest-column algorithm. `estimateHeight` prop for balance.
- **`useMobile()`**: Single breakpoint check for mobile-specific UI (hamburger menu, etc.).

### Interaction Patterns (Borrow)

- **`?new=1` auto-open dialog**: List pages detect the query param, open the create dialog, immediately clean the URL via `router.replace(pathname)`.
- **SlidePanel**: CSS `translate-x-full → translate-x-0` transition, backdrop, Escape handler, focus trap. Simpler than a full dialog for settings/detail panels.
- **Hover-reveal actions**: `opacity-0 group-hover:opacity-100` on card action buttons.
- **Optimistic updates with rollback**: Update state immediately, call API, rollback on failure. Error auto-clears after 3 seconds.
- **Display/edit toggle**: Settings fields switch between `<span>` and `<input>` with a single edit/save button.

### What to NOT Borrow from Frontend

- **vinext workarounds**: `routerRef` pattern (Next.js `useRouter` is stable), null-prototype params fix, `next/font/google` default import hack, `wrapHandler` for NextRequest conversion. All eliminated by using standard Next.js 15.
- **Chinese-language UI text**: New project should use English by default (i18n as later-phase).
- **Twitter-specific component names**: Rename `TweetCard` → `PostCard`, `UserCard` → `ProfileCard`, etc.

---

## Python Backend Blueprint

*What backend capabilities need to be rebuilt in Python, and how.*

### Core Framework

| Choice | Technology | Rationale |
|--------|-----------|-----------|
| Web framework | **FastAPI** 0.115+ | Async-native, Pydantic validation, auto-generated OpenAPI docs, SSE support via `StreamingResponse` |
| ASGI server | **uvicorn** | Production-grade, works with Azure Container Apps |
| ORM | **SQLAlchemy 2.0** (async mode) | Mature, PostgreSQL-native, Alembic migrations |
| Migrations | **Alembic** | Auto-generate from SQLAlchemy models, proper version tracking |
| Validation | **Pydantic v2** | Request/response models, settings loading |
| HTTP client | **httpx** (async) | For TweAPI and AI provider API calls |
| AI SDK | **anthropic** + **openai** Python packages | Direct equivalents of Vercel AI SDK |
| Testing | **pytest** + **pytest-asyncio** + **httpx** | Async test support, `TestClient` for API tests |
| Linting | **ruff** | Fast, replaces flake8 + isort + black |
| Type checking | **mypy** or **pyright** | Strict mode |

### Database Schema (PostgreSQL)

Port all 18 tables from SQLite to PostgreSQL. Key changes:

| SQLite Pattern | PostgreSQL Replacement |
|---------------|----------------------|
| `INTEGER PRIMARY KEY AUTOINCREMENT` | `SERIAL` or `BIGSERIAL` |
| `TEXT` for timestamps | `TIMESTAMPTZ` |
| `INT DEFAULT (unixepoch())` | `TIMESTAMPTZ DEFAULT now()` |
| `TEXT` for JSON blobs (`tweet_json`, `errors`) | `JSONB` |
| `TEXT` for booleans (`is_verified`) | `BOOLEAN` |
| `initSchema()` + `safeAddColumn()` | Alembic migration files |

**Auth tables**: If using NextAuth with PostgreSQL, use the `@auth/pg-adapter` in the Next.js layer. The Python backend does NOT manage auth tables — it trusts the `X-User-Id` header from the Next.js proxy.

**Business tables**: Identical structure to reference, with PostgreSQL types. The `ScopedDB` pattern ports directly:

```python
class ScopedDB:
    def __init__(self, user_id: str, session: AsyncSession):
        self.user_id = user_id
        self.session = session
        self.watchlists = WatchlistRepo(user_id, session)
        self.members = MemberRepo(user_id, session)
        self.tags = TagRepo(user_id, session)
        self.posts = PostRepo(user_id, session)
        # ... all 13 repos
```

Each repo method auto-injects `WHERE user_id = :uid`. Same "correct by construction" guarantee.

### API Route Mapping

All routes from the reference project, mapped to FastAPI routers:

**`routes/watchlists.py`** — `APIRouter(prefix="/api/v1/watchlists")`

| Method | Path | Reference Equivalent | Notes |
|--------|------|---------------------|-------|
| GET | `/` | `GET /api/watchlists` | List all for user |
| POST | `/` | `POST /api/watchlists` | Create |
| PUT | `/{id}` | `PUT /api/watchlists` | Update |
| DELETE | `/{id}` | `DELETE /api/watchlists?id=N` | Delete with cascade |
| GET | `/{id}/members` | `GET /api/watchlists/[id]/members` | Members + tags + profiles |
| POST | `/{id}/members` | `POST /api/watchlists/[id]/members` | Add member |
| PUT | `/{id}/members/{member_id}` | `PUT /api/watchlists/[id]/members` | Update member |
| DELETE | `/{id}/members/{member_id}` | `DELETE /api/watchlists/[id]/members?id=N` | Remove member |
| POST | `/{id}/fetch` | `POST /api/watchlists/[id]/fetch` | SSE fetch stream |
| POST | `/{id}/translate` | `POST /api/watchlists/[id]/translate` | SSE translate stream |
| GET | `/{id}/posts` | `GET /api/watchlists/[id]/posts` | List posts with filters |
| DELETE | `/{id}/posts/{post_id}` | `DELETE /api/watchlists/[id]/posts?postId=N` | Delete post |
| GET | `/{id}/settings` | `GET /api/watchlists/[id]/settings` | Per-watchlist settings |
| PUT | `/{id}/settings` | `PUT /api/watchlists/[id]/settings` | Update settings |
| GET | `/{id}/logs` | `GET /api/watchlists/[id]/logs` | Fetch/translate history |

**`routes/groups.py`** — `APIRouter(prefix="/api/v1/groups")` — Same CRUD + members pattern.

**`routes/explore.py`** — `APIRouter(prefix="/api/v1/explore")` — Search, user profiles, bookmarks, likes, lists, inbox, messages.

**`routes/twitter.py`** — `APIRouter(prefix="/api/v1/twitter")` — External webhook-auth routes. Same endpoints as explore but authenticated via `X-Webhook-Key`.

**`routes/settings.py`** — Credentials CRUD, AI settings CRUD, AI connection test.

**`routes/webhooks.py`** — Webhook CRUD + key rotation.

**`routes/translate.py`** — Single-text translation endpoint.

**`routes/credits.py`**, **`routes/usage.py`**, **`routes/health.py`** — Utility endpoints.

### Provider Interface (Python Protocol)

```python
from typing import Protocol

class ISocialProvider(Protocol):
    async def fetch_user_info(self, username: str) -> UserInfo: ...
    async def fetch_user_tweets(self, username: str, *, count: int = 20) -> list[Post]: ...
    async def fetch_user_timeline(self, username: str) -> list[Post]: ...
    async def search_tweets(self, query: str, *, count: int = 20) -> list[Post]: ...
    async def fetch_tweet_details(self, tweet_id: str) -> Post: ...
    async def fetch_tweet_replies(self, tweet_id: str) -> list[Post]: ...
    # ... all 20 methods from reference TweAPIProvider
```

`TweAPIProvider` implements this using `httpx.AsyncClient`. `MockProvider` returns fixture data for tests.

Factory: `create_provider_for_user(user_id, db_session) -> ISocialProvider | None` — loads credentials from DB, returns provider or None (caller returns 503).

### SSE Implementation (FastAPI)

```python
from fastapi.responses import StreamingResponse

@router.post("/{watchlist_id}/fetch")
async def fetch_watchlist(watchlist_id: int, user_id: str = Depends(get_current_user)):
    async def event_stream():
        # ... loop over members, fetch, yield SSE events
        yield f"event: progress\ndata: {json.dumps(payload)}\n\n"
        yield f"event: done\ndata: {json.dumps(summary)}\n\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream")
```

Client disconnect detection: `asyncio.CancelledError` in the generator when the client closes the connection.

### AI Translation Service

Port the reference service to Python:

1. **Provider registry**: Dict of `{ id: { label, base_url, default_model, sdk_type } }`.
2. **Settings loader**: Read `ai.*` keys from `settings` table → `AiConfig` Pydantic model.
3. **Prompt renderer**: Mustache-style template with `{{#quoted}}...{{/quoted}}` blocks.
4. **Client creation**: `anthropic.AsyncAnthropic(api_key=..., base_url=...)` or `openai.AsyncOpenAI(...)` based on `sdk_type`.
5. **Response parser**: Split on `[翻译]`, `[引用翻译]`, `[锐评]` markers → `TranslationResult`.
6. **Batch translation**: `asyncio.Semaphore(3)` for sliding-window concurrency.

### Webhook Auth

Port from reference:

```python
import hashlib, secrets, hmac

def generate_webhook_key() -> str:
    return secrets.token_hex(32)  # 64-char hex

def hash_webhook_key(key: str) -> str:
    return hashlib.sha256(key.encode()).hexdigest()

def verify_webhook_key(provided: str, stored_hash: str) -> bool:
    return hmac.compare_digest(hash_webhook_key(provided), stored_hash)
```

### Auth Dependency

```python
from fastapi import Depends, Header, HTTPException

async def get_current_user(x_user_id: str = Header(...)) -> str:
    """Trust the X-User-Id header from the Next.js proxy."""
    if not x_user_id:
        raise HTTPException(401, "Not authenticated")
    return x_user_id

async def require_auth(user_id: str = Depends(get_current_user)) -> ScopedDB:
    """Return a ScopedDB bound to the authenticated user."""
    session = get_db_session()
    return ScopedDB(user_id, session)
```

> **Security note**: The `X-User-Id` header is trusted because the Python backend is only reachable from the Next.js proxy within the same Azure Container Apps environment (internal networking). External traffic uses the webhook key path.

### Testing Strategy

| Layer | Tool | What |
|-------|------|------|
| Unit | pytest | DB repos, normalizer, crypto, translation parser |
| Integration | pytest + TestClient | API routes with test DB |
| E2E (API) | pytest + httpx | Full server + test DB, E2E_SKIP_AUTH mode |
| E2E (Browser) | Playwright (in frontend/) | Full stack with mock provider |

Test DB: PostgreSQL test database (Docker or `testcontainers-python`), transactions rolled back per test.

### Configuration

```python
# backend/app/config.py
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    database_url: str = "postgresql+asyncpg://user:pass@localhost:5432/feedscope"
    tweapi_base_url: str = "https://api.tweapi.io"
    tweapi_timeout_ms: int = 30000
    mock_provider: bool = False
    e2e_skip_auth: bool = False
    cors_origins: list[str] = ["http://localhost:3000"]

    class Config:
        env_file = ".env"
```

### Technology Choices Summary

| Responsibility | Reference (TypeScript) | Feedscope (Python) |
|---------------|----------------------|---------------------|
| HTTP framework | vinext API routes | FastAPI |
| ORM | Drizzle ORM | SQLAlchemy 2.0 (async) |
| Migrations | `initSchema()` + `safeAddColumn()` | Alembic |
| Request validation | Manual + TypeScript types | Pydantic v2 |
| HTTP client | `fetch()` | `httpx.AsyncClient` |
| AI SDKs | `@ai-sdk/anthropic`, `@ai-sdk/openai` | `anthropic`, `openai` |
| SSE | `ReadableStream` + manual encoding | `StreamingResponse` + async generator |
| Hashing | `crypto.createHash("sha256")` | `hashlib.sha256` |
| Secret generation | `crypto.randomBytes(32)` | `secrets.token_hex(32)` |
| Test runner | Bun test | pytest |
| Linter | ESLint | ruff |
| Type checker | TypeScript | mypy / pyright |
