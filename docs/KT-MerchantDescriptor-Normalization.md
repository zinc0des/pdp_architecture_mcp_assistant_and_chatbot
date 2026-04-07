# KT Handout: MerchantDescriptor Normalization

**Author:** Satavisha Roy  
**Period:** July 2025 – April 2026  
**Audience:** New team member onboarding  
**Last Updated:** April 2026

---

## 1. Problem Statement

The `MerchantDescriptor` column in Payment Transactions contains raw, high-cardinality values — millions of unique strings like `MICROSOFT-G136136964`, `MSFT*XBOX GAME PASS`, `Microsoft*Microsoft 365`.

**Impact:**
- AAS cube performance degrades as the `dim_merchant` dimension inflates
- BI slicing by merchant is impractical — analysts can't group by "Microsoft" when thousands of variants exist
- Cube refresh and query times scale with cardinality

---

## 2. Solution: Three-Column Design

A regex-based normalization pipeline that preserves the raw value while providing normalized views.

| Column | Purpose | Example |
|--------|---------|---------|
| `MerchantDescriptor_Source` | Original raw value (immutable audit trail) | `MICROSOFT-G136136964` |
| `MerchantDescriptor` | Normalized value used in dim_merchant | `MICROSOFT` |
| `MerchantDescriptor_vNext` | Enhanced categorization with improved pattern matching | `MICROSOFT` |

The `_vNext` column allows iterating on normalization rules without breaking existing reports.

---

## 3. Architecture & Data Flow

```
Silver Stage1 (payments_journal_stage1)
  └── NormalizationAndEnrichment logic applies CASE/RLIKE/LIKE patterns
       ├── MerchantDescriptor_Source = raw value preserved
       ├── MerchantDescriptor_vNext = normalized via regex patterns
       └── MerchantDescriptor = (initially null for validation, then = vNext)
           │
           ▼
Silver Stage2 → Stage3
           │
           ▼
Gold PaymentsJournal
           │
           ▼
Gold PaymentsBilling
           │
           ▼
Gold DimMerchant ──► Gold FactTransactions ──► AAS Cube
```

**Cross-repo scope:** Changes span both `PaymentsJournal` and `BillingService` repos.

---

## 4. Key Code Locations

### 4.1 Schema Addition (Silver Layer)

The three columns are added to the Silver transactions table via schema evolution:

**File:** `src/databricks/workspace/notebooks/PaymentTransactions/Silver/Transactions/TransactionsTable.py`

```python
# Altering existing delta table schema without recreating table
try:
    spark.sql(
        f"ALTER TABLE {SILVER_TRANSACTIONS_TABLE_NAME} ADD COLUMNS "
        f"MerchantDescriptor_Source STRING, MerchantDescriptor_vNext STRING"
    )
except Exception as e:
    if 'already exists' not in str(e).lower():
        raise
```

### 4.2 Gold DimMerchant — Dimension Build

**File:** `src/databricks/workspace/notebooks/PaymentTransactions/Gold/Gold-DimMerchant.py`

```python
# Create the merchant dimension with a monotonically increasing id
# TEMPORARY: Setting MerchantDescriptor to null prior to release in the week of 2026/02/02
df_dim_merchant_delta = (
    df_transactions.withColumn('MerchantDescriptor', lit(None).cast('string'))
    .groupBy('MerchantID', 'GatewayMerchantId', 'MerchantDescriptor',
             'MerchantCountry', 'MerchantCategoryCode', 'SellerOfRecord',
             'ThirdPartySeller')
    .count()
    .drop("count")
)
```

The dimension uses a MERGE pattern to insert only new combinations:

```python
dt_dim_merchant.alias("old").merge(
    source = df_dim_merchant_delta.alias("new"),
    condition = "old.MerchantID <=> new.MerchantID and \
                old.GatewayMerchantId <=> new.GatewayMerchantId and \
                old.MerchantDescriptor <=> new.MerchantDescriptor and \
                old.MerchantCountry <=> new.MerchantCountry and \
                old.MerchantCategoryCode <=> new.MerchantCategoryCode and \
                old.SellerOfRecord <=> new.SellerOfRecord and \
                old.ThirdPartySeller <=> new.ThirdPartySeller")
    .whenNotMatchedInsert(values = { ... })
    .execute()
```

> **Note:** The `<=>` (null-safe equality) operator is critical here since `MerchantDescriptor` may be null during validation.

### 4.3 Gold FactTransactions — FK Join

**File:** `src/databricks/workspace/notebooks/PaymentTransactions/Gold/Gold-FactTransactions.py`

