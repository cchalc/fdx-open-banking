# fdx-open-banking

A prototype of Canadian open banking on Databricks, built on the **FDX API v6** standard.

In November 2026 the Department of Finance Canada designated the Financial Data Exchange (FDX)
as the technical standards body for the Consumer-Driven Banking framework. This project shows
what that means for data teams. A data recipient gets scoped, time-bound consent through
OAuth 2.0 / FAPI, pulls FDX JSON (accounts, transactions, statements), and lands it in governed
Delta tables on Databricks. It replaces credential sharing and screen scraping.

> **Status:** early prototype. Expect breaking changes. See [`tasks.md`](./tasks.md).

## How it works

1. **Source:** Mastercard's open-source FDX mock auth and resource servers run locally under
   podman, seeded with synthetic Canadian accounts and transactions.
2. **Client:** `fdx_open_banking` (Python, httpx) gets a token, calls `/fdx/v6/...` with cursor
   pagination, and parses FDX errors.
3. **Landing:** raw JSON pages are written to a Unity Catalog Volume.
4. **Lakehouse:** a Lakeflow Spark Declarative Pipeline builds bronze (raw), silver (typed
   accounts and transactions) and gold (spend by category, balances over time) tables.
5. **Consent story:** a notebook maps scopes to data categories and shows time-bound consent
   and revocation.

The design rationale is in [`architecture.md`](./architecture.md), and the research notes are
in [`docs/research/`](./docs/research/).

## Quickstart

Prerequisites: [direnv](https://direnv.net/), [uv](https://docs.astral.sh/uv/), Python 3.11+,
[just](https://just.systems/), [podman](https://podman.io/), and the
[Databricks CLI](https://docs.databricks.com/dev-tools/cli/) for the bundle.
[devenv](https://devenv.sh/) is optional; it's preferred if you have Nix.

```bash
direnv allow        # loads devenv (or the plain uv fallback); the venv lives in ~/.virtualenvs/
just setup          # uv sync
just check          # lint + tests (the same gate as CI)

just mocks-up       # start the FDX mock servers (podman)
just seed           # seed synthetic accounts/transactions
just ingest         # fetch FDX data and land raw JSON

just bundle-validate   # validate the Databricks Asset Bundle (dev target)
```

## Contributing

`main` and `dev` are protected. Every change goes through a pull request into `dev`.
Open an issue first, then branch as `<user>/#<issue>-<short-desc>`. Commit and PR conventions
are in [`CLAUDE.md`](./CLAUDE.md).

## Disclaimer

This is a demo built on public mock servers and synthetic data. It is not affiliated with
FDX, Mastercard, or any financial institution, and it is not production banking software.
