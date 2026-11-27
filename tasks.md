# Tasks

Keyed to GitHub issues. Branch per issue: `cchalc/#N-desc` off `dev`.

## In progress
- [ ] #1 Project scaffold: dev standards, env, living docs, CI. Branch `cchalc/#1-project-scaffold`
- [ ] #2 Initial FDX v6 spec research → `docs/research/`. Branch `cchalc/#2-fdx-spec-research`
- [ ] #3 FDX v6 Python client and local mock servers. Branch `cchalc/#3-fdx-client-and-mocks`
- [ ] #4 Lakehouse bundle: DAB and the bronze/silver/gold pipeline. Branch `cchalc/#4-lakehouse-bundle`

## Next
- [ ] Run the mocks end to end under podman: seed → fetch → land.
- [ ] First `just bundle-deploy` and pipeline run (needs the catalog and owner approval).
  `bundle validate` already passes.
- [ ] Consent-story notebook: scopes → data categories, time-bound consent, revocation.
- [ ] Gold layer: spend by category, daily balances. Add an AI/BI dashboard on top.

## Decisions for the owner
- [ ] Pick a license (no LICENSE file yet; the repo is public).
- [ ] Pick the Unity Catalog catalog on fevm-cjc for the bundle (`BUNDLE_VAR_catalog`). The
  dev schema becomes `dev_<user>_fdx_open_banking`.
- [ ] Optional: dbdemos usage tracking for any app or dashboard this demo ships.
- [ ] Optional: a second ingest source, the Chariot FDX v6 sandbox (needs credentials).

## Open research questions (from the brief)
- [ ] Will the FDX Canada Council publish Canada-specific v6 deltas (Interac rails, TFSA, RRSP, FHSA)?
- [ ] Is FDX membership needed for the full data dictionary to get field-level fidelity?