```python
# TEMPORARY: Setting MerchantDescriptor to null prior to release in the week of 2026/02/02
df_transactions = (
    df_transactions.withColumn('MerchantDescriptor', lit(None).cast('string'))
    .join(df_dim_merchant,
          ['MerchantID', 'GatewayMerchantId', 'MerchantDescriptor',
           'MerchantCountry', 'MerchantCategoryCode', 'SellerOfRecord',
           'ThirdPartySeller'], 'left_outer')
    .withColumn('MerchantId', df_dim_merchant.Id)
    .fillna({'MerchantId':0})
    .fillna({'GatewayMerchantId':0})
)
```

### 4.4 Shadow Streaming — vNext Activation

**File:** `src/databricks/workspace/notebooks/PaymentTransactions/Gold/ShadowStreaming/Gold-DimMerchant-ShadowStreaming.py`

Shadow streaming uses `coalesce` to activate `MerchantDescriptor_vNext` with fallback:

```python
def process_and_merge(df_micro_batch, batch_id):
    df_micro_batch = df_micro_batch.withColumn(
        'MerchantDescriptor',
        coalesce(col('MerchantDescriptor_vNext'), col('MerchantDescriptor'))
    )
    df_micro_batch = dedupe(df_micro_batch)
    df_micro_batch = df_micro_batch.withColumn("IngestionTimestamp", current_timestamp())
    
    dt_dim_merchant.alias("old").merge(
        source=df_micro_batch.alias("new"),
        condition="""
            old.MerchantID <=> new.MerchantID AND
            old.GatewayMerchantId <=> new.GatewayMerchantId AND
            old.MerchantDescriptor <=> new.MerchantDescriptor AND ...
        """
    )
    .whenNotMatchedInsertAll()
    .execute()
```

---

## 5. Rollout Timeline

| Date | Milestone | Detail |
|------|-----------|--------|
| Jul–Dec 2025 | Design & implementation | Normalization logic, schema additions, three-column design |
| Feb 2026 | Shipped with null override | `lit(None).cast('string')` in DimMerchant & FactTransactions for validation |
| Feb 2026 | Shadow Streaming activated | `coalesce(MerchantDescriptor_vNext, MerchantDescriptor)` running in parallel |
| Apr 6, 2026 | Full activation PR | PR to remove null override → `MerchantDescriptor_vNext` used directly in `dim_merchant` and `gold.fact_transactions` |

---

## 6. Impact

- **Cardinality:** Millions of raw values → ~50 normalized categories
- **Cube performance:** Enables Wave 1 of cube optimization
- **BI usability:** Analysts can now slice by merchant brand (Microsoft, Xbox, Battle.net, etc.)

---

## 7. Testing Strategy

### 7.1 Integration Tests (Canary)

**File:** `src/databricks/workspace/notebooks/PaymentTransactions/Test/Integration/merchantdescriptor_completeness_accuracy_test.py`

The testing strategy covers two DQ dimensions across both Silver and Gold layers:

#### Completeness Tests
Validate that the normalization columns exist in production tables:

```python
@pytest.mark.testclassification(
    test_type="Integration", is_canary="True", severity="SEV2.5", frequency="Daily",
    alert_name="PDP Alert | SEV2.5 | Completeness | Silver | MerchantDescriptor normalization columns missing"
)
def test_completeness_merchantdescriptor_columns_in_silver(silver_pj_stage1_data):
    columns = [c.lower() for c in silver_pj_stage1_data.columns]
    missing = []
    if "merchantdescriptor_source" not in columns:
        missing.append("MerchantDescriptor_Source")
    if "merchantdescriptor_vnext" not in columns:
        missing.append("MerchantDescriptor_vNext")
    assert len(missing) == 0, f"Missing columns in silver: {missing}"
```

#### Accuracy Tests
Validate cardinality reduction and that key patterns are NOT incorrectly collapsed:

```python
@pytest.mark.testclassification(
    test_type="Integration", is_canary="True", severity="SEV3", frequency="Daily",
    alert_name="PDP Alert | SEV3 | Accuracy | Silver | MerchantDescriptor_vNext normalization quality"
)
def test_accuracy_merchantdescriptor_vnext_in_silver(silver_pj_stage1_data):
    metrics = df.agg(
        countDistinct(col("MerchantDescriptor_Source")).alias("source_cardinality"),
        countDistinct(col("MerchantDescriptor_vNext")).alias("vnext_cardinality"),
        # Verify MICROSOFT*MICROSOFT 365 is NOT collapsed to just "MICROSOFT"
        spark_sum(when(
            col("_stripped").startswith("MICROSOFTMICROSOFT365") & 
            (col("MerchantDescriptor_vNext") == lit("MICROSOFT")), 1
        ).otherwise(0)).alias("ms365_collapsed_incorrectly"),
        # Verify XBOX GAME PASS is NOT collapsed to just "XBOX"
        spark_sum(when(
            col("_stripped").contains("XBOXGAMEPASS") & 
            col("MerchantDescriptor_vNext").isin(["XBOX", "MICROSOFT*XBOX"]), 1
        ).otherwise(0)).alias("gamepass_collapsed_incorrectly"),
    ).collect()[0]

    # vNext cardinality must be LESS than source (normalization is working)
    assert metrics["vnext_cardinality"] < metrics["source_cardinality"]
    # No bad collapses
    assert metrics["ms365_collapsed_incorrectly"] == 0
    assert metrics["gamepass_collapsed_incorrectly"] == 0
```

