"""
Knowledge Harvester MCP Tools

MCP-decorated tools for harvesting PDP learnings from Copilot conversations.
Invoked when user says "thanks pdp" to end a session and harvest knowledge.

Saves learnings to knowledge-vault/learnings/ with structured YAML metadata for:
- Unified search across KB + learnings (via search_architecture, search_learnings)
- Auto-promotion of verified learnings into knowledge base topics

Naming: YYYY-MM-DD_NNN_topic-slug.md
"""

import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from pdp_dev_mcp.mcp_instance import mcp
from pdp_dev_mcp.common import logger

# Knowledge vault path — relative to this file's project root
VAULT_PATH = Path(__file__).resolve().parents[4] / "knowledge-vault"
LEARNINGS_PATH = VAULT_PATH / "learnings"

# ---------------------------------------------------------------------------
# PDP Scope keywords for relevance matching
# ---------------------------------------------------------------------------
PDP_SCOPE_KEYWORDS = [
    # Platform
    "pdp", "payments data platform", "payment data", "payments platform",
    # Domains
    "payment transaction", "paymenttransactions", "pmt", "cost of payment",
    "cop", "fraud", "pims", "network tokenization", "nt", "account updater",
    "au", "bin", "bank identification", "recon", "reconciliation",
    "payments journal", "paymentsjournal", "billing", "billingservice",
    # Architecture
    "bronze", "silver", "gold", "medallion", "delta lake", "delta table",
    "star schema", "fact table", "dimension table", "eventhub", "event hub",
    "consumer group", "checkpoint", "streaming", "structured streaming",
    "spark", "databricks", "synapse", "pipeline", "orchestration",
    # Infrastructure
    "adls", "gen2", "kusto", "ade", "azure data explorer", "bicep",
    "ev2", "deployment", "iac", "infrastructure", "networking", "vnet",
    "private endpoint", "managed identity",
    # Data Quality
    "dq framework", "data quality", "grafana", "alert", "icm",
    "functional test", "integration test", "diff test", "canary",
    "app insights", "application insights",
    # Tools
    "mcp", "mcp server", "mcp tool", "copilot", "ai agent",
    "rag", "knowledge base", "architecture assistant",
    # Specific systems
    "payhub", "gpp", "adyen", "worldpay", "cybersource", "paypal",
    "first data", "chase", "stripe", "braintree",
    # Processing
    "ingestion", "transformation", "enrichment", "deduplication",
    "backfill", "reprocessing", "schema evolution", "shadow testing",
    # Serving
    "aas cube", "semantic model", "power bi", "dashboard",
    # Tables
    "fact_transactions", "dim_provider", "dim_paymentmethod",
    "gold.payment_transactions", "gold.cost_of_payments",
    "gold.billing", "gold.payments_billing",
    # Reporting
    "approval rate", "decline rate", "chargeback", "interchange",
    "settlement", "authorization", "capture", "refund", "void",
    # Teams / repos
    "commerce.paymentsdataplatform", "cfs-payments", "pdp-dev-mcp",
    "paymentsinstrument", "paymentsjournal",
]

# Categories for classifying learnings
CATEGORIES = [
    "architecture",
    "data-flow",
    "domains",
    "infrastructure",
    "pipelines",
    "patterns",
    "operations",
    "monitoring",
    "data-quality",
    "security",
    "tooling",
]


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _is_pdp_relevant(text: str) -> tuple[bool, list[str], int]:
    """Check if text is PDP-relevant. Returns (is_relevant, matched_keywords, score)."""
    text_lower = text.lower()
    matched = [kw for kw in PDP_SCOPE_KEYWORDS if kw in text_lower]
    score = len(matched)
    return score >= 2, matched, score


