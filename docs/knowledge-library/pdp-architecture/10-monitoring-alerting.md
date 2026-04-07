# PDP Monitoring and Alerting

## Monitoring Stack

### Grafana (Primary DQ Dashboard)
- **URL**: PDP DQ Dashboard on Azure Managed Grafana
- **Purpose**: Visualize data quality test results, alert status, trends
- **Data source**: App Insights (KQL queries)
- **Panels**: Per subject area, per test type, trend lines, failure counts

### Azure Application Insights
- **Purpose**: Telemetry store for DQ test results
- **Custom events**: Test execution results with structured dimensions
- **Custom dimensions**: test_id, subject_area, severity, test_type, is_active
- **Query language**: KQL (Kusto Query Language)

### ICM (Incident Management)
- **Purpose**: Incident tracking and on-call management
- **Integration**: Auto-create incidents on pipeline failures and SLA breaches
- **Routing**: Based on subject area → team mapping
- **SLA tracking**: Time to acknowledge, time to mitigate, time to resolve
- **SEV promotion**: "PDP SLA Breach" alerts auto-promoted to SEV25 by ICM automation

## Alert Configuration

### Alert Naming Convention
```
PDP Alert | {Category} | {Type/Service} | {SubjectArea} | {Description}
```

### Alert Categories (from deployed Bicep)

| Category | Example | Repos |
|----------|---------|-------|
| **Reliability** | `PDP Alert \| Reliability \| Data Pipeline Failure \| BIN \| BIN_Master_V2` | All repos |
| **Reliability** | `PDP Alert \| Reliability \| Databricks Job Failure \| BillingService \| job-name` | BillingService, PI |
| **Data Freshness** | `PDP Alert \| Data Freshness \| PMT \| gold.transactions (ADLS) is out of SLA` | Main PDP only |
| **Data Freshness** | `PDP Alert \| Data Freshness \| PMT \| Stale materialized view for gold_transactions_mv (Kusto)` | Main PDP only |
| **Performance** | `PDP Alert \| Performance \| Kusto \| High cache utilization` | Main PDP only |
| **Performance** | `PDP Alert \| Performance \| Kusto \| Degraded query performance` | Main PDP only |
| **Accuracy** | `PDP Alert \| Accuracy \| Test Failure \| {SubjectArea} \| {TestName}` | Designed, not yet deployed |

### Action Groups

| Action Group | Short Name | ICM | Email | Purpose |
|-------------|-----------|-----|-------|---------|
| PaymentsDataPlatfrom Alerts | `Alerts` | Yes | — | Pipeline failures, SLA breaches |
| PaymentsDataPlatfrom Alerts No ICM | `AlertsNoICM` | No | `pdp_dev@microsoft.com` | Informational, non-critical |

**Note:** "Platfrom" typo in action group name is intentional (deployed, do not change).

### Alert Configuration Details

- **Evaluation frequency**: PT5M (5 minutes) for most alerts
- **Window size**: PT15M (15 minutes) for metric aggregation
- **Standard severity**: SEV3 for all deployed alerts
- **SLA alerts**: Auto-promoted to SEV25 by ICM automation

### Alerts by Repo

**Commerce.PaymentsDataPlatform (main)** — Broadest coverage:
- Kusto health: stale materialized views, high cache utilization, degraded query performance
- SLA breaches: gold_transactions (Kusto + ADLS), Payment Transactions data cube, corp.gold.transactions
- Pipeline failures: PMT (AnomalyReport, Bronze-BingAds, Bronze-LegacyBilling, Bronze-ModernBilling), NT (Load Dimensions), Fraud (PIMSEvents_Tests)
- Test failure tracking from App Insights

**CFS-Payments-DataPlatform-BIN** — BIN_Master_Databricks, BIN_Master_V2, BIN_Visa_Download, BIN_Visa_Load

**CFS-Payments-DataPlatform-BillingService** — BillingService-MasterPipeline-V2 (Synapse), Databricks job failures

**CFS-Payments-DataPlatform-COP** — COP pipeline alerts

**CFS-Payments-DataPlatform-PaymentInstrument** — NT pipelines, AU jobs

**CFS-PaymentsJournal** — Payments journal pipeline alerts

### Alert Severity Mapping

| SEV | Response | Notification |
|-----|----------|-------------|
| SEV1 | Immediate (< 15 min) | Page on-call + team lead |
| SEV2 | Urgent (< 30 min) | Team notification + lead |
| SEV3 | High (< 2 hours) | Team notification (standard for all deployed alerts) |
| SEV4 | Normal (< 24 hours) | Daily digest |

## Subject Area Upstream Sources

Understanding upstream dependencies is critical for alert triage:

| Subject Area | Primary Upstream Sources |
|-------------|------------------------|
| PMT / PJ | EventHub (`pdp-eventhub-prod-westus2-big`), Cosmos (historical) |
| COP | Provider fee files (Amex, Fiserv), Recon Parquet, EventHub (`cop` topic) |
| Fraud / PIMS | Kusto PIMS Events table |
| NT | PIMS File Stores (Legacy + Modern), NTS Logs (Cosmos, Request, Notification) |
| AU | Kusto AU Event Tables (9+ tables) |
| BIN | Card network draft files (Visa, MC, Amex, FDC, JCB, Discover, CUP, ELO) via API/SFTP |
| Billing | Modern Billing Journal EH, MCF EH, Legacy CTP SStream |

## Key Metrics to Monitor

### Data Quality Metrics
- Test pass rate (by subject area, by severity)
- Time since last successful test run
- Number of open SEV1/SEV2 incidents
- Trend: failure rate over 7/30/90 days

### Pipeline Health Metrics
- Data freshness (time since last record in Gold)
- Processing lag (EventHub consumer lag)
- Job failure rate
- Cluster utilization

### Business Metrics (indirect)
- Transaction volume trends (sudden drops indicate issues)
- Provider mix changes
- Geographic distribution shifts
