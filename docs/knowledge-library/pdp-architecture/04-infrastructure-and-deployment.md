# PDP Infrastructure and Deployment

## Azure Resources

### Core Resources (per environment)

| Resource | Purpose |
|----------|---------|
| ADLS Gen2 Storage Account | Delta Lake storage for all medallion layers |
| Azure Databricks Workspace | Spark processing, streaming, notebooks |
| Azure Synapse Analytics | Pipeline orchestration, serverless SQL |
| Azure Event Hubs Namespace | Real-time event ingestion |
| Azure Data Explorer (Kusto) | Time-series analytics, materialized views |
| Azure Analysis Services | OLAP cubes for Power BI |
| Azure Key Vault | Secrets, connection strings |
| Azure Monitor / App Insights | Telemetry, logging, alerting |
| Azure Managed Grafana | DQ dashboards, freshness panels |
| Azure Logic App | Email processing (BIN domain) |
| Azure Function App | Utility functions |
| Azure Fabric | Emerging data platform integration |

### Networking

- **VNet Integration**: All services connected via managed VNet (`vnet.bicep`, `vnet_PME.bicep`)
- **Private Endpoints**: Storage, EventHub, Key Vault accessed via private endpoints (`privateEndpoint.bicep`)
- **Network Security Perimeter**: NSP configuration (`nsp.bicep`)
- **NSGs**: Network Security Groups restricting traffic flow
- **Power BI VNet**: Dedicated VNet for Power BI gateway (`vnetPowerBi.bicep`)
- **No public internet access** for data-plane operations

## Environment Matrix

| Environment | Subscription | Resource Group |
|-------------|-------------|----------------|
| CORP-Test | `dc958e7f-...` | `payDataPlat-test-rg` |
| PME-Test | `128496e3-...` | `payDataPlat-pme-test-rg` (West US) |
| PME-Prod | `abf75b9d-...` | `payDataPlat-pme-prod-rg` (West US) |

**Note:** PaymentsJournal also has a separate Dev environment.

## Infrastructure as Code (Bicep)

All Azure resources are defined in Bicep templates, located in `deployment/bicep/` per repository.

### Bicep Inventory by Repo

| Repo | Files | Scope |
|------|-------|-------|
| **Commerce.PaymentsDataPlatform** (main) | **36 files** | Full infra: Synapse, Databricks, Storage, Kusto, VNets, Workbooks, Alerts |
| **CFS-Payments-DataPlatform-BIN** | 7 files | Alerts + Logic App |
| **CFS-Payments-DataPlatform-COP** | 5 files | Alerts only |
| **CFS-Payments-DataPlatform-BillingService** | 5 files | Alerts only |
| **CFS-Payments-DataPlatform-PaymentInstrument** | 5 files | Alerts only |
| **CFS-PaymentsJournal** | 4 files | Alerts only |

### Main PDP Repo Bicep Categories

**Infrastructure (8 files):**
- `vnet.bicep`, `vnet_PME.bicep`, `vnetUpload.bicep`, `vnetPowerBi.bicep`
- `nsp.bicep`, `privateEndpoint.bicep`
- `keyVault.bicep`, `userAssignedIdentities.bicep`, `adlsAcl.bicep`

**Data Resources (9 files):**
- `synapse.bicep`, `databricks.bicep`, `databricks_PME.bicep`
- `storage.bicep`, `eventHubs.bicep`, `fabric.bicep`
- `logAnalytics.bicep`, `appInsights.bicep`, `kusto.bicep`

**Monitoring & Dashboards (6 files):**
- `alert.bicep`, `alert_PME.bicep`
- `paymentsDataQualityDashboard.bicep`, `prodDiffDashboard.bicep`
- `reliabilityWorkbook_Test.bicep`, `reliabilityWorkbook_PME.bicep`

**Orchestration Entry Points:**
- `mainAlerts.bicep`, `mainAlerts_PME.bicep` (alert deployment)
- `mainInfra.bicep`, `mainInfra_PME.bicep` (infrastructure deployment)

### Domain Repo Bicep Pattern (common across BIN, COP, BillingService, PI)
```
deployment/bicep/
  alert.bicep           # Alert rule definitions
  alert_PME.bicep       # PME-specific alert rules
  mainAlerts.bicep      # Main alert entry point
  mainAlerts_PME.bicep  # PME alert entry point
  install_bicep.ps1     # Bicep CLI installation script
```

## EV2 (Express v2) Deployment

Safe deployment framework for Azure resources with phased rollouts and health checks.

### EV2 Standard Structure (all repos)
```
deployment/ev2/
├── buildver.txt                # Version (e.g., 1.0.0.0)
├── Alerts/                     # Alert deployment specs
│   ├── ServiceModel.Test.json
│   ├── ServiceModel.PME.Test.json
│   ├── ServiceModel.PME.Prod.json
│   ├── RolloutSpec.Test.json
│   ├── RolloutSpec.PME.Test.json
│   ├── RolloutSpec.PME.Prod.json
│   └── ScopeBindings.json
├── AssetBundle/                # Bundled artifacts (Dev staging)
├── Databricks/                 # DAB deployment scripts
│   ├── DABDeployment.ps1       # Deploy Databricks Asset Bundles
│   ├── ExecuteTests.ps1        # Integration test execution
│   └── DeployAlert.ps1         # Alert deployment (not currently invoked)
├── DataPlane/                  # Data-plane deployment specs
│   ├── ServiceModel.{ENV}.json
│   ├── RolloutSpec.{ENV}.json
│   └── ScopeBindings.{ENV}.json
├── Parameters/                 # Environment-specific parameter files
│   ├── Alerts.{ENV}.parameters.{tier}.json
│   ├── ExecuteDAB.{ENV}.parameters.{tier}.json
│   └── ExecuteAlert.{AREA}.parameters.{tier}.json
└── Templates/                  # ARM templates (placeholder .keep files)
```

### EV2 Parameter File Naming Convention
| Purpose | Pattern | Example |
|---------|---------|---------|
| Alert parameters | `Alerts.{ENV}.parameters.{tier}.json` | `Alerts.PME.parameters.prod.json` |
| DAB execution | `ExecuteDAB.{ENV}.parameters.{tier}.json` | `ExecuteDAB.PME.parameters.test.json` |
| Alert execution | `ExecuteAlert.{AREA}.parameters.{tier}.json` | `ExecuteAlert.PME.parameters.prod.json` |
| Synapse triggers | `Synapse.HttpExtension.{ACTION}.{DOMAIN}.{ENV}.parameters.{tier}.json` | `Synapse.HttpExtension.StartTriggers.BIN.PME.parameters.prod.json` |

### EV2 Deployment Flow
```
Official Build Pipeline
  → 1. Compile Bicep → ARM Templates
  → 2. Create AssetBundle (Templates + Parameters + Scripts)
  → 3. EV2 Orchestration (Safe Deployment)
      ├─ Validate templates & parameters
      ├─ Deploy to Test environment
      ├─ Deploy to PME Test environment
      ├─ Deploy to PME Prod environment
      ├─ Monitor health metrics
      └─ Auto-rollback on failure
  → 4. Notification (pdp_dev@microsoft.com on error/complete)
```

- **Rollout type**: `Major` (safe, phased, monitored)
- **Shell image**: `adm-mariner-20-l:v12` (for DAB deployments)
- **Notification**: Email to `pdp_dev@microsoft.com` on `onError` and `onComplete`

## Databricks Asset Bundles

- Job definitions as YAML in `src/databricks/workspace/resources/`
- Deployed via `databricks bundle deploy` (orchestrated by `DABDeployment.ps1`)
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
