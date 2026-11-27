# Running the Mastercard FDX mock servers under podman

Status: research notes, 2026-11-26. Sources are the upstream repos and their files, cited inline. Nothing was cloned, built or run; the curl sequence and compose file are from reading source and are **unverified at runtime** unless marked otherwise. Repo-relative file names below are paths inside the upstream repos.

Repos:
- Auth server: https://github.com/Mastercard/Fdx-Mock-Auth-Server (last push per GitHub API: 2026-09-29)
- Resource server: https://github.com/Mastercard/Fdx-Mock-Resource-Server (last push per GitHub API: 2026-11-10)

## 1. License

- Both repos ship `LICENSE.md` with the full Apache License 2.0 text, and GitHub reports `spdx_id: Apache-2.0` for each:
  - https://github.com/Mastercard/Fdx-Mock-Resource-Server/blob/main/LICENSE.md
  - https://github.com/Mastercard/Fdx-Mock-Auth-Server/blob/main/LICENSE.md
- **Conflict:** the resource server README says, under "License": "This is an open-source project and does not have any specific licensing." https://github.com/Mastercard/Fdx-Mock-Resource-Server/blob/main/README.md. Treat the Apache-2.0 `LICENSE.md` as the operative license and note the discrepancy.
- Redistribution of the mock code under Apache-2.0 is a separate question from the FDX spec (see `spec-sources.md`). The mock repos include FDX-derived JSON fixtures (for example `src/main/resources/json/*.json`) and a committed PEM key (`src/main/resources/dh/dhpk.txt`); this runbook does not reproduce either.

## 2. Images: published or build from source

- **No published image found.** Neither repo has a `.github/` directory (both return 404 to `gh api .../contents/.github`), so there is no CI workflow that publishes images. I could not check GHCR or Docker Hub for `Mastercard/*` packages (the GitHub token lacks `read:packages`). Treat **published images as unverified**, and build from source.
- Build instructions are in each README: `docker build -t fdx-mock-resource-server .` and `docker run -d --network=my-network -p 8080:8080 --name fdx.mock.auth.server fdx-mock-auth-server` (resource server analogue on 9090). https://github.com/Mastercard/Fdx-Mock-Resource-Server/blob/main/README.md
- **Base images and Java:**
  - Both Dockerfiles use a Maven build stage `FROM maven:3-openjdk-17 as build`, then a runtime stage `FROM alpine:3.17.3 as deploy` that installs `openjdk17-jre` with `apk`.
  - Auth server Dockerfile: https://github.com/Mastercard/Fdx-Mock-Auth-Server/blob/main/Dockerfile. Resource server Dockerfile: https://github.com/Mastercard/Fdx-Mock-Resource-Server/blob/main/Dockerfile.
  - Java 17: both poms set `<java.version>17</java.version>`. Resource server pom: https://github.com/Mastercard/Fdx-Mock-Resource-Server/blob/main/pom.xml (Spring Boot 3.4.5). Auth server pom: https://github.com/Mastercard/Fdx-Mock-Auth-Server/blob/main/pom.xml (Spring Boot 3.3.11).
- **Things that will break or rot:**
  - Alpine 3.17 reached end of support on 2024-11-22 ("on request" only after that). https://www.alpinelinux.org/releases/ . Replace the runtime base image (for example a current Alpine or a Temurin JRE image) and check that `apk add openjdk17-jre` still resolves on the new base. **Unverified** for any specific replacement.
  - The `openjdk` official image on Docker Hub is officially deprecated and the docs recommend replacements such as `eclipse-temurin`. https://github.com/docker-library/openjdk/blob/master/README.md . So `maven:3-openjdk-17` may be stale. Suggested replacement `maven:3-eclipse-temurin-17` is **unverified** (I did not fetch the Docker Hub tag page).
- **Build stage needs the network.** The auth server pom includes `frontend-maven-plugin` (v1.12.1) that installs Node `v18.12.0` and Yarn `v1.22.19` and runs `yarn install` and a build of `src/main/frontend` during `package`. https://github.com/Mastercard/Fdx-Mock-Auth-Server/blob/main/pom.xml . Expect outbound downloads during `podman build`; corporate proxies or TLS interception are a likely failure point. The resource server pom does not include a frontend plugin.
- `Dockerfile` runtime stage runs as a non-root user `app` (`adduser app ... USER app`). Rootless podman is fine with that; no privileged ports are used (8080, 9090).

## 3. Ports, config, and how the two servers find each other

