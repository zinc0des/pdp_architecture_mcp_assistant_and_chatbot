# PDP Platform Overview

## What is PDP?

The **Payments Data Platform (PDP)** is Microsoft's central data platform for payments analytics,
reporting, and operational intelligence. It ingests, processes, and serves payments data across
all Microsoft commerce payment flows.

## Strategic Purpose

- **Single source of truth** for payments data across Microsoft Commerce
- **Enable data-driven decisions** for payments optimization (approval rates, cost reduction, fraud prevention)
- **Self-service analytics** via Power BI, Kusto, and AI-powered tools
- **Real-time monitoring** of payment system health and data quality

## Scale

- Processes billions of payment transactions annually
- Covers 200+ countries/regions
- Supports 100+ payment providers globally
- Near real-time data freshness (minutes for streaming, hours for batch)

## Tech Stack Summary

| Layer | Technology |
|-------|-----------|
| Ingestion | Azure Event Hubs, Cosmos Change Feed, Batch files |
| Processing | Databricks (Spark), Synapse Analytics |
| Storage | ADLS Gen2, Delta Lake |
| Serving | Kusto (Azure Data Explorer), AAS Cubes, Semantic Models |
| Presentation | Power BI, Kusto Dashboards, MCP AI Agents |
| Orchestration | Synapse Pipelines, Databricks Jobs, EV2, Bicep |
| Quality | Custom DQ Framework, Grafana, App Insights, ICM |

## Subject Areas (Domains)

| Domain | Code | Description |
|--------|------|------------|
| Payment Transactions | PMT | Core transaction lifecycle (auth, capture, settle, refund) |
| Cost of Payments | COP | Provider fees, interchange, processing costs |
| Fraud | Fraud | PIMS events, risk scoring, fraud detection |
| Network Tokenization | NT | Token provisioning, lifecycle, DPAN management |
| Account Updater | AU | Card-on-file update events |
| BIN | BIN | Bank Identification Number lookups and enrichment |
| Reconciliation | Recon | Variance detection between systems |
| Payments Journal | PJ | Streaming journal of all payment events |
| Billing | Billing | Billing events, commercial and consumer |

## Repositories

| Repo | Purpose |
|------|---------|
| Commerce.PaymentsDataPlatform | Core platform (PMT, Kusto, Synapse, shared infra) |
| CFS-Payments-DataPlatform-PaymentsJournal | Payments Journal streaming pipeline |
| CFS-Payments-DataPlatform-COP | Cost of Payments domain |
| CFS-Payments-DataPlatform-BIN | BIN domain |
| CFS-Payments-DataPlatform-BillingService | Billing domain |
| CFS-Payments-DataPlatform-PaymentInstrument | NT + AU domains |
| CFS-Payments-DataPlatform-MCP | MCP server (Copilot tools for data queries) |
| pdp-dev-mcp | Dev MCP server (architecture assistant, code review, DQ tools) |
