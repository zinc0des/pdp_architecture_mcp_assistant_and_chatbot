# KT Handout: Cube Optimization & Benchmark Infrastructure

**Author:** Satavisha Roy  
**Period:** July 2025 – April 2026  
**Audience:** New team member onboarding  
**Last Updated:** April 2026  
**Master Plan:** [PaymentTransactions_Cube_Optimization_Plan.md](./PaymentTransactions_Cube_Optimization_Plan.md)

---

## 1. Problem Statement

The PaymentTransactions AAS cube processes **4.18 billion rows** through **21 foreign key joins** with **432 DAX measures**. This results in:

- **15–65 second render times** per Power BI visual
- **S4 AAS SKU** at **$8.06/hr** — the most expensive tier
- Cube refresh failures requiring manual on-call re-triggers

---

## 2. Solution Overview

A three-wave optimization approach targeting the semantic layer, star schema architecture, and cascading FK drops:

```
┌─────────────────────────────────────────────────────────────────────────┐
│                        Combined Impact                                  │
│  Measures: 432 → 146 (66% reduction)                                   │
│  Fact rows: 4.18B → 628M (85% reduction)                              │
│  AAS SKU: S4 → S1 ($8.06/hr → $2.02/hr, 50-75% cost savings)         │
│  Query performance: 8-12× improvement projected                        │
└─────────────────────────────────────────────────────────────────────────┘
```

| Metric | Current | After Wave 1 | After Wave 2 | After Wave 3 |
|--------|:-------:|:------------:|:------------:|:------------:|
| **Measures** | 432 | 146 | 146 | 146 |
| **Fact Rows** | 4.18B | 4.18B | 628M | 628M |
| **Foreign Keys** | 21 | 21 | 9 (+3 denorm) | 8 (+3 denorm) |
| **AAS SKU** | S4 | S4 → S2 | S2 → S1 | S1 |
| **Refresh Time** | Baseline | ~40% faster | ~70% faster | ~75% faster |

---

## 3. Wave 1: Semantic Layer Cleanup

**Owner:** Data Science Team  
**Scope:** AAS Model.bim — measure visibility  
**Risk:** LOW — measures are hidden, not deleted

### 3.1 Methodology

596 AAS tokens were classified via 90-day telemetry from `AzureDiagnostics` QueryEnd events:

| Category | Count | Description |
|----------|:-----:|-------------|
| **KEEP (survivors)** | 146 | Actively used measures |
| ASDQ (system/DQ) | 102 | Out of scope |
| NON_MEASURE | 62 | Dimension columns/artifacts |
| **Removal candidates** | 286 | Unused or replaceable measures |

### 3.2 Risk Tiers

Removal candidates are organized into three risk tiers:

| Tier | Count | Action | Risk |
|------|:-----:|--------|------|
| **HIDE_NOW** | 204 | Zero consumers → hide immediately | 🟢 ZERO |
| **HIDE_AFTER_NOTICE** | 43 | 2-week notification to consumers → hide | 🟡 LOW |
| **MIGRATE_FIRST** | 39 | Build replacement measures first → hide | 🟠 MEDIUM |

### 3.3 Categories Removed

- Time Intelligence variants (YoY, QoQ, MoM for low-usage measures)
- `_MI` / `_CI` (Merchant Initiated / Customer Initiated) duplicates
- Dunning consumer/commercial splits
- Forecast/share breakdowns

---

## 4. Wave 2: Star Schema Reduction

**Owner:** PDP Engineering  
**Scope:** `gold.fact_transactions` Delta table  
**Risk:** MEDIUM — requires fact table rebuild

### Phase 2.1: Denormalize dim_geo (Hybrid Approach)

**Validated: `(Country, Currency)` is a unique composite key in dim_geo (2,472 rows, 0 duplicates).**
dim_product and dim_purchase retain their surrogate FK joins — no valid natural key exists (`ProductGroup` has 107 "Other" rows; `StorefrontGroup` has only 22 distinct values across 4,856 rows).

