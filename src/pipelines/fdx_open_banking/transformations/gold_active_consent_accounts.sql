-- Accounts currently covered by an ACTIVE, unexpired consent, per granted scope.
-- Gold tables join to this so revoked or expired consent drops data from analytics.
CREATE OR REFRESH MATERIALIZED VIEW gold_active_consent_accounts
COMMENT 'Account x scope pairs covered by an active consent right now.'
AS SELECT DISTINCT
  account_id,
  scope,
  consent_id,
  duration_type,
  expires_at
FROM silver_consents
LATERAL VIEW explode(account_ids) a AS account_id
LATERAL VIEW explode(scopes) s AS scope
WHERE __END_AT IS NULL
  AND status = 'ACTIVE'
  AND revoked_at IS NULL
  AND (expires_at IS NULL OR expires_at > current_timestamp());