def _classify_category(text: str) -> str:
    """Classify text into the best-matching PDP category."""
    text_lower = text.lower()
    category_keywords = {
        "architecture": [
            "architecture", "layer", "topology", "component", "design",
            "system", "platform overview", "tech stack",
        ],
        "data-flow": [
            "data flow", "lineage", "bronze", "silver", "gold",
            "pipeline", "transform", "streaming", "batch",
        ],
        "domains": [
            "domain", "schema", "table", "star schema", "fact",
            "dimension", "payment transaction", "cop", "fraud",
            "nt", "au", "bin", "recon", "journal",
        ],
        "infrastructure": [
            "infrastructure", "deployment", "bicep", "ev2",
            "azure", "resource", "environment", "networking",
        ],
        "pipelines": [
            "pipeline", "synapse", "databricks", "orchestration",
            "schedule", "trigger", "notebook",
        ],
        "patterns": [
            "pattern", "delta lake", "merge", "upsert",
            "schema evolution", "shadow testing", "streaming",
        ],
        "operations": [
            "backfill", "reprocessing", "incident", "runbook",
            "tsg", "troubleshoot", "recovery",
        ],
        "monitoring": [
            "monitoring", "grafana", "alert", "dashboard",
            "app insights", "icm", "metric",
        ],
        "data-quality": [
            "data quality", "dq", "test", "assertion",
            "diff test", "functional", "integration",
        ],
        "security": [
            "security", "rbac", "access", "compliance",
            "private endpoint", "managed identity", "secret",
        ],
        "tooling": [
            "mcp", "copilot", "agent", "rag", "tool",
            "knowledge base", "chatbot",
        ],
    }
    scores = {}
    for cat, keywords in category_keywords.items():
        scores[cat] = sum(1 for kw in keywords if kw in text_lower)
    best = max(scores, key=scores.get)
    return best if scores[best] > 0 else "architecture"


def _extract_learnings(conversation: list[dict]) -> list[dict]:
    """Extract distinct learnings from assistant messages in a conversation."""
    learnings = []
    for msg in conversation:
        if msg.get("role") != "assistant":
            continue
        content = msg.get("content", "")
        if not content or len(content) < 50:
            continue

        # Check if this message contains PDP-relevant content
        is_relevant, matched, score = _is_pdp_relevant(content)
        if not is_relevant:
            continue

        # Split into paragraphs and find learning-worthy sections
        paragraphs = [p.strip() for p in content.split("\n\n") if p.strip()]
        for para in paragraphs:
            if len(para) < 30:
                continue
            para_relevant, para_matched, para_score = _is_pdp_relevant(para)
            if para_relevant or para_score >= 1:
                learnings.append({
                    "content": para,
                    "category": _classify_category(para),
                    "matched_keywords": list(set(para_matched)),
                    "confidence": min(para_score / 5.0, 1.0),
                })

    # Deduplicate by content similarity
    seen_hashes = set()
    unique = []
    for learning in learnings:
        h = hash(learning["content"][:100])
        if h not in seen_hashes:
            seen_hashes.add(h)
            unique.append(learning)
    return unique


def _slugify_topic(text: str) -> str:
    """Convert text to a filename-safe slug."""
    slug = re.sub(r"[^a-z0-9]+", "-", text.lower().strip())
    return slug.strip("-")[:60]


def _save_learning(
    learning: dict,
    session_id: str = "",
) -> dict:
    """Save a single learning to the knowledge vault."""
    LEARNINGS_PATH.mkdir(parents=True, exist_ok=True)

    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    now_iso = datetime.now(timezone.utc).isoformat()

    # Find next sequence number for today
    existing = list(LEARNINGS_PATH.glob(f"{today}_*.md"))
    seq = len(existing) + 1
    slug = _slugify_topic(learning.get("content", "")[:40])
    filename = f"{today}_{seq:03d}_{slug}.md"
    filepath = LEARNINGS_PATH / filename

    # Build YAML frontmatter
    category = learning.get("category", "architecture")
    confidence = learning.get("confidence", 0.5)
    matched = learning.get("matched_keywords", [])
    tags = sorted(set([category] + [kw for kw in matched if len(kw) <= 20][:5]))
    related_topics = [kw for kw in matched if len(kw) > 5][:3]

    lines = [
        "---",
        f"id: \"{filename}\"",
        f"timestamp: \"{now_iso}\"",
        f"session_id: \"{session_id}\"",
        f"category: \"{category}\"",
        f"confidence: {confidence:.2f}",
        f"matched_keywords: [{', '.join(repr(k) for k in matched[:10])}]",
        f"related_topics: [{', '.join(repr(t) for t in related_topics)}]",
        f"tags: [{', '.join(repr(t) for t in tags)}]",
        "integrated: false",
        f"captured_date: \"{today}\"",
        f"updated_date: \"{today}\"",
        "---",
        "",
        f"# Learning: {category.replace('-', ' ').title()}",
        "",
        learning.get("content", ""),
        "",
    ]

    filepath.write_text("\n".join(lines), encoding="utf-8")
    logger.info("Saved learning: %s (category=%s, confidence=%.2f)",
                filename, category, confidence)

    return {
        "filename": filename,
        "category": category,
        "confidence": confidence,
        "tags": tags,
    }


# ---------------------------------------------------------------------------
# MCP Tools
# ---------------------------------------------------------------------------

