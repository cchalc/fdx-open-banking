-- Every balance observation, append-only, for balances-over-time.
CREATE OR REFRESH STREAMING TABLE silver_account_balances (
  CONSTRAINT has_account EXPECT (account_id IS NOT NULL) ON VIOLATION DROP ROW
)
COMMENT 'Balance snapshots per account per fetch.'
AS SELECT
  account_id,
  account_type,
  currency_code,
  current_balance,
  available_balance,
  balance_as_of,
  fetched_at
FROM STREAM(account_records);
