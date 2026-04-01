# Feedscope API Contract

> This document defines the API contract between the Next.js frontend and the FastAPI backend.
> Updated per-phase as routes are built.

## Conventions

- Base URL (frontend proxy): `/api/proxy/...` → backend `/api/v1/...`
- Auth: Next.js proxy adds `X-User-Id` header (trusted internal)
- Response envelope: `{ "success": boolean, "data": T | null, "error": string | null }`

## Endpoints

### Health

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| GET | `/health` | Public | Health check → `{"status": "ok"}` |

### Auth

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| GET | `/api/v1/me` | Required | Returns `{"user_id": "<id>"}` for authenticated user |

### Settings — Credentials

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| GET | `/api/v1/settings/credentials` | Required | List credentials (no secrets in response) |
| PUT | `/api/v1/settings/credentials` | Required | Upsert credential `{ provider, api_key?, cookie? }` |
| DELETE | `/api/v1/settings/credentials/{provider}` | Required | Delete credential for provider |

### Settings — AI

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| GET | `/api/v1/settings/ai` | Required | Get AI config (provider_id, model, has_api_key, etc.) |
| PUT | `/api/v1/settings/ai` | Required | Update AI settings `{ provider_id?, api_key?, model?, ... }` |
| POST | `/api/v1/settings/ai/test` | Required | Test AI connection with saved settings |

_(More endpoints added in subsequent phases)_

### Watchlists

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| GET | `/api/v1/watchlists` | Required | List all watchlists (with member_count, post_count) |
| POST | `/api/v1/watchlists` | Required | Create watchlist `{ name, description? }` → 201 |
| PUT | `/api/v1/watchlists/{id}` | Required | Update watchlist `{ name?, description? }` |
| DELETE | `/api/v1/watchlists/{id}` | Required | Delete watchlist (cascade members, posts, logs, settings) |

### Watchlist Members

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| GET | `/api/v1/watchlists/{id}/members` | Required | List members with tags |
| POST | `/api/v1/watchlists/{id}/members` | Required | Add member `{ username, display_name?, notes?, tags?: string[] }` → 201 |
| PUT | `/api/v1/watchlists/{id}/members/{mid}` | Required | Update member `{ display_name?, notes?, tags?: string[] }` |
| DELETE | `/api/v1/watchlists/{id}/members/{mid}` | Required | Remove member (cascade posts) |

### Watchlist Posts

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| GET | `/api/v1/watchlists/{id}/posts` | Required | List posts `?tag=&member_id=&offset=0&limit=50` → `{ data, total }` |
| DELETE | `/api/v1/watchlists/{id}/posts/{pid}` | Required | Delete single post |

### Watchlist Settings

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| GET | `/api/v1/watchlists/{id}/settings` | Required | Get all settings for watchlist |
| PUT | `/api/v1/watchlists/{id}/settings` | Required | Upsert setting `{ key, value }` |

### Fetch Logs

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| GET | `/api/v1/watchlists/{id}/logs` | Required | List fetch/translate logs |

### SSE Streaming

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| POST | `/api/v1/watchlists/{id}/fetch` | Required | Stream tweet fetch via SSE (returns 503 if no TweAPI credentials) |

#### SSE Event Format (`POST /api/v1/watchlists/{id}/fetch`)

```
event: cleanup
data: {"watchlist_id": <int>}

event: progress
data: {"member": "<username>", "index": <int>, "total": <int>}

event: posts
data: {"member": "<username>", "count": <int>}

event: error
data: {"member": "<username>", "error": "<message>"}

event: done
data: {"total_posts": <int>, "errors": <int>}
```

### Translation

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| POST | `/api/v1/translate` | Required | Translate single text `{ text, quoted_text? }` → `{ translation, editorial?, quoted_translation? }` |
| POST | `/api/v1/watchlists/{id}/translate` | Required | Batch translate all untranslated posts via SSE (returns 503 if no AI config) |

#### Request/Response: `POST /api/v1/translate`

```json
// Request
{ "text": "<post content>", "quoted_text": "<optional quoted tweet>" }

// Response
{
  "success": true,
  "data": {
    "translation": "<Chinese translation>",
    "editorial": "<brief commentary>",
    "quoted_translation": "<quoted tweet translation or null>"
  }
}

// Error 400: {"detail": "Text is required"}
// Error 503: {"detail": "No AI provider configured. Add an API key in Settings."}
// Error 502: {"detail": "AI translation failed: <error>"}
```

