# Architecture

## Goal
Show, on Databricks, what Canadian consumer-driven banking looks like with FDX API v6 as the
technical standard: a data recipient obtains scoped, time-bound consent through OAuth 2.0/FAPI,
pulls FDX JSON, and lands it in governed Delta tables. The consent story matters as much as the
data.

## Data path

```
 Mastercard FDX mocks (podman, local)        Databricks (bundle: fdx_open_banking)
 ┌────────────────────┐                      ┌──────────────────────────────────────┐
 │ Fdx-Mock-Auth      │  OAuth token         │ UC Volume  raw/fdx/<entity>/*.json   │
 │ Fdx-Mock-Resource  │◀── fdx_open_banking ─┤   │ Auto Loader                      │
 │  /fdx/v6/accounts… │    client (httpx)    │   ▼                                  │
 └────────▲───────────┘        │             │ bronze_*  (raw JSON + ingest meta)   │
          │ Upload Data         │ land.py     │   ▼                                  │
     seed.py (synthetic)        └────────────▶ silver_accounts, silver_transactions │
                                 SDK upload   │   ▼                                  │
                                              │ gold_spend_by_category,              │
                                              │ gold_balances_daily                  │
                                              └──────────────────────────────────────┘
```

**Why land JSON from the laptop instead of calling the mocks from a notebook?** The mocks run
on localhost, which a workspace can't reach. Landing raw pages in a UC Volume keeps the
lakehouse side identical whether the source is the local mock, a public sandbox (Chariot), or
a real data provider later: only the landing step changes.

**Why raw JSON in bronze?** FDX payloads are polymorphic (transaction variants per account
type). Bronze keeps every byte; silver selects the typed fields per variant, so schema
decisions can change without re-ingesting.

## Environment
`devenv.nix` (preferred) or bare `direnv + uv` (fallback). Both point the venv at
`~/.virtualenvs/fdx-open-banking`, a hardcoded path so `wt` worktrees share one venv instead
of building one per branch. Cost: renaming the repo dir means editing `.envrc` and
`devenv.nix`.

## VCS
jj is the primary local VCS (colocated with git); GitHub interop goes through `jj git push`.
worktrunk (`wt`) creates sibling git worktrees for parallel work. jj can't colocate inside a git
worktree, so worktrees use plain git and the main checkout's jj imports the result.
`main` and `dev` are PR-only.

## Decisions log
| Decision | Why |
|---|---|
| Mastercard mocks as the first source | Open source and runnable locally, with seeding endpoints; no FDX membership needed. |
| podman, not Docker | Docker isn't installed on the dev host; podman runs the same images. |
| `uv.lock` not committed | Local resolution goes through a private index; a lock would embed its URLs and break public CI. |
| Bundle names a profile, not a host | The repo is public; workspace hosts stay out of it. |
