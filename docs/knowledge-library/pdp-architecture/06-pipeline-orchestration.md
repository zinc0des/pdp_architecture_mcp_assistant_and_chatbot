# PDP Pipeline Orchestration

## Overview

PDP uses two primary orchestration engines: **Synapse Pipelines** for batch workflows
and **Databricks Jobs** for streaming and notebook-based processing.

## Synapse Pipelines

### Structure
- Pipelines defined in Synapse Studio or ARM/Bicep
- Triggers: Schedule, Tumbling Window, Event-based
- Activities: Copy, Notebook, Dataflow, Web, ForEach

### Common Pipeline Patterns
1. **Ingest → Process → Publish**: Copy from source, run notebook, update state
2. **Incremental load**: Watermark-based extraction with tumbling window triggers
3. **Backfill**: Parameterized pipelines with date range inputs

### Key Pipelines (PMT)
- Transaction ingestion pipeline (scheduled hourly)
- Cube refresh pipeline (scheduled after gold processing)
- DQ test execution pipeline (scheduled daily)

## Databricks Jobs

### Job Types
- **Continuous streaming** (`continuous: pause_status: UNPAUSED`)
  - Used for: EventHub consumers, streaming transformations
  - Example: Modern Billing ingestion, MCF ingestion, Gold-Billing processor
- **Scheduled batch** (`trigger` or `schedule` sections)
  - Used for: Backfills, aggregations, DQ tests
  - Example: SubscriptionEvent processing, historical reprocessing

### Databricks Asset Bundles (DAB)
- YAML-defined job configurations in `src/databricks/workspace/resources/`
- Naming: `{Component}_{Action}_Job.yml`
- Deploy via `databricks bundle deploy -t {target}`

### Job Configuration Pattern
```yaml
resources:
  jobs:
    my_job:
      name: "My Job Name"
      job_clusters:
        - job_cluster_key: main_cluster
          new_cluster:
            instance_pool_id: ${var.pool_id}
            spark_version: 18.0.x-scala2.12
            num_workers: 4
      tasks:
        - task_key: process
          job_cluster_key: main_cluster
          notebook_task:
            notebook_path: /Workspace/notebooks/Domain/Process.py
            source: WORKSPACE
      tags:
        DataGroup: PDP
        SubjectArea: MyDomain
```

### Trigger Modes
- `trigger(availableNow=True)`: Process all available data then stop (batch streaming)
- `trigger(processingTime="30 seconds")`: Continuous micro-batch (real-time)
- Databricks job schedule: Cron-based for periodic batch runs

## DQ Test Orchestration

- Tests run as Databricks jobs triggered on schedule
- Results published to App Insights
- Grafana dashboards poll App Insights for visualization
- ICM alerts fire on SEV1/SEV2 failures

## Deployment Flow

```
Code commit → PR → Merge to main
  → OneBranch CI build
    → EV2 deployment (Bicep resources)
    → DAB deployment (Databricks jobs + notebooks)
    → Synapse deployment (pipelines + linked services)
```
