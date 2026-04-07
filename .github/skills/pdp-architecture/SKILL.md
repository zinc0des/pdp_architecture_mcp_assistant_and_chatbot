---
name: pdp-architecture
description: "Use this skill when the user asks about the Payments Data Platform (PDP) architecture, system design, Bronze/Silver/Gold layers, data flow and lineage, Databricks, Synapse, Event Hub, domain schemas, pipeline orchestration, Grafana/App Insights monitoring, or PDP security and RBAC."
metadata:
  version: "1.0"
  category: architecture
---

# PDP Architecture Assistant Skill

Use this skill to answer questions about the internal architecture, data flows,
infrastructure, and engineering patterns of the Payments Data Platform (PDP).

## When to Use

- User asks about PDP system design, layers, or topology
- User asks about data flows (Bronze → Silver → Gold)
- User asks about infrastructure (Azure resources, Bicep, EV2)
- User asks about domain schemas (PMT, COP, Fraud, NT, AU, BIN)
- User asks about pipeline orchestration (Synapse, Databricks)
- User asks about engineering patterns (Delta Lake, streaming, schema evolution)
- User asks about monitoring and alerting (Grafana, App Insights, ICM)
- User asks about security and access control (RBAC, networking)

## Available Tools

| Tool | Purpose |
|------|---------|
| `list_architecture_topics` | List all 12 KB topics |
| `get_architecture_topic` | Load full topic content |
| `search_architecture` | Keyword search across all topics |
| `get_layer_detail` | Deep-dive on specific layer (1-8) |
| `get_domain_schema` | Get schema info for a domain |
| `get_data_flow` | Get end-to-end data lineage |
| `grafana_get_alert_resolution_guidance` | Alert resolution steps |
| `grafana_get_upstream_check_guidance` | Upstream data source checks |
| `grafana_diagnose_network_issues` | Network diagnostics |
| `grafana_get_alert_best_practices` | Alert best practices |
| `grafana_analyze_alert_pattern` | Pattern analysis |
| `harvest_pdp_learnings` | Extract learnings (trigger: "thanks pdp") |
| `validate_pdp_relevance` | Check PDP relevance |
| `search_learnings` | Search harvested learnings |
| `list_learnings` | List recent learnings |
| `scan_repos_for_knowledge` | Scan repos for changes |

## How to Use

1. For general architecture questions: use `search_architecture` first
2. For layer-specific questions: use `get_layer_detail` directly
3. For schema questions: use `get_domain_schema`
4. For data flow questions: use `get_data_flow`
5. For alert investigation: use the `grafana_*` tools
6. Always cite the specific layer, domain, or topic in responses
