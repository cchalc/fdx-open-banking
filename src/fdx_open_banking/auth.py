"""OAuth 2.0 helpers for an FDX data recipient.

Covers what the demo needs: client credentials (machine-to-machine), and the
authorization-code flow with PKCE and optional Pushed Authorization Requests (PAR,
RFC 9126). It's not a FAPI-certified client: no mTLS or private_key_jwt.
"""

from __future__ import annotations

import base64
import hashlib
import json
import secrets
import time
from dataclasses import dataclass, field
from pathlib import Path
from urllib.parse import urlencode

import httpx

from .errors import parse_error


@dataclass
class Token:
    access_token: str
    token_type: str = "Bearer"
    expires_in: int | None = None
    scope: str | None = None
    refresh_token: str | None = None
    obtained_at: float = field(default_factory=time.time)
    raw: dict = field(default_factory=dict)

    @classmethod
    def from_response(cls, body: dict) -> Token:
        return cls(
            access_token=body["access_token"],
            token_type=body.get("token_type", "Bearer"),
            expires_in=body.get("expires_in"),
            scope=body.get("scope"),
            refresh_token=body.get("refresh_token"),
            raw=body,
        )

    @property
    def scopes(self) -> list[str]:
        return self.scope.split() if self.scope else []

    @property
    def expires_at(self) -> float | None:
        return self.obtained_at + self.expires_in if self.expires_in else None

    def is_expired(self, leeway: float = 30.0) -> bool:
        return self.expires_at is not None and time.time() >= self.expires_at - leeway


# FDX scope names, and the OAuth scope strings some servers use for them
# (the Mastercard mock uses "fdx:<scope>:read").
FDX_SCOPES = (
    "ACCOUNT_BASIC",
    "ACCOUNT_DETAILED",
    "ACCOUNT_PAYMENTS",
    "CUSTOMER_CONTACT",
    "CUSTOMER_PERSONAL",
    "INVESTMENTS",
    "PAYMENT_SUPPORT",
    "PRODUCTS",
    "STATEMENTS",
    "TAX_DOCUMENTS",
    "TRANSACTIONS",
)
_COMPACT = {s.replace("_", "").lower(): s for s in FDX_SCOPES}


def normalize_scope(scope: str) -> str | None:
    """Map an OAuth scope string to its FDX scope name, or None if it isn't one.

    >>> normalize_scope("fdx:transactions:read")
    'TRANSACTIONS'
    >>> normalize_scope("ACCOUNT_DETAILED")
    'ACCOUNT_DETAILED'
    >>> normalize_scope("openid") is None
    True
    """
    if scope in FDX_SCOPES:
        return scope
    parts = scope.split(":")
    core = parts[1] if len(parts) >= 2 and parts[0].lower() == "fdx" else scope
    return _COMPACT.get(core.replace("_", "").replace("-", "").lower())


def fdx_scopes(scopes: list[str]) -> list[str]:
    """FDX scope names covered by a list of OAuth scopes, de-duplicated and sorted."""
    return sorted({n for s in scopes if (n := normalize_scope(s))})


def _post_token(
    http: httpx.Client, token_url: str, data: dict, client_id: str, client_secret: str | None
) -> Token:
    auth = (client_id, client_secret) if client_secret else None
    if not client_secret:
        data = {**data, "client_id": client_id}
    resp = http.post(token_url, data=data, auth=auth, headers={"Accept": "application/json"})
    if resp.is_error:
        raise parse_error(resp)
    return Token.from_response(resp.json())


def client_credentials(
    http: httpx.Client,
    token_url: str,
    client_id: str,
    client_secret: str,
    scopes: list[str] | None = None,
) -> Token:
    """Get a token with the client-credentials grant."""
    data = {"grant_type": "client_credentials"}
    if scopes:
        data["scope"] = " ".join(scopes)
    return _post_token(http, token_url, data, client_id, client_secret)


@dataclass
class Pkce:
    verifier: str
    challenge: str
    method: str = "S256"

    @classmethod
    def generate(cls) -> Pkce:
        verifier = secrets.token_urlsafe(64)[:96]
        digest = hashlib.sha256(verifier.encode()).digest()
        challenge = base64.urlsafe_b64encode(digest).rstrip(b"=").decode()
        return cls(verifier=verifier, challenge=challenge)


def authorization_url(
    authorize_url: str,
    client_id: str,
    redirect_uri: str,
    scopes: list[str],
    state: str,
    pkce: Pkce,
    request_uri: str | None = None,
) -> str:
    """Build the user-facing authorization URL (plain, or a PAR request_uri reference)."""
    if request_uri:
        params = {"client_id": client_id, "request_uri": request_uri}
    else:
        params = {
            "response_type": "code",
            "client_id": client_id,
            "redirect_uri": redirect_uri,
            "scope": " ".join(scopes),
            "state": state,
            "code_challenge": pkce.challenge,
            "code_challenge_method": pkce.method,
        }
    return f"{authorize_url}?{urlencode(params)}"


def pushed_authorization_request(
    http: httpx.Client,
    par_url: str,
    client_id: str,
    client_secret: str | None,
    redirect_uri: str,
    scopes: list[str],
    state: str,
    pkce: Pkce,
) -> str:
    """Push the authorization request (RFC 9126) and return its request_uri."""
    data = {
        "response_type": "code",
        "redirect_uri": redirect_uri,
        "scope": " ".join(scopes),
        "state": state,
        "code_challenge": pkce.challenge,
        "code_challenge_method": pkce.method,
    }
    auth = (client_id, client_secret) if client_secret else None
    if not client_secret:
        data["client_id"] = client_id
    resp = http.post(par_url, data=data, auth=auth)
    if resp.is_error:
        raise parse_error(resp)
    return resp.json()["request_uri"]


def exchange_code(
    http: httpx.Client,
    token_url: str,
    client_id: str,
    client_secret: str | None,
    code: str,
    redirect_uri: str,
    pkce: Pkce,
) -> Token:
    """Exchange an authorization code (with its PKCE verifier) for a token."""
    data = {
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": redirect_uri,
        "code_verifier": pkce.verifier,
    }
    return _post_token(http, token_url, data, client_id, client_secret)


def save_token(token: Token, path: Path) -> None:
    """Write a token to disk (e.g. .local/token.json, which is gitignored)."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({**token.raw, "obtained_at": token.obtained_at}, indent=2))
    path.chmod(0o600)


def load_token(path: Path) -> Token:
    body = json.loads(path.read_text())
    token = Token.from_response(body)
    token.obtained_at = float(body.get("obtained_at", token.obtained_at))
    return token
