"""
Architecture Knowledge Base Service

Provides retrieval functions against the PDP Architecture knowledge library.
The knowledge base consists of pre-consolidated markdown files organized by topic,
located at docs/knowledge-library/pdp-architecture/.
"""

import os
from pathlib import Path
from typing import Optional

from pdp_dev_mcp.common import logger


def _resolve_project_root() -> Path:
    """Resolve the pdp-dev-mcp project root robustly.

    Tries in order:
    1. PDP_DEV_MCP_ROOT env var (explicit override — works everywhere)
    2. Source-layout traversal from __file__ (editable install / dev checkout)
    3. Common workspace-relative paths (for api/ or other callers)
    """
    env_root = os.environ.get("PDP_DEV_MCP_ROOT")
    if env_root:
        root = Path(env_root)
        kb = root / "docs" / "knowledge-library" / "pdp-architecture"
        if kb.is_dir():
            return root
        logger.warning("PDP_DEV_MCP_ROOT=%s set but KB dir not found at %s", env_root, kb)

    # Walk up from this file: src/pdp_dev_mcp/tools/architecture/ -> pdp-dev-mcp root
    candidate = Path(__file__).resolve().parents[4]
    kb = candidate / "docs" / "knowledge-library" / "pdp-architecture"
    if kb.is_dir():
        return candidate

    raise FileNotFoundError(
        "Could not locate KB directory. Set PDP_DEV_MCP_ROOT or run from the pdp-dev-mcp directory."
    )


_PROJECT_ROOT = _resolve_project_root()
KNOWLEDGE_BASE_DIR = _PROJECT_ROOT / "docs" / "knowledge-library" / "pdp-architecture"

# --------------------------------------------------------------------------- #
# Topic Registry
# --------------------------------------------------------------------------- #
TOPIC_REGISTRY: dict[str, dict[str, str]] = {
    "overview": {
        "file": "01-platform-overview.md",
        "description": "What PDP is, why it exists, strategic purpose, scale numbers, tech stack summary",
        "keywords": "pdp,platform,overview,purpose,scale,commerce,payments,what is,tech stack",
    },
    "layers": {
        "file": "02-layers-and-topology.md",
        "description": "8 architectural layers (Ingestion, Streaming, Processing, Data, Serving, Presentation, Quality, Orchestration), component topology",
        "keywords": "layer,topology,ingestion,streaming,processing,data,serving,presentation,quality,orchestration,architecture,lambda,medallion",
    },
    "data-flow": {
        "file": "03-data-flow-and-lineage.md",
        "description": "End-to-end data flow, Bronze to Silver to Gold per domain, streaming vs batch paths, table lineage",
        "keywords": "data flow,lineage,bronze,silver,gold,pipeline,eventhub,event hub,streaming,batch,delta,transform",
    },
    "infrastructure": {
        "file": "04-infrastructure-and-deployment.md",
        "description": "Azure resources, Bicep IaC, EV2 deployment, environment matrix (CORP/PME x Test/Prod), networking",
        "keywords": "infrastructure,deployment,bicep,ev2,azure,resource,environment,corp,pme,region,vnet,networking,iac",
    },
    "domains": {
        "file": "05-domain-models.md",
        "description": "Per-domain tables, schemas, relationships — PaymentTransactions, COP, Fraud, NT, AU, BIN, Recon",
        "keywords": "domain,model,schema,table,fact,dimension,payment transaction,cost of payment,fraud,network tokenization,account updater,bin,recon,star schema",
    },
    "pipelines": {
        "file": "06-pipeline-orchestration.md",
        "description": "Synapse pipelines, Databricks jobs/workflows, Bronze to Silver to Gold task chains, schedules, DQ monitoring",
        "keywords": "pipeline,orchestration,synapse,databricks,job,workflow,schedule,hourly,daily,trigger,task,dq,data quality",
    },
    "patterns": {
        "file": "07-engineering-patterns.md",
        "description": "Delta Lake operations, structured streaming, checkpoint management, schema evolution, shadow testing, merge/upsert, DQ framework",
        "keywords": "pattern,delta,streaming,checkpoint,schema evolution,shadow,merge,upsert,deduplication,dq framework,engineering,design",
    },
    "reliability": {
        "file": "08-reliability.md",
        "description": "DQ rule catalog, JSON DQ Framework schema, StreamingListener vs MetricCollector, rule types, Synapse test pipelines, pytest/conftest patterns, BDD style, App Insights telemetry",
        "keywords": "reliability,dq,data quality,rule,json rule,streaming listener,metric collector,pytest,conftest,bdd,app insights,alert,sev2,sev3,sev4,volume,completeness,freshness,bronze,silver,gold,test,canary",
    },
    "operations": {
        "file": "09-operations-runbook.md",
        "description": "Operational runbook covering backfill procedures, incident response, on-call playbook, common failure scenarios, manual recovery steps",
        "keywords": "operations,runbook,backfill,incident,on-call,recovery,failure,retry,manual,reprocess,restart,troubleshoot,playbook,escalation",
    },
    "monitoring": {
        "file": "10-monitoring-alerting.md",
        "description": "Monitoring and alerting strategy — Grafana dashboards, App Insights telemetry, alert severity tiers, KQL queries, PagerDuty/IcM integration",
        "keywords": "monitoring,alerting,grafana,dashboard,app insights,telemetry,kql,pagerduty,icm,sev2,sev3,sev4,metric,threshold,latency,volume,freshness",
    },
    "mcp-tooling": {
        "file": "11-mcp-ai-tooling.md",
        "description": "MCP server architecture, AI-powered development tools, architecture assistant chatbot, RAG retrieval, code review automation, PR analysis",
        "keywords": "mcp,ai,tooling,chatbot,rag,retrieval,architecture assistant,code review,pr,pull request,copilot,llm,gpt,azure ai,foundry,semantic search",
    },
    "security": {
        "file": "12-security-access.md",
        "description": "Security posture, RBAC model, managed identities, network security (VNet/NSP/private endpoints), data classification, key vault, compliance",
        "keywords": "security,access,rbac,managed identity,msi,vnet,private endpoint,nsp,key vault,encryption,compliance,gdpr,pci,soc2,firewall,network security,data classification",
    },
}


