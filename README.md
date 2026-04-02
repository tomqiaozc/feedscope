# Feedscope

Multi-tenant social media analytics platform for monitoring Twitter/X accounts, exploring content, and translating tweets with AI commentary.

## Features

### Watchlists

Create watchlists to track Twitter/X accounts. Add members with tags (e.g. "tech", "influencer") for filtering. The **Fetch** button pulls the latest tweets from all tracked members via real-time SSE streaming with a live progress bar showing member-by-member status -- cancellable mid-stream. Fetched posts display with media grids, engagement metrics (likes, retweets, replies, views), and auto-linkified URLs.

### AI Translation

Translate tweets to Chinese with editorial commentary using Anthropic Claude, OpenAI, or any OpenAI-compatible provider. Each translation produces three parts: the translation itself, an optional editorial/commentary note, and a quoted tweet translation. **Translate All** batch-translates untranslated posts via SSE streaming with per-post progress updates. Configure your AI provider, model, and API key in the AI Settings page with a built-in connection test.

### Explore

Search Twitter/X by keyword and browse results in a masonry grid. Click into any user's profile to see their avatar, bio, verified badge, follower stats, and six tabbed views: Tweets, Timeline, Replies, Highlights, Followers, and Following. Follower/Following lists are clickable for profile-to-profile navigation.

### Groups

Organize Twitter accounts into custom groups. Add members individually or **bulk-import from `.txt`/`.csv` files** -- usernames are parsed from comma or newline-separated values with `@` prefixes auto-stripped.

### Webhook API

Generate API keys for external programmatic access to Feedscope's Twitter data endpoints (search, user info, user tweets, bookmarks, tweet details). Keys support rotation (old key invalidated immediately) and are shown only once at creation with a copy-to-clipboard flow. Usage per key is tracked with last-used timestamps.

### Usage Analytics

View API call counts grouped by date and endpoint over a configurable date range. Summary cards show total calls, webhook calls, and remaining TwitterAPI.io credits with a visual progress bar. The breakdown table supports sortable columns and date-grouped subtotals.

### Dashboard

A single-page overview aggregating credentials status, AI provider config, watchlist/group counts, 7-day API call total, and credit balance -- all loaded in one request.

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | Next.js 16, React 19, TypeScript, Tailwind CSS v4, shadcn/ui |
| Backend | Python 3.12, FastAPI, SQLAlchemy 2.0 (async), Alembic |
| Database | PostgreSQL 16 |
| Auth | NextAuth v5 + Google OAuth, `@auth/pg-adapter` |
| AI | Anthropic SDK, OpenAI SDK |
| Twitter Data | TweAPI / TwitterAPI.io (configurable) |
| Observability | OpenTelemetry + Azure Application Insights |
| Deployment | Azure App Service, ghcr.io, GitHub Actions CI/CD |

## Architecture

```
Browser → Next.js Frontend → /api/proxy/* → FastAPI Backend → PostgreSQL
                ↓                                  ↓
          NextAuth (Google)              TweAPI / AI Providers
```

The frontend authenticates users via Google OAuth and proxies all API requests to the backend, injecting the `X-User-Id` header. The backend trusts this header for multi-tenancy (all business data is scoped by `user_id`).

## Quick Start

### Prerequisites

