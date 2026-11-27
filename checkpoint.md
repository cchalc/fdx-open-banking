# Checkpoint

_Last updated: 2026-11-27_

## Where things stand
- `main` and `dev` are protected (PR-only, no force-push or deletion, enforced for admins).
  `main` still holds only the initial commit. Everything else is on `dev`, awaiting the
  owner's `dev` → `main` PR.
- On `dev`:
  - #1: the scaffold and dev standards
  - #2: research in `docs/research/` (start at its README)
  - #3: the Python client, login, seeding and landing (36 tests)
  - #4: the bundle and the SQL pipeline (`bundle validate` OK, nothing deployed yet)
- CI (ruff lint and pytest) is green on every PR.
- The project is tracked as a Buildpad Idea; the id is in the local-only `.local/buildpad.md`.

## Blockers
- The mocks can't be built on the dev host, because Maven Central and Yarn are unreachable.
  Nothing has run end to end yet. See `tasks.md` → Next.
- The bundle catalog isn't chosen yet (an owner decision).

## Next session
1. Read `tasks.md`. Choose how to build the mocks, and pick the catalog.
2. Run the end-to-end path, then fix the silver field paths against real payloads.
