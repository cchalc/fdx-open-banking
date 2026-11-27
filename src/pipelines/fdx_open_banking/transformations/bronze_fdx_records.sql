-- Bronze: every landed FDX record, one VARIANT per NDJSON line (docs/landing-contract.md).
-- FDX payloads are polymorphic (depositAccount, locAccount, depositTransaction, ...), so
-- bronze keeps the raw document and silver picks typed fields per entity.
CREATE OR REFRESH STREAMING TABLE bronze_fdx_records (
  CONSTRAINT known_entity EXPECT (entity IN ('accounts', 'transactions', 'consents')),
  CONSTRAINT has_record EXPECT (raw:record IS NOT NULL) ON VIOLATION DROP ROW
)
COMMENT 'Raw FDX v6 records as landed by fdx_open_banking.land.'
AS SELECT
  raw:entity::string AS entity,
  raw:record_type::string AS record_type,
  raw:source::string AS source,
  raw:account_id::string AS account_id,
  raw:fetched_at::timestamp AS fetched_at,
  raw,
  _metadata.file_path AS source_file,
  current_timestamp() AS ingested_at
FROM STREAM read_files(
  '${fdx.raw_path}',
  format => 'json',
  singleVariantColumn => 'raw'
);
