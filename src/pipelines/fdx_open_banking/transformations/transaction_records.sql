-- Typed transactions from bronze. FDX wraps each transaction by account type
-- (depositTransaction, locTransaction, ...); land.py unwraps it into `record`.
CREATE TEMPORARY VIEW transaction_records AS
SELECT
  coalesce(raw:record.accountId::string, account_id) AS account_id,
  raw:record.transactionId::string AS transaction_id,
  record_type,
  raw:record.postedTimestamp::timestamp AS posted_ts,
  raw:record.transactionTimestamp::timestamp AS transaction_ts,
  raw:record.description::string AS description,
  raw:record.debitCreditMemo::string AS debit_credit_memo,
  raw:record.category::string AS category,
  raw:record.subCategory::string AS sub_category,
  raw:record.status::string AS status,
  raw:record.amount::decimal(18, 2) AS amount,
  CASE
    WHEN raw:record.debitCreditMemo::string = 'DEBIT' THEN -raw:record.amount::decimal(18, 2)
    ELSE raw:record.amount::decimal(18, 2)
  END AS signed_amount,
  source,
  fetched_at
FROM STREAM(bronze_fdx_records)
WHERE entity = 'transactions';
