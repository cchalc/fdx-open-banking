# FDX consent model and scopes (API v6)

Research date: 2026-11-26. Public sources only.

**Legend:** `[V]` verified against a primary or official page fetched for this note. `[S]` secondary or implementer source (SDK, vendor docs, aggregator); treat as indicative. `[U]` unverified: could not confirm from an accessible source.

**Access caveat:** The canonical FDX API specification, data dictionary and implementation guides are members-only or licensed (see the FDX FAQ below). Nothing in this note is a substitute for the spec. Where the public mock servers and vendor docs disagree with each other, this note says so.

---

## 1. Sharing protocol

| Element | Status | Finding | Source |
|---|---|---|---|
| FDX API 6.0 release | [V] | Released with "the incorporation of the FAPI security schema." Release page dated 2023-12-18. No FAPI version, PAR or consent detail in the release text. | https://financialdataexchange.org/fdx-feed/financial-data-exchange-releases-fdx-api-6-0/ |
| FAPI profile version (1.0 Advanced vs 2.0) | [U] | Could not determine which FAPI profile FDX v6 mandates. Secondary sources say FDX historically referenced FAPI 1.0 Advanced, but I found no primary text. FDX's Canada page says a single Canadian security profile is still planned. | https://financialdataexchange.org/fdx-canada/ |
| FAPI 2.0 Security Profile | [V] | Final, published February 2025. Authorization servers must support client-authenticated PAR and must issue sender-constrained access tokens (MTLS per RFC 8705 or DPoP per RFC 9449). Section 5.5 lists breaking differences from FAPI 1.0. | https://openid.net/specs/fapi-security-profile-2_0.html |
| Pushed Authorization Requests | [V] for RFC; [S] for FDX use | RFC 9126 (OAuth 2.0 PAR), September 2021. FDX use of PAR with `authorization_details` is described by implementers, not in a primary FDX text I could read. | https://www.rfc-editor.org/rfc/rfc9126.html ; FDX use: [S] https://docs.akoya.com/reference/revoke-a-consent-grant-v6-1-0 (provider doc) |
| Dynamic client registration | [U] for FDX path | RFC 7591 is the standard. The brief's `/fdx/v6/register` path is not confirmed from a primary source. The Mastercard mock auth server does not expose its DCR path on its public page. | RFC 7591 (not fetched): https://www.rfc-editor.org/info/rfc7591 |
| Token introspection | [U] for FDX path | RFC 7662 is the standard (not fetched). No FDX-specific introspection path confirmed. | https://www.rfc-editor.org/info/rfc7662 |
| Token revocation | [U] for FDX path | RFC 7009 is the standard (not fetched). Consent revocation path is covered in section 2. | https://www.rfc-editor.org/info/rfc7009 |
| Consent OAuth scope | [S] | Implementers send `openid` (and `offline_access` in some flows) as the OAuth scope, and carry the FDX consent detail in `authorization_details` of type `fdx_v1.0`. | [S] https://docs.uat.developer.mikomobanking.com/guides/par-authorization-flow-guide |

**Mock implementation (public, buildable):** Mastercard's FDX mock auth server README says its API responses are "fully compliant with the Financial Data Exchange (FDX) 6.0 standard" and that it uses OAuth 2.0 and OIDC. Its public README does not list DCR, introspection, revocation, DPoP or mTLS paths, so the mock cannot yet be used to confirm them. https://github.com/Mastercard/Fdx-Mock-Auth-Server

---

## 2. Consent durations and the consent resource

### Duration types

| Value | Status | Meaning (as described) | Source |
|---|---|---|---|
| `ONE_TIME` | [S] | Single retrieval tied to one user action. Secondary text suggests a cap such as "not to exceed 24 hours." | FDX SBREFA response, 2023-01-25 (quoted in search results; the direct PDF fetch returned HTTP 404 during this research, so the wording is [U] at primary level): https://www.financialdataexchange.org/common/Uploaded%20files/Blog%20Assets/FDX%202023%20CFPB%20SBREFA%20Response%20-%2001-25-2023.pdf |
| `PERSISTENT` | [S] | Access until the end user revokes. | Same SBREFA response [U at primary level] |
| `TIME_BOUND` | [S] | Fixed window from grant, supplied as `durationPeriod` in days. Some implementers write `time_based`. Exact enum spelling must be checked against the spec. | Same SBREFA response; [S] https://pkg.go.dev/github.com/cloudentity/acp-client-go/clients/fdx/models |

The brief's three names match the implementer material, but I could not confirm the enum spellings from a primary FDX text. Treat the spellings as `[U]` until checked against the licensed spec or a conformance-tested implementation.

### Consent resource fields (implementer view)

