"""Security baseline — authentication dependency + role-based access control.

Phase 0 ships the *seams*, not the full identity stack:
  - A `Principal` (the authenticated caller) + `Role` enum.
  - A `require_role(...)` dependency factory used to guard routes.
  - Two auth backends behind one interface: `dev` (local, open) and `oauth`
    (wired to the shared Google-OAuth module in a later phase).

This means routes are written against the final security model now; swapping
`UE_AUTH_MODE=dev` → `oauth` later changes wiring only, not the routes.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from enum import StrEnum

from fastapi import Depends, HTTPException, status

from app.core.config import AuthMode, get_settings


class Role(StrEnum):
    admin = "admin"
    operator = "operator"
    viewer = "viewer"


_ORDER = {Role.viewer: 0, Role.operator: 1, Role.admin: 2}


@dataclass(frozen=True)
class Principal:
    user_id: str
    email: str
    role: Role


# Local development identity. Never reachable when UE_AUTH_MODE=oauth.
_DEV_PRINCIPAL = Principal(user_id="dev", email="dev@local", role=Role.admin)


def get_current_principal() -> Principal:
    """Resolve the caller. Dev mode returns a fixed admin; oauth mode is wired later."""
    settings = get_settings()
    if settings.auth_mode is AuthMode.dev:
        if settings.is_prod:  # safety: never allow open auth in production
            raise RuntimeError("AUTH_MODE=dev is forbidden in production")
        return _DEV_PRINCIPAL
    # AuthMode.oauth — integrated with shared-auth in a later phase.
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="OAuth auth backend not yet wired (Phase: security).",
    )


def require_role(minimum: Role) -> Callable[..., Principal]:
    """Dependency factory: guard a route by a minimum role (viewer < operator < admin)."""

    def _guard(principal: Principal = Depends(get_current_principal)) -> Principal:
        if _ORDER[principal.role] < _ORDER[minimum]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"requires role >= {minimum.value}",
            )
        return principal

    return _guard
