import httpx
import pytest
import respx

from fdx_open_banking.client import FdxClient, unwrap
from fdx_open_banking.errors import FdxApiError

BASE = "https://fdx.test/fdx/v6"


def make_client() -> FdxClient:
    return FdxClient(BASE, "tok")


def test_unwrap_type_key() -> None:
    rt, rec = unwrap({"depositAccount": {"accountId": "1"}}, "account")
    assert rt == "depositAccount"
    assert rec == {"accountId": "1"}


def test_unwrap_flat_item_keeps_default_type() -> None:
    rt, rec = unwrap({"accountId": "1", "accountType": "CHECKING"}, "account")
    assert rt == "account"
    assert rec["accountType"] == "CHECKING"


def test_unwrap_single_scalar_key_is_not_unwrapped() -> None:
    assert unwrap({"accountId": "1"}, "account") == ("account", {"accountId": "1"})


@respx.mock
def test_sends_bearer_token() -> None:
    route = respx.get(f"{BASE}/accounts").mock(return_value=httpx.Response(200, json={}))
    list(make_client().accounts())
    assert route.calls.last.request.headers["Authorization"] == "Bearer tok"


@respx.mock
def test_paginates_with_page_key() -> None:
    respx.get(f"{BASE}/accounts", params={"pageKey": "p2"}).mock(
        return_value=httpx.Response(
            200, json={"accounts": [{"depositAccount": {"accountId": "2"}}]}
        )
    )
    respx.get(f"{BASE}/accounts").mock(
        return_value=httpx.Response(
            200,
            json={
                "page": {"nextPageKey": "p2"},
                "accounts": [{"depositAccount": {"accountId": "1"}}],
            },
        )
    )
    ids = [rec["accountId"] for _, rec in make_client().accounts()]
    assert ids == ["1", "2"]


@respx.mock
def test_paginates_with_links_next_and_keeps_filters() -> None:
    url = f"{BASE}/accounts/1/transactions"
    respx.get(url, params={"startTime": "2026-01-01", "offset": "2"}).mock(
        return_value=httpx.Response(
            200, json={"transactions": [{"depositTransaction": {"transactionId": "t3"}}]}
        )
    )
    respx.get(url, params={"startTime": "2026-01-01"}).mock(
        return_value=httpx.Response(
            200,
            json={
                "links": {"next": {"href": "/fdx/v6/accounts/1/transactions?offset=2"}},
                "transactions": [
                    {"depositTransaction": {"transactionId": "t1"}},
                    {"depositTransaction": {"transactionId": "t2"}},
                ],
            },
        )
    )
    from datetime import date

    txns = list(make_client().transactions("1", start_time=date(2026, 1, 1)))
    assert [r["transactionId"] for _, r in txns] == ["t1", "t2", "t3"]
    assert {rt for rt, _ in txns} == {"depositTransaction"}


@respx.mock
def test_repeated_cursor_stops() -> None:
    respx.get(f"{BASE}/accounts").mock(
        return_value=httpx.Response(
            200,
            json={"page": {"nextPageKey": "same"}, "accounts": [{"account": {"accountId": "1"}}]},
        )
    )
    assert len(list(make_client().accounts())) == 2  # first page + one follow, then stop


@respx.mock
def test_fdx_error_schema() -> None:
    respx.get(f"{BASE}/accounts/9").mock(
        return_value=httpx.Response(
            404, json={"code": "701", "message": "Account not found", "debugMessage": "id=9"}
        )
    )
    with pytest.raises(FdxApiError) as exc:
        make_client().account("9")
    assert exc.value.status == 404
    assert exc.value.code == "701"
    assert exc.value.debug_message == "id=9"


@respx.mock
def test_problem_json_error() -> None:
    respx.get(f"{BASE}/accounts").mock(
        return_value=httpx.Response(
            403, json={"type": "urn:fdx:consent", "title": "Forbidden", "detail": "scope missing"}
        )
    )
    with pytest.raises(FdxApiError, match="scope missing"):
        list(make_client().accounts())


@respx.mock
def test_plain_text_error() -> None:
    respx.get(f"{BASE}/accounts").mock(return_value=httpx.Response(500, text="boom"))
    with pytest.raises(FdxApiError, match="boom"):
        list(make_client().accounts())
