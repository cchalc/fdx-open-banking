import json
from pathlib import Path

import httpx
import respx

from fdx_open_banking.auth import Token
from fdx_open_banking.client import FdxClient
from fdx_open_banking.land import Lander, LocalSink, consent_record, land_all

BASE = "https://fdx.test/fdx/v6"


def read_jsonl(root: Path, entity: str) -> list[dict]:
    files = sorted((root / "fdx" / entity).rglob("*.jsonl"))
    return [json.loads(line) for f in files for line in f.read_text().splitlines()]


@respx.mock
def test_land_all_writes_contract_envelopes(tmp_path: Path) -> None:
    respx.get(f"{BASE}/accounts").mock(
        return_value=httpx.Response(
            200,
            json={"accounts": [{"depositAccount": {"accountId": "A1", "currentBalance": 10}}]},
        )
    )
    respx.get(f"{BASE}/accounts/A1/transactions").mock(
        return_value=httpx.Response(
            200,
            json={"transactions": [{"depositTransaction": {"transactionId": "T1", "amount": 5}}]},
        )
    )
    token = Token(access_token="t", scope="ACCOUNT_DETAILED TRANSACTIONS", expires_in=3600)
    consent = consent_record(token, ["A1"], client_id="demo", consent_id="c-1")

    counts = land_all(FdxClient(BASE, "t"), Lander(LocalSink(tmp_path), "test"), consent)
    assert counts == {"accounts": 1, "transactions": 1, "consents": 1}

    (acct,) = read_jsonl(tmp_path, "accounts")
    assert acct["envelope_version"] == 1
    assert acct["entity"] == "accounts"
    assert acct["record_type"] == "depositAccount"
    assert acct["record"] == {"accountId": "A1", "currentBalance": 10}
    assert acct["account_id"] is None
    assert acct["fetched_at"].endswith("Z")

    (txn,) = read_jsonl(tmp_path, "transactions")
    assert txn["account_id"] == "A1"
    assert txn["record_type"] == "depositTransaction"

    (con,) = read_jsonl(tmp_path, "consents")
    assert con["record"]["consentId"] == "c-1"
    assert con["record"]["scopes"] == ["ACCOUNT_DETAILED", "TRANSACTIONS"]
    assert con["record"]["status"] == "ACTIVE"
    assert con["record"]["expiresAt"] is not None


def test_persistent_consent_has_no_expiry() -> None:
    rec = consent_record(Token(access_token="t"), [], client_id="x", duration_type="PERSISTENT")
    assert rec["expiresAt"] is None