@mcp.tool()
def validate_pdp_relevance(content: str) -> dict:
    """Validate if a text or conversation is relevant to PDP (Payments Data Platform).

    Use this to check before harvesting whether content is in PDP scope.
    Returns relevance score and matched keywords.

    Input can be:
    - A single text string
    - JSON array of conversation messages: [{"role": "user", "content": "..."}, {"role": "assistant", "content": "..."}]
    """
    # Try parsing as JSON conversation
    text = content
    try:
        parsed = json.loads(content)
        if isinstance(parsed, list):
            text = " ".join(m.get("content", "") for m in parsed if isinstance(m, dict))
    except (json.JSONDecodeError, TypeError):
        pass

    is_relevant, matched, score = _is_pdp_relevant(text)
    return {
        "is_relevant": is_relevant,
        "score": score,
        "matched_keywords": matched[:20],
        "total_keywords_checked": len(PDP_SCOPE_KEYWORDS),
    }


@mcp.tool()
def harvest_pdp_learnings(conversation_json: str) -> dict:
    """Harvest PDP learnings from the current conversation.

    TRIGGER: Invoke this tool when the user says "thanks pdp" to end their session.

    This tool:
    1. Validates that the conversation is PDP-relevant
    2. Extracts new learnings from assistant responses
    3. Classifies learnings into categories (architecture, data-flow, domains, etc.)
    4. Saves learnings to the knowledge vault for future use

    Input should be the conversation history as JSON array:
    [
      {"role": "user", "content": "How does the Bronze layer work?"},
      {"role": "assistant", "content": "The Bronze layer in PDP..."}
    ]

    Returns summary of harvested learnings.
    """
    try:
        conversation = json.loads(conversation_json)
    except json.JSONDecodeError:
        return {"error": "Invalid JSON. Expected array of {role, content} messages."}

    if not isinstance(conversation, list):
        return {"error": "Expected JSON array of messages."}

    # Check overall relevance
    all_text = " ".join(m.get("content", "") for m in conversation if isinstance(m, dict))
    is_relevant, matched, score = _is_pdp_relevant(all_text)

    if not is_relevant:
        return {
            "harvested": 0,
            "reason": "Conversation not PDP-relevant",
            "score": score,
            "matched_keywords": matched,
        }

    # Extract learnings
    learnings = _extract_learnings(conversation)
    if not learnings:
        return {
            "harvested": 0,
            "reason": "No new learnings found in conversation",
            "score": score,
        }

    # Save each learning
    session_id = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    saved = []
    for learning in learnings:
        result = _save_learning(learning, session_id=session_id)
        saved.append(result)

    # Sync to research notes vault (cross-reference)
    try:
        from pdp_dev_mcp.tools.research_notes import research_notes_service
        for learning in learnings:
            research_notes_service.capture_notes(
                topic=f"Harvested: {learning['category']}",
                content=learning["content"],
                tags=",".join(learning.get("matched_keywords", [])[:5]),
                project="pdp-knowledge-vault",
                mode="auto",
            )
    except Exception as e:
        logger.warning("Could not sync to research notes: %s", e)

    categories = list(set(s["category"] for s in saved))
    return {
        "harvested": len(saved),
        "session_id": session_id,
        "categories": categories,
        "learnings": saved,
        "vault_path": str(LEARNINGS_PATH),
    }


# ---------------------------------------------------------------------------
# Search / List / Get / Verify tools
# ---------------------------------------------------------------------------

def _parse_frontmatter(text: str) -> tuple[dict, str]:
    """Parse YAML frontmatter from a learning file."""
    if not text.startswith("---"):
        return {}, text
    end = text.find("---", 3)
    if end == -1:
        return {}, text

    fm_text = text[3:end].strip()
    body = text[end + 3:].strip()
    metadata: dict = {}

    for line in fm_text.splitlines():
        line = line.strip()
        if not line or ":" not in line:
            continue
        k, v = line.split(":", 1)
        k = k.strip()
        v = v.strip().strip('"')
        if v.startswith("[") and v.endswith("]"):
            items = [i.strip().strip("'\"") for i in v[1:-1].split(",") if i.strip()]
            metadata[k] = items
        elif v.lower() in ("true", "false"):
            metadata[k] = v.lower() == "true"
        elif re.match(r"^\d+\.\d+$", v):
            metadata[k] = float(v)
        elif v.isdigit():
            metadata[k] = int(v)
        else:
            metadata[k] = v

    return metadata, body