| | Auth server | Resource server |
|---|---|---|
| Port | `server.port=8080` (`EXPOSE 8080 8081`) | `server.port=9090` (`EXPOSE 9090 9091`) |
| Health | `GET /health` | `GET /health` |
| DB | H2 in memory (`jdbc:h2:mem:testdb`), schema from `scripts/sql/*.sql` at boot | H2 in memory (`jdbc:h2:mem:mockResourceServer`), `ddl-auto=create` |
| Container start CMD | `java --add-opens java.base/java.io=ALL-UNNAMED -jar app.jar` | `java -jar` (shell form) |

Sources: https://github.com/Mastercard/Fdx-Mock-Auth-Server/blob/main/src/main/resources/application.properties ; https://github.com/Mastercard/Fdx-Mock-Resource-Server/blob/main/src/main/resources/application.properties ; https://github.com/Mastercard/Fdx-Mock-Auth-Server/blob/main/src/main/java/com/mastercard/fdx/mock/oauth2/server/config/H2DbConfig.java ; health controllers: https://github.com/Mastercard/Fdx-Mock-Resource-Server/blob/main/src/main/java/com/mastercard/fdx/mock/controller/ApplicationCheckController.java and https://github.com/Mastercard/Fdx-Mock-Auth-Server/blob/main/src/main/java/com/mastercard/fdx/mock/oauth2/server/controller/ApplicationCheckController.java .

Both use in-memory H2, so **all data resets on every container restart**. The resource server's `DataLoader` reloads the fixture users and accounts at each boot (https://github.com/Mastercard/Fdx-Mock-Resource-Server/blob/main/src/main/java/com/mastercard/fdx/mock/config/DataLoader.java), so your own seeds must be re-applied after a restart.

### Config keys that matter (defaults are all `localhost`)

Defaults in the upstream files point everything at `localhost`. Inside containers that breaks, so set these as environment variables. Spring maps `mock.auth.server.baseurl` to `MOCK_AUTH_SERVER_BASEURL`, and so on; env vars override the properties files.

Auth server (`application.properties`):
- `mock.auth.server.baseurl=http://localhost:8080`: this is the **issuer** (`iss`) written into tokens, from `providerSettings().issuer(props.getAuthServerBaseUrl())` in https://github.com/Mastercard/Fdx-Mock-Auth-Server/blob/main/src/main/java/com/mastercard/fdx/mock/oauth2/server/config/AuthorizationServerConfig.java
- `mock.auth.server.baseSecureUrl`, `mock.auth.server.consent_uri=http://localhost:8080/consent`
- `mock.res.server.baseurl=http://localhost:9090`: where the AS calls the RS for consent (`/consent/accounts`, `/consent`).
- `mock.res.server.userurl=http://localhost:9090/user`: where the AS looks up users for login. Source: https://github.com/Mastercard/Fdx-Mock-Auth-Server/blob/main/src/main/java/com/mastercard/fdx/mock/oauth2/server/security/user/FdxUserService.java
- `mock.res.server.auth.code=test_auth_code`: the shared "internal" token the AS sends to the RS.

Resource server (`application.properties`):
- `mock.auth.server.url=http://localhost:8080`: base URL the RS uses to fetch JWKS (`mock.auth.server.url + /oauth2/jwks`). Source: https://github.com/Mastercard/Fdx-Mock-Resource-Server/blob/main/src/main/java/com/mastercard/fdx/mock/interceptor/AuthorizationInterceptor.java
- `mock.auth.issuer.url=${mock.auth.server.url}`: expected `iss` claim. Same file.
- `mock.auth.server.jwks.uri.path=/oauth2/jwks`
- `mock.res.server.auth.code=test_auth_code`

The RS README's Docker instructions say to uncomment `mock.auth.issuer.url=http://localhost:8080` and `mock.auth.server.url=http://fdx.mock.auth.server:8080`. Those commented lines are already in the file. The README's build instructions are at https://github.com/Mastercard/Fdx-Mock-Resource-Server/blob/main/README.md

**Key design point:** the issuer must stay `http://localhost:8080`, because the host-side httpx client gets tokens from `localhost:8080` and the RS checks `iss` against `MOCK_AUTH_ISSUER_URL`. The RS must fetch JWKS from the service name `http://fdx-auth:8080`. The two values are different on purpose. Source for the `iss` check: `AuthorizationInterceptor.java` above.

### How they find each other