| FK Dropped | Dimension | Cardinality | Columns Inlined |
|------------|-----------|:-----------:|----------------|
| `GeoId` | dim_geo | 2,472 | `Country`, `Region`, `Currency` |
| *(retained)* | dim_product | 179 | *(surrogate FK — no valid natural key)* |
| *(retained)* | dim_purchase | 4,856 | *(surrogate FK — no valid natural key)* |

### Phase 2.2: BinId → BinCardType

**3.02B → 1.25B rows (70.2% cumulative reduction)**

| FK Dropped | Dimension | Cardinality | Column Inlined |
|------------|-----------|:-----------:|---------------|
| `BinId` | dim_bin | 620,693 | `BinCardType` (4–5 values after canonicalization: Credit, Debit, Prepaid, Unknown) |

BinCardType requires case normalization before inlining (test data shows 7 values: CREDIT/Credit, DEBIT/Debit, PREPAID, NA, empty).

### Phase 2.3: Drop 8 Unused Foreign Keys

**1.25B → 628M rows (85% cumulative reduction)**

8 FK columns where **0 of 230 DAX measures** reference the underlying dimension (confirmed via Model.bim + 90-day telemetry):

| FK Dropped | Dimension | Cardinality |
|------------|-----------|:-----------:|
| `PaymentExtendedId` | dim_payment_extended | 120,414 |
| `ResponseCodeId` | dim_response_code | 19,024 |
| `PaymentMethodId` | dim_payment_method | 4,634 |
| `BillingId` | dim_billing | 3,917 |
| `NetworkTokenId` | dim_network_token | 448 |
| `AuthenticationId` | dim_authentication | 144 |
| `TrustedMIDId` | dim_trusted_MID | 26 |
| `MerchantId` | dim_merchant | 1 |

---

## 5. Wave 3: Cascade Optimization

**Owner:** PDP Engineering (triggered by Wave 1 results)  
**Dependency:** Requires Wave 1 measure dispositions

Conditional FK drops based on Wave 1 measure removals. If ALL measures depending on a dimension are hidden, that dimension's FK becomes droppable:

| Dimension | FK Cardinality | Rows | Dependent Measures | Cascade Condition |
|-----------|:-:|:-:|:-:|:--|
| **dim_chargeback** | 8 | 8 | ~4 measures | If ALL chargeback measures hidden |

Gate check: Run validation query Q5 from `pbi_dax_optimization_validation.kql`.

---

## 6. CubeRefresh Automated Retry Pipeline

**File:** `src/synapse/pipeline/CubeRefresh_WithRetry.json`

### Before
Manual re-trigger by on-call person after cube refresh failure.

### After
Automatic retry with exponential backoff:

```
Parameters: MaxRetries: 3, RetryIntervalSeconds: 300 (5 min)
```

```json
{
    "name": "CubeRefresh_WithRetry",
    "properties": {
        "description": "Wrapper pipeline that executes CubeRefreshViaFunctionApp
                        with retry logic using ForEach loop pattern",
        "activities": [{
            "name": "RetryLoop",
            "type": "ForEach",
            "typeProperties": {
                "items": "@range(1, pipeline().parameters.MaxRetries)",
                "isSequential": true,
                "activities": [
                    {
                        "name": "Check If Already Succeeded",
                        "type": "IfCondition",
                        "expression": "@equals(variables('CubeRefreshSuccess'), false)",
                        "ifTrueActivities": [
                            { "name": "CubeRefresh", "type": "ExecutePipeline",
                              "pipeline": "CubeRefreshViaFunctionApp" },
                            { "name": "Set Success True",
                              "type": "SetVariable", "value": true },
                            { "name": "Wait Before Retry",
                              "type": "Wait", "depends": "CubeRefresh [Failed]" }
                        ]
                    }
                ]
            }
        }]
    }
}
```

