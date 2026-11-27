import random
from datetime import UTC, datetime
from pathlib import Path

import httpx
import pytest
import respx

from fdx_open_banking.auth import Token, load_token, save_token
from fdx_open_banking.login import extract_code
from fdx_open_banking.seed import account_payload, make_accounts, make_transactions, upload

NOW = datetime(2026, 11, 27, 12, tzinfo=UTC)


def test_seed_is_deterministic_and_canadian() -> None:
    accounts = make_accounts(910000)
    a = make_transactions(accounts, 30, random.Random(1), NOW)
    b = make_transactions(accounts, 30, random.Random(1), NOW)
    assert a == b
    assert len({t["transactionId"] for t in a}) == len(a)
    assert {account_payload(x)["currency"]["currencyCode"] for x in accounts} == {"CAD"}
    assert all(t["amount"] > 0 and t["debitCreditMemo"] in ("DEBIT", "CREDIT") for t in a)


def test_loc_account_reports_available_credit() -> None:
    card = next(a for a in make_accounts(0) if a.category == "LOC_ACCOUNT")
    payload = account_payload(card)
    assert "availableBalance" not in payload
    assert payload["availableCredit"] == round(5000 - card.balance, 2)


@respx.mock
def test_upload_posts_both_endpoints() -> None:
    acct = respx.post("http://mock/upload/addAccount", params={"userId": "fdxuser"}).mock(
        return_value=httpx.Response(200, json={"code": 0, "message": "Success"})
    )
    txn = respx.post("http://mock/upload/addTransactions").mock(
        return_value=httpx.Response(200, json={"code": 0, "message": "Success"})
    )
    with httpx.Client() as http:
        upload(http, "http://mock", "fdxuser", [{"accountId": "1"}], [{"transactionId": "t"}])
    assert acct.called and txn.called


@respx.mock
def test_upload_raises_on_mock_error() -> None:
    respx.post("http://mock/upload/addAccount").mock(
        return_value=httpx.Response(400, json={"code": "1001", "message": "No User Found"})
    )
    with httpx.Client() as http, pytest.raises(Exception, match="No User Found"):
        upload(http, "http://mock", "nobody", [], [])


def test_extract_code_variants() -> None:
    assert extract_code("abc", "s") == "abc"
    assert extract_code("https://cb/?code=xyz&state=s", "s") == "xyz"
    with pytest.raises(SystemExit, match="state mismatch"):
        extract_code("https://cb/?code=xyz&state=other", "s")
    with pytest.raises(SystemExit, match="access_denied"):
        extract_code("https://cb/?error=access_denied&state=s", "s")


def test_token_file_round_trip(tmp_path: Path) -> None:
    tok = Token.from_response({"access_token": "a", "expires_in": 300, "scope": "openid x"})
    path = tmp_path / "token.json"
    save_token(tok, path)
    assert oct(path.stat().st_mode & 0o777) == "0o600"
    back = load_token(path)
    assert back.access_token == "a"
    assert back.obtained_at == tok.obtained_at
    assert back.scopes == ["openid", "x"]
