# 05 — Launch Blockers & Risks

## 11. Manual User Actions

These items **cannot be automated** by an AI coding agent. They require human action in external portals or consoles.

### Before Development Starts

| # | Action | Blocking? | Details |
|---|--------|-----------|---------|
| M-1 | **Create Azure subscription** | `Launch Blocking` | Required for all Azure resources. If using an existing subscription, confirm it and the target region. |
| M-2 | **Create Google Cloud OAuth credentials** | `Launch Blocking` | Go to [Google Cloud Console](https://console.cloud.google.com/apis/credentials) → Create OAuth 2.0 Client ID → Set authorized redirect URIs for both localhost and production domain. |
| M-3 | **Obtain TweAPI API key** | `Launch Blocking` | Register at [tweapi.io](https://tweapi.io), subscribe to a plan, get an API key. This is the only Twitter data source. |
| M-4 | **Choose a product name** | `Confirmed` — **Feedscope** | Domain and branding direction still open. |
| M-5 | **Choose a domain name** | Not blocking for dev | Needed for production deployment. Register and configure DNS. |

### During Phase 1 (Auth)

| # | Action | Blocking? | Details |
|---|--------|-----------|---------|
| M-6 | **Set Google OAuth callback URLs** | `Launch Blocking` | Add `http://localhost:3000/api/auth/callback/google` for dev; add production URL later. |
| M-7 | **Generate NextAuth secret** | `Launch Blocking` | `openssl rand -base64 32` — store in `.env` and later in Azure Key Vault. |
| M-8 | **Define ALLOWED_EMAILS list** | `Launch Blocking` | Comma-separated list of Google email addresses permitted to sign in. |

### During Phase 7–8 (CI/CD + Azure)

| # | Action | Blocking? | Details |
|---|--------|-----------|---------|
| M-9 | **Provision Azure resources** | `Launch Blocking` | Create resource group, Container Apps Environment, PostgreSQL Flexible Server, ACR, Key Vault, Log Analytics. Can use Bicep/Terraform templates but human must trigger deployment. |
| M-10 | **Configure Azure Container Registry credentials** | `Launch Blocking` | Create ACR, configure GitHub Actions with ACR push credentials (service principal or managed identity). |
| M-11 | **Populate Azure Key Vault secrets** | `Launch Blocking` | Add: `GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET`, `NEXTAUTH_SECRET`, `TWEAPI_API_KEY`, `DATABASE_URL`, `ALLOWED_EMAILS`. |
| M-12 | **Configure custom domain DNS** | `Launch Blocking` | Add CNAME/A records pointing to Azure Container Apps ingress. Verify domain ownership. |
| M-13 | **Update Google OAuth redirect URI for production** | `Launch Blocking` | Add `https://{production-domain}/api/auth/callback/google` in Google Cloud Console. |
| M-14 | **Create PostgreSQL database** | `Launch Blocking` | Create database in Azure PostgreSQL, configure firewall rules (allow Azure services), note connection string. |
| M-15 | **Run initial Alembic migration on production DB** | `Launch Blocking` | `alembic upgrade head` against production PostgreSQL. Can be automated in CI/CD but first run needs manual verification. |

### Optional / Later-Phase

| # | Action | Blocking? | Details |
|---|--------|-----------|---------|
| M-16 | Set up Azure Monitor alerts | Not blocking | Configure alerts for error rates, response times, DB connection failures. |
| M-17 | Configure AI provider accounts | Not blocking (TweAPI works without AI) | Create accounts at Anthropic, OpenAI, or other providers; get API keys. Can be done per-user via Settings page. |
| M-18 | Set up Microsoft Entra ID (if enterprise auth needed) | Not blocking | Register app in Entra ID, configure as additional NextAuth provider. `Pending Confirmation` |

---

## 12. Launch Blockers And Risks

### Hard Blockers (Must Resolve Before Launch)

| # | Blocker | Category | Mitigation |
|---|---------|----------|------------|
| B-1 | **No Azure subscription** | Infrastructure | User must create or provide an Azure subscription (M-1). |
| B-2 | **No Google OAuth credentials** | Auth | Must register OAuth app in Google Cloud Console (M-2). Without this, no one can sign in. |
| B-3 | **No TweAPI key** | Data source | Must register and pay for TweAPI plan (M-3). Without this, all Twitter data endpoints return 503. |
| B-4 | **No production domain** | Deployment | Container Apps provides a default `.azurecontainerapps.io` domain, but Google OAuth requires a stable callback URL. `Pending Confirmation`: acceptable to use Azure default domain for MVP? |
| B-5 | **PostgreSQL not provisioned** | Infrastructure | Backend cannot start without a database. Include in Azure resource provisioning (M-9). |
| B-6 | **Alembic migrations not run** | Data | Backend will crash if tables don't exist. Include migration step in deployment pipeline. |

### High Risks

| # | Risk | Impact | Likelihood | Mitigation |
|---|------|--------|-----------|------------|
| R-1 | **SSE streaming through Azure Container Apps ingress** | SSE connections may be buffered or dropped by the Azure ingress proxy | Medium | Test early in Phase 3. Azure Container Apps supports streaming, but may need `Transfer-Encoding: chunked` and `X-Accel-Buffering: no` headers. Fallback: use polling instead of SSE. |
| R-2 | **NextAuth + PostgreSQL adapter instability** | NextAuth v5 is still in beta; adapter compatibility may break | Medium | Pin exact versions. Test auth flow thoroughly in Phase 1. Have a fallback plan to use `authlib` in Python if NextAuth proves unreliable. |
| R-3 | **TweAPI rate limiting or downtime** | All Twitter data is sourced from TweAPI; if it's down, the app is useless | Medium | Implement retry with exponential backoff. Cache responses where possible (profiles table). Display clear error messages to users. |
| R-4 | **Next.js proxy adds latency to all API calls** | Every data request goes through an extra hop (browser → Next.js → backend) | Low | Measure in Phase 3. If unacceptable, consider direct backend access with token-based auth (eliminate proxy). |
| R-5 | **AI provider cost surprises** | Batch translation of hundreds of posts can be expensive | Medium | Show estimated cost before batch translate. Enforce per-user daily limits. Default to cheaper models (Claude Haiku, GPT-4o-mini). |
| R-6 | **PostgreSQL connection exhaustion** | FastAPI async + many concurrent SSE streams may exhaust PostgreSQL connections | Low | Configure `asyncpg` connection pool (min=5, max=20). Use connection pooling (PgBouncer or Azure built-in). |
| R-7 | **TweAPI response shape changes** | TweAPI is a third-party API; response shapes may change without notice | Medium | Normalize all responses through Pydantic models with `model_config = ConfigDict(extra="ignore")`. Log unknown fields. Pin to specific TweAPI API version if available. |
| R-8 | **Cold start latency on Azure Container Apps** | Containers may scale to zero and take seconds to cold start | Low | Set minimum replicas to 1 for production. Accept cold starts on staging. |

### Medium Risks

| # | Risk | Impact | Likelihood | Mitigation |
|---|------|--------|-----------|------------|
| R-9 | Frontend/backend API contract drift | Frontend expects fields the backend doesn't provide | Medium | Maintain `shared/api-contract.md` as the source of truth. Use Pydantic models for response shapes. |
| R-10 | Alembic migration conflicts in team development | Multiple developers adding migrations simultaneously | Low | Use sequential naming. Review migration files in PR. |
| R-11 | Cookie-authenticated TweAPI endpoints (bookmarks, likes, DMs) | Twitter cookies expire unpredictably | High | Display clear status. Prompt user to refresh cookie. These features are best-effort. |
| R-12 | Large watchlists (100+ members) cause slow SSE fetch | Sequential fetch of 100 members × 30 tweets each | Medium | Add concurrency (2–3 parallel fetches) with rate limit awareness. Show ETA in progress UI. |

---

## 13. Pending Confirmations

These are assumptions that need the user's explicit sign-off. Implementation proceeds with the `Assumed` value unless the user says otherwise.

| # | Question | Assumed | Impact if Different |
|---|----------|---------|-------------------|
| P-1 | **Product name?** | **Feedscope** `Confirmed` | Domain and branding direction still to be decided. |
| P-2 | **Azure region?** | `East US 2` (cost-effective, full service availability) | Affects latency, compliance, pricing. |
| P-3 | **Azure subscription type?** | Pay-as-you-go | Enterprise Agreement or MSDN subscription may have different resource limits. |
| P-4 | **Auth provider(s)?** | Google OAuth only (same as reference) | Adding Microsoft Entra ID changes auth flow, requires app registration in Entra. |
| P-5 | **UI language?** | English (default) | If Chinese UI is needed (like reference project), affects all page text, prompts, and documentation. |
| P-6 | **Translation target language?** | Chinese (信达雅 style, same as reference) | If translating to a different language, default prompts and response markers must change. |
| P-7 | **Custom domain name?** | None for v1 (use `.azurecontainerapps.io` default) | Custom domain needs DNS setup (M-12), SSL cert (auto-managed by Azure). |
| P-8 | **Expected traffic level?** | Low — 1–5 concurrent users, <1000 API calls/day | Affects Azure tier selection, connection pool sizing, scaling config. |
| P-9 | **PostgreSQL tier?** | Burstable B1ms (1 vCore, 2 GB RAM, 32 GB storage) | ~$13/month. If higher load expected, move to General Purpose. |
| P-10 | **Container Apps tier?** | Consumption plan (pay per use, scale to zero in staging) | If always-on needed, use Dedicated plan. |
| P-11 | **Do we need the Next.js proxy pattern, or should the backend handle auth directly?** | Next.js proxy (matches reference architecture) | Direct backend auth simplifies deployment to 1 container + 1 static site, but requires re-implementing session validation in Python. |
| P-12 | **Should the agent/scripts from the reference project be ported?** | No — they are reference-project-specific CLI tools | If the user wants automated batch analysis, we'd build a Python CLI or Azure Function instead. |
| P-13 | **Team/multi-user workspace needed in v1?** | No — each user is independent (same as reference) | If yes, adds RBAC, shared watchlists, team management — significant scope increase. |
| P-14 | **Compliance requirements?** | None assumed | GDPR, SOC2, or other compliance needs affect data handling, logging, and infrastructure choices. |
| P-15 | **AI provider budget?** | User manages their own API keys (no centralized billing) | If the platform provides AI access, need billing/metering infrastructure. |
