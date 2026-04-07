"""
Architecture Knowledge Base Tools

MCP-decorated tools that expose the PDP Architecture knowledge library to AI agents.
Each tool wraps a service function from architecture_service.py.
"""

from typing import Optional

from pdp_dev_mcp.mcp_instance import mcp
from pdp_dev_mcp.common import logger
from . import architecture_service as service


@mcp.tool()
def list_architecture_topics() -> list[dict[str, str]]:
    """List all available PDP architecture knowledge base topics.
    Returns topic keys and descriptions to help decide which topic to query.

    Topics cover: platform overview, architectural layers, data flow & lineage,
    infrastructure & deployment, domain models, pipeline orchestration, engineering patterns.
    """
    return service.list_topics()


@mcp.tool()
def get_architecture_topic(topic: str) -> str:
    """Retrieve the full content of a PDP architecture knowledge base topic.

    Available topics:
    - overview: What PDP is, strategic purpose, tech stack
    - layers: 8 architectural layers (Ingestion → Orchestration), topology
    - data-flow: End-to-end Bronze→Silver→Gold per domain, streaming vs batch
    - infrastructure: Azure resources, Bicep IaC, EV2, environment matrix
    - domains: Per-domain tables/schemas (PMT, COP, Fraud, NT, AU, BIN)
    - pipelines: Synapse/Databricks orchestration, schedules, DQ monitoring
    - patterns: Delta Lake ops, streaming, schema evolution, shadow testing

    Use list_architecture_topics() first if unsure which topic to query.
    For a specific question, use search_architecture() for targeted results.
    """
    return service.get_topic_content(topic)


@mcp.tool()
def search_architecture(query: str) -> list[dict]:
    """Search across all PDP architecture knowledge base files by keywords.

    Performs keyword search across all topic files AND harvested learnings,
    returning matching sections with surrounding context. Use space-separated
    terms — results include lines matching any term, ranked by relevance.

    Searches BOTH:
    - Static knowledge base (docs/knowledge-library/pdp-architecture/)
    - Harvested learnings (knowledge-vault/learnings/)

    Good for questions like:
    - "EventHub partitions streaming checkpoint"
    - "gold transactions star schema"
    - "Bicep EV2 deployment"
    - "shadow testing production"
    """
    return service.search_knowledge_base(query)


@mcp.tool()
def get_layer_detail(layer_name: str) -> str:
    """Get detailed information about a specific PDP architecture layer.

    PDP has 8 layers:
    1. Ingestion — Event Hubs, Cosmos Change Feed, batch sources
    2. Streaming — Spark Structured Streaming, Kusto direct ingest
    3. Processing — Medallion architecture (Bronze/Silver/Gold)
    4. Data — ADLS Gen2, Delta Lake, Synapse SQL, Kusto DB
    5. Serving — AAS Cubes, Kusto analytics, Semantic Models
    6. Presentation — Power BI, Kusto Dashboards, MCP AI Agents
    7. Quality — DQ Framework, Azure Monitor, ICM alerts
    8. Orchestration — Synapse Pipelines, Databricks Jobs, EV2, Bicep

    Accepts layer name or number (e.g., 'ingestion', '3', 'processing', 'medallion').
    """
    return service.get_layer_detail(layer_name)


@mcp.tool()
def get_domain_schema(domain: str) -> str:
    """Get schema and table information for a specific PDP data domain.

    Available domains:
    - PaymentTransactions (or PMT) — gold star schema: FactTransactions + dimensions
    - PaymentsJournal (or journal) — streaming pipeline, payments_journal tables
    - COP (Cost of Payments) — fee analytics, billed fees
    - Fraud (or risk) — PIMS events, fraud detection
    - NT (Network Tokenization) — token lifecycle
    - AU (Account Updater) — card-on-file updates
    - BIN — Bank Identification Number lookups
    - Recon (Reconciliation) — variance detection
    """
    return service.get_domain_schema(domain)


@mcp.tool()
def get_data_flow(domain: Optional[str] = None) -> str:
    """Get data flow and lineage information for PDP.

    Returns end-to-end data flow documentation showing how data moves from
    source systems through Bronze→Silver→Gold layers to serving endpoints.

    Optionally filter by domain to see domain-specific flow (e.g., PaymentsJournal
    4-stage silver pipeline, or Fraud PIMS events flow).
    """
    return service.get_data_flow(domain)
