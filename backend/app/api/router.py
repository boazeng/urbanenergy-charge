"""Aggregate API router — everything is mounted under /api."""

from __future__ import annotations

from fastapi import APIRouter

from app.api.routes import analytics, health, locations, partners, sessions

api_router = APIRouter(prefix="/api")
api_router.include_router(health.router)
api_router.include_router(analytics.router)
api_router.include_router(partners.router)
api_router.include_router(locations.router)
api_router.include_router(sessions.router)
