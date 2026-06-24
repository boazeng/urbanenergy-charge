"""Application entry point — the FastAPI app factory.

Wires the cross-cutting concerns once: structured logging, request-id
correlation, CORS, error handling, optional Sentry, and the data-source
selection (Ports & Adapters). Run with:

    uvicorn app.main:app --port 8060
"""

from __future__ import annotations

import logging
import uuid
from collections.abc import AsyncIterator, Awaitable, Callable
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.adapters.factory import build_data_source
from app.api.router import api_router
from app.core.config import get_settings
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
    return app


app = create_app()
