# PDP Security and Access Control

## RBAC (Role-Based Access Control)

### Databricks Access
- Workspace-level access groups (readers, contributors, admins)
- Table-level grants via Unity Catalog (where enabled)
- Service principals for automated jobs

### Azure Resource Access
- Managed identities for service-to-service auth
- Key Vault for secrets management
- RBAC roles: Reader, Contributor, Owner per resource group

## Networking

### VNet Integration
- All Databricks workspaces deployed in managed VNets
- Private endpoints for Storage, EventHub, Key Vault
- No public internet access for data-plane operations

### Network Security Groups (NSGs)
- Restrict inbound/outbound traffic by port and source
- Databricks control plane access via secure cluster connectivity

### Private Endpoints

| Service | Private Endpoint |
|---------|-----------------|
| ADLS Gen2 | Blob, DFS endpoints |
| Event Hubs | Namespace endpoint |
| Key Vault | Vault endpoint |
| Synapse | SQL, Dev endpoints |
| Kusto | Cluster endpoint |

## Secrets Management

### Azure Key Vault
- All connection strings, API keys stored in Key Vault
- Databricks secret scopes backed by Key Vault
- Rotation policies for service principal credentials

### Secret Scopes (Databricks)
```python
dbutils.secrets.get(scope="pdp-keyvault", key="eventhub-connection-string")
```

## Compliance

### Data Classification
- Payment data classified as **Highly Confidential**
- PII fields (cardholder name, PAN) handled per PCI-DSS
- Tokenized/masked in analytics tables

### Audit Logging
- Azure Activity Logs for resource changes
- Databricks Audit Logs for workspace activity
- Delta Lake history for data changes

### Retention
- Bronze: 90 days (raw data retention)
- Silver: 1 year
- Gold: 3+ years (business reporting)
- Kusto: Hot cache 30 days, cold storage 2 years

## PCI-DSS Considerations
- No full PAN stored in PDP analytics tables
- Tokenized identifiers used throughout
- Network isolation for payment data processing
- Encryption at rest (Azure Storage encryption) and in transit (TLS 1.2+)
