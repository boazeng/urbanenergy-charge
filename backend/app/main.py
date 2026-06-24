"""Application entry point — the FastAPI app factory.

Wires the cross-cutting concerns once: structured logging, request-id
correlation, CORS, error handling, optional Sentry, and the data-source
selection (Ports & Adapters). Run with:

    uvicorn app.main:app --port 8060
"""

from __future__ import annotations

import logging
import os
import uuid
from collections.abc import AsyncIterator, Awaitable, Callable
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from app.adapters.factory import build_data_source
from app.api.router import api_router
from app.core.config import Settings, get_settings
from app.core.logging import configure_logging, request_id_ctx

log = logging.getLogger("app")


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    settings = get_settings()
    configure_logging(settings.log_level)
    _init_sentry(settings.sentry_dsn, settings.env.value)
    app.state.data_source = build_data_source(settings)
    log.info(
        "startup complete",
        extra={"env": settings.env.value, "data_source": settings.data_source.value},
    )
    yield
    log.info("shutdown")


def _init_sentry(dsn: str, env: str) -> None:
    if not dsn:
        return
    try:  # optional dependency — only used when a DSN is configured
        import sentry_sdk  # type: ignore[import-not-found]

        sentry_sdk.init(dsn=dsn, environment=env, traces_sample_rate=0.1)
        log.info("sentry initialised")
    except ImportError:
        log.warning("UE_SENTRY_DSN set but sentry-sdk not installed")


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(
        title="Urban Energy CSMS — Management API",
        version="0.1.0",
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_list,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.middleware("http")
    async def correlation_id(
        request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        rid = request.headers.get("x-request-id") or uuid.uuid4().hex[:16]
        token = request_id_ctx.set(rid)
        try:
            response = await call_next(request)
        finally:
            request_id_ctx.reset(token)
        response.headers["x-request-id"] = rid
        return response

    @app.exception_handler(Exception)
    async def unhandled(request: Request, exc: Exception) -> JSONResponse:
        # Log full detail server-side; never leak internals to the client.
        log.exception("unhandled error", extra={"path": request.url.path})
        return JSONResponse(status_code=500, content={"detail": "internal error"})

    app.include_router(api_router)
    _install_auth(app, settings)
    _mount_spa(app, settings)
    return app


def _install_auth(app: FastAPI, settings: Settings) -> None:
    """Install shared-auth (Google login + roles). Guards everything but the
    health probes; unauthenticated browsers are redirected to Google, API calls
    get 401. Safety nets (super-admin, emergency login) come from shared-auth.
    """
    if not settings.auth_enabled:
        log.warning("auth DISABLED — site is open (rely on Cloudflare Access at the edge)")
        return
    from shared_auth import install_auth

    install_auth(
        app,
        db_path=settings.auth_db_path,
        redirect_uri=settings.auth_redirect_uri,
        initial_users=[{"email": settings.auth_initial_admin, "role": "admin"}],
        public_prefixes=("/api/health", "/api/ready"),
    )
    log.info("shared-auth installed", extra={"redirect_uri": settings.auth_redirect_uri})


def _mount_spa(app: FastAPI, settings: Settings) -> None:
    """Serve the built React SPA from the same origin (single-container deploy)."""
    if os.path.isdir(settings.static_dir):
        app.mount("/", StaticFiles(directory=settings.static_dir, html=True), name="spa")
        log.info("serving SPA", extra={"dir": settings.static_dir})


app = create_app()
