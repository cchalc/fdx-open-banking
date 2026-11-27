"""A small FDX v6 resource-API client: bearer auth, cursor pagination, FDX errors."""

from __future__ import annotations

from collections.abc import Callable, Iterator
from datetime import date
from typing import Any
from urllib.parse import parse_qsl, urlsplit

import httpx

from .errors import parse_error

TokenProvider = Callable[[], str]

# FDX wraps polymorphic objects in a single type key, e.g. {"depositAccount": {...}}.
_WRAPPER_SUFFIXES = ("Account", "Transaction", "Statement")


# Flat items (e.g. the Mastercard mock) carry accountCategory instead of a wrapper key.
_CATEGORY_PREFIX = {
    "DEPOSIT_ACCOUNT": "deposit",
    "LOAN_ACCOUNT": "loan",
    "LOC_ACCOUNT": "loc",
    "INVESTMENT_ACCOUNT": "investment",
    "INSURANCE_ACCOUNT": "insurance",
    "ANNUITY_ACCOUNT": "annuity",
}


def unwrap(item: dict, default_type: str) -> tuple[str, dict]:
    """Return (record_type, record) for an FDX list item.

    Wrapped items ({"depositAccount": {...}}) are unwrapped. Flat items get a record type
    from their accountCategory (DEPOSIT_ACCOUNT -> depositAccount / depositTransaction).
    """
    if len(item) == 1:
        ((key, value),) = item.items()
        if isinstance(value, dict) and (key.endswith(_WRAPPER_SUFFIXES) or key == default_type):
            return key, value
    prefix = _CATEGORY_PREFIX.get(str(item.get("accountCategory", "")))
    if prefix and default_type in ("account", "transaction", "statement"):
        return prefix + default_type.capitalize(), item
    return default_type, item


def _next_params(body: dict, current: dict[str, Any]) -> dict[str, Any] | None:
    """Work out the query params for the next page, or None at the end.

    Supports the three styles seen across FDX implementations: a `links.next.href`,
    a `page.nextPageKey` cursor (sent back as `pageKey`), and a `page.nextOffset`.
    """
    links = body.get("links") or {}
    nxt = links.get("next")
    href = nxt.get("href") if isinstance(nxt, dict) else nxt
    if href:
        query = dict(parse_qsl(urlsplit(href).query))
        return {**current, **query} if query else None

    page = body.get("page") or {}
    for field, param in (("nextPageKey", "pageKey"), ("nextOffset", "offset")):
        value = page.get(field)
        if value not in (None, ""):
            return {**current, param: value}
    return None


class FdxClient:
    """Read-only FDX v6 client for a data recipient.

    `token` is a static bearer token or a zero-argument callable that returns one,
    so callers can plug in refresh logic.
    """

    def __init__(
        self,
        base_url: str,
        token: str | TokenProvider,
        *,
        http: httpx.Client | None = None,
        timeout: float = 30.0,
        max_pages: int = 1000,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self._token = token
        self._http = http or httpx.Client(timeout=timeout)
        self.max_pages = max_pages

    # -- plumbing ---------------------------------------------------------------------

    def _headers(self) -> dict[str, str]:
        token = self._token() if callable(self._token) else self._token
        return {"Authorization": f"Bearer {token}", "Accept": "application/json"}

    def get(self, path: str, params: dict[str, Any] | None = None) -> dict:
        resp = self._http.get(f"{self.base_url}{path}", params=params, headers=self._headers())
        if resp.is_error:
            raise parse_error(resp)
        return resp.json()

    def paginate(
        self, path: str, items_key: str, params: dict[str, Any] | None = None
    ) -> Iterator[dict]:
        """Yield each raw page body for a list endpoint, following the cursor."""
        current = dict(params or {})
        seen: set[tuple] = set()
        for _ in range(self.max_pages):
            body = self.get(path, current or None)
            yield body
            nxt = _next_params(body, current)
            if nxt is None or not body.get(items_key):
                return
            marker = tuple(sorted((k, str(v)) for k, v in nxt.items()))
            if marker in seen:  # a server that repeats its cursor would loop forever
                return
            seen.add(marker)
            current = nxt
        raise RuntimeError(f"{path}: more than {self.max_pages} pages")

    def _items(
        self, path: str, items_key: str, default_type: str, params: dict | None = None
    ) -> Iterator[tuple[str, dict]]:
        for body in self.paginate(path, items_key, params):
            for item in body.get(items_key) or []:
                yield unwrap(item, default_type)

    # -- FDX v6 endpoints -------------------------------------------------------------

    def accounts(self) -> Iterator[tuple[str, dict]]:
        """GET /accounts (scope ACCOUNT_BASIC). Yields (record_type, account)."""
        return self._items("/accounts", "accounts", "account")

    def account(self, account_id: str) -> tuple[str, dict]:
        """GET /accounts/{accountId} (scope ACCOUNT_DETAILED)."""
        return unwrap(self.get(f"/accounts/{account_id}"), "account")

    def transactions(
        self,
        account_id: str,
        start_time: date | None = None,
        end_time: date | None = None,
    ) -> Iterator[tuple[str, dict]]:
        """GET /accounts/{accountId}/transactions (scope TRANSACTIONS)."""
        params: dict[str, Any] = {}
        if start_time:
            params["startTime"] = start_time.isoformat()
        if end_time:
            params["endTime"] = end_time.isoformat()
        return self._items(
            f"/accounts/{account_id}/transactions", "transactions", "transaction", params
        )

    def statements(self, account_id: str) -> Iterator[tuple[str, dict]]:
        """GET /accounts/{accountId}/statements (scope STATEMENTS)."""
        return self._items(f"/accounts/{account_id}/statements", "statements", "statement")

    def contact(self, account_id: str) -> dict:
        """GET /accounts/{accountId}/contact (scope CUSTOMER_CONTACT)."""
        return self.get(f"/accounts/{account_id}/contact")

    def payment_networks(self, account_id: str) -> dict:
        """GET /accounts/{accountId}/payment-networks (scope ACCOUNT_PAYMENTS)."""
        return self.get(f"/accounts/{account_id}/payment-networks")

    def current_customer(self) -> dict:
        """GET /customers/current."""
        return self.get("/customers/current")

    def close(self) -> None:
        self._http.close()

    def __enter__(self) -> FdxClient:
        return self

    def __exit__(self, *exc: object) -> None:
        self.close()