### 7.2 Shadow Diff Tests

**File:** `src/databricks/workspace/notebooks/PaymentTransactions/Gold/ShadowStreaming/DimTables-ShadowDiffTest.py`

Compares `DIM_MERCHANT_VNEXT` (shadow) vs `DIM_MERCHANT` (production) tables using structural equality:

```python
df_actual = spark.read.table(DIM_MERCHANT_VNEXT_TABLE_NAME)
df_expected = spark.read.table(DIM_MERCHANT_TABLE_NAME)

columns_to_ignore = ["IngestionTimestamp", "Id"]
pk_list = ["MerchantID", "GatewayMerchantId", "MerchantDescriptor",
           "MerchantCountry", "MerchantCategoryCode", "SellerOfRecord",
           "ThirdPartySeller"]

assert_df_equality(df_actual, df_expected, pk_list, columns_to_ignore)
```

### 7.3 Grafana Data Quality Monitoring

**File:** `src/databricks/workspace/libraries/CommonModules/PDPCommon/DQFramework/RuleConfig/MetricCollector/payments/gold_merchantdescriptor.json`

Continuous cardinality monitoring via the DQ Framework:

```json
{
    "rules": [{
        "rule_name": "merchantdescriptor_cardinality",
        "rule_type": "custom_query",
        "constraint": [
            "SELECT COUNT(DISTINCT MerchantDescriptor_vNext) FROM gold.transactions
             WHERE Date >= current_date() - INTERVAL 1 DAY"
        ],
        "frequency": "daily",
        "alert_severity": "high",
        "description": "[sev3] | PDP Alert | Accuracy | Cardinality | PMT |
                        gold.transactions.MerchantDescriptor_vNext distinct count anomaly"
    }]
}
```

### 7.4 Test Organization

Tests run via the centralized `Pytest-Runner.py` on Databricks, organized by:

```
Test/
├── Unit/           # SparkTestBase, in-memory DataFrames
├── Functional/     # End-to-end pipeline validation
├── Integration/    # Live table reads + DQ checks (canary-marked)
├── Diff/           # Shadow vs production comparisons
└── Canary/         # Subset of integration tests for alerting
```

Each test is decorated with `@pytest.mark.testclassification(...)` providing:
- `test_type` — Unit/Functional/Integration
- `severity` — SEV1 through SEV3
- `is_canary` — Whether it feeds into on-call alerting
- `frequency` — Daily/Hourly
- `alert_name` — PDP Alert string for incident routing

---

## 8. Key Files Reference

| File | Purpose |
|------|---------|
| `Silver/Transactions/TransactionsTable.py` | Schema evolution (adds columns) |
| `Gold/Gold-DimMerchant.py` | Dimension build with MerchantDescriptor |
| `Gold/Gold-FactTransactions.py` | FK join with dim_merchant |
| `Gold/ShadowStreaming/Gold-DimMerchant-ShadowStreaming.py` | Shadow streaming with `coalesce` activation |
| `Gold/ShadowStreaming/DimTables-ShadowDiffTest.py` | Shadow vs production diff validation |
| `Test/Integration/merchantdescriptor_completeness_accuracy_test.py` | Completeness + accuracy canary tests |
| `DQFramework/RuleConfig/.../gold_merchantdescriptor.json` | Grafana cardinality monitoring rule |

---

## 9. Common Pitfalls & Notes

1. **Null-safe equality (`<=>`):** The merge condition in DimMerchant uses `<=>` not `=`. This is essential because `MerchantDescriptor` may be null during the validation period.

2. **Null override removal:** When removing `lit(None).cast('string')`, update **both** `Gold-DimMerchant.py` and `Gold-FactTransactions.py` simultaneously — they must agree or the FK join breaks.

3. **Cross-repo dependency:** Normalization logic originates in the PaymentsJournal repo. If normalization patterns change upstream, coordinate with that team.

4. **Shadow Streaming divergence:** During the validation period, shadow streaming (`DIM_MERCHANT_VNEXT`) uses `coalesce(vNext, MerchantDescriptor)` while production uses `lit(None)`. The diff test catches divergence.

5. **Cardinality monitoring:** The DQ rule alerts if `MerchantDescriptor_vNext` distinct count anomalies are detected. If normalization patterns are updated, the threshold may need adjustment.
