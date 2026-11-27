# FDX API v6 spec sources: what is public, what is licensed

Status: research notes, 2026-11-26. Every claim cites a URL. Items marked **unverified** could not be confirmed from a fetched source. This is engineering analysis, not legal advice; the redistribution verdict below should be confirmed by counsel before anything is committed publicly.

## Summary

| Source | Exposes | Machine-readable | License / terms | Can YAML go in a public repo? |
|---|---|---|---|---|
| Mastercard FDX Developer Hub | Authorization + resource API reference (OpenAPI) | Yes (per third-party mirrors) | Not verifiable: hub returned 401/404 to WebFetch. Secondhand summary of Mastercard's developer terms restricts redistribution (unverified) | **No** |
| Chariot FDX docs (sandbox) | Live FDX v6 sandbox at `/fdx/v6`; prose docs; no OpenAPI file located | Docs are HTML; `llms.txt` exists | No software or API license stated | Not applicable (no spec file to copy) |
| APIs.io / API Evangelist profile | Catalog entries that link to third-party OpenAPI copies | Yes (artifact URLs) | Profile states no license; the Slash FDX API it lists is a different company's API | **No** (third-party copies, no license) |
| FDX (financialdataexchange.org) | Public about/resources pages; the FDX API License Agreement; spec is members-only | Spec: via members-only portal | FDX API License Agreement (Last Modified July 15, 2026) forbids copying, modifying and distributing the API | **No** |
| openbankingframework.com | Commentary; no spec | No | "All Rights Reserved" footer (per fetch summary) | No spec to copy |

## Mastercard FDX Developer Hub

- Documentation root: https://developer.mastercard.com/fdx-dev-hub/documentation returned HTTP 401 to WebFetch. The hub root https://developer.mastercard.com/fdx-dev-hub/ also returned 401. https://developer.mastercard.com/fdx-dev-hub/documentation/api-reference/ returned 404. The API reference could not be read.
- **Exact download URLs for `fdx-authorization-api-openapi.yaml` and `fdx-resource-api-openapi.yaml`: unverified.** I could not reach the hub. A web-search answer pointed at a third-party raw URL for the resource YAML (`https://raw.githubusercontent.com/api-evangelist/mastercard-developer-hub-for-fdx-apis/main/openapi/fdx-resource-api-openapi.yaml`). That URL returns 404 today (checked with curl), so it is not a usable source.
- What I could verify is a third-party copy of the authorization API: https://artifacts.apis.io/mastercard-developer-hub-for-fdx-apis/openapi/mastercard-developer-hub-for-fdx-apis-par-rar-authorize-api-openapi.yml. Its info block says: title "Mastercard Developer Hub for FDX APIs FDX Authorization…", version 1.0.0, description "Dynamic Client Registration, Token, Introspection, Authorize API", servers `http://localhost:8080`, contact `apisupport@mastercard.com` (https://developer.mastercard.com/support). It names no license and no termsOfService. Caveat: this is an APIs.io-hosted copy, not Mastercard's own file. The fetch summary lists `/oauth2/par` as the only top-level path, which may be a truncation artifact.
- Mastercard's own license for the YAML is **unverified**. A web-search summary says the resource YAML's header declares `license: "Mastercard Product"` pointing to mastercard.com. I could not confirm that from the file, because the only copy I could reach is the APIs.io one, which has no license field.
- Terms that govern Mastercard developer materials: the Mastercard Developers Evaluation Agreement (Aug 2021), https://asset.mastercard.com/content/dam/gdpr/mastercarddevelopers/mastercard-developers-revised-terms-august-2021.pdf. WebFetch returned 403, so **I could not read it**. Secondhand search summaries say it allows only evaluation use, limits distribution to machine-readable form inside a "Licensed Implementation", bars sublicensing or distributing the materials, and restricts applying open-source licenses to them. All of that is **unverified** until someone reads the PDF.
- Mock servers from the same vendor: https://github.com/Mastercard/Fdx-Mock-Resource-Server and https://github.com/Mastercard/Fdx-Mock-Auth-Server both point at the hub (`https://developer.mastercard.com/fdx-dev-hub/documentation`) in their READMEs. Both repos are Apache-2.0 (see `mock-servers.md`). That license covers the mock code, not the API spec.

