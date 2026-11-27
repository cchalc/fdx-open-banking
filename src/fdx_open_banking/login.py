"""Get an account-scoped token from the FDX mock auth server (authorization code + PKCE).

The Mastercard mock only grants account access through a consent screen, so this is
interactive: open the printed URL, log in (mock default fdxuser / password), pick the
accounts to share, then paste the URL you were redirected to.

    python -m fdx_open_banking.login            # saves .local/token.json
    python -m fdx_open_banking.land             # picks the token up from there

Defaults are the mock's public upstream values (docs/research/mock-servers.md).
Access tokens from the mock last about 5 minutes, so land soon after logging in.
"""

from __future__ import annotations

import argparse
import os
import secrets
from pathlib import Path
from urllib.parse import parse_qs, urlsplit

import httpx

from .auth import Pkce, authorization_url, exchange_code, fdx_scopes, save_token

MOCK_AUTH = "http://localhost:8080"
MOCK_CLIENT_ID = "dh-fdx-client-registrar-1"
MOCK_CLIENT_SECRET = "secret"  # public upstream mock default, not a real credential
MOCK_REDIRECT = "https://oauth.pstmn.io/v1/browser-callback"
MOCK_SCOPES = "openid fdx:accountbasic:read fdx:transactions:read"


def extract_code(pasted: str, expected_state: str) -> str:
    """Accept either the full redirect URL or a bare code; check state when present."""
    pasted = pasted.strip()
    if "://" not in pasted and "code=" not in pasted:
        return pasted
    query = parse_qs(urlsplit(pasted).query if "://" in pasted else pasted)
    if "error" in query:
        raise SystemExit(f"authorization failed: {query['error'][0]}")
    state = query.get("state", [expected_state])[0]
    if state != expected_state:
        raise SystemExit("state mismatch: the redirect isn't from this login attempt")
    try:
        return query["code"][0]
    except KeyError:
        raise SystemExit("no code= in the pasted URL") from None


def main(argv: list[str] | None = None) -> None:
    env = os.environ.get
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawTextHelpFormatter)
    p.add_argument("--auth-base", default=env("FDX_AUTH_BASE", MOCK_AUTH))
    p.add_argument("--client-id", default=env("FDX_CLIENT_ID", MOCK_CLIENT_ID))
    p.add_argument("--client-secret", default=env("FDX_CLIENT_SECRET", MOCK_CLIENT_SECRET))
    p.add_argument("--redirect-uri", default=env("FDX_REDIRECT_URI", MOCK_REDIRECT))
    p.add_argument("--scopes", default=env("FDX_SCOPES", MOCK_SCOPES))
    p.add_argument("--token-file", type=Path, default=Path(".local/token.json"))
    args = p.parse_args(argv)

    pkce = Pkce.generate()
    state = secrets.token_urlsafe(16)
    url = authorization_url(
        f"{args.auth_base}/oauth2/authorize",
        args.client_id,
        args.redirect_uri,
        args.scopes.split(),
        state,
        pkce,
    )
    print("Open this URL, log in, and choose the accounts to share:\n")
    print(url, "\n")
    code = extract_code(input("Paste the redirect URL (or just the code): "), state)

    with httpx.Client(timeout=30.0) as http:
        token = exchange_code(
            http,
            f"{args.auth_base}/oauth2/token",
            args.client_id,
            args.client_secret,
            code,
            args.redirect_uri,
            pkce,
        )
    save_token(token, args.token_file)
    print(
        f"Saved token to {args.token_file}: FDX scopes {fdx_scopes(token.scopes)}, "
        f"expires in {token.expires_in}s"
    )


if __name__ == "__main__":
    main()
