# PDP Reliability and Data Quality

## DQ Framework Overview

PDP uses a custom PySpark-based data quality framework for automated testing.

### Test Types

| Type | Purpose | Trigger |
|------|---------|---------|
| Functional | Validate business rules on data | Scheduled (daily) |
| Integration | Cross-system consistency checks | Scheduled (daily) |
| Diff | Compare current vs baseline data | Scheduled (daily) |
| Canary | Lightweight freshness/health checks | Scheduled (hourly) |

### Test Convention
- All tests use `@pytest.mark.testclassification` decorator
- Severity: Always SEV3 (never SEV1/SEV2 in test definitions)
- Test IDs: Unique format `{area}-func-{NNN}` (e.g., `pb-func-001`)
- Alert naming: `PDP Alert | {SEV} | {Pipeline} | {Description}`

### Test Location
- Tests in `src/databricks/workspace/notebooks/{SubjectArea}/Test/`
- Each subject area has its own test directory
- Shared utilities in `PDPCommon` package

## Alert Severity Levels

| Severity | Response Time | Impact | Action |
|----------|--------------|--------|--------|
| SEV1 | < 15 min | Critical production impact | Page on-call immediately |
| SEV2 | < 30 min | High impact, data degradation | Notify team lead |
| SEV3 | < 2 hours | Significant but localized | Team notification |
| SEV4 | < 24 hours | Low impact, minor deviation | Track for trending |

## Monitoring Stack

### Grafana
- PDP DQ Dashboard (primary operational view)
- Alert rules fire on test failures
- Dashboard panels per subject area and test type

### App Insights
- Test results published as custom events
- Query via KQL for historical analysis
- Custom dimensions: test_id, subject_area, severity, test_type

### ICM (Incident Management)
- SEV1/SEV2 failures auto-create ICM incidents
- On-call rotation per subject area
- Escalation chains defined per severity

## Reliability Patterns

### Idempotent Processing
- All pipelines designed for safe re-execution
- MERGE operations handle duplicates gracefully
- Watermark-based state tracking prevents reprocessing

### At-Least-Once Delivery
- EventHub guarantees at-least-once delivery
- Deduplication in Silver layer handles duplicates
- Checkpoint-based recovery after failures

### Circuit Breaker
- Pipelines detect upstream failures and pause
- Prevents cascade of bad data through medallion layers
- Manual intervention to resume after root cause resolved

### Data Freshness SLAs

| Domain | Freshness Target |
|--------|-----------------|
| PMT (streaming) | < 30 minutes |
| PMT (batch) | < 4 hours |
| COP | < 24 hours |
| Fraud | < 15 minutes |
| BIN | < 24 hours |
| Journal | < 5 minutes |
