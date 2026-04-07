"""
Grafana Alert Analysis and Resolution Tools

Provides AI-accessible tools for diagnosing PDP Grafana alerts, recommending
resolution steps, and guiding investigation of upstream data and network issues.

These tools follow the established PDP alert naming convention:
- PDP Alert | SEV{n} | {SubjectArea} | {TestType} | {Description}

And work with the PDP DQ Dashboard at:
https://gpcgrafana-f4dzaccqayhrgzh5.eus.grafana.azure.com/d/few2ggy2ohqf4f/payments-dq-dashboard-daily
"""

import os
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
from pathlib import Path

from pdp_dev_mcp.mcp_instance import mcp
from pdp_dev_mcp.common import logger, load_prompt_content


PDP_GRAFANA_DASHBOARD_URL = (
    "https://gpcgrafana-f4dzaccqayhrgzh5.eus.grafana.azure.com"
    "/d/few2ggy2ohqf4f/payments-dq-dashboard-daily"
)

# ---------------------------------------------------------------------------
# Severity Levels
# ---------------------------------------------------------------------------
SEVERITY_LEVELS: Dict[str, Dict[str, str]] = {
    "SEV1": {
        "response_time": "Immediate (< 15 min)",
        "impact": "Critical production impact - data pipeline completely blocked",
        "action": "Immediate on-call escalation required",
    },
    "SEV2": {
        "response_time": "Urgent (< 30 min)",
        "impact": "High impact - critical data quality degradation",
        "action": "Notify team lead, consider on-call escalation",
    },
    "SEV3": {
        "response_time": "High (< 2 hours)",
        "impact": "Significant impact - data quality issues affecting consumers",
        "action": "Team notification required",
    },
    "SEV4": {
        "response_time": "Moderate (< 4 hours)",
        "impact": "Moderate impact - localized data quality issues",
        "action": "Log and track, team awareness",
    },
    "SEV5": {
        "response_time": "Normal (< 24 hours)",
        "impact": "Low impact - minor data quality deviations",
        "action": "Track for trending",
    },
    "SEV6": {
        "response_time": "Low (< 48 hours)",
        "impact": "Minimal impact - cosmetic or edge case issues",
        "action": "Log for batch review",
    },
}

# ---------------------------------------------------------------------------
# Upstream Sources per Subject Area
# ---------------------------------------------------------------------------
SUBJECT_AREA_UPSTREAM_SOURCES: Dict[str, Dict[str, Any]] = {
    "PMT": {
        "name": "PaymentTransactions",
        "sources": ["GPP EventHub", "PayHub EventHub", "Cosmos Change Feed"],
        "bronze_tables": ["bronze.gpp_events", "bronze.payhub_events"],
        "silver_tables": ["silver.payment_transactions"],
        "gold_tables": ["gold.fact_transactions", "gold.dim_*"],
        "pipeline": "Synapse PaymentTransactions pipeline",
        "check_order": [
            "EventHub consumer group lag",
            "Bronze table freshness (< 15 min expected)",
            "Silver merge completion",
            "Gold star schema refresh",
        ],
    },
    "BIN": {
        "name": "BIN",
        "sources": ["BIN file drops (SFTP)", "Mastercard/Visa feeds"],
        "bronze_tables": ["bronze.bin_raw"],
        "silver_tables": ["silver.bin_lookup"],
        "gold_tables": ["gold.bin_enriched"],
        "pipeline": "Databricks BIN pipeline",
        "check_order": [
            "Source file arrival check",
            "Bronze ingestion status",
            "Silver dedup/merge",
            "Gold enrichment completion",
        ],
    },
    "COP": {
        "name": "CostOfPayments",
        "sources": ["Provider fee files", "Adyen/Stripe/PayPal feeds"],
        "bronze_tables": ["bronze.cop_raw_fees"],
        "silver_tables": ["silver.cop_fees"],
        "gold_tables": ["gold.fact_cop", "gold.dim_fee_category"],
        "pipeline": "Databricks COP pipeline",
        "check_order": [
            "Provider file arrival",
            "Bronze ingestion status",
            "Silver fee normalization",
            "Gold aggregation completion",
        ],
    },
    "NT": {
        "name": "NetworkTokenization",
        "sources": ["Token lifecycle events", "Network token APIs"],
        "bronze_tables": ["bronze.nt_events"],
        "silver_tables": ["silver.nt_lifecycle"],
        "gold_tables": ["gold.nt_summary"],
        "pipeline": "Databricks NT pipeline",
        "check_order": [
            "Event source connectivity",
            "Bronze event ingestion",
            "Silver lifecycle tracking",
            "Gold summary refresh",
        ],
    },
    "AU": {
        "name": "AccountUpdater",
        "sources": ["AU response files", "Card network updates"],
        "bronze_tables": ["bronze.au_responses"],
        "silver_tables": ["silver.au_updates"],
        "gold_tables": ["gold.au_summary"],
        "pipeline": "Databricks AU pipeline",
        "check_order": [
            "Response file arrival",
            "Bronze ingestion",
            "Silver dedup/merge",
            "Gold summary refresh",
        ],
    },
    "AuthN": {
        "name": "Authentication",
        "sources": ["3DS authentication events"],
        "bronze_tables": ["bronze.authn_events"],
        "silver_tables": ["silver.authn_results"],
        "gold_tables": ["gold.authn_summary"],
        "pipeline": "Databricks AuthN pipeline",
        "check_order": [
            "Event source connectivity",
            "Bronze ingestion status",
            "Silver processing",
            "Gold aggregation",
        ],
    },
}

