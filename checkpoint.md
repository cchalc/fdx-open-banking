# Checkpoint

_Last updated: 2026-11-26_

## Where things stand
- The repo is bootstrapped: jj is colocated in the main checkout, `dev` is created, and `main`
  and `dev` are both protected (PR-only, no force-push, no deletion, enforced for admins).
- GitHub issues #1–#4 track the four workstreams. Each has its own wt worktree off `dev`.
- #1 (this scaffold) adds the dev standards, environment, living docs and CI.

## Next session
1. Read `tasks.md` for the status of #2–#4.
2. If a feature PR is open, check CI with `gh pr checks <n> --watch`, then merge to `dev`.
