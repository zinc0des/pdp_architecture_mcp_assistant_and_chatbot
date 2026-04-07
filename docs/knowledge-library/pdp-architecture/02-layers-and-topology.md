# PDP Architectural Layers and Topology

## 8 Layers of PDP Architecture

PDP follows a layered architecture with clear separation of concerns.
Each layer has distinct responsibilities, teams, and technology choices.

### Layer 1 — Ingestion

**Purpose**: Receive raw data from source systems into PDP.

- **Event Hubs**: Primary real-time ingestion (PayHub events, PIMS fraud events, Billing journals)
- **Cosmos Change Feed**: CDC from operational stores
- **Batch sources**: SStream files, Azure Blob drops, scheduled API pulls
- **Key patterns**: Consumer groups per downstream, checkpointing, at-least-once delivery

### Layer 2 — Streaming

**Purpose**: Real-time processing of ingested events.

- **Spark Structured Streaming**: Primary streaming engine on Databricks
- **Kusto Direct Ingest**: For near-real-time analytics tables
- **Patterns**: Trigger modes (availableNow for batch, processingTime for continuous)
- **Checkpoint management**: ADLS-based reliable checkpointing

### Layer 3 — Processing (Medallion Architecture)

**Purpose**: Transform raw data through progressive quality levels.

- **Bronze**: Raw, unprocessed data as received from source. Schema-on-read.
- **Silver**: Cleaned, deduplicated, and typed. Business rules applied. Join-enriched.
- **Gold**: Business-ready aggregates, star schemas, consumer-facing datasets.
- **Key operations**: Deduplication, normalization, enrichment, aggregation

### Layer 4 — Data (Storage)

**Purpose**: Persistent storage of all data assets.

- **ADLS Gen2**: Primary data lake storage for Delta tables
- **Delta Lake**: ACID transactions, time travel, schema enforcement
- **Synapse SQL**: Serverless SQL for ad-hoc querying
- **Kusto DB**: Time-series analytics and operational dashboards
- **Patterns**: Liquid clustering (new), partition pruning, Z-ORDER optimization

### Layer 5 — Serving

**Purpose**: Expose processed data to consumers.

- **AAS Cubes** (Azure Analysis Services): Pre-aggregated OLAP cubes for Power BI
- **Kusto Analytics**: Real-time analytics queries
- **Semantic Models**: Power BI semantic layer for self-service
- **Delta Sharing**: Cross-team data sharing

### Layer 6 — Presentation

**Purpose**: End-user facing tools and interfaces.

- **Power BI**: Primary BI tool for reports and dashboards
- **Kusto Dashboards**: Real-time operational dashboards
- **MCP AI Agents**: Copilot-powered analytics (payment_analyst, architecture assistant)
- **APIs**: Programmatic data access for partner teams

### Layer 7 — Quality

**Purpose**: Ensure data accuracy, completeness, and freshness.

- **DQ Framework**: Custom PySpark-based test framework
- **Test types**: Functional, Integration, Diff, Canary
- **Monitoring**: Grafana dashboards, App Insights telemetry
- **Alerting**: ICM integration, PagerDuty, Teams notifications
- **Severity**: SEV1-SEV4 tiered response

### Layer 8 — Orchestration

**Purpose**: Schedule, coordinate, and deploy data workflows.

- **Synapse Pipelines**: Batch orchestration, triggers, linked services
- **Databricks Jobs**: Notebook/JAR workflows, continuous streaming jobs
- **EV2 (Express v2)**: Safe deployment across environments
- **Bicep**: Infrastructure as Code for Azure resources
- **Databricks Asset Bundles**: Job and cluster configuration as YAML

## Component Topology

```
Source Systems (PayHub, PIMS, Cosmos, Batch)
    │
    ▼
┌─────────────────────────────────────────┐
│  Layer 1: Ingestion (Event Hubs, CDC)   │
└─────────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────────┐
│  Layer 2: Streaming (Spark SS, Kusto)   │
└─────────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────────┐
│  Layer 3: Processing (Bronze→Silver→Gold)│
└─────────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────────┐
│  Layer 4: Data (ADLS, Delta, Kusto)     │
└─────────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────────┐
│  Layer 5: Serving (AAS, Semantic, API)  │
└─────────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────────┐
│  Layer 6: Presentation (PBI, Kusto, AI) │
└─────────────────────────────────────────┘

Cross-cutting:
┌─────────────────────────────────────────┐
│  Layer 7: Quality (DQ, Grafana, ICM)    │
│  Layer 8: Orchestration (Synapse, EV2)  │
└─────────────────────────────────────────┘
```