# ---------------------------------------------------------------------------
# Test Type Check Patterns
# ---------------------------------------------------------------------------
TEST_TYPE_CHECK_PATTERNS: Dict[str, Dict[str, Any]] = {
    "Diff": {
        "description": "Compares data between two sources or time windows",
        "common_causes": [
            "Source data delayed or missing",
            "Schema change in upstream",
            "Timezone/partition boundary mismatch",
            "Pipeline processing lag",
        ],
        "investigation_steps": [
            "Check both source timestamps for alignment",
            "Verify schema compatibility between sources",
            "Check for recent deployments affecting the pipeline",
            "Review partition boundaries and timezone handling",
        ],
    },
    "Functional": {
        "description": "Validates business rules and data constraints",
        "common_causes": [
            "New data pattern not covered by rules",
            "Business rule change not reflected in tests",
            "Data quality issue in source",
            "Edge case in transformation logic",
        ],
        "investigation_steps": [
            "Review failing assertion details",
            "Sample failing records to understand pattern",
            "Check for recent business rule changes",
            "Verify transformation logic matches specification",
        ],
    },
    "Integration": {
        "description": "End-to-end flow validation across pipeline stages",
        "common_causes": [
            "Pipeline stage failure or timeout",
            "Data loss between stages",
            "Configuration mismatch across environments",
            "Resource contention or throttling",
        ],
        "investigation_steps": [
            "Check each pipeline stage health",
            "Verify data counts across stages",
            "Review recent configuration changes",
            "Check for resource limits or throttling",
        ],
    },
}

# ---------------------------------------------------------------------------
# Network Issue Patterns
# ---------------------------------------------------------------------------
NETWORK_ISSUE_PATTERNS: Dict[str, Dict[str, Any]] = {
    "EventHub": {
        "symptoms": [
            "Consumer group lag increasing",
            "Connection timeout errors",
            "Checkpoint offset stale",
        ],
        "checks": [
            "Verify EventHub namespace connectivity",
            "Check consumer group offset vs latest",
            "Review EventHub throughput units",
            "Check network security rules (NSG/firewall)",
        ],
        "common_fixes": [
            "Restart consumer/Spark streaming job",
            "Scale EventHub throughput units",
            "Reset consumer group offset if needed",
        ],
    },
    "Webhooks": {
        "symptoms": [
            "Missing webhook deliveries",
            "HTTP 429/503 from webhook endpoint",
            "Payload validation failures",
        ],
        "checks": [
            "Check webhook endpoint health",
            "Verify authentication tokens",
            "Review rate limit headers",
            "Check payload schema compatibility",
        ],
        "common_fixes": [
            "Retry failed deliveries",
            "Update authentication credentials",
            "Adjust retry/backoff configuration",
        ],
    },
    "Databricks": {
        "symptoms": [
            "Job cluster startup failures",
            "Driver/worker lost errors",
            "Notebook timeout",
        ],
        "checks": [
            "Check workspace status and region health",
            "Verify instance pool availability",
            "Review cluster event logs",
            "Check for quota/capacity issues",
        ],
        "common_fixes": [
            "Retry with fresh cluster",
            "Switch to different instance pool",
            "Scale down cluster size if capacity issue",
        ],
    },
    "Synapse": {
        "symptoms": [
            "Pipeline run stuck in queued state",
            "Data movement activity timeout",
            "Integration runtime offline",
        ],
        "checks": [
            "Check integration runtime status",
            "Verify linked service connectivity",
            "Review pipeline concurrency limits",
            "Check Synapse workspace health",
        ],
        "common_fixes": [
            "Restart integration runtime",
            "Cancel stuck pipeline run and retry",
            "Update linked service credentials",
        ],
    },
}


