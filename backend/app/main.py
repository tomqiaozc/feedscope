from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_user
from app.config import settings
from app.db.engine import get_db_session
from app.providers.base import (
    AuthRequiredError,
    ProviderError,
    ProviderTimeoutError,
    RateLimitError,
    UpstreamError,
)
from app.routes.dashboard import router as dashboard_router
from app.routes.explore import router as explore_router
from app.routes.external import router as external_router
from app.routes.groups import router as groups_router
from app.routes.profiles import router as profiles_router
from app.routes.settings import router as settings_router
from app.routes.translate import router as translate_router
from app.routes.usage import router as usage_router
from app.routes.watchlists import router as watchlists_router
from app.routes.webhooks import router as webhooks_router
from app.telemetry import setup_telemetry


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    yield
    from app.db.engine import engine

    await engine.dispose()


app = FastAPI(title="Feedscope API", version="0.1.0", lifespan=lifespan)

# OpenTelemetry instrumentation (optional — no-op if packages missing or unconfigured)
setup_telemetry(app)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# --- Provider exception handlers ---


@app.exception_handler(RateLimitError)
async def rate_limit_handler(request, exc: RateLimitError):
    headers = {}
    if exc.retry_after:
        headers["Retry-After"] = str(exc.retry_after)
    return JSONResponse(
        status_code=429,
        content={"success": False, "error": str(exc)},
        headers=headers,
    )


@app.exception_handler(AuthRequiredError)
async def auth_required_handler(request, exc: AuthRequiredError):
    return JSONResponse(status_code=401, content={"success": False, "error": str(exc)})


@app.exception_handler(ProviderTimeoutError)
async def timeout_handler(request, exc: ProviderTimeoutError):
    return JSONResponse(
        status_code=504,
        content={"success": False, "error": "Provider request timed out"},
    )


@app.exception_handler(UpstreamError)
async def upstream_handler(request, exc: UpstreamError):
    return JSONResponse(status_code=502, content={"success": False, "error": str(exc)})


@app.exception_handler(ProviderError)
async def provider_error_handler(request, exc: ProviderError):
    return JSONResponse(status_code=503, content={"success": False, "error": str(exc)})


@app.get("/health")
async def health_check():
    return {"status": "ok"}


@app.get("/health/ready")
async def readiness_check(session: AsyncSession = Depends(get_db_session)):
    try:
        await session.execute(text("SELECT 1"))
        return {"status": "ready"}
    except Exception as exc:
        return JSONResponse(
            status_code=503,
            content={"status": "not_ready", "error": str(exc)},
        )


@app.get("/api/v1/me")
async def me(user_id: str = Depends(get_current_user)):
    return {"user_id": user_id}


app.include_router(dashboard_router)
app.include_router(explore_router)
app.include_router(external_router)
app.include_router(groups_router)
app.include_router(profiles_router)
app.include_router(settings_router)
app.include_router(translate_router)
app.include_router(usage_router)
app.include_router(watchlists_router)
app.include_router(webhooks_router)
