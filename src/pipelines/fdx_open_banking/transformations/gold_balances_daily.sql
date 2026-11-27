-- End-of-day balance per account (last observation that day), consented accounts only.
CREATE OR REFRESH MATERIALIZED VIEW gold_balances_daily
COMMENT 'Daily closing balance per account (consented accounts only).'
AS SELECT
  b.account_id,
  b.account_type,
  b.currency_code,
  to_date(b.balance_as_of) AS balance_date,
  max_by(b.current_balance, b.balance_as_of) AS current_balance,
  max_by(b.available_balance, b.balance_as_of) AS available_balance
FROM silver_account_balances b
WHERE EXISTS (
  SELECT 1 FROM gold_active_consent_accounts c
  WHERE c.account_id = b.account_id AND c.scope IN ('ACCOUNT_BASIC', 'ACCOUNT_DETAILED')
)
GROUP BY ALL;
