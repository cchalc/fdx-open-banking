-- Typed transactions from bronze. Sources disagree on shape: FDX puts direction in
-- debitCreditMemo with a positive amount, while some (e.g. seeded Mastercard mock data)
-- omit the memo and sign the amount, or only set transactionType (POSDEBIT, ...).
-- Normalise to: amount >= 0, debit_credit_memo always set, signed_amount for balances.
CREATE TEMPORARY VIEW transaction_records AS
WITH typed AS (
  SELECT
    coalesce(raw:record.accountId::string, account_id) AS account_id,
    raw:record.transactionId::string AS transaction_id,
    record_type,
    raw:record.postedTimestamp::timestamp AS posted_ts,
    raw:record.transactionTimestamp::timestamp AS transaction_ts,
    raw:record.description::string AS description,
    raw:record.payee::string AS payee,
    raw:record.transactionType::string AS transaction_type,
    raw:record.debitCreditMemo::string AS memo,
    raw:record.category::string AS category,
    raw:record.subCategory::string AS sub_category,
    raw:record.status::string AS status,
    raw:record.amount::decimal(18, 2) AS raw_amount,
    source,
    fetched_at
  FROM STREAM(bronze_fdx_records)
  WHERE entity = 'transactions'
),
directed AS (
  SELECT
    *,
    CASE
      WHEN memo IN ('DEBIT', 'CREDIT') THEN memo
      WHEN raw_amount < 0 THEN 'DEBIT'
      WHEN upper(transaction_type) LIKE '%DEBIT%' THEN 'DEBIT'
      ELSE 'CREDIT'
    END AS debit_credit_memo
  FROM typed
)
SELECT
  account_id,
  transaction_id,
  record_type,
  posted_ts,
  transaction_ts,
  description,
  payee,
  transaction_type,
  debit_credit_memo,
  category,
  sub_category,
  status,
  abs(raw_amount) AS amount,
  CASE WHEN debit_credit_memo = 'DEBIT' THEN -abs(raw_amount) ELSE abs(raw_amount) END
    AS signed_amount,
  source,
  fetched_at
FROM directed;
