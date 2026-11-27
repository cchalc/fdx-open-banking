import base64
import hashlib
from urllib.parse import parse_qs, urlsplit

import httpx
import respx

from fdx_open_banking.auth import Pkce, Token, authorization_url, client_credentials

TOKEN_URL = "https://auth.test/oauth2/token"


@respx.mock
def test_client_credentials_uses_basic_auth_and_scopes() -> None:
    route = respx.post(TOKEN_URL).mock(
        return_value=httpx.Response(
            200, json={"access_token": "abc", "expires_in": 3600, "scope": "TRANSACTIONS"}
        )
    )
    with httpx.Client() as http:
        tok = client_credentials(http, TOKEN_URL, "cid", "secret", ["TRANSACTIONS"])
    req = route.calls.last.request
    assert req.headers["Authorization"].startswith("Basic ")
    assert b"grant_type=client_credentials" in req.content
    assert b"scope=TRANSACTIONS" in req.content
    assert tok.access_token == "abc"
    assert tok.scopes == ["TRANSACTIONS"]
    assert not tok.is_expired()


def test_token_expiry() -> None:
    tok = Token(access_token="x", expires_in=10, obtained_at=0)
    assert tok.is_expired()
    assert Token(access_token="x").expires_at is None


def test_pkce_s256() -> None:
    p = Pkce.generate()
    expected = base64.urlsafe_b64encode(hashlib.sha256(p.verifier.encode()).digest())
    assert p.challenge == expected.rstrip(b"=").decode()
    assert 43 <= len(p.verifier) <= 128


def test_authorization_url_plain_and_par() -> None:
    p = Pkce.generate()
    url = authorization_url("https://auth.test/authorize", "cid", "http://cb", ["A", "B"], "s", p)
    q = parse_qs(urlsplit(url).query)
    assert q["scope"] == ["A B"]
    assert q["code_challenge_method"] == ["S256"]
    par = authorization_url(
        "https://auth.test/authorize", "cid", "http://cb", [], "s", p, request_uri="urn:x"
    )
    assert parse_qs(urlsplit(par).query) == {"client_id": ["cid"], "request_uri": ["urn:x"]}
