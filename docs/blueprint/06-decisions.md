# 06 — Architecture & Process Decisions

> Decisions confirmed by the user during development. These override any conflicting `Pending Confirmation` labels in earlier blueprint documents.

| # | Decision | Choice | Date | Rationale |
|---|----------|--------|------|-----------|
| D-1 | Auth pattern (was P-11) | **Next.js proxy pattern** — NextAuth handles auth in Next.js, proxy forwards `X-User-Id` to backend | 2026-04-01 | Matches blueprint architecture. Simpler backend auth (trust internal header). No need to reimplement session validation in Python. |
| D-2 | Dev workflow (was G-5) | **Native dev + Docker Postgres only** — docker-compose.yml runs PostgreSQL; frontend (`npm run dev`) and backend (`uvicorn --reload`) run natively | 2026-04-01 | Faster hot reload. Avoids Docker volume mount performance issues on macOS. docker-compose.yml also includes a full-container profile for CI/production testing. |
| D-3 | Tailwind version (was G-3) | **Tailwind v4** — validate shadcn/ui compatibility in Phase 0.2. Fall back to v3 if incompatible. | 2026-04-01 | Blueprint specifies v4. shadcn/ui has added v4 support in recent releases but needs validation. |
| D-4 | `.env` management (was G-1) | **Separate `.env` files per service** — `frontend/.env.local`, `backend/.env`, root `.env` for docker-compose shared vars | 2026-04-01 | Clean separation. Each service manages its own secrets. Root `.env` only has POSTGRES_* vars for docker-compose. |
| D-5 | Product name (was P-1) | **Feedscope** | 2026-04-01 | Confirmed. |
| D-6 | Next.js version | **Next.js 16** (was 15 in blueprint) — `create-next-app@latest` installs v16.2.2 | 2026-04-01 | v16 is the latest stable. React 19.2.4. Fully compatible with App Router, Tailwind v4, shadcn/ui. No reason to pin v15. |
| D-7 | Tailwind v4 + shadcn/ui compat (was G-3 risk) | **Confirmed compatible** — `npx shadcn@latest init -d` works cleanly with Tailwind v4 | 2026-04-01 | Risk G-3 resolved. No fallback to v3 needed. |
| D-8 | Python version | **Python 3.13** (was 3.12 in blueprint) — system Python is 3.13.12 | 2026-04-01 | 3.13 is the latest stable. FastAPI, SQLAlchemy, asyncpg all compatible. pyproject.toml updated to `requires-python = ">=3.12"` so both work. |

## Implications for docker-compose.yml

Since D-2 chose "native dev + Docker Postgres only", the `docker-compose.yml` should:

1. **Default profile**: PostgreSQL only (for `docker compose up`)
2. **Full profile**: PostgreSQL + frontend + backend containers (for `docker compose --profile full up`)
3. Dev scripts in each service's package.json / pyproject.toml assume PostgreSQL is available at `localhost:5432`

## Implications for Phase 0 Tasks

- Task #14 (docker-compose.yml) should create a Postgres-only default config with an optional full-container profile
- Task #10 (frontend scaffold) should include `frontend/.env.local.example` (not root `.env`)
- Task #15 (backend scaffold) should include `backend/.env.example` (not root `.env`)
