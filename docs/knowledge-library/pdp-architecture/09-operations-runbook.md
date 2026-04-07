# PDP Operations Runbook

## Backfill Procedures

### When to Backfill
- After a schema change that requires reprocessing
- After fixing a bug that corrupted data in a specific time range
- After upstream source provides corrected historical data
- After deploying a new enrichment that should apply retroactively

### Backfill Steps
1. **Identify scope**: Time range, affected tables, upstream dependency
2. **Prepare**: Create backfill job with parameterized date range
3. **Test**: Run on a small date range in PME-Test first
4. **Execute**: Run in production with monitoring
5. **Validate**: Run DQ tests on backfilled data
6. **Document**: Log the backfill in the operations journal

### Backfill Patterns
- **Full table rebuild**: Truncate and reload (rare, only for small tables)
- **Time-range reprocess**: Reprocess specific date partitions
- **Incremental catch-up**: Resume from a watermark with `availableNow=True`

## Incident Response

### Step-by-Step
1. **Detect**: Alert fires in Grafana or ICM
2. **Assess**: Check severity, impacted domain, blast radius
3. **Triage**: Determine root cause category (data, infra, upstream, code)
4. **Mitigate**: Apply immediate fix (restart job, manual data correction)
5. **Communicate**: Update stakeholders via Teams/ICM
6. **Resolve**: Deploy permanent fix
7. **Post-mortem**: Document in TSG for future reference

### Common Incident Types

| Type | Symptoms | Typical Resolution |
|------|----------|-------------------|
| Pipeline stall | No new data in Gold | Restart streaming job, check cluster |
| Data gaps | Missing records | Check EventHub offsets, backfill |
| Schema break | Processing errors | Fix schema, deploy, reprocess |
| Provider outage | Zero volume from one provider | Wait for provider, backfill later |
| Infra failure | Cluster unreachable | Check Databricks workspace health |

## Gold Table Reprocessing (BillingService)

### TSG: Gold Billing Reprocess
1. Stop the continuous Gold-Billing streaming job
2. Delete checkpoint for the affected consumer group
3. Set eventHub offset to desired replay point
4. Restart the job — it will reprocess from the offset
5. Monitor for duplicates (Smart Merge handles most cases)
6. Run DQ tests to validate

## Useful Commands

### Check Databricks Job Status
- Workspace UI → Jobs → Search by job name
- Look for failed/pending/running status

### Check EventHub Lag
- Azure Portal → EventHub Namespace → Consumer Groups
- Compare incoming vs outgoing offsets

### Check Delta Table History
```sql
DESCRIBE HISTORY gold.fact_transactions LIMIT 20
```

### Check Data Freshness
```sql
SELECT MAX(ProcessedDate) as latest FROM gold.fact_transactions
```