# --------------------------------------------------------------------------- #
# Service Functions
# --------------------------------------------------------------------------- #

def list_topics() -> list[dict[str, str]]:
    """Return the list of available architecture topics with descriptions."""
    return [
        {"topic": key, "description": meta["description"]}
        for key, meta in TOPIC_REGISTRY.items()
    ]


def get_topic_content(topic: str) -> str:
    """Load the full content of a knowledge base topic file."""
    if topic not in TOPIC_REGISTRY:
        available = ", ".join(TOPIC_REGISTRY.keys())
        return f"Unknown topic '{topic}'. Available topics: {available}"

    filepath = KNOWLEDGE_BASE_DIR / TOPIC_REGISTRY[topic]["file"]
    if not filepath.is_file():
        return f"Knowledge base file not found: {filepath}. Expected at: docs/knowledge-library/pdp-architecture/"

    return filepath.read_text(encoding="utf-8")


def classify_question(question: str) -> list[str]:
    """Classify a question into 1-2 relevant topic keys based on keyword matching."""
    question_lower = question.lower()
    scores: list[tuple[str, int]] = []
    for key, meta in TOPIC_REGISTRY.items():
        keywords = meta["keywords"].split(",")
        score = sum(1 for kw in keywords if kw.strip() in question_lower)
        if score > 0:
            scores.append((key, score))

    scores.sort(key=lambda x: x[1], reverse=True)
    if not scores:
        return ["overview", "layers"]
    return [s[0] for s in scores[:2]]


def search_knowledge_base(query: str) -> list[dict]:
    """Search across all knowledge base files for lines matching the query terms.

    Args:
        query: Space-separated search terms

    Returns:
        List of result dicts with topic, file, line, matched_terms, and context.
    """
    terms = [t.lower().strip() for t in query.split() if len(t.strip()) >= 3]
    if not terms:
        return [{"error": "Query too short. Provide at least one term with 3+ characters."}]

    results = []
    for key, meta in TOPIC_REGISTRY.items():
        filepath = KNOWLEDGE_BASE_DIR / meta["file"]
        if not filepath.is_file():
            continue
        content = filepath.read_text(encoding="utf-8")
        for i, line in enumerate(content.splitlines(), start=1):
            line_lower = line.lower()
            matched = [t for t in terms if t in line_lower]
            if matched:
                # Grab surrounding context
                all_lines = content.splitlines()
                start = max(0, i - 3)
                end = min(len(all_lines), i + 2)
                context = "\n".join(all_lines[start:end])
                results.append({
                    "topic": key,
                    "file": meta["file"],
                    "line": i,
                    "matched_terms": matched,
                    "context": context,
                })

    results.sort(key=lambda r: len(r["matched_terms"]), reverse=True)
    return results[:20]


