"""FDX error parsing (FDX Error schema and RFC 7807 problem+json)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import httpx


@dataclass
class FdxApiError(Exception):
    """An error response from an FDX endpoint."""

    status: int
    code: str | None
    message: str
    debug_message: str | None = None
    body: Any = None

    def __str__(self) -> str:
        code = f" [{self.code}]" if self.code else ""
        return f"FDX API error {self.status}{code}: {self.message}"


def parse_error(response: httpx.Response) -> FdxApiError:
    """Build an FdxApiError from an FDX Error body, an RFC 7807 body, or plain text."""
    try:
        body: Any = response.json()
    except ValueError:
        body = None

    if isinstance(body, dict):
        # FDX Error schema: {"code": "...", "message": "...", "debugMessage": "..."}
        if "code" in body or "message" in body:
            return FdxApiError(
                status=response.status_code,
                code=str(body["code"]) if body.get("code") is not None else None,
                message=str(body.get("message") or response.reason_phrase),
                debug_message=body.get("debugMessage"),
                body=body,
            )
        # RFC 7807: {"type": ..., "title": ..., "status": ..., "detail": ...}
        if "title" in body or "detail" in body:
            return FdxApiError(
                status=response.status_code,
                code=body.get("type"),
                message=str(body.get("detail") or body.get("title")),
                body=body,
            )

    return FdxApiError(
        status=response.status_code,
        code=None,
        message=response.text.strip() or response.reason_phrase,
        body=body,
    )
