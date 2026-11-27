# Landing contract: FDX data → UC Volume

This is the interface between the Python landing step (`fdx_open_banking.land`, issue #3) and
the pipeline (`src/pipelines/fdx_open_banking`, issue #4). Change it in one PR that updates
both sides.

## Location

```
/Volumes/<catalog>/<schema>/<raw_volume>/fdx/<entity>/<YYYY-MM-DD>/<run_id>-<seq>.jsonl
```

- `entity` is one of `accounts`, `transactions`, or `consents`.
- Files are NDJSON (one JSON object per line), and once written they're never rewritten.
  A re-fetch writes new files. Silver deduplicates with Auto CDC.
- The pipeline reads everything under `.../fdx/` with Auto Loader (`fdx.raw_path`).

## Envelope (one per line)

```json
{
  "envelope_version": 1,
  "entity": "transactions",
  "record_type": "depositTransaction",
  "source": "mastercard-fdx-mock",
  "fetched_at": "2026-11-26T22:15:03Z",
  "account_id": "10001",
  "record": { "transactionId": "...", "postedTimestamp": "...", "amount": 42.5, "...": "..." }
}
```

| Field | Meaning |
|---|---|
| `envelope_version` | Contract version; bump it on breaking changes. |
| `entity` | Partition of the landing path, and the silver table it feeds. |
| `record_type` | The FDX wrapper key the record was unwrapped from (`depositAccount`, `locAccount`, `loanAccount`, `investmentAccount`, `depositTransaction`, ...). For consents it is `consent`. |
| `source` | Where it came from (`mastercard-fdx-mock`, `chariot-sandbox`, ...). |
| `fetched_at` | UTC ISO-8601 time of the API call. Silver uses it as the Auto CDC sequence. |
| `account_id` | The account the call was scoped to (null for account lists and consents). |
| `record` | The FDX object, **unwrapped** from its type key, with fields as the API returned them. |

## Consent records

FDX consent details come from the authorization side (the token grant, introspection, or a
consent API), not from the resource API. The landing step writes one `consents` record each
time it observes a grant:

```json
{
  "consentId": "c-123",
  "status": "ACTIVE",
  "durationType": "TIME_BOUND",
  "scopes": ["ACCOUNT_DETAILED", "TRANSACTIONS"],
  "accountIds": ["10001", "10002"],
  "clientId": "demo-data-recipient",
  "grantedAt": "2026-11-26T22:00:00Z",
  "expiresAt": "2027-02-24T22:00:00Z",
  "revokedAt": null
}
```

Status values are `ACTIVE`, `EXPIRED`, and `REVOKED`. Revoking a grant means writing a new
record with `status: "REVOKED"` and `revokedAt` set. `silver_consents` (SCD Type 2) keeps the
history, and gold tables drop the account from analytics.
