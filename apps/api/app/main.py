from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware

from apps.api.app.config import get_settings
from apps.api.app.middleware.request_context import RequestContextMiddleware
from apps.api.app.routers import (
    auth,
    competitions,
    datasets,
    jobs,
    leaderboard,
    scoring,
    submissions,
    users,
)
from apps.api.app.services.bootstrap import bootstrap_local_state
from packages.observability.logging import configure_logging


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
    settings = get_settings()
    configure_logging()
    bootstrap_local_state(settings)
    yield


app = FastAPI(title="Pelatnas Competition API", version="0.1.0", lifespan=lifespan)
settings = get_settings()

app.add_middleware(RequestContextMiddleware)
app.add_middleware(
    SessionMiddleware,
    secret_key=settings.session_secret,
    session_cookie=settings.session_cookie_name,
    max_age=settings.session_max_age_seconds,
    same_site="lax",
    https_only=False,
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.web_origin],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/api/v1/health")
def api_health() -> dict[str, str]:
    return {"status": "ok"}


app.include_router(auth.router, prefix="/api/v1")
app.include_router(competitions.router, prefix="/api/v1")
app.include_router(datasets.router, prefix="/api/v1")
app.include_router(submissions.router, prefix="/api/v1")
app.include_router(jobs.router, prefix="/api/v1")
app.include_router(leaderboard.router, prefix="/api/v1")
app.include_router(scoring.router, prefix="/api/v1")
app.include_router(users.router, prefix="/api/v1")