- `durationType`, `durationPeriod` (integer days, required for time-bound), `lookbackPeriod` (integer days, measured from each data request, not from grant), `resources` (requested), `granted_resources` (actually granted), `createdTime`, `expirationTime`, `status`. [S] https://pkg.go.dev/github.com/cloudentity/acp-client-go/clients/fdx/models
- Revocation: `PUT /fdx/v6/consents/{consentId}/revocation` with body `{"initiator": "INDIVIDUAL", "reason": "USER_ACTION"}`, expected `204 No Content`. [S] https://docs.akoya.com/reference/revoke-a-consent-grant-v6-1-0 (a provider's API doc, not the FDX spec). Some providers instead use `DELETE /consents/{id}`. [U]

### Is there a public consent resource?

Not in a form I could confirm. The public material shows field names from SDKs and provider docs. The FDX spec text, which would define the consent resource normatively, is not public. The Mastercard mock resource server does not expose a consent endpoint on its public page.

---

## 3. Scope (dataCluster) to data category and endpoints

Scope names are from implementer and secondary material. Endpoint paths are from the public Mastercard mock resource server where marked, otherwise from third-party docs and marked `[S]` or `[U]`. The brief's paths are prefixed `/fdx/v6`. The mock server paths below are shown without that prefix, so the prefix is probably a base-URL convention. [U]

| Scope (dataCluster) | Data category (as described) | Endpoints | Status |
|---|---|---|---|
| `ACCOUNT_BASIC` | Account list and basic account identification and status | `GET /accounts` | Endpoint `[V]` on Mastercard mock resource server. Scope-to-endpoint mapping `[U]`. |
| `ACCOUNT_DETAILED` | Full account detail (balances, product type, dates, rates) | `GET /accounts/{account_id}` | Endpoint `[V]` on mock. Mapping `[U]`. |
| `TRANSACTIONS` | Transaction history, date filters, pagination | `GET /accounts/{account_id}/transactions` | Endpoint `[V]` on mock. Lookback rules `[S]`. |
| `STATEMENTS` | Statement list and documents | `GET /accounts/{account_id}/statements`, `GET /accounts/{account_id}/statements/{statement_id}` | Endpoints `[V]` on mock. |
| `CUSTOMER_CONTACT` | Account-holder and customer contact details | `GET /accounts/{account_id}/contact`. Brief also lists `GET /customers/current`. | Account contact `[V]` on mock. `/customers/current` `[U]`. |
| `ACCOUNT_PAYMENTS` | Payment networks and routing identifiers (ACH, RTP, wires, limits) | `GET /accounts/{account_id}/payment-networks` | Endpoint `[V]` on mock. Cluster-to-endpoint link `[U]`. |
| `PAYMENT_SUPPORT` | Money movement (write-side). Brief lists `POST /payment-support/transfers`. | Not on the mock resource server. Provider docs describe transfer endpoints `[S]`. | `[U]`. Write-side, so phase 2 in Canada (see canada-context.md). |
| `TAX_DOCUMENTS` | Tax forms and documents | Tax API mirror lists `GET /tax-forms`, `GET /tax-forms/{taxFormId}`, `POST /tax-forms`, `PUT /tax-forms/{taxFormId}`. Brief lists `GET /tax-documents`. | Tax mirror `[V]` for its own paths: https://www.taxdataexchange.org/docs/fdx/v6.4.1/ . Banking `TAX_DOCUMENTS` path `[U]`. |
| `PRODUCTS` | Product definitions, rates, terms | `GET /products`, `GET /products/{productId}` | `[S]` only (brief and one aggregator). |

**Note on the mock server:** The resource server exposes accounts, account details, transactions, payment networks, contact and statements. It does not expose the other clusters (`PAYMENT_SUPPORT`, `TAX_DOCUMENTS`, `PRODUCTS`, `CUSTOMER_CONTACT` at customer level) on its public page. Source: https://github.com/Mastercard/Fdx-Mock-Resource-Server

**Note on enforcement:** The mock resource server says access is controlled through "authentication and authorization mechanisms" and takes an authorization token. It does not say which clusters it checks. [U] whether it enforces per-cluster scope.

---

## 4. FDX error schema and RFC 7807

| Element | Status | Finding | Source |
|---|---|---|---|
| Error entity fields | [V] for the Tax-docs mirror | `code` (error code defined by FDX API spec or data provider), `message` (end-user displayable), `debugMessage` (for root-cause debugging, "should not be used in consumer's business logic"). All strings. Error codes are defined in section 6.2 (Errors) of the FDX API spec, which I could not read. | https://www.taxdataexchange.org/docs/fdx/v6.4.1/entities/Error.html |
| Section 6.2 error code list | [U] | Not accessed. | FDX spec (members or licensed) |
| RFC 7807 | [V] for status | Superseded by RFC 9457 (Problem Details for HTTP APIs), published July 2023, which "obsoletes RFC 7807." | https://www.rfc-editor.org/rfc/rfc9457.html ; https://datatracker.ietf.org/doc/html/rfc7807 |
| FDX uses RFC 7807 or 9457 | [U] | No FDX source I could read says FDX mandates problem+json. The brief says "some implementations use RFC 7807 problem+json." Treat as a vendor option. | - |

