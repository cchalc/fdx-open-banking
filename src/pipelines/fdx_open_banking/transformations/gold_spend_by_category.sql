-- Monthly spend (debits) by category, only for accounts whose TRANSACTIONS scope is
-- under active consent. Keeps the dimensions a dashboard filters by.
CREATE OR REFRESH MATERIALIZED VIEW gold_spend_by_category
COMMENT 'Monthly debit spend by account, category and currency (consented accounts only).'
AS SELECT
  date_trunc('MONTH', coalesce(t.posted_ts, t.transaction_ts)) AS month,
  t.account_id,
  a.account_type,
  a.currency_code,
  coalesce(t.category, 'UNCATEGORIZED') AS category,
  count(*) AS transaction_count,
  sum(t.amount) AS spend
FROM silver_transactions t
JOIN silver_accounts a ON a.account_id = t.account_id
WHERE t.debit_credit_memo = 'DEBIT'
  AND EXISTS (
    SELECT 1 FROM gold_active_consent_accounts c
    WHERE c.account_id = t.account_id AND c.scope = 'TRANSACTIONS'
  )
GROUP BY ALL;
