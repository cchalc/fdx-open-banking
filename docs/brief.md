# FDX & Canadian Open Banking — Brief

Thread 23 — Nov 22, 2026. Trigger: Ottawa named FDX the technical standards
body for Canadian open banking (Investment Executive link shared by Christopher).

## The news

- The Department of Finance Canada designated the Financial Data Exchange (FDX)
  as the official Technical Standards Body under the Consumer-Driven Banking Act.
  Orders signed Nov 13, 2026, published in the Canada Gazette; announced Fri
  Nov 20–21, 2026.
- FDX acts through an **FDX Canada Council**, created to answer sovereignty
  concerns: it can make decisions independently from the wider FDX board, and
  voting membership is limited to Canadian residents and businesses. FDX itself
  is a US-based non-profit.
- OBSI (Ombudsman for Banking Services and Investments) was named the
  designated external complaints body. The Bank of Canada will supervise
  providers and maintain a public registry of accredited services.
- FDX has been in Canada since 2020 via the FDX Canada Working Group (BMO,
  CIBC, Koho, Flinks, etc.). The Canada Council is its evolution.
- Sources: BetaKit via
  https://www.europesays.com/canada/301522/ and
  https://northwardab.ca/news/canada-open-banking-fdx-obsi-november-2026/

## The standard: FDX API v6.0

- **Data format:** JSON over REST. Endpoints under `/fdx/v6/`:
  - `GET /fdx/v6/accounts` — list consented accounts
  - `GET /fdx/v6/accounts/{accountId}` — account detail (balance, product type)
  - `GET /fdx/v6/accounts/{accountId}/transactions` — transaction history
  - `GET /fdx/v6/accounts/{accountId}/contact` — account-holder contact
  - `GET /fdx/v6/accounts/{accountId}/payment-networks` — payment rails/limits
  - `GET /fdx/v6/accounts/{accountId}/statements` (+ `/{statementId}`)
  - `GET /fdx/v6/customers/current`, `GET /fdx/v6/tax-documents`,
    `GET /fdx/v6/products`, `POST /payment-support/transfers`
- **Data models:** accounts by type (CHECKING, SAVINGS, CREDITCARD, MORTGAGE,
  LOAN, LINEOFCREDIT, INVESTMENTACCOUNT, CD, MONEYMARKET…); transaction
  variants per account type (DepositTransaction, InvestmentTransaction,
  LineOfCreditTransaction…); statements; contact/customer; payment networks.
- **Sharing protocol:** OAuth 2.0 + OpenID Connect under the FAPI
  (Financial-grade API) security profile. Dynamic client registration
  (`/fdx/v6/register`), Pushed Authorization Requests (PAR, RFC 9126), token
  introspection, consent durations ONE_TIME / PERSISTENT / TIME_BOUND, and
  scopes such as ACCOUNT_BASIC, ACCOUNT_DETAILED, TRANSACTIONS, STATEMENTS,
  CUSTOMER_CONTACT, ACCOUNT_PAYMENTS, PAYMENT_SUPPORT, TAX_DOCUMENTS,
  PRODUCTS. Errors follow the FDX Error schema (some implementations use
  RFC 7807 problem+json).
- **The catch:** the canonical FDX API specification, data dictionary and
  implementation guides are members-only at financialdataexchange.org. The
  public material below is what you can actually build against without
  membership.

## Where to get the spec (public, buildable)

1. **Mastercard FDX Developer Hub** — the best starting point.
   Docs: https://developer.mastercard.com/fdx-dev-hub/documentation
   API reference (FDX 6.0): https://developer.mastercard.com/fdx-dev-hub/documentation/api-reference/
   OpenAPI YAMLs: `fdx-authorization-api-openapi.yaml`,
   `fdx-resource-api-openapi.yaml` (linked from the hub).
   Mock servers (open source, Spring Boot, Docker images available):
   - https://github.com/Mastercard/Fdx-Mock-Auth-Server
   - https://github.com/Mastercard/Fdx-Mock-Resource-Server
   The mock resource server has "Upload Data" endpoints to seed fake accounts
   and transactions, and an API simulator. Reference-app setup guide:
   https://developer.mastercard.com/fdx-dev-hub/documentation/reference-app/
2. **Chariot FDX docs** — a live FDX v6 implementation with a sandbox:
   https://docs.givechariot.com/fdx/introduction
   Sandbox base URL: `https://sandboxapi.givechariot.com/fdx/v6`
   (production: `https://api.givechariot.com/fdx/v6`). Cursor pagination
   (`pageKey`), date filtering, 24 months of data.
3. **APIs.io profile of the FDX API** — machine-readable OpenAPI 3.2.0
   (8 operations, 19 schemas) showing the JSON shapes:
   https://apis.apievangelist.com/store/joinslash-com-fdx-api/
4. **Open Banking Framework reference** — endpoint/scope table:
   https://www.openbankingframework.com/
5. **FDX itself:** https://financialdataexchange.org/ (full spec is
   members-only; FAPI background at https://openid.net/wg/fapi/).

## Databricks demo sketch

1. Run Mastercard's Fdx-Mock-Auth-Server + Fdx-Mock-Resource-Server locally
   (Docker) and seed synthetic accounts/transactions via the mock's Upload
   Data endpoints.
2. From a Databricks notebook: run the OAuth 2.0 authorization-code flow
   against the mock auth server (or client credentials for the demo), then
   call `/fdx/v6/accounts` and `/fdx/v6/accounts/{id}/transactions`.
3. Land raw JSON as Delta bronze tables, parse into typed silver tables
   (accounts, transactions), build a gold aggregate (spending by category,
   balances over time).
4. Demo the consent story, not just the data: token scopes map to data
   categories, consent is time-bound, and the flow replaces credential
   sharing (screen scraping) entirely.
5. Canadian angle for the narrative: the FDX Canada Council + Bank of Canada
   registry + OBSI complaints path is what makes this the Canadian framework,
   not just the US FDX standard.

## Open questions

- Whether the FDX Canada Council publishes Canada-specific deltas to the
  v6.0 spec (e.g., Interac rails, Canadian account types) — worth checking
  once the Council's materials appear.
- Whether FDX membership is needed for the full data dictionary if the demo
  needs exact field-level fidelity beyond what the mock servers expose.