**Proposed mapping (a design choice, not an FDX requirement):** Return `application/problem+json` with the RFC 9457 members (`type`, `title`, `status`, `detail`, `instance`) and carry FDX `code` and `message` as extension members. Keep `debugMessage` out of responses to clients outside the support path.

---

## 5. How a demo should tell the consent story

Items 1 to 5 are about what to show. Items 6 to 8 are Databricks proposals and are labelled as such.

1. **Scopes as categories, not strings.** Show the consent screen with "Account basics", "Transactions", "Statements" and so on, then show the raw cluster names as a secondary view. Cluster-to-category wording is the demo's own; FDX's category text is not verified. [U]
2. **Duration is visible.** Show the duration type (ONE_TIME, PERSISTENT or TIME_BOUND) and, for TIME_BOUND, the expiry date. Enum names are `[U]` until checked against the spec. The SBREFA response, which asks for the expiry to be shown, is `[S]`.
3. **Lookback is separate from duration.** Show that a transaction lookback is measured from each request, not from consent grant. [S] (implementer SDK)
4. **Revocation is a user action with an immediate effect.** Demo a revoke and show the next resource call failing. The revocation path `[S]` is from a provider doc and is not confirmed for FDX.
5. **No screen scraping.** The Canadian framework prohibits screen scraping, but the prohibition takes effect only "once the framework is fully operational" (Department of Finance, Budget 2025 open banking page). The demo should say this is the target state, not current law. https://www.canada.ca/en/department-finance/programs/financial-sector-policy/open-banking-implementation/budget-2025-canadas-framework-for-consumer-driven-banking.html
6. **PROPOSAL: consent records as a governed table.** A `consent_records` table in Unity Catalog (`consent_id`, `subject_id`, `recipient_id`, `data_clusters`, `duration_type`, `expires_at`, `status`, `revoked_at`) is the source of truth for what a recipient may read. Unity Catalog row filters are SQL UDFs bound with `ALTER TABLE ... SET ROW FILTER` and evaluated at query time. https://docs.databricks.com/en/data-governance/unity-catalog/row-and-column-filters.html
7. **PROPOSAL: enforce cluster grants with filters and masks.** Row filter on `accounts` and `transactions` checks an active, unexpired consent with the relevant cluster. Column mask on `contact` fields checks the `CUSTOMER_CONTACT` grant. Column masks are also SQL UDFs (same docs page).
8. **PROPOSAL: revocation propagation.** A revoke updates `consent_records.status`, so the next query returns no rows. Note that row filters run per query, so the demo should show that the change is immediate and explain any caching assumption. Check Databricks behaviour before claiming it is immediate.

---

## Open items for the spec

- Confirm FAPI profile (1.0 Advanced vs 2.0) from the licensed FDX spec or FDX Canada output.
- Confirm consent enum spellings and the consent resource schema.
- Confirm DCR, introspection and revocation paths for FDX v6.
- Confirm cluster-to-endpoint mapping and whether the mock server enforces it.
- Confirm the FDX error code list in section 6.2.

## Sources

- FDX API 6.0 release: https://financialdataexchange.org/fdx-feed/financial-data-exchange-releases-fdx-api-6-0/
- FDX FAQ (spec access, membership): https://financialdataexchange.org/about-fdx/faqs/
- FDX Canada: https://financialdataexchange.org/fdx-canada/
- FAPI 2.0 Security Profile: https://openid.net/specs/fapi-security-profile-2_0.html
- RFC 9126: https://www.rfc-editor.org/rfc/rfc9126.html
- RFC 9457: https://www.rfc-editor.org/rfc/rfc9457.html
- Mastercard mock auth server: https://github.com/Mastercard/Fdx-Mock-Auth-Server
- Mastercard mock resource server: https://github.com/Mastercard/Fdx-Mock-Resource-Server
- FDX Tax docs mirror: https://www.taxdataexchange.org/docs/fdx/v6.4.1/
- FDX Error entity (Tax mirror): https://www.taxdataexchange.org/docs/fdx/v6.4.1/entities/Error.html
- Databricks row filters and column masks: https://docs.databricks.com/en/data-governance/unity-catalog/row-and-column-filters.html
- Implementer SDK (durations, consent fields): https://pkg.go.dev/github.com/cloudentity/acp-client-go/clients/fdx/models
- Provider revocation doc: https://docs.akoya.com/reference/revoke-a-consent-grant-v6-1-0
