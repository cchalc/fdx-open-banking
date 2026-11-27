-- Full consent history (SCD Type 2): every grant, extension and revocation is kept,
-- so you can answer "was this data covered by consent when we used it?".
CREATE OR REFRESH STREAMING TABLE silver_consents
COMMENT 'Consent history per consent_id (__START_AT / __END_AT).';

CREATE FLOW silver_consents_cdc AS AUTO CDC INTO silver_consents
FROM STREAM(consent_records)
KEYS (consent_id)
SEQUENCE BY fetched_at
STORED AS SCD TYPE 2;
