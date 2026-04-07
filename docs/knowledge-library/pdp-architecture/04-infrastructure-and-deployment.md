# PDP Infrastructure and Deployment

## Azure Resources

### Core Resources (per environment)

| Resource | Purpose |
|----------|---------|
| ADLS Gen2 Storage Account | Delta Lake storage for all medallion layers |
| Azure Databricks Workspace | Spark processing, streaming, notebooks |
| Azure Synapse Analytics | Pipeline orchestration, serverless SQL |
| Azure Event Hubs Namespace | Real-time event ingestion |
| Azure Data Explorer (Kusto) | Time-series analytics |
| Azure Analysis Services | OLAP cubes for Power BI |
| Azure Key Vault | Secrets, connection strings |
| Azure Monitor / App Insights | Telemetry, logging, alerting |
| Grafana (Azure Managed) | DQ dashboards |

### Networking

- **VNet Integration**: All services connected via managed VNet
- **Private Endpoints**: Storage, EventHub, Key Vault accessed via private endpoints
- **NSGs**: Network Security Groups restricting traffic flow
- **No public internet access** for data-plane operations

## Environment Matrix

| Environment | Purpose | Workspace |
|-------------|---------|-----------|
| CORP-Test | Development and testing (corporate network) | Dev Databricks |
| CORP-Prod | Not used for PDP | — |
| PME-Test | Pre-production validation (production-mirrored) | PME Test Databricks |
| PME-Prod | Production workloads | PME Prod Databricks |

## Infrastructure as Code (Bicep)

- All Azure resources defined in Bicep templates
- Located in `deployment/bicep/` per repository
- Parameterized by environment (test/prod)
- Deployed via EV2 service deployment

### Bicep Pattern
```
deployment/
  bicep/
    alert.bicep          # Alert rules
    alert_PME.bicep      # PME-specific alert rules
    mainAlerts.bicep      # Main alert orchestration
    mainAlerts_PME.bicep  # PME alert orchestration
    install_bicep.ps1     # Installation script
```

## EV2 (Express v2) Deployment

- Safe deployment framework for Azure resources
- Rollout specifications define deployment order
- Supports staged rollouts with health checks
- Located in `deployment/ev2/` per repository

### EV2 Structure
```
deployment/
  ev2/
    buildver.txt
    Alerts/              # Alert deployment specs
    AssetBundle/         # Databricks asset bundles
    Databricks/          # Notebook/cluster deployment
    DataPlane/           # Data-plane configurations
    Parameters/          # Environment-specific parameters
```

## Databricks Asset Bundles

- Job definitions as YAML in `src/databricks/workspace/resources/`
- Deployed via `databricks bundle deploy`
- Naming: `{Component}_{Action}_Job.yml`
- Bundle config in `databricks.yml` with target environments

### Target Environments
```yaml
targets:
  dev:
    mode: development
  pme_test:
    workspace:
      host: https://adb-xxx.azuredatabricks.net
  pme_prod:
    workspace:
      host: https://adb-yyy.azuredatabricks.net
```
