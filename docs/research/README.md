# Research notes

First-pass research for the prototype (November 2026). Every claim in these notes cites a
public URL, and anything marked **unverified** still needs checking.

| File | What it covers |
|---|---|
| [`spec-sources.md`](./spec-sources.md) | Public FDX v6 sources (Mastercard FDX Dev Hub, Chariot sandbox, APIs.io, FDX itself), what each exposes, and their licences |
| [`mock-servers.md`](./mock-servers.md) | A runbook for the Mastercard FDX mock auth and resource servers: build, ports, auth, seeding, gotchas |
| [`consent-and-scopes.md`](./consent-and-scopes.md) | The OAuth 2.0 / FAPI sharing protocol, consent durations, the scope-to-data-category map, and the error schema |
| [`canada-context.md`](./canada-context.md) | The Consumer-Driven Banking Act framework, the roles of FDX, the FDX Canada Council, the Bank of Canada and OBSI, and the timeline |

## Headline findings

- **Don't commit the FDX OpenAPI YAMLs.** The FDX API License Agreement bars copying and
  distributing the spec. Fetch copies into the gitignored `vendor/` and hand-write models.
  The Mastercard YAML licence is unverified.
- **The mocks are Apache-2.0, but they publish no images.** You build them from source
  (Java 17, Spring Boot). Their base images are EOL, and the build needs Maven Central and
  Yarn. The auth server runs on 8080 and the resource server on 9090.
- **Account data needs the auth-code + consent flow** (PKCE, login `fdxuser` / `password`).
  Client-credentials tokens carry no account claim. Mock access tokens last about 5 minutes.
- **The mock differs from FDX:** list items are flat, there's no pagination, date filters are
  ignored, and there's no `/customers` endpoint. Chariot's sandbox follows the spec more
  closely (`pageKey`, date query params), but its credentials come from support, not
  self-service.
- **Canada:** FDX is the designated Technical Standards Body (announced 2026-11-20). The
  Consumer-Driven Banking Act came in through Bill C-15 (Royal Assent 2026-03-26).
  Phase 2 (write access and payments) is a mid-2027 legislative target tied to the
  Real-Time Rail. Phase 1 has no published launch date.
- **Open questions from the brief:** (a) no Canada-specific deltas to the v6 spec are
  published yet, since the "Canadian local profile" is still being finalized; (b) access to
  the spec needs licence acceptance rather than membership, but whether the data
  dictionary is gated is unverified.