- Docker and Docker Compose
- Node.js 20+
- Python 3.12+
- Google OAuth credentials ([Google Cloud Console](https://console.cloud.google.com/apis/credentials))

### 1. Clone and configure

```bash
git clone https://github.com/tomqiaozc/feedscope.git
cd feedscope
cp .env.example .env
```

### 2. Start PostgreSQL

```bash
docker compose up -d db
```

### 3. Run backend

```bash
cd backend
cp .env.example .env
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
alembic upgrade head
uvicorn app.main:app --reload --port 8000
```

### 4. Run frontend

```bash
cd frontend
cp .env.example .env.local
# Fill in GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET, NEXTAUTH_SECRET
npm install
npm run dev
```

Visit `http://localhost:3000`, sign in with Google, and start building watchlists.

### Full stack with Docker Compose

```bash
docker compose --profile full up --build
```

## Environment Variables

### Backend (`backend/.env`)

| Variable | Default | Description |
|----------|---------|-------------|
| `DATABASE_URL` | `postgresql+asyncpg://feedscope:feedscope@localhost:5432/feedscope` | PostgreSQL connection string |
| `CORS_ORIGINS` | `["http://localhost:3000"]` | Allowed origins (JSON array or comma-separated) |
| `MOCK_PROVIDER` | `false` | Use mock Twitter data provider |
| `E2E_SKIP_AUTH` | `false` | Skip auth for E2E tests (ignored in production) |

### Frontend (`frontend/.env.local`)

| Variable | Default | Description |
|----------|---------|-------------|
| `NEXTAUTH_SECRET` | -- | Random secret for NextAuth JWT signing |
| `NEXTAUTH_URL` | `http://localhost:3000` | Canonical app URL |
| `GOOGLE_CLIENT_ID` | -- | Google OAuth client ID |
| `GOOGLE_CLIENT_SECRET` | -- | Google OAuth client secret |
| `BACKEND_URL` | `http://localhost:8000` | Backend API URL |
| `ALLOWED_EMAILS` | -- | Comma-separated email allowlist (empty = allow all) |

## Project Structure

```
feedscope/
├── backend/
│   ├── app/
│   │   ├── main.py              # FastAPI entry point
│   │   ├── config.py            # Pydantic settings
│   │   ├── auth/                # Auth dependencies
│   │   ├── db/                  # Models, engine, repositories
│   │   ├── routes/              # 10 API route modules (~65 endpoints)
│   │   ├── schemas/             # Pydantic request/response schemas
│   │   ├── services/            # AI translation, SSE, prompts
│   │   └── providers/           # Twitter data providers (TweAPI, mock)
│   ├── alembic/                 # Database migrations
│   ├── tests/                   # Unit + integration tests (13 files)
│   ├── Dockerfile
│   └── entrypoint.sh            # Migration + server startup
├── frontend/
│   ├── src/
│   │   ├── app/                 # Next.js App Router pages
│   │   │   ├── (dashboard)/     # 8 authenticated pages
│   │   │   ├── api/             # NextAuth + backend proxy routes
│   │   │   └── login/           # Login page
│   │   ├── components/          # Domain, layout, and UI components
│   │   ├── hooks/               # 8 custom React hooks
│   │   ├── lib/                 # Auth config, API client, SSE parser
│   │   └── types/               # TypeScript type definitions
│   ├── e2e/                     # Playwright E2E tests
│   └── Dockerfile
├── shared/api-contract.md       # Full API documentation
├── docs/blueprint/              # Architectural blueprint
├── infra/deploy.sh              # Azure provisioning script
├── docker-compose.yml
└── .github/workflows/
    ├── ci.yml                   # Lint, test, build, E2E
    └── cd.yml                   # Build images, deploy to Azure
```

## Testing

```bash
# Backend
cd backend
pytest                          # All tests
pytest tests/unit               # Unit tests only
pytest tests/integration        # Integration tests only
pytest --cov=app                # With coverage

# Frontend
cd frontend
npm run lint                    # ESLint
npx playwright test             # E2E tests
```

## Deployment

Production runs on Azure App Service with Docker containers from ghcr.io.

```
GitHub push → CI (lint + test + build) → CD (build images → ghcr.io → Azure App Service)
```

**Azure resources** (shared with other projects in `rg-rewind-ea`):
- App Service Plan: `plan-rwnd-prod` (B1 Linux)
- PostgreSQL: `pg-rwnd-prod` (B1ms) with `feedscope` database
- Key Vault: `kv-rwnd-prod` for secrets
- Application Insights: `ai-feedscope-prod`

**URLs:**
- Backend: `https://app-backend-feedscope-prod.azurewebsites.net`
- Frontend: `https://app-frontend-feedscope-prod.azurewebsites.net`

See `infra/deploy.sh` for the full provisioning script.

## License

Private project.
