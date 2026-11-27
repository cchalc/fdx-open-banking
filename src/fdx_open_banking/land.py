"""Fetch FDX data and land it as NDJSON envelopes (docs/landing-contract.md).

Destination is a local directory or a Unity Catalog Volume path (/Volumes/...), which is
written through the Databricks SDK so the workspace never needs to reach the local mocks.

    python -m fdx_open_banking.land --dest ./.local/landing
    python -m fdx_open_banking.land --dest /Volumes/<cat>/<schema>/fdx_raw --profile <profile>
"""

from __future__ import annotations

import argparse
import io
import json
import os
import uuid
from collections.abc import Iterable
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any, Protocol

import httpx

from .auth import Token, client_credentials, fdx_scopes, load_token
from .client import FdxClient

ENVELOPE_VERSION = 1


def utc_now() -> datetime:
    return datetime.now(UTC)


def iso(ts: datetime) -> str:
    return ts.astimezone(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


def envelope(
    entity: str,
    record_type: str,
    record: dict,
    *,
    source: str,
    fetched_at: datetime,
    account_id: str | None = None,
) -> dict[str, Any]:
    return {
        "envelope_version": ENVELOPE_VERSION,
        "entity": entity,
        "record_type": record_type,
        "source": source,
        "fetched_at": iso(fetched_at),
        "account_id": account_id,
        "record": record,
    }


def consent_record(
    token: Token,
    account_ids: list[str],
    *,
    client_id: str,
    duration_type: str = "TIME_BOUND",
    duration_days: int | None = 90,
    consent_id: str | None = None,
    status: str = "ACTIVE",
    granted_at: datetime | None = None,
) -> dict[str, Any]:
    """Describe the consent this token represents, in the landing contract's shape."""
    granted = granted_at or datetime.fromtimestamp(token.obtained_at, UTC)
    expires = (
        granted + timedelta(days=duration_days)
        if duration_type == "TIME_BOUND" and duration_days
        else None
    )
    return {
        "consentId": consent_id or token.raw.get("consentId") or f"c-{uuid.uuid4().hex[:12]}",
        "status": status,
        "durationType": duration_type,
        "scopes": fdx_scopes(token.scopes),
        "accountIds": account_ids,
        "clientId": client_id,
        "grantedAt": iso(granted),
        "expiresAt": iso(expires) if expires else None,
        "revokedAt": None,
    }


class Sink(Protocol):
    def write(self, relpath: str, data: bytes) -> str: ...


@dataclass
class LocalSink:
    root: Path

    def write(self, relpath: str, data: bytes) -> str:
        path = self.root / relpath
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
        return str(path)


@dataclass
class VolumeSink:
    """Writes into /Volumes/<catalog>/<schema>/<volume> via the Files API."""

    root: str
    profile: str | None = None
    _ws: Any = field(default=None, init=False, repr=False)

    def write(self, relpath: str, data: bytes) -> str:
        if self._ws is None:
            from databricks.sdk import WorkspaceClient

            self._ws = WorkspaceClient(profile=self.profile)
        path = f"{self.root.rstrip('/')}/{relpath}"
        self._ws.files.upload(path, io.BytesIO(data), overwrite=False)
        return path


@dataclass
class Lander:
    sink: Sink
    source: str
    run_id: str = field(default_factory=lambda: utc_now().strftime("%Y%m%dT%H%M%SZ"))
    _seq: int = 0

    def write(self, entity: str, envelopes: Iterable[dict]) -> str | None:
        lines = [json.dumps(e, separators=(",", ":"), default=str) for e in envelopes]
        if not lines:
            return None
        self._seq += 1
        day = utc_now().strftime("%Y-%m-%d")
        relpath = f"fdx/{entity}/{day}/{self.run_id}-{self._seq:04d}.jsonl"
        return self.sink.write(relpath, ("\n".join(lines) + "\n").encode())


def land_all(client: FdxClient, lander: Lander, consent: dict | None = None) -> dict[str, int]:
    """Fetch accounts and their transactions, then land them (and the consent) as NDJSON."""
    counts = {"accounts": 0, "transactions": 0, "consents": 0}
    fetched = utc_now()
    accounts = list(client.accounts())
    lander.write(
        "accounts",
        (
            envelope("accounts", rt, rec, source=lander.source, fetched_at=fetched)
            for rt, rec in accounts
        ),
    )
    counts["accounts"] = len(accounts)

    for _, acct in accounts:
        account_id = acct.get("accountId")
        if not account_id:
            continue
        fetched = utc_now()
        txns = [
            envelope(
                "transactions",
                rt,
                rec,
                source=lander.source,
                fetched_at=fetched,
                account_id=account_id,
            )
            for rt, rec in client.transactions(account_id)
        ]
        lander.write("transactions", txns)
        counts["transactions"] += len(txns)

    if consent is not None:
        lander.write(
            "consents",
            [envelope("consents", "consent", consent, source=lander.source, fetched_at=utc_now())],
        )
        counts["consents"] = 1
    return counts


def _env(name: str, default: str | None = None) -> str | None:
    return os.environ.get(name, default)


def main(argv: list[str] | None = None) -> None:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawTextHelpFormatter)
    p.add_argument("--base-url", default=_env("FDX_BASE_URL", "http://localhost:9090/fdx/v6"))
    p.add_argument("--token-url", default=_env("FDX_TOKEN_URL"))
    p.add_argument("--client-id", default=_env("FDX_CLIENT_ID"))
    p.add_argument("--client-secret", default=_env("FDX_CLIENT_SECRET"))
    p.add_argument("--scopes", default=_env("FDX_SCOPES", "ACCOUNT_DETAILED TRANSACTIONS"))
    p.add_argument("--token", default=_env("FDX_ACCESS_TOKEN"), help="skip the token call")
    p.add_argument("--token-file", type=Path, default=Path(".local/token.json"))
    p.add_argument("--dest", default=".local/landing", help="local dir or /Volumes/... path")
    p.add_argument("--profile", default=_env("DATABRICKS_CONFIG_PROFILE"))
    p.add_argument("--source", default="mastercard-fdx-mock")
    p.add_argument(
        "--duration-type", default="TIME_BOUND", choices=["ONE_TIME", "TIME_BOUND", "PERSISTENT"]
    )
    p.add_argument("--duration-days", type=int, default=90)
    args = p.parse_args(argv)

    http = httpx.Client(timeout=30.0)
    if args.token:
        token = Token(access_token=args.token, scope=args.scopes)
    elif args.token_file.exists():
        token = load_token(args.token_file)
        if token.is_expired(leeway=0):
            p.error(f"{args.token_file} has expired; run `python -m fdx_open_banking.login`")
    else:
        if not (args.token_url and args.client_id and args.client_secret):
            p.error(
                "no token: run `python -m fdx_open_banking.login`, pass --token, or set "
                "--token-url/--client-id/--client-secret (or FDX_* env)"
            )
        token = client_credentials(
            http, args.token_url, args.client_id, args.client_secret, args.scopes.split()
        )

    sink: Sink = (
        VolumeSink(args.dest, profile=args.profile)
        if args.dest.startswith("/Volumes/")
        else LocalSink(Path(args.dest))
    )
    lander = Lander(sink=sink, source=args.source)
    with FdxClient(args.base_url, token.access_token, http=http) as client:
        account_ids = [a.get("accountId") for _, a in client.accounts() if a.get("accountId")]
        consent = consent_record(
            token,
            account_ids,
            client_id=args.client_id or "unknown",
            duration_type=args.duration_type,
            duration_days=args.duration_days,
        )
        counts = land_all(client, lander, consent)
    print(json.dumps({"dest": args.dest, "run_id": lander.run_id, **counts}))


if __name__ == "__main__":
    main()
