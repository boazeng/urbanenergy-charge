"""Low-level HTTP client for the Evoltsoft (Urban Energy) backend.

Responsibilities are narrow on purpose: transport + authentication only. It
knows *how* to talk to Evoltsoft (Firebase auth, the persona-role header, error
handling), not *what* the endpoints mean — that lives in EvoltsoftAdapter.

Observed in the captured traffic: the analytics/portal Cloud Functions accept a
`persona-role: Admin` header and did not carry a bearer token. We still support
Firebase email/password auth (the API key is public, in the web bundle) so the
client keeps working if the vendor starts enforcing it.
"""

from __future__ import annotations

import time
from typing import Any

import httpx

_FIREBASE_SIGNIN = "https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword"
# refresh the id token a minute before it actually expires
_TOKEN_SKEW_S = 60.0


class EvoltsoftError(RuntimeError):
    """Raised when an Evoltsoft request fails."""


class EvoltsoftClient:
    def __init__(
        self,
        *,
        base_url: str,
        firebase_api_key: str = "",
        email: str = "",
        password: str = "",
        timeout_s: float = 20.0,
        client: httpx.AsyncClient | None = None,
    ) -> None:
        self._api_key = firebase_api_key
        self._email = email
        self._password = password
        self._has_creds = bool(firebase_api_key and email and password)
        self._token: str | None = None
        self._token_expiry: float = 0.0
        # Injectable client makes the adapter unit-testable with MockTransport.
        self._http = client or httpx.AsyncClient(base_url=base_url, timeout=timeout_s)

    async def aclose(self) -> None:
        await self._http.aclose()

    async def _auth_token(self) -> str | None:
        if not self._has_creds:
            return None
        if self._token and time.monotonic() < self._token_expiry:
            return self._token
        resp = await self._http.post(
            _FIREBASE_SIGNIN,
            params={"key": self._api_key},
            json={"email": self._email, "password": self._password, "returnSecureToken": True},
        )
        if resp.status_code != httpx.codes.OK:
            raise EvoltsoftError(f"Firebase sign-in failed: {resp.status_code}")
        data = resp.json()
        self._token = str(data["idToken"])
        self._token_expiry = time.monotonic() + float(data.get("expiresIn", 3600)) - _TOKEN_SKEW_S
        return self._token

    async def _headers(self) -> dict[str, str]:
        headers = {"persona-role": "Admin", "content-type": "application/json"}
        token = await self._auth_token()
        if token:
            headers["authorization"] = f"Bearer {token}"
        return headers

    async def _request(self, method: str, path: str, payload: dict[str, Any]) -> Any:
        try:
            resp = await self._http.request(
                method, path, json=payload, headers=await self._headers()
            )
        except httpx.HTTPError as exc:  # network/timeout
            raise EvoltsoftError(f"{path}: transport error: {exc}") from exc
        if resp.status_code != httpx.codes.OK:
            raise EvoltsoftError(f"{path}: HTTP {resp.status_code}")
        return resp.json()

    async def post(self, path: str, payload: dict[str, Any]) -> Any:
        """POST a Cloud Function and return parsed JSON. Raises EvoltsoftError on failure."""
        return await self._request("POST", path, payload)

    async def put(self, path: str, payload: dict[str, Any]) -> Any:
        """PUT a Cloud Function (e.g. the revenue series) and return parsed JSON."""
        return await self._request("PUT", path, payload)
