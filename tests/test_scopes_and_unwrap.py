import doctest

import pytest

from fdx_open_banking import auth
from fdx_open_banking.auth import fdx_scopes, normalize_scope
from fdx_open_banking.client import unwrap


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("TRANSACTIONS", "TRANSACTIONS"),
        ("fdx:transactions:read", "TRANSACTIONS"),
        ("fdx:accountbasic:read", "ACCOUNT_BASIC"),
        ("fdx:accountdetailed:read", "ACCOUNT_DETAILED"),
        ("fdx:tax-documents:read", "TAX_DOCUMENTS"),
        ("openid", None),
        ("offline_access", None),
    ],
)
def test_normalize_scope(raw: str, expected: str | None) -> None:
    assert normalize_scope(raw) == expected


def test_fdx_scopes_dedupes_and_drops_oidc() -> None:
    assert fdx_scopes(["openid", "fdx:transactions:read", "TRANSACTIONS"]) == ["TRANSACTIONS"]


def test_auth_doctests() -> None:
    assert doctest.testmod(auth).failed == 0


@pytest.mark.parametrize(
    ("category", "default", "expected"),
    [
        ("DEPOSIT_ACCOUNT", "account", "depositAccount"),
        ("LOC_ACCOUNT", "transaction", "locTransaction"),
        ("INVESTMENT_ACCOUNT", "account", "investmentAccount"),
        ("SOMETHING_NEW", "account", "account"),
    ],
)
def test_flat_items_typed_from_account_category(category: str, default: str, expected: str) -> None:
    rt, rec = unwrap({"accountId": "1", "accountCategory": category}, default)
    assert rt == expected
    assert rec["accountId"] == "1"