**Flow:**
1. Loop iterates up to `MaxRetries` times
2. Skips if previous attempt succeeded (`CubeRefreshSuccess == true`)
3. Executes `CubeRefreshViaFunctionApp` pipeline
4. On success → sets flag, loop exits on next iteration
5. On failure → waits `RetryIntervalSeconds` → retries
6. After all retries exhausted → pipeline fails → on-call paged

---

## 7. Benchmark Test Infrastructure

### 7.1 Fabric Load Test Framework

Load tests execute DAX queries against the AAS cube and emit telemetry to App Insights.

**Dashboard:** Azure Workbook (`fabric-loadtest-perfomance-columns.json`)

**Metrics collected per visual/query:**
- `p50`, `p90`, `p95`, `p99` latency
- `CV%` (coefficient of variation) for stability assessment
- Delta vs baseline comparison

**Test labels used:**
- `baseline` — before optimization
- `MerchantDescriptor Normalization` — after normalization activation
- `null merchantdescriptor` — during null override validation period

### 7.2 Cube Validation Helpers

**File:** `src/databricks/workspace/notebooks/PaymentTransactions/Test/conftest_pmt.py`

Shared fixtures for cube-aware tests:

```python
def get_cube_row_count():
    """Returns current cube row count for validation."""
    ...

def check_twodayscube_data():
    """Skips tests if cube data hasn't refreshed in 2 days."""
    ...
```

### 7.3 Cube Calculation Simulation

**File:** `src/databricks/workspace/notebooks/PME Migration/Test/Simulate_cube_caculations.py`

A 366-line simulation notebook for validating cube calculations and diff-style comparisons before/after optimization changes.

---

## 8. Testing Strategy

### 8.1 Test Pyramid

```
                    ┌──────────────┐
                    │   Canary     │  Subset of integration tests
                    │  (Alerting)  │  feeding on-call PagerDuty
                    ├──────────────┤
                    │ Integration  │  Live table reads + Spark transforms
                    │              │  + DQ checks (Databricks jobs)
                    ├──────────────┤
                    │  Functional  │  End-to-end pipeline validation
                    ├──────────────┤
                    │  Diff/Shadow │  Shadow vs production table
                    │              │  comparison (assert_df_equality)
                    ├──────────────┤
                    │    Unit      │  SparkTestBase + in-memory
                    │              │  DataFrames + direct assertions
                    └──────────────┘
```

### 8.2 Test Classification Decorators

Every test is decorated with metadata for routing and alerting:

```python
@pytest.mark.testclassification(
    test_type="Integration",        # Unit / Functional / Integration
    subject_area="PaymentTransactions",
    severity="SEV2.5",              # SEV1 through SEV3
    is_active="True",
    is_canary="True",               # Feeds on-call alerting
    frequency="Daily",              # Daily / Hourly
    test_id="unique-guid",
    alert_name="PDP Alert | SEV2.5 | ...",
    description="Human-readable test description"
)
```

### 8.3 Test Execution Infrastructure

Tests are orchestrated via centralized Databricks jobs:

| Job | Scope |
|-----|-------|
| `PDP_Integration_Test_Job.yml` | Integration/canary tests against live tables |
| `PDP_Functional_Test_Job.yml` | Full pipeline functional tests |
| `PDP_Pytest_Collector_Job.yml` | Test discovery and collection |

All tests are routed through `Pytest-Runner.py`, which enforces the directory convention:

```
Test/
├── Unit/           # SparkTestBase, in-memory DataFrames
├── Functional/     # End-to-end pipeline validation
├── Integration/    # Live table reads + DQ checks
├── Diff/           # Shadow vs production comparisons
└── Canary/         # Subset of integration tests for alerting
```

### 8.4 Gold Layer Consistency Tests

**File:** `Test/Integration/gold.transactions_Consistency_test.py`