#### SSE Event Format (`POST /api/v1/watchlists/{id}/translate`)

```
event: start
data: {"watchlist_id": <int>, "total": <int>}

event: translating
data: {"post_id": <int>, "index": <int>, "total": <int>}

event: translated
data: {"post_id": <int>, "index": <int>, "total": <int>, "translation": "<text>"}

event: error
data: {"post_id": <int>, "index": <int>, "error": "<message>"}

event: done
data: {"translated": <int>, "errors": <int>}
```

### Explore

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| GET | `/api/v1/explore/search` | Required | Search tweets `?q=&count=20` |
| GET | `/api/v1/explore/user/{username}` | Required | User profile info |
| GET | `/api/v1/explore/user/{username}/tweets` | Required | User's tweets `?count=20` |
| GET | `/api/v1/explore/user/{username}/timeline` | Required | User's timeline |
| GET | `/api/v1/explore/user/{username}/replies` | Required | User's replies |
| GET | `/api/v1/explore/user/{username}/highlights` | Required | User's highlights |
| GET | `/api/v1/explore/user/{username}/followers` | Required | Followers list `?count=20` |
| GET | `/api/v1/explore/user/{username}/following` | Required | Following list `?count=20` |
| GET | `/api/v1/explore/bookmarks` | Required | User's bookmarks (cookie auth) `?count=20` |
| GET | `/api/v1/explore/likes` | Required | User's likes (cookie auth) `?username=&count=20` |
| GET | `/api/v1/explore/tweet/{tweet_id}` | Required | Single tweet details |
| GET | `/api/v1/explore/tweet/{tweet_id}/replies` | Required | Tweet replies `?count=20` |

### Groups

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| GET | `/api/v1/groups` | Required | List all groups (with member_count) |
| POST | `/api/v1/groups` | Required | Create group `{ name, description? }` → 201 |
| PUT | `/api/v1/groups/{id}` | Required | Update group `{ name?, description? }` |
| DELETE | `/api/v1/groups/{id}` | Required | Delete group (cascade members) |
| GET | `/api/v1/groups/{id}/members` | Required | List group members |
| POST | `/api/v1/groups/{id}/members` | Required | Add member `{ username, display_name?, notes? }` → 201 |
| POST | `/api/v1/groups/{id}/members/batch` | Required | Batch add members `{ members: [...] }` → 201 |
| DELETE | `/api/v1/groups/{id}/members/batch` | Required | Batch delete members `{ member_ids: [...] }` |
| DELETE | `/api/v1/groups/{id}/members/{mid}` | Required | Remove single member |

### Profiles

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| POST | `/api/v1/profiles/refresh` | Required | Refresh profiles `{ usernames: [...] }` → upserts + returns updated profiles |

### Webhooks

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| GET | `/api/v1/webhooks` | Required | List all webhook keys (prefix + metadata, no secrets) |
| POST | `/api/v1/webhooks` | Required | Create webhook key `{ name }` → 201 (returns full key ONCE) |
| DELETE | `/api/v1/webhooks/{id}` | Required | Revoke/delete webhook key |
| POST | `/api/v1/webhooks/{id}/rotate` | Required | Rotate key (returns new key ONCE) |
| GET | `/api/v1/webhooks/usage` | Required | Webhook usage summary `?date_from=&date_to=` |
| GET | `/api/v1/webhooks/{id}/usage` | Required | Usage for specific webhook key `?limit=50` |

### External API (Webhook Auth)

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| GET | `/api/v1/external/search` | Webhook | Search tweets `?q=&count=20` |
| GET | `/api/v1/external/user/{username}` | Webhook | User profile info |
| GET | `/api/v1/external/user/{username}/tweets` | Webhook | User's tweets `?count=20` |
| GET | `/api/v1/external/bookmarks` | Webhook | User's bookmarks `?count=20` |
| GET | `/api/v1/external/tweet/{tweet_id}` | Webhook | Single tweet details |

> External endpoints use `X-Webhook-Key` header instead of `X-User-Id`. Usage is automatically tracked.

### Usage & Credits

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| GET | `/api/v1/usage` | Required | Usage summary for current user `?date_from=&date_to=` |
| GET | `/api/v1/credits` | Required | TweAPI credit balance (remaining, total, reset_at) |
