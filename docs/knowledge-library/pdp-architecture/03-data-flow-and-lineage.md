# PDP Data Flow and Lineage

## Overview

Data flows through PDP in a medallion pattern: **Bronze → Silver → Gold**.
Each domain has its own flow, but all follow consistent patterns.

## Streaming vs Batch Paths

### Streaming Path (Near Real-Time)
```
Source → EventHub → Spark Structured Streaming → Bronze Delta → Silver Delta → Gold Delta
```
- Latency: Minutes
- Used by: PaymentsJournal, BillingService (Modern), parts of PMT
- Trigger: `processingTime` (continuous) or `availableNow` (micro-batch)

### Batch Path (Scheduled)
```
Source → Blob/API/SStream → Synapse Pipeline → Bronze Delta → Silver Delta → Gold Delta
```
- Latency: Hours
- Used by: COP, BIN, parts of PMT, Legacy Billing
- Trigger: Synapse schedule triggers, Databricks cron jobs

## Per-Domain Data Flows

### Payment Transactions (PMT)
```
PayHub → EventHub → Bronze.PaymentEvents
  → Silver.Transactions (deduplicated, normalized)
    → Gold.FactTransactions + Dimensions (star schema)
      → AAS Cube → Power BI
      → Kusto → Dashboards
```

### Cost of Payments (COP)
```
Provider Fee Files → Blob Storage → Synapse Pipeline
  → Bronze.ProviderFees
    → Silver.NormalizedFees (standardized schema)
      → Gold.CostOfPayments (aggregated by provider, method, region)
        → Semantic Model → Power BI
```

### Payments Journal
```
PayHub → EventHub → Spark Streaming
  → Bronze.JournalEvents
    → Silver.JournalStage1 → Stage2 → Stage3 → Stage4
      → Gold.PaymentsJournal
```
- 4-stage silver pipeline with progressive enrichment
- CDF (Change Data Feed) tracking for incremental processing

### Fraud / PIMS
```
PIMS → EventHub → Bronze.PIMSEvents
  → Silver.FraudSignals (enriched, scored)
    → Gold.FraudMetrics (aggregated)
      → Kusto → Real-time dashboards
```

### BillingService
```
Modern Billing Journal → EventHub → Bronze
  → PDP Billing EventHub (unified internal bus)
    → Gold.Billing (streaming merge)

MCF (Modern Cash Flow) → EventHub → Bronze
  → PDP Billing EventHub
    → Gold.Billing

Legacy CTP → SStream → Bronze
  → PDP Billing EventHub
    → Gold.Billing

Gold.Billing → CDF → Gold.PaymentsBilling
```

### Network Tokenization (NT)
```
Token Events → EventHub → Bronze.TokenEvents
  → Silver.TokenLifecycle
    → Gold.NetworkTokenization
```

### Account Updater (AU)
```
AU Events → EventHub → Bronze.AUEvents
  → Silver.CardUpdates
    → Gold.AccountUpdater
```

### BIN
```
BIN Files → Blob → Synapse Pipeline
  → Bronze.BINData
    → Silver.BINLookup
      → Gold.BINReference (used as dimension by other domains)
```

## Lineage Tracking

- **Delta Lake time travel**: All tables support versioning via Delta Lake
- **CDF (Change Data Feed)**: Enabled on key tables for incremental downstream processing
- **Pipeline metadata**: Synapse pipeline run IDs and Databricks job run IDs tracked in records
- **Watermarks**: Processing watermarks stored in state tables for exactly-once semantics