Compares `gold.fact_transactions` vs `gold.transactions` on key additive measures (`AmountUSD`, `TransactionCount`) to catch divergence after schema changes.

### 8.5 Unit Tests (BDD-Style)

**File:** `src/databricks/workspace/tests/PaymentTransactions/test_microsoft_decline.py`

Uses `SparkTestBase` with Given/When/Then docstrings:

```python
class TestMicrosoftDecline(SparkTestBase):
    """Given a Microsoft decline transaction
       When processed through the gold pipeline
       Then the decline reason should be categorized correctly"""

    def test_verify_count(self):
        self._verify_count(expected=5)

    def test_verify_schema(self):
        self._verify_schema(expected_columns=[...])
```

### 8.6 Data Quality Monitoring (Grafana)

DQ rules are defined as JSON and feed into Grafana dashboards for continuous monitoring:

**File:** `DQFramework/RuleConfig/MetricCollector/payments/gold.json`

Covers freshness, processing latency, null rates, and cardinality for:
- `dim_merchant` — merchant dimension health
- `fact_transactions` — fact table freshness and null rates

---

## 9. Key Files Reference

| File | Purpose |
|------|---------|
| `docs/PaymentTransactions_Cube_Optimization_Plan.md` | Master optimization plan (Waves 1-3) |
| `docs/AAS_PaymentTransactions_Performance_Investigation_Report.md` | AAS performance investigation |
| `docs/DataScience_Cube_Optimization_Proposal.md` | Data Science team's measure assessment |
| `src/synapse/pipeline/CubeRefresh_WithRetry.json` | Automated retry pipeline |
| `Test/Integration/gold.transactions_Consistency_test.py` | Gold layer consistency tests |
| `Test/conftest_pmt.py` | Shared fixtures (cube helpers, table fixtures) |
| `PME Migration/Test/Simulate_cube_caculations.py` | Cube calculation simulation |
| `DQFramework/RuleConfig/.../gold.json` | Grafana DQ rules for gold layer |

---

## 10. Execution Dependencies

```
Wave 1 (Semantic Layer)          Wave 2 (Star Schema)
    │                                │
    │  Can run in PARALLEL           │
    │                                │
    ▼                                ▼
Wave 1 measure dispositions ──► Wave 3 (Cascade)
                                Gate check: Are all dependent
                                measures hidden?
                                    │
                                    ▼
                              Drop eligible FKs
```

---

## 11. Validation Queries

The optimization plan includes a comprehensive KQL validation suite (`pbi_dax_optimization_validation.kql`) with queries:

| Query | Purpose |
|-------|---------|
| Q1 | Full measure classification from AAS telemetry |
| Q2 | FK dependency analysis (which measures use which FKs) |
| Q3 | Unused FK identification |
| Q4 | Zero-query measures in 90-day window |
| Q5 | Chargeback measure dependency check |
| Q6 | Authorization response dependency check |
| Q7 | Payment instrument dependency check |

---

## 12. Common Pitfalls & Notes

1. **Wave ordering:** Waves 1 and 2 are independent and can run in parallel. Wave 3 depends on Wave 1 results.

2. **Measure hiding vs deletion:** Wave 1 **hides** measures in Model.bim — they're not deleted. This is reversible if a consumer reports a missing measure.

3. **Fact table rebuild:** Wave 2 requires rebuilding `gold.fact_transactions`. Plan for downtime and validate with consistency tests before/after.

4. **Telemetry lag:** The 90-day telemetry window means a measure used once 89 days ago still counts as "active." Re-run classification queries before executing Wave 3.

5. **CubeRefresh retries:** The retry pipeline uses `isSequential: true` in the ForEach — retries happen one at a time, not in parallel. `RetryIntervalSeconds: 300` provides 5-minute spacing.

6. **Benchmark labels:** Always tag load test runs with descriptive labels (`baseline`, optimization name) for meaningful before/after comparison in the Azure Workbook.
