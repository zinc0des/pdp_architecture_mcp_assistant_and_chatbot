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
- **Integration**: Auto-create incidents on SEV1/SEV2 DQ failures
- **Routing**: Based on subject area → team mapping
- **SLA tracking**: Time to acknowledge, time to mitigate, time to resolve

## Alert Configuration

### Alert Naming Convention
```
PDP Alert | {SEV} | {SubjectArea} | {TestType} | {Description}
```
Examples:
- `PDP Alert | SEV3 | PMT | Functional | Null PaymentMethodFamily in Gold`
- `PDP Alert | SEV2 | BillingService | Integration | Bronze-Gold count mismatch`

### Alert Severity Mapping

| SEV | Response | Notification |
|-----|----------|-------------|
| SEV1 | Immediate (< 15 min) | Page on-call + team lead |
| SEV2 | Urgent (< 30 min) | Team notification + lead |
| SEV3 | High (< 2 hours) | Team notification |
| SEV4 | Normal (< 24 hours) | Daily digest |

## Subject Area Upstream Sources

Understanding upstream dependencies is critical for alert triage:

| Subject Area | Primary Upstream Sources |
|-------------|------------------------|
| PMT | PayHub EventHub, Provider APIs |
| COP | Provider fee files (Blob), Billing APIs |
| Fraud | PIMS EventHub |
| NT | Token service EventHub |
| AU | Account updater service EventHub |
| BIN | BIN file drops (Blob) |
| Journal | PayHub EventHub (same as PMT, different consumer group) |
| Billing | Modern Billing EH, MCF EH, Legacy SStream |

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
