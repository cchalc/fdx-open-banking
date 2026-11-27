# fdx-open-banking

Prototype: pull FDX API v6 open-banking data (accounts, transactions, consent) from the
Mastercard FDX mock servers into Databricks as Delta bronze/silver/gold, told as a Canadian
consumer-driven-banking consent story. Background: `docs/brief.md`; research: `docs/research/`.

**This repo is public.** Never commit secrets, internal URLs, workspace hosts, customer data,
or internal tracker links. Bundle config names a CLI profile only, never a host.

## Living docs (read these in order at session start)
1. `checkpoint.md` — where work left off
2. `tasks.md` — in progress + next, keyed to GitHub issues
3. `lessons.md` — append-only, dated learnings (consult when stuck)
4. `architecture.md` — why things are shaped this way

At session end: overwrite `checkpoint.md` with the current state.
On surprises: append a dated entry to `lessons.md`.

## Repo layout
- `src/fdx_open_banking/` — Python package: FDX v6 client, auth, models, mock seeding, landing
- `tests/`                — pytest (+ respx for HTTP)
- `mock/`                 — podman compose for the Mastercard FDX mock servers + seed data
- `databricks.yml`, `resources/`, `src/pipelines/`, `notebooks/` — the Databricks Asset Bundle
- `docs/`                 — brief, research notes, design notes
- `specs/openapi/`        — FDX OpenAPI files only if their license allows; otherwise
  `vendor/` (gitignored, fetched)

## VCS: jj + worktrunk, never commit to main
- `main` and `dev` are protected on GitHub: PR-only, no force-push, no deletion (admins too).
- `dev` is the integration branch. Feature branches come off `dev` and merge back by PR;
  `dev` → `main` is a PR the owner merges.
- Branch names: `cchalc/#<issue>-<brief-description>` — open a GitHub issue first.
- Main checkout: `jj` (colocated with git). Publish with `jj git push --bookmark <name>`.
- Parallel work: `wt switch --create 'cchalc/#N-desc' --base dev` → sibling worktree
  `../fdx-open-banking.cchalc-#N-desc`. **jj cannot run inside a git worktree** (lessons.md
  2026-11-26), so use plain `git` there; the main checkout's jj picks the commits up on
  `jj git fetch` / import.
- Commits: `type(#N): lowercase imperative subject` (≤50 chars, no trailing period;
  type ∈ feat, fix, docs, style, refactor, perf, test, chore), blank line, mandatory
  `Problem:` and `Solution:` paragraphs, every line ≤72. End with the trailer
  `Co-authored-by: Isaac <no-reply@databricks.com>`. The user's global commit-msg hook
  enforces the header (lessons.md 2026-11-26).
- Signing: git signs via SSH from the user's global git config, so commits made with git are
  signed. jj has no signing configured; unsigned jj commits are an accepted exception for this
  prototype.
- PRs: target `dev`, Problem/Solution description, end the body with
  `This pull request and its description were written by Isaac.`
- GitHub account: the repo lives on the personal `cchalc` account. If a push or `gh` call
  says "not found" or read-only, run `gh auth switch --user cchalc`.

## Python
- One shared venv at `~/.virtualenvs/fdx-open-banking` for every worktree.
- `direnv allow` once; devenv (preferred) or plain uv fallback.
- `uv add <pkg>` to add deps; `uv run …` to run. `uv.lock` is gitignored (lessons.md).
- `just check` = lint + test, the same gate as CI.

## Databricks
- Bundle dev target uses CLI profile `fevm-cjc`. Pass `--profile` explicitly; never
  auto-select a different one.
- `just bundle-validate` is safe. Ask before `just bundle-deploy` or any job/pipeline run.

## Tooling rules
- Containers: podman (no Docker on this host). Never Homebrew.
- Third-party sources (mock servers, specs) are run from published images or fetched into
  `vendor/`; never vendored into `src/`.