# ---------------------------------------------------------------------------
# Data Classes
# ---------------------------------------------------------------------------
@dataclass
class AlertContext:
    """Parsed context from a PDP alert name."""
    severity: str = ""
    subject_area: str = ""
    test_type: str = ""
    description: str = ""
    raw_name: str = ""


@dataclass
class ResolutionGuidance:
    """Structured resolution guidance for an alert."""
    alert_context: AlertContext = field(default_factory=AlertContext)
    severity_info: Dict[str, str] = field(default_factory=dict)
    immediate_steps: List[str] = field(default_factory=list)
    investigation_steps: List[str] = field(default_factory=list)
    common_causes: List[str] = field(default_factory=list)
    escalation_info: str = ""
    dashboard_url: str = PDP_GRAFANA_DASHBOARD_URL


def _parse_alert_name(alert_name: str) -> AlertContext:
    """Parse a PDP alert name into structured context.

    Expected format: PDP Alert | SEV{n} | {SubjectArea} | {TestType} | {Description}
    """
    ctx = AlertContext(raw_name=alert_name)
    parts = [p.strip() for p in alert_name.split("|")]

    if len(parts) >= 2:
        sev = parts[1].strip().upper()
        if sev.startswith("SEV"):
            ctx.severity = sev
    if len(parts) >= 3:
        ctx.subject_area = parts[2].strip()
    if len(parts) >= 4:
        ctx.test_type = parts[3].strip()
    if len(parts) >= 5:
        ctx.description = parts[4].strip()

    return ctx


# ---------------------------------------------------------------------------
# MCP Tools
# ---------------------------------------------------------------------------

@mcp.tool()
def grafana_get_alert_resolution_guidance(alert_name: str) -> str:
    """Get step-by-step resolution guidance for a PDP Grafana alert.

    Parses the alert name to identify severity, subject area, and test type,
    then provides targeted resolution steps.

    Args:
        alert_name: Full alert name, e.g. 'PDP Alert | SEV3 | PMT | Diff | Volume variance > 10%'
    """
    ctx = _parse_alert_name(alert_name)

    lines = [f"# Alert Resolution Guidance", f"**Alert:** {alert_name}", ""]

    # Severity info
    sev_info = SEVERITY_LEVELS.get(ctx.severity, {})
    if sev_info:
        lines.append(f"## Severity: {ctx.severity}")
        lines.append(f"- **Response Time:** {sev_info['response_time']}")
        lines.append(f"- **Impact:** {sev_info['impact']}")
        lines.append(f"- **Action:** {sev_info['action']}")
        lines.append("")

    # Test type guidance
    test_info = TEST_TYPE_CHECK_PATTERNS.get(ctx.test_type, {})
    if test_info:
        lines.append(f"## Test Type: {ctx.test_type}")
        lines.append(f"_{test_info['description']}_")
        lines.append("")
        lines.append("### Common Causes")
        for cause in test_info.get("common_causes", []):
            lines.append(f"- {cause}")
        lines.append("")
        lines.append("### Investigation Steps")
        for i, step in enumerate(test_info.get("investigation_steps", []), 1):
            lines.append(f"{i}. {step}")
        lines.append("")

    # Subject area upstream checks
    sa_info = SUBJECT_AREA_UPSTREAM_SOURCES.get(ctx.subject_area, {})
    if sa_info:
        lines.append(f"## Subject Area: {sa_info['name']}")
        lines.append(f"**Sources:** {', '.join(sa_info.get('sources', []))}")
        lines.append("")
        lines.append("### Pipeline Check Order")
        for i, check in enumerate(sa_info.get("check_order", []), 1):
            lines.append(f"{i}. {check}")
        lines.append("")

    # Escalation
    if ctx.severity in ("SEV1", "SEV2"):
        lines.append("## ⚠️ Escalation Required")
        lines.append("This is a high-severity alert. Escalate to on-call immediately if not resolved within the response window.")
    
    lines.append(f"\n**Dashboard:** {PDP_GRAFANA_DASHBOARD_URL}")
    return "\n".join(lines)