def get_layer_detail(layer_name: str) -> str:
    """Get detailed information about a specific PDP architecture layer."""
    layer_map = {
        "1": "ingestion", "ingestion": "ingestion", "ingest": "ingestion",
        "2": "streaming", "streaming": "streaming", "stream": "streaming",
        "real-time": "streaming", "realtime": "streaming",
        "3": "processing", "processing": "processing", "medallion": "processing",
        "bronze": "processing", "silver": "processing", "gold": "processing",
        "4": "data", "data": "data", "storage": "data", "persistence": "data",
        "adls": "data", "delta lake": "data",
        "5": "serving", "serving": "serving", "analytics": "serving", "cubes": "serving",
        "6": "presentation", "presentation": "presentation", "visualization": "presentation",
        "power bi": "presentation", "powerbi": "presentation", "dashboard": "presentation",
        "7": "quality", "quality": "quality", "monitoring": "quality", "alerts": "quality",
        "8": "orchestration", "orchestration": "orchestration", "deployment": "orchestration",
        "cicd": "orchestration", "ci/cd": "orchestration",
    }

    layer_names = "1-Ingestion, 2-Streaming, 3-Processing, 4-Data, 5-Serving, 6-Presentation, 7-Quality, 8-Orchestration"
    normalized = layer_map.get(layer_name.lower().strip())
    if not normalized:
        return f"Unknown layer '{layer_name}'. Available layers: {layer_names}"

    # Load the layers topic and extract the relevant section
    content = get_topic_content("layers")
    if content.startswith("Unknown topic") or content.startswith("Knowledge base file"):
        return content

    # Find the section for this layer
    lines = content.splitlines()
    section_lines: list[str] = []
    capturing = False
    for line in lines:
        if line.lower().startswith("##") and normalized in line.lower():
            capturing = True
        elif capturing and line.startswith("## "):
            break
        if capturing:
            section_lines.append(line)

    if section_lines:
        return "\n".join(section_lines)
    return f"Layer '{normalized}' section not found in the layers topic. Try get_topic_content('layers') for the full document."


def get_domain_schema(domain: str) -> str:
    """Get schema/table information for a specific PDP data domain."""
    domain_map = {
        "pmt": "PaymentTransactions", "paymenttransactions": "PaymentTransactions",
        "payment transactions": "PaymentTransactions",
        "journal": "PaymentsJournal", "paymentsjournal": "PaymentsJournal",
        "payments journal": "PaymentsJournal",
        "cop": "COP", "cost of payments": "COP", "costofpayments": "COP",
        "fraud": "Fraud", "risk": "Fraud",
        "nt": "NT", "network tokenization": "NT", "networktokenization": "NT",
        "au": "AU", "account updater": "AU", "accountupdater": "AU",
        "bin": "BIN",
        "recon": "Recon", "reconciliation": "Recon",
    }

    available = "PaymentTransactions, PaymentsJournal, COP, Fraud, NT, AU, BIN, Recon"
    normalized = domain_map.get(domain.lower().strip())
    if not normalized:
        return f"Unknown domain '{domain}'. Available: {available}"

    content = get_topic_content("domains")
    if content.startswith("Unknown topic") or content.startswith("Knowledge base file"):
        return content

    # Find the section for this domain
    lines = content.splitlines()
    section_lines: list[str] = []
    capturing = False
    for line in lines:
        if line.lower().startswith("##") and normalized.lower() in line.lower():
            capturing = True
        elif capturing and line.startswith("## "):
            break
        if capturing:
            section_lines.append(line)

    if section_lines:
        return "\n".join(section_lines)
    return f"Domain '{normalized}' section not found in the domains topic. Try get_topic_content('domains') for the full document."


def get_data_flow(domain: Optional[str] = None) -> str:
    """Get data flow/lineage information, optionally filtered by domain."""
    content = get_topic_content("data-flow")
    if content.startswith("Unknown topic") or content.startswith("Knowledge base file"):
        return content

    if not domain:
        return content

    # Filter to domain-specific section
    lines = content.splitlines()
    section_lines: list[str] = []
    capturing = False
    for line in lines:
        if line.lower().startswith("##") and domain.lower() in line.lower():
            capturing = True
        elif capturing and line.startswith("## "):
            break
        if capturing:
            section_lines.append(line)

    if section_lines:
        return "\n".join(section_lines)
    return content  # Return full content if domain section not found
