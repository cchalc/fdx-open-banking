-- Typed account snapshots from bronze. Field names follow FDX v6 account models;
-- loan accounts report principalBalance instead of currentBalance.
CREATE TEMPORARY VIEW account_records AS
SELECT
  raw:record.accountId::string AS account_id,
  record_type,
  raw:record.accountType::string AS account_type,
  raw:record.accountCategory::string AS account_category,
  raw:record.displayName::string AS display_name,
  raw:record.nickname::string AS nickname,
  raw:record.status::string AS status,
  raw:record.currency.currencyCode::string AS currency_code,
  coalesce(
    raw:record.currentBalance::decimal(18, 2),
    raw:record.principalBalance::decimal(18, 2)
  ) AS current_balance,
  coalesce(
    raw:record.availableBalance::decimal(18, 2),
    raw:record.availableCredit::decimal(18, 2)
  ) AS available_balance,
  coalesce(raw:record.balanceAsOf::timestamp, fetched_at) AS balance_as_of,
  source,
  fetched_at
FROM STREAM(bronze_fdx_records)
WHERE entity = 'accounts';