@mcp.tool()
def grafana_get_upstream_check_guidance(subject_area: str) -> str:
    """Get guidance for checking upstream data sources for a PDP subject area.

    Args:
        subject_area: The subject area code (PMT, BIN, COP, NT, AU, AuthN)
    """
    sa_key = subject_area.strip().upper()
    sa_info = SUBJECT_AREA_UPSTREAM_SOURCES.get(sa_key)

    if not sa_info:
        available = ", ".join(SUBJECT_AREA_UPSTREAM_SOURCES.keys())
        return f"Unknown subject area '{subject_area}'. Available: {available}"

    lines = [
        f"# Upstream Check Guidance: {sa_info['name']}",
        "",
        "## Data Sources",
    ]
    for src in sa_info.get("sources", []):
        lines.append(f"- {src}")

    lines.append("")
    lines.append("## Pipeline Layers")
    lines.append(f"- **Bronze:** {', '.join(sa_info.get('bronze_tables', []))}")
    lines.append(f"- **Silver:** {', '.join(sa_info.get('silver_tables', []))}")
    lines.append(f"- **Gold:** {', '.join(sa_info.get('gold_tables', []))}")
    lines.append(f"- **Pipeline:** {sa_info.get('pipeline', 'N/A')}")

    lines.append("")
    lines.append("## Check Order (follow sequentially)")
    for i, check in enumerate(sa_info.get("check_order", []), 1):
        lines.append(f"{i}. {check}")

    lines.append("")
    lines.append("## General Tips")
    lines.append("- Check each layer's freshness from **bottom-up** (Bronze → Silver → Gold)")
    lines.append("- If Bronze is stale, the issue is at ingestion/source level")
    lines.append("- If Bronze is fresh but Silver is stale, check processing pipeline")
    lines.append(f"\n**Dashboard:** {PDP_GRAFANA_DASHBOARD_URL}")

    return "\n".join(lines)


@mcp.tool()
def grafana_diagnose_network_issues(component: str) -> str:
    """Diagnose network and connectivity issues for a PDP infrastructure component.

    Args:
        component: The component type (EventHub, Webhooks, Databricks, Synapse)
    """
    # Try case-insensitive match
    match = None
    for key in NETWORK_ISSUE_PATTERNS:
        if key.lower() == component.lower().strip():
            match = key
            break

    if not match:
        available = ", ".join(NETWORK_ISSUE_PATTERNS.keys())
        return f"Unknown component '{component}'. Available: {available}"

    info = NETWORK_ISSUE_PATTERNS[match]

    lines = [
        f"# Network Diagnostics: {match}",
        "",
        "## Common Symptoms",
    ]
    for symptom in info.get("symptoms", []):
        lines.append(f"- {symptom}")

    lines.append("")
    lines.append("## Diagnostic Checks")
    for i, check in enumerate(info.get("checks", []), 1):
        lines.append(f"{i}. {check}")

    lines.append("")
    lines.append("## Common Fixes")
    for fix in info.get("common_fixes", []):
        lines.append(f"- {fix}")

    return "\n".join(lines)


@mcp.tool()
def grafana_get_alert_best_practices() -> str:
    """Get best practices for PDP Grafana alert investigation and management.

    Returns comprehensive guidance on alert triage, investigation methodology,
    and operational best practices for the PDP DQ monitoring system.
    """
    # Try to load from file first, fall back to inline content
    prompt_dir = Path(__file__).parent / "grafana_alert_best_practices.md"
    if prompt_dir.is_file():
        return load_prompt_content(prompt_dir)

    return """# PDP Alert Investigation Best Practices

## Triage Methodology

### 1. Parse the Alert Name
PDP alerts follow: `PDP Alert | SEV{n} | {SubjectArea} | {TestType} | {Description}`
- **Severity** determines response urgency
- **Subject Area** identifies the data domain
- **Test Type** guides investigation approach

### 2. Check Alert Context
- When did it start firing?
- Is it a new alert or recurring?
- Are other alerts in the same subject area also firing?

### 3. Follow the Data Path
Always investigate bottom-up through the pipeline layers:
1. **Source** → Is data arriving from upstream?
2. **Bronze** → Is ingestion working?
3. **Silver** → Is processing/merging completing?
4. **Gold** → Are aggregations current?

### 4. Correlation Analysis
- Check if multiple subject areas are affected (suggests infrastructure issue)
- Check if the issue is time-bounded (suggests data delay vs data loss)
- Check recent deployments or configuration changes

## Severity Response Guidelines

| Severity | Response Time | Escalation |
|----------|-------------|------------|
| SEV1 | < 15 min | Immediate on-call |
| SEV2 | < 30 min | Team lead + on-call |
| SEV3 | < 2 hours | Team notification |
| SEV4 | < 4 hours | Track and log |
| SEV5 | < 24 hours | Batch review |

## Common Pitfalls
- Don't assume the alert is a false positive without checking data
- Don't restart pipelines without understanding the root cause first
- Always check for recent deployments before deep investigation
- Document your findings for future reference
"""