1. **RS to AS (token validation):** the RS fetches `…/oauth2/jwks` from `MOCK_AUTH_SERVER_URL` and verifies PS256 JWTs with `typ` `JWT` or `at+jwt`, and `iss` equal to `MOCK_AUTH_ISSUER_URL`. Sources: `AuthorizationInterceptor.java` (above); the AS JWKS and kids in https://github.com/Mastercard/Fdx-Mock-Auth-Server/blob/main/src/main/java/com/mastercard/fdx/mock/oauth2/server/common/ApplicationConstant.java
2. **AS to RS (login and consent):** the AS calls the RS at `MOCK_RES_SERVER_USERURL` and `MOCK_RES_SERVER_BASEURL`, sending `Authorization: test_auth_code` (raw, no `Bearer`). The RS validates that exact string for `/user` and `/consent` (`RequestInterceptor.java`, https://github.com/Mastercard/Fdx-Mock-Resource-Server/blob/main/src/main/java/com/mastercard/fdx/mock/interceptor/RequestInterceptor.java , and `security-interceptor.properties`).

## 4. Auth server

### Grants, endpoints

Registered clients carry the grant types `refresh_token`, `client_credentials`, `authorization_code`. PKCE is required and consent is required (`settings.client.require-proof-key: true`, `require-authorization-consent: true`). Source: https://github.com/Mastercard/Fdx-Mock-Auth-Server/blob/main/src/main/resources/scripts/sql/add-dh-adr-client-registrar.sql

| Path | Method | Purpose / source |
|---|---|---|
| `/.well-known/openid-configuration` | GET | OIDC discovery (Postman "OIDC Discovery document") |
| `/oauth2/jwks` | GET | Signing keys, PS256 and RS256 (`jwkSetEndpoint`, `AuthorizationServerConfig.java`) |
| `/oauth2/authorize` | GET | Authorization code, PKCE (Postman "Non PAR Authorize") |
| `/login` | GET/POST | Spring form login, backed by RS `/user/{id}` (`formLogin(withDefaults())`, `DefaultSecurityConfig.java`) |
| `/consent` | GET | Consent UI page; lists accounts via RS (`AccountConsentController.java`) |
| `/consent` | POST | Registers consent; needs an authenticated session and a `Cookie` header |
| `/consent/accounts` | GET | Lists accounts for the logged-in user |
| `/oauth2/token` | POST | Token endpoint (`AuthServerService.java` uses `/oauth2/token`). Note `ApplicationConstant` also defines `/oauth2/v1/token`, which is not the Spring endpoint. |
| `/oauth2/par` | POST | Pushed Authorization Request (`PushedAuthorizationRequestController.java`) |
| `/oauth2/introspect` | POST | Introspection (constant `OAUTH2_INTROSPECT_URI`, Postman "Introspection") |
| `/revoke` | POST | Default revocation endpoint (constant `DEFAULT_TOKEN_REVOCATION_ENDPOINT_URI`) |
| `/fdx/v6/register` | POST | Dynamic client registration; `permitAll` in `DefaultSecurityConfig.java` |
| `/fdx/v6/register/{clientId}` | GET, PUT, DELETE | DCR management; `Authorization` header required (`DynamicClientRegistrationController.java`) |
| `/fdx/v6/consents/{consentId}` | GET | Consent read (`ConsentController.java`) |
| `/fdx/v6/consents/{consentId}/revocation` | PUT | Consent revoke |
| `/h2` | GET | H2 console (`H2DbConfig`, `DefaultSecurityConfig.allowH2`) |

Sources for the table: https://github.com/Mastercard/Fdx-Mock-Auth-Server/tree/main/src/main/java/com/mastercard/fdx/mock/oauth2/server/controller and the Postman collection at https://github.com/Mastercard/Fdx-Mock-Auth-Server/blob/main/src/main/resources/postman/FDX%20Developer%20Hub.postman_collection.json

The `permitAll` list in `DefaultSecurityConfig.java` also names `/add-accounts` and `/connect/register`. I found no controller for `/add-accounts` in the source tree, so treat it as **unverified** (not implemented).

Access tokens: `access-token-time-to-live` 300 s, refresh tokens 3600 s, access token format `self-contained` (a JWT), per the SQL client settings above. Tokens carry `fdxConsentId`, `sharing_expires_at` and `account_id` (an array of consented account IDs) claims, added in `AuthorizationServerConfig.addConsentClaims`. The RS uses `account_id` to authorize each account request: https://github.com/Mastercard/Fdx-Mock-Auth-Server/blob/main/src/main/java/com/mastercard/fdx/mock/oauth2/server/config/AuthorizationServerConfig.java and https://github.com/Mastercard/Fdx-Mock-Resource-Server/blob/main/src/main/java/com/mastercard/fdx/mock/service/FdxResourceService.java

### Default clients, users, keys (all public mock defaults)

- **Client `dh-fdx-client-registrar-1`:** `client_secret_basic`. Secret `secret` according to `application.properties` (`mock.auth.server.dh.clientId` and `clientSecret`) and the Postman environment (`clientSecret = secret`). The stored value is a bcrypt hash, and I did not verify that it matches `secret`; **unverified**. Registered redirect URI: `https://oauth.pstmn.io/v1/browser-callback` only. Scopes include `openid`, `fdx:accountbasic:read`, `fdx:accountdetailed:read`, `fdx:transactions:read`, `fdx:customercontact:read` and others.
- **Client `dh-fdx-client-registrar-2`:** `private_key_jwt`, `token-endpoint-authentication-signing-algorithm` PS256. Its client JWK set is fetched from `https://www.jsonkeeper.com/b/3FJT`, an **external** URL. Token issuance therefore needs internet access, and whether that URL is still live is **unverified**. Source: the SQL file above.
- **Users:** `fdxuser`, `fdxuser1`, `fdxuser2`, `fdxuser3`, all with password `password` (`DataLoader.java` `pwd = "password"`, https://github.com/Mastercard/Fdx-Mock-Resource-Server/blob/main/src/main/java/com/mastercard/fdx/mock/config/DataLoader.java).
- **Accounts:** `fdxuser` consents to `10001, 20001, 3746272, 5326884` (`DataLoader.java` line 117). `fdxuser1` has `6468990, 4568922, 500011` (line 192). The accounts for `fdxuser2` and `fdxuser3` were not extracted.
- **Signing keys:** RSA PEM at `src/main/resources/dh/dhpk.txt` (committed to the repo) is loaded in `AuthorizationServerConfig.jwkSource()`. Kids: PS256 `99bc33ee-a04d-4a89-8ae0-5debd2145aab`, RS256 `372f1117-21ec-41db-a5ab-3bebdd5faac4` (`ApplicationConstant.java`). Do not reproduce the key in your repo; use the upstream one, or generate a fresh key and set the matching kids.
- **Internal token:** `test_auth_code` (`mock.res.server.auth.code`).

### Authorization-code flow (the only way to get account-scoped tokens)

A client-credentials token has no `account_id` claim, so account requests on the RS are refused ("Invalid Token", error 1003) or return an empty list. The account-scoped token needs an authorization-code flow with a consent step. The Postman collection is the reference: "Non PAR Authorize" issues `GET {{host}}/oauth2/authorize?client_id=…&response_type=code&code_challenge=…&code_challenge_method=S256&scope=…&redirect_uri=…&state=…`, then the browser logs in and the consent page picks accounts. https://github.com/Mastercard/Fdx-Mock-Auth-Server/blob/main/src/main/resources/postman/FDX%20Developer%20Hub.postman_collection.json . The consent step is UI-driven and its exact parameters are **unverified** for a headless curl run; plan on using a browser once.

## 5. Resource server

### Endpoints

Base `http://localhost:9090`. Source: https://github.com/Mastercard/Fdx-Mock-Resource-Server/blob/main/src/main/java/com/mastercard/fdx/mock/controller/FdxResourceServerController.java

| Method | Path | Auth | Behaviour (source) |
|---|---|---|---|
| GET | `/fdx/v6/accounts` | Bearer JWT | Accounts whose IDs are in the token's `account_id` claim (`getAccountsList`) |
| GET | `/fdx/v6/accounts/{accountId}` | Bearer | `AccountDescriptor`; 400 "Invalid Token" (1003) if the ID is not in the token (`validateTokenWithRequestAccountId`) |
| GET | `/fdx/v6/accounts/{accountId}/contact` | Bearer | `AccountContact` (holders) |
| GET | `/fdx/v6/accounts/{accountId}/transactions` | Bearer | All transactions for the account; `startTime`/`endTime` headers read but **not used** |
| GET | `/fdx/v6/accounts/{accountId}/payment-networks` | Bearer | Payment networks list |
| GET | `/fdx/v6/accounts/{accountId}/statements` | Bearer | Statement list |
| GET | `/fdx/v6/accounts/{accountId}/statements/{statementId}` | Bearer | Statement PDF bytes (`statement.getFile()`) |
| GET | `/consent/accounts?userId=` | Internal `test_auth_code` | Used by AS consent UI |
| POST | `/consent` | Internal | Register consent (`AccountConsentController.java`, RS) |
| GET, PUT | `/consent/{consentId}` | Internal | Read or amend consent |
| GET | `/user/{userId}` | Internal | Used by AS login (`FdxUserDetailsController.java`) |
| POST | `/user` | Internal | Create user; body `{"userId": "...", "password": "..."}`; hashes the password, 409 if the user exists (`FdxUserService.saveUser`) |
| POST | `/upload/addAccount?userId=` | **None** | Seed accounts (section 6) |
| POST | `/upload/addTransactions` | **None** | Seed transactions (section 6) |
| GET | `/health`, `/startupStatus`, `/livenessProbe` | None | Health |

Auth rules come from `AuthorizationInterceptor` (JWT on `/fdx/v6`) and `RequestInterceptor` (internal token on `/consent` and `/user`, and `/upload` is excluded) with `intercept.int.res.server.excluded.urls` including `/upload` (`application.properties`).

- **Customers:** there is no `/customers` endpoint. The controller has no customer path and the repo tree has no customer file (checked). The nearest is `/accounts/{accountId}/contact`.
- **Pagination:** none. `FdxResourceService` only sets `page.total`. The `Page` DTO has a `nextOffset` field that is never set, and no `pageKey` or `limit` parameter exists: https://github.com/Mastercard/Fdx-Mock-Resource-Server/blob/main/src/main/java/com/mastercard/fdx/mock/dto/Page.java
- **Date filters:** `startTime` and `endTime` are `@RequestHeader` values on the transactions handler, and `getTransactions(accountId)` ignores them. So the mock does not filter by date. Chariot's sandbox documents `startTime`/`endTime` as `YYYY-MM-DD` (see `spec-sources.md`). The mock's header-based design is a real divergence to keep in mind.

### Upload Data (seeding)

Source: https://github.com/Mastercard/Fdx-Mock-Resource-Server/blob/main/src/main/java/com/mastercard/fdx/mock/controller/DataUploadController.java and `service/DataUploadService.java` (same tree). Both endpoints are unauthenticated.

**`POST /upload/addAccount?userId=<existing user>`**
- Body: a JSON **array**. Each element needs `accountCategory`, one of `DEPOSIT_ACCOUNT`, `LOAN_ACCOUNT`, `INVESTMENT_ACCOUNT`, `LOC_ACCOUNT`. The element's `accountId` is stored as the unique `institutionAccountId` (`AccountDescriptor.java`: `@JsonProperty("accountId") @Column(unique = true)`).
- `userId` must already exist (`validateUserId`), otherwise HTTP 400 with `errorCode` 1001 "No User Found". Create a user first with `POST /user` (internal token).
- Accounts are appended to the user's existing consent list (`DataUploadService.addAccount`).
- Success body: `{"code":0,"message":"Success"}` (`DataUploadResponsePojo`).
- **Postman quirk:** the collection calls `…/upload/addAccount?accountCategory=DEPOSIT_ACCOUNT&userId=fdxuser1`. The controller only takes `userId`, so the extra query param is ignored.
- Re-using an `accountId` that already exists (for example `10001` for `fdxuser`) hits the unique constraint. The code catches that and returns HTTP 500 with `errorCode` 1004 (`DataUploadService` generic catch). **Inferred from source; not run.**

**`POST /upload/addTransactions`**
- Body: a JSON **array** of `TransactionsDetails` (https://github.com/Mastercard/Fdx-Mock-Resource-Server/blob/main/src/main/java/com/mastercard/fdx/mock/transaction/dto/TransactionsDetails.java). Key fields: `accountId`, `accountCategory`, `transactionId`, `transactionType`, `postedTimestamp`, `transactionTimestamp` (ISO 8601 strings), `description`, `status`, `amount`, optional `memo`, `category`, `payee`.
- `accountId` is not validated against existing accounts. `transactionId` is not unique and the row `id` is an identity column, so **re-posting creates duplicates** (`TransactionsRepository` is a plain `JpaRepository`).
- Success body: `{"code":0,"message":"Success"}`.

**Request example, verbatim shape:**

```bash
curl -sS -X POST 'http://localhost:9090/upload/addAccount?userId=fdxuser' \
  -H 'Content-Type: application/json' \
  -d '[{
        "accountId": "900001",
        "accountCategory": "DEPOSIT_ACCOUNT",
        "accountType": "CHECKING",
        "nickname": "Demo Checking",
        "status": "OPEN",
        "productName": "Demo",
        "description": "Demo checking account",
        "accountNumber": "7000900001",
        "accountNumberDisplay": "0001",
        "currentBalance": 1234.56,
        "availableBalance": 1234.56,
        "currency": {"currencyCode": "USD", "originalCurrencyCode": "USD"}
      }]'
```

Field names are taken from the fixture `deposit_acc_details.json` (https://github.com/Mastercard/Fdx-Mock-Resource-Server/blob/main/src/main/resources/json/deposit_acc_details.json). Which fields are strictly required is **unverified**.

```bash
curl -sS -X POST 'http://localhost:9090/upload/addTransactions' \
  -H 'Content-Type: application/json' \
  -d '[{
        "accountId": "900001",
        "accountCategory": "DEPOSIT_ACCOUNT",
        "transactionId": "demo-txn-0001",
        "transactionType": "POSDEBIT",
        "postedTimestamp": "2026-11-01T12:00:00.000Z",
        "transactionTimestamp": "2026-11-01T12:00:00.000Z",
        "description": "Demo coffee",
        "status": "POSTED",
        "amount": -4.50
      }]'
```

### Example responses (fixtures as the mock returns them)

These are the fixture JSON files the mock loads at boot. The live response is the Jackson serialisation of the same entities, so field order and null handling may differ. **Unverified** against a live run.

Account (`GET /fdx/v6/accounts/10001`), trimmed from `deposit_acc_details.json`:

```json
{
  "accountId": "10001",
  "accountCategory": "DEPOSIT_ACCOUNT",
  "accountType": "CHECKING",
  "displayName": "******3223",
  "status": "OPEN",
  "productName": "Cash Management",
  "currency": {"currencyRate": null, "currencyCode": "USD", "originalCurrencyCode": "USD"},
  "description": "My Checking Acc XXXX3223",
  "nickname": "My Checking Acc XXXX3223",
  "accountNumber": "7000003223",
  "accountNumberDisplay": "3223",
  "routingTransitNumber": "256074974",
  "balanceType": "ASSET",
  "transactionsIncluded": false,
  "currentBalance": 4984.46,
  "availableBalance": 4984.46,
  "fiAttributes": [
    {"name": "interestPaidLastYear", "value": "14.08"},
    {"name": "interestPayoutFrequency", "value": "Annually (And At Maturity)"}
  ]
}
```

Source: https://github.com/Mastercard/Fdx-Mock-Resource-Server/blob/main/src/main/resources/json/deposit_acc_details.json (the fixture also has `interestYtd`, `maturityDate` and other fields, elided here). The internal `accountId` (int) is `@JsonIgnore`d, and the public `accountId` is `institutionAccountId` (`AccountDescriptor.java`).

Transaction (`GET /fdx/v6/accounts/10001/transactions`), from `depositTransaction.json` (https://github.com/Mastercard/Fdx-Mock-Resource-Server/blob/main/src/main/resources/json/depositTransaction.json):

```json
{
  "page": {"total": 4},
  "transactions": [
    {
      "accountId": "10001",
      "accountCategory": "DEPOSIT_ACCOUNT",
      "transactionId": "5705141948",
      "postedTimestamp": "2019-02-26T12:00:00.000Z",
      "transactionTimestamp": "2019-02-26T12:00:00.000Z",
      "description": "VENMO CASHOUT",
      "debitCreditMemo": "CREDIT",
      "status": "POSTED",
      "amount": 101.72,
      "transactionType": "POSCREDIT",
      "checkNumber": 45400222,
      "payee": "Test User"
    }
  ]
}
```

The fixture has four transactions; one is shown. There is no `pageKey`, no `links`, and the `page` object only has `total`.

## 6. Podman, arm64 and rootless gotchas

- **Base images:** Alpine 3.17 is EOL and `maven:3-openjdk-17` is deprecated (section 2). Expect to swap both before a build is reliable.
- **Build network:** the auth server build downloads Node and Yarn (section 2). Podman's default build network needs outbound access; behind a proxy, pass `--build-arg`/proxy env through.
- **Service-name wiring:** the defaults are `localhost`, which inside a container means the container itself. Set the env vars in the compose snippet below, otherwise the RS cannot fetch JWKS and the AS cannot reach the RS. Tokens still need `iss=http://localhost:8080`.
- **Network DNS:** service names resolve on the compose default network. The README's own `docker network create` example uses container names (https://github.com/Mastercard/Fdx-Mock-Resource-Server/blob/main/README.md). Confirm DNS on your podman version; **unverified** here.
- **Port 8080 on macOS:** commonly used by other tools. Pick another host port if needed, but keep the issuer at `http://localhost:8080` or change `MOCK_AUTH_SERVER_BASEURL` and `MOCK_AUTH_ISSUER_URL` together, consistently.
- **Outbound at token time:** `dh-fdx-client-registrar-2` fetches its JWK set from `https://www.jsonkeeper.com/b/3FJT` (section 4). Use `dh-fdx-client-registrar-1` (client_secret_basic) to avoid that dependency.
- **Restart wipes data:** H2 is in memory, so re-seed after every restart (section 5).
- **arm64:** neither pom contains native dependencies that I could see. Nimbus, BouncyCastle and JaCoCo are pure Java. The base image architecture coverage is **unverified**. Avoid forcing `--platform linux/amd64` (emulation is slow and unnecessary if the base images are multi-arch).
- **Startup time:** Spring Boot with JPA and a Thymeleaf UI can take a while. Use healthchecks (below) rather than sleeps.
- **Logging:** both configs set `spring.jpa.show-sql=true` (and `format_sql` on the RS), so logs are noisy.
- **Java 17 reflection:** the auth server's `CMD` adds `--add-opens java.base/java.io=ALL-UNNAMED`, and the resource server's does not. Keep the flag if you hit reflection errors.
- **Runtime stage:** the resource server's `CMD java -jar ...` is shell form, so the JVM is not PID 1 and `podman stop` may wait out the default timeout. Harmless for a mock.

## 7. Suggested `compose.yaml`

Put it outside `vendor/` (for example at the repo root) and clone the upstream sources into `vendor/` (gitignored, see `spec-sources.md`). Image names are local tags; no upstream image exists to pull.

```yaml
name: fdx-mock

services:
  fdx-auth:
    build:
      context: ./vendor/Fdx-Mock-Auth-Server
      # swap the base images in the Dockerfile first (Alpine 3.17 is EOL, see mock-servers.md section 2)
    image: localhost/fdx-mock-auth-server:local
    ports:
      - "8080:8080"
    environment:
      # issuer (iss) must stay localhost so host-side clients and the RS agree on it
      MOCK_AUTH_SERVER_BASEURL: http://localhost:8080
      MOCK_AUTH_SERVER_BASESECUREURL: http://localhost:8080
      MOCK_AUTH_SERVER_CONSENT_URI: http://localhost:8080/consent
      # AS -> RS calls use the compose service name
      MOCK_RES_SERVER_BASEURL: http://fdx-resource:9090
      MOCK_RES_SERVER_USERURL: http://fdx-resource:9090/user
    healthcheck:
      test: ["CMD", "curl", "-fsS", "http://localhost:8080/health"]
      interval: 5s
      timeout: 3s
      retries: 40

  fdx-resource:
    build:
      context: ./vendor/Fdx-Mock-Resource-Server
    image: localhost/fdx-mock-resource-server:local
    ports:
      - "9090:9090"
    environment:
      # RS fetches JWKS from the AS service name...
      MOCK_AUTH_SERVER_URL: http://fdx-auth:8080
      # ...but expects tokens whose iss is the localhost issuer
      MOCK_AUTH_ISSUER_URL: http://localhost:8080
    depends_on:
      fdx-auth:
        condition: service_healthy
    healthcheck:
      test: ["CMD", "curl", "-fsS", "http://localhost:9090/health"]
      interval: 5s
      timeout: 3s
      retries: 40
```

Notes: the healthcheck relies on `curl`, which both Dockerfiles install. `depends_on` with `service_healthy` needs a compose implementation that supports it (`podman compose` with a compose provider, or `podman-compose`); **unverified** for your setup. Build with `podman compose up -d --build`. To build without compose: `podman build -t localhost/fdx-mock-auth-server:local vendor/Fdx-Mock-Auth-Server`.

To fetch the sources (run by you; not done here): `gh repo clone Mastercard/Fdx-Mock-Auth-Server vendor/Fdx-Mock-Auth-Server` and the same for the resource server.

## 8. Seed, then fetch: curl sequence

Steps 1–3 use only endpoints and bodies verified from source. Steps 4–5 (token) are **unverified end-to-end**; plan to do the consent step in a browser once.

```bash
# 0) Health (both should return 200)
curl -fsS http://localhost:9090/health
curl -fsS http://localhost:8080/health

# 1) Seed an account for the existing user fdxuser (no auth on /upload)
curl -sS -X POST 'http://localhost:9090/upload/addAccount?userId=fdxuser' \
  -H 'Content-Type: application/json' \
  -d '[{"accountId":"900001","accountCategory":"DEPOSIT_ACCOUNT","accountType":"CHECKING",
        "nickname":"Demo Checking","status":"OPEN","productName":"Demo",
        "description":"Demo checking account","accountNumber":"7000900001",
        "accountNumberDisplay":"0001","currentBalance":1234.56,"availableBalance":1234.56,
        "currency":{"currencyCode":"USD"}}]'
# expect: {"code":0,"message":"Success"}

# 2) Seed a transaction for it (body is an array)
curl -sS -X POST 'http://localhost:9090/upload/addTransactions' \
  -H 'Content-Type: application/json' \
  -d '[{"accountId":"900001","accountCategory":"DEPOSIT_ACCOUNT","transactionId":"demo-txn-0001",
        "transactionType":"POSDEBIT","postedTimestamp":"2026-11-01T12:00:00.000Z",
        "transactionTimestamp":"2026-11-01T12:00:00.000Z","description":"Demo coffee",
        "status":"POSTED","amount":-4.50}]'
# expect: {"code":0,"message":"Success"}

# 3) Check the seed through the internal endpoint (internal token, not a JWT)
curl -sS 'http://localhost:9090/consent/accounts?userId=fdxuser' \
  -H 'Authorization: test_auth_code'
# expect 900001 to appear in the list (unverified response shape)

# 4) Get an account-scoped token: authorization code + PKCE (UNVERIFIED end-to-end)
VERIFIER=$(python3 -I -c 'import secrets; print(secrets.token_urlsafe(64))')
CHALLENGE=$(python3 -I -c 'import base64,hashlib,sys; d=hashlib.sha256(sys.argv[1].encode()).digest(); print(base64.urlsafe_b64encode(d).rstrip(b"=").decode())' "$VERIFIER")
echo "Open in a browser and log in as fdxuser / password, then select accounts in the consent UI:"
echo "http://localhost:8080/oauth2/authorize?client_id=dh-fdx-client-registrar-1&response_type=code&code_challenge=${CHALLENGE}&code_challenge_method=S256&scope=openid%20fdx:accountbasic:read%20fdx:transactions:read&redirect_uri=https://oauth.pstmn.io/v1/browser-callback&state=demo123"
# The browser then redirects to https://oauth.pstmn.io/v1/browser-callback?code=...&state=demo123.
# Copy the code from the address bar; the page itself does not need to load.
CODE='PASTE_CODE_HERE'

curl -sS -u 'dh-fdx-client-registrar-1:secret' http://localhost:8080/oauth2/token \
  -d grant_type=authorization_code \
  -d "code=${CODE}" \
  -d redirect_uri=https://oauth.pstmn.io/v1/browser-callback \
  -d "code_verifier=${VERIFIER}"
# expect JSON with access_token (300 s) and refresh_token (3600 s)

# 5) Fetch seeded data with the bearer token
TOKEN='PASTE_ACCESS_TOKEN_HERE'
curl -sS http://localhost:9090/fdx/v6/accounts -H "Authorization: Bearer ${TOKEN}"
curl -sS http://localhost:9090/fdx/v6/accounts/900001 -H "Authorization: Bearer ${TOKEN}"
curl -sS http://localhost:9090/fdx/v6/accounts/900001/transactions -H "Authorization: Bearer ${TOKEN}"
# Date filters: the mock reads these as headers and ignores them
curl -sS http://localhost:9090/fdx/v6/accounts/900001/transactions -H "Authorization: Bearer ${TOKEN}" \
  -H 'startTime: 2026-10-01' -H 'endTime: 2026-11-30'
```

Caveats for steps 4–5:
- `900001` is only visible through the token if the consent UI selected it. That depends on the RS listing it via `/consent/accounts` (step 3). **Unverified.**
- The `code_verifier` must match the challenge. The client is `client_secret_basic`, and the secret `secret` is the upstream default (hash unverified).
- Use `fdxuser` (not a new user) so the seeded account joins an account list that already has a working consent path.

## 9. Not verified

- Any live run: nothing was built, started or called.
- Published images on Docker Hub or GHCR (not searchable with the current token scope).
- Whether `secret` matches the stored bcrypt hash for `dh-fdx-client-registrar-1`.
- Whether `https://www.jsonkeeper.com/b/3FJT` is still live.
- The exact consent UI parameters needed for a headless flow, and whether `/add-accounts` exists (no controller found).
- Whether `maven:3-eclipse-temurin-17` and the replacement Alpine packages exist as named.
- Exact required fields for `addAccount`; the JSON response of `/consent/accounts`.
- Whether the Mastercard YAML specs themselves are needed for this runbook (they are not; the mock is described by its own controllers). See `spec-sources.md` for the redistribution question.
