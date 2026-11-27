-- Current state of each consented account (SCD Type 1: latest fetch wins).
CREATE OR REFRESH STREAMING TABLE silver_accounts
COMMENT 'Latest known state of each FDX account.';

CREATE FLOW silver_accounts_cdc AS AUTO CDC INTO silver_accounts
FROM STREAM(account_records)
KEYS (account_id)
SEQUENCE BY fetched_at;
