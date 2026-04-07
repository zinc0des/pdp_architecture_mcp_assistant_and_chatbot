# PDP Grafana Alert Best Practices

## Alert Investigation Methodology

### 1. Initial Triage
- **Read the alert name carefully** — it follows the convention: `PDP Alert | SEV{n} | {SubjectArea} | {TestType} | {Description}`
- **Check severity** — SEV1/SEV2 require immediate attention; SEV3/SEV4 can be batched
- **Open the DQ Dashboard** — Verify the alert visually on the Payments DQ Dashboard
- **Note the time window** — When did the alert fire? Is it ongoing or resolved?

### 2. Understand the Test Type
- **Diff Tests**: Compare current data against a baseline or previous period. Failures indicate unexpected variance.
- **Functional Tests**: Validate business rules (e.g., "all gold records must have a PaymentMethodFamily"). Failures indicate data integrity issues.
- **Integration Tests**: Validate cross-system consistency (e.g., Bronze count should match EventHub ingestion). Failures indicate pipeline issues.
- **Canary Tests**: Lightweight health checks on freshness and basic counts. Failures indicate pipeline stalls.

### 3. Check Upstream Sources
- Every subject area has known upstream dependencies
- Check the upstream system's health before investigating downstream
- Common sources: EventHub, Cosmos Change Feed, Synapse Pipelines, Databricks Jobs

### 4. Check for Known Patterns
- **Weekend/holiday effects**: Lower volume is expected on weekends
- **Month-end spikes**: Higher transaction volumes at month-end
- **Deployment windows**: Upstream deployments can cause temporary gaps
- **Provider maintenance**: Payment providers have maintenance windows

### 5. Escalation Guidelines
- **SEV1**: Immediate escalation — page on-call, notify team lead
- **SEV2**: Urgent — notify team within 30 minutes
- **SEV3**: High priority — investigate within 2 hours, team notification
- **SEV4**: Normal — investigate within business day

## Common Root Causes

### Data Pipeline Issues
- **Checkpoint lag**: Spark streaming checkpoints falling behind
- **Schema mismatch**: Upstream schema change not reflected downstream
- **Cluster issues**: Databricks cluster failures or slow restarts
- **EventHub throttling**: Consumer group hitting partition limits

### Data Quality Issues
- **Null propagation**: Null values in key fields propagating through pipeline
- **Duplicate records**: Reprocessing or at-least-once delivery creating duplicates
- **Late-arriving data**: Data arriving after the test window has closed
- **Source system bugs**: Upstream systems sending malformed data

### Infrastructure Issues
- **Network connectivity**: VNet/Private Endpoint issues blocking data flow
- **Storage throttling**: ADLS Gen2 throttling on high-volume writes
- **Resource limits**: Memory/CPU limits causing OOM or slow processing

## Resolution Patterns

### Quick Fixes
1. **Restart the streaming job** — resolves transient checkpoint issues
2. **Check the Databricks job run** — look for failed/pending runs
3. **Verify EventHub consumer group** — ensure no stuck consumers
4. **Check Synapse pipeline status** — look for failed activities

### Deep Investigation
1. **Compare Bronze counts** — match against EventHub incoming message counts
2. **Check Silver transformations** — verify join conditions and filter logic
3. **Validate Gold merge** — ensure merge keys are correct and not creating dups
4. **Review Delta table history** — check for unexpected MERGE/DELETE operations

### Prevention
- Set up redundant alerts at multiple pipeline stages
- Use watermark-based freshness checks, not just count-based
- Implement dead-letter queues for malformed messages
- Add schema validation at ingestion time
