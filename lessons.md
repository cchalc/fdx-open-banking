# Lessons

Append-only, dated. Newest at the bottom.

## 2026-11-26: jj can't run inside a worktrunk (git) worktree
`wt switch --create` makes a plain git worktree. In it, `jj st` fails with "There is no jj repo",
and `jj git init --colocate` refuses: "Cannot create a colocated jj repo inside a Git worktree"
(jj 0.45.1). **Do:** use plain `git` for commits inside wt worktrees. Keep jj in the main
checkout, where `jj git fetch` (or the automatic import) shows the worktree branches as bookmarks.
`jj workspace add` is jj's own alternative, but it isn't what `wt` creates.

## 2026-11-26: Don't commit uv.lock
On the dev host, public PyPI is unreachable and uv resolves through a private proxy index set in
the user's uv config. `uv.lock` would record those proxy URLs: CI on GitHub couldn't fetch them,
and the public repo would expose the internal URL. **Do:** keep `uv.lock` gitignored. CI runs
`uv sync` straight from PyPI.

## 2026-11-26: The GitHub Python .gitignore template ignores `.envrc`
The template lists `.envrc` under "Environments", so add `!.envrc` after it to keep the
direnv entry point tracked.

## 2026-11-26: gh's active account is the EMU account, which has READ on this repo
`cchalc/fdx-open-banking` is on the personal `cchalc` account. Pushes over SSH work either way,
but `gh` calls (issues, PRs, branch protection) need `gh auth switch --user cchalc`.

## 2026-11-26: The commit-msg hook enforces `type(scope): subject`
A home-manager git template hook (`.git/hooks/commit-msg.py`) rejects the dev-standards
`[#N] Subject` header. It requires `type(scope): description`: type is one of feat, fix,
docs, style, refactor, perf, test or chore; the subject is lowercase and imperative with no
trailing dot; the header is at most 50 chars; line 2 is blank; every line is at most 72 chars.
**Do:** put the issue id in the scope, `chore(#1): add project scaffold`, and keep the
Problem/Solution body from dev standards.
