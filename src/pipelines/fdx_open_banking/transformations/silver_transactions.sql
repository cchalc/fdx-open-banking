-- Deduplicated transactions: re-fetching the same window updates rows instead of
-- duplicating them (pending -> posted transitions land as updates).
CREATE OR REFRESH STREAMING TABLE silver_transactions
COMMENT 'One row per FDX transaction (latest fetch wins).';

CREATE FLOW silver_transactions_cdc AS AUTO CDC INTO silver_transactions
FROM STREAM(transaction_records)
KEYS (account_id, transaction_id)
SEQUENCE BY fetched_at;
