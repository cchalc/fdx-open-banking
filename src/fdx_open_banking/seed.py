"""Generate synthetic Canadian accounts and transactions and push them into the FDX mock.

Uses the Mastercard resource server's unauthenticated Upload Data endpoints
(POST /upload/addAccount?userId=..., POST /upload/addTransactions). The mock keeps data
in memory, so re-seed after every restart. Account ids must be unique per mock run: pass
a different --id-base to seed again without restarting.

    python -m fdx_open_banking.seed --dry-run          # write JSON to .local/seed/ only
    python -m fdx_open_banking.seed                    # seed http://localhost:9090
"""

from __future__ import annotations

import argparse
import json
import os
import random
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from pathlib import Path

import httpx

from .errors import parse_error

# (merchant, category, typical amount CAD) — synthetic, Canadian flavour.
MERCHANTS = [
    ("Tim Hortons", "Restaurants", 6.50),
    ("Loblaws", "Groceries", 85.00),
    ("Sobeys", "Groceries", 64.00),
    ("PRESTO", "Transportation", 3.35),
    ("Petro-Canada", "Gas", 62.00),
    ("Hydro One", "Utilities", 140.00),
    ("Rogers", "Telecom", 95.00),
    ("Canadian Tire", "Shopping", 48.00),
    ("Shoppers Drug Mart", "Pharmacy", 27.00),
    ("Cineplex", "Entertainment", 32.00),
]


@dataclass(frozen=True)
class SeedAccount:
    account_id: str
    category: str  # FDX accountCategory
    account_type: str  # FDX accountType
    nickname: str
    balance: float


def make_accounts(id_base: int) -> list[SeedAccount]:
    return [
        SeedAccount(str(id_base + 1), "DEPOSIT_ACCOUNT", "CHECKING", "Everyday Chequing", 2450.17),
        SeedAccount(
            str(id_base + 2), "DEPOSIT_ACCOUNT", "SAVINGS", "High Interest Savings", 9120.00
        ),
        SeedAccount(str(id_base + 3), "LOC_ACCOUNT", "CREDITCARD", "Cash Back Visa", 612.45),
    ]


def account_payload(a: SeedAccount) -> dict:
    last4 = a.account_id[-4:]
    payload = {
        "accountId": a.account_id,
        "accountCategory": a.category,
        "accountType": a.account_type,
        "nickname": a.nickname,
        "displayName": f"******{last4}",
        "status": "OPEN",
        "productName": a.nickname,
        "description": f"{a.nickname} XXXX{last4}",
        "accountNumber": f"70{a.account_id.zfill(8)}",
        "accountNumberDisplay": last4,
        "currency": {"currencyCode": "CAD", "originalCurrencyCode": "CAD"},
        "currentBalance": a.balance,
    }
    if a.category == "DEPOSIT_ACCOUNT":
        payload["availableBalance"] = a.balance
    else:
        payload["availableCredit"] = round(5000 - a.balance, 2)
        payload["creditLine"] = 5000.0
    return payload


def make_transactions(
    accounts: list[SeedAccount], days: int, rng: random.Random, now: datetime
) -> list[dict]:
    txns: list[dict] = []
    for a in accounts:
        if a.account_type == "SAVINGS":
            # monthly interest only
            for m in range(0, days, 30):
                txns.append(_txn(a, now - timedelta(days=m), "Interest", "Interest", 7.6, "CREDIT"))
            continue
        for d in range(days):
            day = now - timedelta(days=d)
            if a.account_type == "CHECKING" and day.day in (1, 15):
                txns.append(_txn(a, day, "Payroll Deposit", "Income", 2850.0, "CREDIT"))
            for _ in range(rng.choice((0, 1, 1, 2, 3))):
                merchant, category, typical = rng.choice(MERCHANTS)
                amount = round(typical * rng.uniform(0.6, 1.5), 2)
                txns.append(_txn(a, day, merchant, category, amount, "DEBIT"))
    for i, t in enumerate(txns, 1):
        t["transactionId"] = f"{t['accountId']}-{i:05d}"
    return txns


def _txn(a: SeedAccount, ts: datetime, desc: str, category: str, amount: float, memo: str) -> dict:
    stamp = ts.astimezone(UTC).strftime("%Y-%m-%dT%H:%M:%S.000Z")
    return {
        "accountId": a.account_id,
        "accountCategory": a.category,
        "transactionType": "POSDEBIT" if memo == "DEBIT" else "POSCREDIT",
        "postedTimestamp": stamp,
        "transactionTimestamp": stamp,
        "description": desc,
        "payee": desc,
        "category": category,
        "debitCreditMemo": memo,
        "status": "POSTED",
        "amount": amount,  # FDX convention: positive amount, direction in debitCreditMemo
    }


def upload(http: httpx.Client, base: str, user_id: str, accounts: list[dict], txns: list[dict]):
    for path, params, body in (
        ("/upload/addAccount", {"userId": user_id}, accounts),
        ("/upload/addTransactions", None, txns),
    ):
        resp = http.post(f"{base}{path}", params=params, json=body)
        if resp.is_error:
            raise parse_error(resp)
        result = resp.json()
        if result.get("code") not in (0, "0"):
            raise RuntimeError(f"{path}: {result}")


def main(argv: list[str] | None = None) -> None:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawTextHelpFormatter)
    p.add_argument(
        "--resource-base", default=os.environ.get("FDX_RESOURCE_BASE", "http://localhost:9090")
    )
    p.add_argument("--user-id", default="fdxuser", help="existing mock user (default fdxuser)")
    p.add_argument("--id-base", type=int, default=910000)
    p.add_argument("--days", type=int, default=90)
    p.add_argument("--seed", type=int, default=2026, help="RNG seed (deterministic output)")
    p.add_argument("--out", type=Path, default=Path(".local/seed"))
    p.add_argument("--dry-run", action="store_true", help="write JSON only; don't call the mock")
    args = p.parse_args(argv)

    accounts = make_accounts(args.id_base)
    rng = random.Random(args.seed)
    now = datetime.now(UTC).replace(hour=12, minute=0, second=0, microsecond=0)
    acct_payloads = [account_payload(a) for a in accounts]
    txns = make_transactions(accounts, args.days, rng, now)

    args.out.mkdir(parents=True, exist_ok=True)
    (args.out / "accounts.json").write_text(json.dumps(acct_payloads, indent=2))
    (args.out / "transactions.json").write_text(json.dumps(txns, indent=2))
    summary = {"accounts": len(acct_payloads), "transactions": len(txns), "out": str(args.out)}
    if not args.dry_run:
        with httpx.Client(timeout=30.0) as http:
            upload(http, args.resource_base, args.user_id, acct_payloads, txns)
        summary["seeded"] = args.resource_base
    print(json.dumps(summary))


if __name__ == "__main__":
    main()
