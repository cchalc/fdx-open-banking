-- Consent grants as recorded by the data recipient at fetch time
-- (scopes, duration, covered accounts, expiry/revocation).
CREATE TEMPORARY VIEW consent_records AS
SELECT
  raw:record.consentId::string AS consent_id,
  raw:record.status::string AS status,
  raw:record.durationType::string AS duration_type,
  raw:record.scopes::array<string> AS scopes,
  raw:record.accountIds::array<string> AS account_ids,
  raw:record.clientId::string AS client_id,
  raw:record.grantedAt::timestamp AS granted_at,
  raw:record.expiresAt::timestamp AS expires_at,
  raw:record.revokedAt::timestamp AS revoked_at,
  fetched_at
FROM STREAM(bronze_fdx_records)
WHERE entity = 'consents';