@mcp.tool()
def grafana_analyze_alert_pattern(
    alert_names: str,
    time_window: str = "last 24 hours",
) -> str:
    """Analyze patterns across multiple PDP alerts to identify correlated issues.

    Accepts a newline-separated list of alert names and analyzes them for
    common patterns, correlated failures, and root cause hypotheses.

    Args:
        alert_names: Newline-separated list of alert names
        time_window: Time window for analysis context (e.g., 'last 24 hours', 'last 7 days')
    """
    alerts = [a.strip() for a in alert_names.strip().split("\n") if a.strip()]
    if not alerts:
        return "No alert names provided. Pass newline-separated alert names."

    contexts = [_parse_alert_name(a) for a in alerts]

    # Analyze patterns
    severities = [c.severity for c in contexts if c.severity]
    subject_areas = [c.subject_area for c in contexts if c.subject_area]
    test_types = [c.test_type for c in contexts if c.test_type]

    unique_sas = set(subject_areas)
    unique_types = set(test_types)

    lines = [
        f"# Alert Pattern Analysis",
        f"**Time Window:** {time_window}",
        f"**Total Alerts:** {len(alerts)}",
        "",
        "## Summary",
        f"- **Severities:** {', '.join(sorted(set(severities)))}",
        f"- **Subject Areas:** {', '.join(sorted(unique_sas))}",
        f"- **Test Types:** {', '.join(sorted(unique_types))}",
        "",
    ]

    # Pattern detection
    lines.append("## Pattern Analysis")

    if len(unique_sas) == 1:
        lines.append(f"- **Single Subject Area ({list(unique_sas)[0]}):** "
                      "All alerts are in the same domain — likely a domain-specific pipeline issue.")
    elif len(unique_sas) > 3:
        lines.append("- **Cross-Domain Impact:** Multiple subject areas affected — "
                      "suggests infrastructure-level issue (EventHub, Databricks, networking).")

    if len(unique_types) == 1:
        lines.append(f"- **Single Test Type ({list(unique_types)[0]}):** "
                      "Consistent failure type across alerts.")

    # Correlation hypothesis
    hypothesis = _generate_correlation_hypothesis(contexts)
    if hypothesis:
        lines.append("")
        lines.append("## Root Cause Hypothesis")
        lines.append(hypothesis)

    lines.append("")
    lines.append("## Recommended Next Steps")
    lines.append("1. Check the PDP DQ Dashboard for visual correlation")
    lines.append("2. Use `grafana_get_upstream_check_guidance` for affected subject areas")
    lines.append("3. Use `grafana_diagnose_network_issues` if infrastructure is suspected")
    lines.append(f"\n**Dashboard:** {PDP_GRAFANA_DASHBOARD_URL}")

    return "\n".join(lines)


def _generate_correlation_hypothesis(contexts: List[AlertContext]) -> str:
    """Generate a correlation hypothesis from multiple alert contexts."""
    subject_areas = set(c.subject_area for c in contexts if c.subject_area)
    test_types = set(c.test_type for c in contexts if c.test_type)

    if len(subject_areas) > 3:
        return ("**Infrastructure Issue Likely:** With >3 subject areas affected, "
                "the root cause is likely at the infrastructure level. "
                "Check EventHub connectivity, Databricks workspace health, "
                "and network security rules.")

    if len(subject_areas) == 1 and len(test_types) > 1:
        sa = list(subject_areas)[0]
        return (f"**Pipeline Issue in {sa}:** Multiple test types failing in a single "
                f"subject area suggests a pipeline processing failure. "
                f"Check the {sa} pipeline stages sequentially.")

    if "Diff" in test_types and len(subject_areas) > 1:
        return ("**Data Sync Issue:** Diff failures across multiple subject areas "
                "may indicate a systemic delay in data synchronization. "
                "Check source system health and EventHub lag.")

    return ""