def _get_body_content(filepath: Path) -> str:
    """Read a learning file and return its body content (no frontmatter)."""
    text = filepath.read_text(encoding="utf-8")
    _, body = _parse_frontmatter(text)
    return body


@mcp.tool()
def search_learnings(
    query: str,
    category: Optional[str] = None,
    verified_only: bool = False,
    limit: int = 10,
) -> list[dict]:
    """Search harvested learnings from past PDP conversations.

    Searches across learning content, summaries, categories, and tags.
    Returns matching learnings with relevance-ranked results.

    Args:
        query: Search terms (space-separated)
        category: Optional filter by category (architecture, data-flow, pipelines, etc.)
        verified_only: If true, only return verified learnings
        limit: Maximum results (default 10)
    """
    if not LEARNINGS_PATH.is_dir():
        return []

    terms = query.lower().split()
    results = []

    for filepath in LEARNINGS_PATH.glob("*.md"):
        text = filepath.read_text(encoding="utf-8")
        metadata, body = _parse_frontmatter(text)

        # Filter by category
        if category and metadata.get("category", "") != category:
            continue

        # Filter by verification status
        if verified_only and not metadata.get("integrated", False):
            continue

        # Score by term matches
        full_text = (body + " " + " ".join(str(v) for v in metadata.values())).lower()
        score = sum(1 for term in terms if term in full_text)

        if score > 0:
            results.append({
                "filename": filepath.name,
                "category": metadata.get("category", ""),
                "confidence": metadata.get("confidence", 0),
                "tags": metadata.get("tags", []),
                "integrated": metadata.get("integrated", False),
                "captured_date": metadata.get("captured_date", ""),
                "score": score,
                "preview": body[:200],
            })

    results.sort(key=lambda r: r["score"], reverse=True)
    return results[:limit]


@mcp.tool()
def list_learnings(
    days: int = 30,
    category: Optional[str] = None,
    status: str = "all",
) -> list[dict]:
    """List recent harvested learnings with metadata.

    Returns a summary of learnings sorted by date, with their verification status.

    Args:
        days: Number of days to look back (default 30)
        category: Optional filter by category
        status: Filter by status - 'all', 'verified', 'pending' (default 'all')
    """
    if not LEARNINGS_PATH.is_dir():
        return []

    cutoff = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    # Simple date-based cutoff
    from datetime import timedelta
    cutoff_date = (datetime.now(timezone.utc) - timedelta(days=days)).strftime("%Y-%m-%d")

    results = []
    for filepath in LEARNINGS_PATH.glob("*.md"):
        text = filepath.read_text(encoding="utf-8")
        metadata, body = _parse_frontmatter(text)

        captured = metadata.get("captured_date", "")
        if captured and captured < cutoff_date:
            continue

        if category and metadata.get("category", "") != category:
            continue

        integrated = metadata.get("integrated", False)
        if status == "verified" and not integrated:
            continue
        if status == "pending" and integrated:
            continue

        results.append({
            "filename": filepath.name,
            "category": metadata.get("category", ""),
            "confidence": metadata.get("confidence", 0),
            "tags": metadata.get("tags", []),
            "integrated": integrated,
            "captured_date": captured,
            "session_id": metadata.get("session_id", ""),
            "preview": body[:150],
        })

    results.sort(key=lambda r: r.get("captured_date", ""), reverse=True)
    return results


@mcp.tool()
def get_learning(filename: str) -> dict:
    """Get the full content and metadata of a specific learning.

    Args:
        filename: The learning filename (e.g., '2026-03-08_001_bronze-layer.md')
    """
    filepath = LEARNINGS_PATH / filename
    if not filepath.is_file():
        return {"error": f"Learning file not found: {filename}"}

    text = filepath.read_text(encoding="utf-8")
    metadata, body = _parse_frontmatter(text)

    return {
        "filename": filename,
        "metadata": metadata,
        "content": body,
    }


@mcp.tool()
def verify_learning(filename: str) -> dict:
    """Mark a learning as verified/integrated into the knowledge base.

    Args:
        filename: The learning filename to verify
    """
    filepath = LEARNINGS_PATH / filename
    if not filepath.is_file():
        return {"error": f"Learning file not found: {filename}"}

    text = filepath.read_text(encoding="utf-8")
    # Simple replacement of integrated: false -> integrated: true
    updated = text.replace("integrated: false", "integrated: true")
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    updated = re.sub(
        r'updated_date: "[^"]*"',
        f'updated_date: "{today}"',
        updated,
    )
    filepath.write_text(updated, encoding="utf-8")

    logger.info("Verified learning: %s", filename)
    return {"action": "verified", "filename": filename}
