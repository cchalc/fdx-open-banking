# Tasks

Keyed to GitHub issues. Branch per issue: `cchalc/#N-desc` off `dev`.

## Done (merged to `dev`, closes when `dev` → `main`)
- [x] #1 Project scaffold: dev standards, env, living docs, CI (PR #5)
- [x] #2 Initial FDX v6 and Canada research → `docs/research/` (PR #8)
- [x] #3 FDX v6 client, auth/login, seeding, landing, mock compose (PR #7)
- [x] #4 Lakehouse bundle: DAB and the bronze/silver/gold pipeline (PR #6)

## Next
- [ ] **Build and run the mocks.** No upstream images exist, and Maven Central and Yarn are
  unreachable from the dev host (lessons.md 2026-11-27). Options: build on an open network,
  build in a GitHub Actions job that publishes to GHCR (the owner must approve publishing),
  or use an approved Maven mirror. Swap the EOL base images while you're at it.
- [ ] End to end against the mocks: `just mocks-fetch && just mocks-up && just seed && just login && just ingest`.
  Then check the silver SQL field paths against the real payloads.
- [ ] First `just bundle-deploy` and pipeline run (needs the catalog and owner approval).
  `bundle validate` already passes.
- [ ] Land to the UC Volume: `just ingest --dest /Volumes/<catalog>/dev_<user>_fdx_open_banking/fdx_raw --profile fevm-cjc`.
- [ ] AI/BI dashboard on `gold_spend_by_category` and `gold_balances_daily`.
- [ ] Consent revocation demo: land a `REVOKED` consent record, re-run, and show the account
  drop out of gold.
- [ ] Update the Buildpad Idea at milestones. Submit an Asset (with `idea_id`) once the demo
  works. The ids are in `.local/buildpad.md`, which is local only.

## Decisions for the owner
- [ ] Pick a license (no LICENSE file yet; the repo is public).
- [ ] Pick the Unity Catalog catalog on fevm-cjc for the bundle (`BUNDLE_VAR_catalog`). The
  dev schema becomes `dev_<user>_fdx_open_banking`.
- [ ] Merge `dev` → `main` when you're happy (a PR, which closes #1–#4).
- [ ] Optional: dbdemos usage tracking for any app or dashboard this demo ships.
- [ ] Optional: a second ingest source, the Chariot FDX v6 sandbox (credentials come from
  their support team; see `docs/research/spec-sources.md`).

## Open research questions
- [ ] Watch for the FDX Canada "Canadian local profile". No Canada-specific v6 deltas
  (Interac, TFSA, RRSP, FHSA) are published yet.
- [ ] Is the FDX data dictionary gated beyond licence acceptance? (unverified)
- [ ] Mastercard FDX YAML licence (unverified). Don't commit the YAMLs either way.
