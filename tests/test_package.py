import fdx_open_banking


def test_api_version() -> None:
    assert fdx_open_banking.FDX_API_VERSION == "v6"
