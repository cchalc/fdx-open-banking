# Databricks notebook source
# MAGIC %md
# MAGIC # FDX open banking: the consent story
# MAGIC
# MAGIC Canada's consumer-driven banking framework uses **FDX API v6** as its technical standard.
# MAGIC The consumer, not the data recipient, decides:
# MAGIC
# MAGIC 1. **what** is shared: OAuth scopes map to FDX data categories,
# MAGIC 2. **for how long**: `ONE_TIME`, `TIME_BOUND`, or `PERSISTENT` consent,
# MAGIC 3. **until when**: consent can be revoked at any time.
# MAGIC
# MAGIC With token-based access, there's no credential sharing or screen scraping. This notebook
# MAGIC walks through the pipeline's tables to show each point.
# MAGIC
# MAGIC _Synthetic data from the Mastercard FDX mock servers. No real customer data._

# COMMAND ----------

dbutils.widgets.text("catalog", "", "Catalog")  # noqa: F821  (Databricks global)
dbutils.widgets.text("schema", "fdx_open_banking", "Schema")  # noqa: F821
catalog = dbutils.widgets.get("catalog")  # noqa: F821
schema = dbutils.widgets.get("schema")  # noqa: F821
assert catalog, "Set the catalog widget"
spark.sql(f"USE `{catalog}`.`{schema}`")  # noqa: F821

# COMMAND ----------

# MAGIC %md
# MAGIC ## 1. Scopes are data categories
# MAGIC Each FDX scope unlocks a specific set of endpoints. A recipient asks only for what its use
# MAGIC case needs (data minimisation).

# COMMAND ----------

scopes = [
    ("ACCOUNT_BASIC", "Account list, type, status", "/accounts"),
    ("ACCOUNT_DETAILED", "Balances, product detail", "/accounts/{id}"),
    ("TRANSACTIONS", "Transaction history", "/accounts/{id}/transactions"),
    ("STATEMENTS", "Statement documents", "/accounts/{id}/statements"),
    ("CUSTOMER_CONTACT", "Account-holder contact", "/accounts/{id}/contact"),
    ("ACCOUNT_PAYMENTS", "Payment networks / rails", "/accounts/{id}/payment-networks"),
    ("TAX_DOCUMENTS", "Tax forms", "/tax-documents"),
]
display(spark.createDataFrame(scopes, "scope string, data_category string, fdx_endpoint string"))  # noqa: F821

# COMMAND ----------

# MAGIC %md
# MAGIC ## 2. Consent has a lifecycle, and we keep all of it
# MAGIC `silver_consents` is SCD Type 2. Every grant, extension, and revocation is a row with
# MAGIC `__START_AT` / `__END_AT`, so you can audit what was covered at any point in time.

# COMMAND ----------

display(  # noqa: F821
    spark.sql(  # noqa: F821
        """
        SELECT consent_id, status, duration_type, scopes, account_ids,
               granted_at, expires_at, revoked_at, __START_AT, __END_AT
        FROM silver_consents
        ORDER BY consent_id, __START_AT
        """
    )
)

# COMMAND ----------

# MAGIC %md
# MAGIC ## 3. Analytics respect consent
# MAGIC Gold tables only include accounts with an **active, unexpired** consent for the matching
# MAGIC scope (`gold_active_consent_accounts`). Revoke a consent, re-run the pipeline, and the
# MAGIC account drops out of `gold_spend_by_category`.

# COMMAND ----------

display(spark.sql("SELECT * FROM gold_active_consent_accounts ORDER BY account_id, scope"))  # noqa: F821

# COMMAND ----------

display(  # noqa: F821
    spark.sql(  # noqa: F821
        """
        SELECT month, account_type, category, currency_code,
               sum(transaction_count) AS transactions, sum(spend) AS spend
        FROM gold_spend_by_category
        GROUP BY ALL
        ORDER BY month DESC, spend DESC
        """
    )
)

# COMMAND ----------

# MAGIC %md
# MAGIC ## 4. Why this is the Canadian framework
# MAGIC - **FDX Canada Council**: Canadian voting membership makes the standards decisions for Canada.
# MAGIC - **Bank of Canada**: supervises providers and keeps the public registry of accredited services.
# MAGIC - **OBSI**: the designated external complaints body for consumers.
# MAGIC
# MAGIC See `docs/research/canada-context.md` for sources.