## Chariot FDX docs (sandbox)

- Intro: https://docs.givechariot.com/fdx/introduction
  - Sandbox base URL: `https://sandboxapi.givechariot.com/fdx/v6` (production `https://api.givechariot.com/fdx/v6`). FDX v6 is stated.
  - Auth: Chariot OAuth 2.0 with Bearer tokens; missing, invalid or expired tokens return 401. Scope named `read_only`.
  - Credentials: email support@givechariot.com for a client name and secret per environment. The page says nothing more about the process.
  - IP whitelisting: the intro page says FDX requires it, and that you send your IP ranges to support.
  - Pagination: cursor-based. Query params `pageKey` (UUID) and `limit` (10–100). Responses carry `page.nextPageKey` when more results exist.
  - Date filters: transactions and statements accept `startTime` and `endTime` as `YYYY-MM-DD`. Both or neither. Default is the last 7 days. Data goes back at most 24 months.
  - License/terms: none stated on the page.
- OAuth guide: https://docs.givechariot.com/v2026-04-01/guides/oauth
  - Authorization Code with PKCE is the nonprofit-scoped flow. Client Credentials is application-level.
  - Sandbox authorize: `https://dashboard.givechariot.com/oauth/sandbox/authorize`. Sandbox token: `https://sandboxapi.givechariot.com/auth/oauth/token`. OIDC discovery: `https://sandboxapi.givechariot.com/.well-known/openid-configuration`.
  - Lifetimes: authorization code 1 minute, single use; access token 15 minutes; refresh token 31-day sliding window, 365-day maximum, single-use rotation.
  - Scopes: per-resource `resource:read|write` (for example `donations:read`). The guide marks `read_only` and `read_write` as **deprecated**.
  - Sandbox credentials are separate from production and are not self-service.
- **Conflicts to resolve with Chariot support before coding:**
  1. The intro says FDX needs `scope=read_only`. The OAuth guide calls `read_only` deprecated and lists no FDX scope. Which scope FDX endpoints accept is **unverified**.
  2. The intro says FDX needs IP whitelisting. The OAuth guide does not mention IP whitelisting.
- Chariot's docs also publish `https://docs.givechariot.com/llms.txt` (linked from the intro page). Not fetched.
- Useful divergence for the client: Chariot documents `startTime`/`endTime` (`YYYY-MM-DD`) and `pageKey`/`limit` by name, and the fetched summary does not say whether they go in the query string (the usual assumption, not confirmed). The Mastercard mock reads `startTime`/`endTime` as HTTP request headers, not query parameters, and ignores them; it also has no pagination (see `mock-servers.md`).

## APIs.io / API Evangelist profile

- https://apis.apievangelist.com/store/joinslash-com-fdx-api/ is a profile of **Slash's** FDX API (ID `joinslash-com:joinslash-com-fdx-api`, base URL `https://api.slash.com`). It is not Mastercard's API and not an FDX reference implementation. The page calls itself "an independent third-party profile" that is not endorsed by Slash.
- Its OpenAPI copy is at https://artifacts.apis.io/joinslash-com/openapi/joinslash-com-fdx-api-openapi.yml (OpenAPI 3.2.0, 8 GET operations). The page states no license.
- The API Evangelist repo https://github.com/api-evangelist/mastercard-developer-hub-for-fdx-apis contains only `README.md` and `.gitignore` (checked with `gh api`). Its license is `null`. Its README says it "contains no software" and is a catalog of public API descriptions. The YAMLs are not in that repo.
- Verdict: APIs.io artifacts are catalog copies with no license. They are not a safe source to vendor.

## FDX (financialdataexchange.org) and openbankingframework.com

