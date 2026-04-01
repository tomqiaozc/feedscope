from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.auth.dependencies import get_current_user
from app.config import settings
from app.routes.explore import router as explore_router
from app.routes.external import router as external_router
from app.routes.groups import router as groups_router
from app.routes.profiles import router as profiles_router
from app.routes.settings import router as settings_router
from app.routes.translate import router as translate_router
from app.routes.usage import router as usage_router
from app.routes.watchlists import router as watchlists_router
from app.routes.webhooks import router as webhooks_router


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    yield
    from app.db.engine import engine

    await engine.dispose()


app = FastAPI(title="Feedscope API", version="0.1.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health_check():
    return {"status": "ok"}


@app.get("/api/v1/me")
async def me(user_id: str = Depends(get_current_user)):
    return {"user_id": user_id}


app.include_router(explore_router)
app.include_router(external_router)
app.include_router(groups_router)
app.include_router(profiles_router)
app.include_router(settings_router)
app.include_router(translate_router)
app.include_router(usage_router)
app.include_router(watchlists_router)
app.include_router(webhooks_router)