- FDX public pages: https://financialdataexchange.org/about-fdx/ and https://financialdataexchange.org/resources/ (Insights, white papers, FDX Feed). https://financialdataexchange.org/agentic-ai-open-finance/ is also public.
- FDX legal documents, public PDFs:
  - FDX API License Agreement (Last Modified: July 15, 2026): https://financialdataexchange.org/wp-content/uploads/2026/08/FDX-API-License-Agreement-July-15-2026-Final-II.pdf
  - Website Terms of Use: https://financialdataexchange.org/wp-content/uploads/2025/12/FDX-Website-Terms-of-Use-TC-8-12-2024.pdf (listed, not read)
- **Members-only:** the Developer Portal https://spechub.financialdataexchange.org/ is labelled "Members Only". The site's "Get the Spec" button goes to an onboarding account page with `membershipType=FDX_OBSERVER` (https://onboarding.financialdataexchange.org/accountview?membershipType=FDX_OBSERVER). The site says members get "member-only tools and resources for building and maintaining FDX API integrations". The spec itself was not accessible to me.

### What the FDX API License Agreement says

I extracted the text from the public PDF with a local parser (no tools were installed for PDF text, so this is a best-effort extraction; check the PDF before quoting it externally):

- Definition: "API means the FDX API (formerly known as the Durable Data API) specification and any API Documentation or other API materials made available by FDX on its website."
- §1 License grant: a limited, non-exclusive, non-transferable, non-sublicensable license "to use the API in developing Your Application(s) and allowing You and others to use the API as part of the use of Your Application."
- §2 Use restrictions. "Except as expressly authorized under this Agreement, you may not: 2.1. copy, modify, or create derivative works of the API ... 2.2. rent, lease, lend, sell, license, sublicense, assign, distribute, publish, transfer, or otherwise make available the API."
- §14.3: "You shall have the right to retain and maintain copies of all API Documentation and specifications provided to you or made publicly available by FDX for purposes of continuing to operate Your Applications."
- §11: FDX may modify the agreement; changes are posted at financialdataexchange.org.
- The definition of "Third Party Materials" covers open-source or other content "that are not proprietary to FDX". Mastercard's YAML is not FDX's own work, so the FDX agreement may not govern it. Mastercard's terms would then apply, and those could not be read (see above).

**Verdict on redistribution:** an FDX spec copy committed to this public repo would conflict with §2.1 and §2.2, because the FDX agreement covers copying and distributing the spec. §14.3 only preserves retained copies for operating your applications. I found no public grant that allows putting the Mastercard YAMLs in a public repo.

## Recommendation

1. **Target FDX API v6.0.** Both Mastercard mock servers describe themselves as FDX 6.0 (RS README: "fully compliant with the latest Financial Data Exchange (FDX) 6.0 standard", https://github.com/Mastercard/Fdx-Mock-Resource-Server/blob/main/README.md; AS README: https://github.com/Mastercard/Fdx-Mock-Auth-Server/blob/main/README.md). Chariot's sandbox serves `/fdx/v6`. Use Chariot's sandbox as the real-world reference and the mock as the local stand-in. Known differences are listed in `mock-servers.md`.
2. **Do not vendor the Mastercard YAMLs into `specs/openapi/`.** Reasons: the FDX agreement restricts copying and distributing the spec (§2.1–2.2); the Mastercard YAML license is unverified; the only reachable copies are third-party mirrors with no license. Keep the repo's `specs/openapi/` for files we author ourselves.
3. **Fetch any downloaded YAML into the gitignored `vendor/` directory.** The repo's `.gitignore` already ignores `vendor/` (line 234–235 of `.gitignore`: "Downloaded third-party specs and sources (fetched, not committed)"). That keeps the copy out of git. Local use to build the client still falls under the FDX §1 "developing Your Application(s)" grant and any Mastercard terms, so have counsel confirm it is acceptable.
4. **Do not generate committed client models from the YAML.** Hand-write the minimal models for the endpoints we use (accounts, transactions, pageKey pagination, statements), using observed JSON from the mock and Chariot's sandbox. This avoids shipping a derivative of the spec. Counsel should confirm this reading too.
5. Before coding, get Chariot's answers on the `read_only` versus per-resource scope question and on IP whitelisting for the sandbox (support@givechariot.com, per the intro page).
