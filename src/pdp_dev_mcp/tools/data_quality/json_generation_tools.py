"""
JSON DQ Framework Rule Generation Tools

Focused on generating JSON configuration rules for the existing
DQ Framework MetricCollector system with proper rule types and thresholds.
"""

import uuid
from typing import Any

from pdp_dev_mcp.mcp_instance import mcp

# JSON DQ Framework Constants
VALID_JSON_RULE_TYPES = [
    "count",  # Volume monitoring
    "null_check",  # Completeness validation
    "duplicate_check",  # Accuracy validation
    "sum",  # Consistency validation
    "custom_query",  # Custom validation logic
    "table_history",  # Timeliness monitoring
    "custom_notebook",  # Complex validation via notebooks
]

SUBJECT_AREA_MAPPING = {
    "PaymentTransactions": "PMT",
    "BIN": "BIN",
    "CostOfPayments": "COP",
    "Fraud": "FRAUD",
    "AccountUpdater": "AU",
    "NetworkTokenization": "NT",
}


def _determine_rule_type(
    data_quality_category: str,
    field_name: str | None,
    table_name: str,
    threshold_value: float | None,
) -> tuple[str, list[str], str]:
    """Determine the best rule_type based on DQ category and context."""

    if data_quality_category == "Completeness":
        if field_name:
            return "null_check", [field_name], "Empty Field"
        else:
            return "count", [], "Volume"

    elif data_quality_category == "Accuracy":
        if field_name and "duplicate" in field_name.lower():
            return "duplicate_check", [field_name], "Duplicate Records"
        elif field_name:
            constraint = [
                f"SELECT COUNT(*) FROM {table_name} WHERE {field_name} IS NOT NULL AND LENGTH(TRIM({field_name})) = 0"
            ]
            return "custom_query", constraint, "Invalid Field"
        else:
            return "count", [], "Volume"

    elif data_quality_category == "Consistency":
        if field_name and any(
            word in field_name.lower() for word in ["amount", "sum", "total", "value"]
        ):
            return "sum", [field_name], "Volume"
        elif field_name:
            constraint = [f"SELECT COUNT(DISTINCT {field_name}) FROM {table_name}"]
            return "custom_query", constraint, "Data Consistency"
        else:
            return "count", [], "Volume"

    elif data_quality_category == "Reliability":
        if "freshness" in table_name or (threshold_value and threshold_value < 24):
            return "table_history", ["MERGE"], "Data Processing"
        else:
            return "count", [], "Volume"

    # Default fallback
    return "custom_query", [f"SELECT COUNT(*) FROM {table_name}"], "Data Quality"


def _generate_thresholds(
    rule_type: str, category: str, threshold_value: float | None
) -> tuple[float, float, int]:
    """Generate appropriate thresholds based on rule type."""

    if rule_type == "count":
        # Volume monitoring
        min_thresh = max_thresh = (
            0.6 if threshold_value is None else (threshold_value / 100.0)
        )
        avg_val = int(threshold_value or 1000000)  # Default 1M records

    elif rule_type == "null_check":
        # Null percentage thresholds (lower is better)
        min_thresh = max_thresh = (
            0.25 if threshold_value is None else (threshold_value / 100.0)
        )
        avg_val = 0  # Target zero nulls

    elif rule_type == "duplicate_check":
        # Duplicate count (should be zero)
        min_thresh = max_thresh = 1.0
        avg_val = 0

    elif rule_type == "sum":
        # Sum monitoring for amounts
        min_thresh = max_thresh = (
            0.75 if threshold_value is None else (threshold_value / 100.0)
        )
        avg_val = int(threshold_value or 150000000)  # Default 150M

    elif rule_type == "table_history":
        # Timeliness monitoring
        min_thresh = max_thresh = 0.25
        avg_val = 0

    else:  # custom_query
        min_thresh = max_thresh = (
            0.25 if threshold_value is None else (threshold_value / 100.0)
        )
        avg_val = int(threshold_value or 0)

    return min_thresh, max_thresh, avg_val


def _map_frequency_to_execution(frequency: str) -> tuple[str, int]:
    """Map frequency to execution mode and latency."""
    frequency_map = {
        "hourly": ("stream", 4),
        "daily": ("batch", 1),
        "weekly": ("batch", 1),
    }
    return frequency_map.get(frequency, ("batch", 1))


def _generate_sla(frequency: str) -> str:
    """Generate appropriate SLA based on frequency."""
    if frequency == "hourly":
        return "12:30:00"
    elif frequency == "daily":
        return "06:00:00"
    else:
        return "13:15:00"


def _map_severity(severity_level: str) -> str:
    """Map severity level to DQ framework format."""
    mapping = {"info": "low", "warning": "medium", "critical": "high"}
    return mapping.get(severity_level.lower(), "high")


@mcp.tool(
    description="Generate JSON DQ Framework rules for continuous operational monitoring with dashboard integration and automated alerting."
)
def generate_json_rule_suggestions(
    table_name: str,
    monitoring_type: str = "volume",
    field_name: str | None = None,
    frequency: str = "hourly",
    threshold: float | None = None,
    severity: str = "warning",
    rule_type_preference: str | None = None,
) -> dict[str, Any]:
    """Generate JSON DQ Framework rules for operational monitoring."""

    # Map monitoring types to DQ categories
    type_mapping = {
        "volume": ("Reliability", "PaymentTransactions"),
        "freshness": ("Reliability", "PaymentTransactions"),
        "completeness": ("Completeness", "PaymentTransactions"),
        "accuracy": ("Accuracy", "PaymentTransactions"),
        "consistency": ("Consistency", "PaymentTransactions"),
        "custom": ("Accuracy", "PaymentTransactions"),
    }

    dq_category, subject_area = type_mapping.get(
        monitoring_type, ("Reliability", "PaymentTransactions")
    )
    subject_abbrev = SUBJECT_AREA_MAPPING.get(subject_area, subject_area)

    # Determine rule type (allow override)
    if rule_type_preference and rule_type_preference in VALID_JSON_RULE_TYPES:
        rule_type = rule_type_preference
        constraint: list[str] = []
        query_description = f"Custom {rule_type} monitoring"
    else:
        rule_type, constraint, query_description = _determine_rule_type(
            dq_category, field_name, table_name, threshold
        )

    # Generate rule name and description
    if field_name:
        rule_name = f"{rule_type}_{field_name.lower()}_{table_name.replace('.', '_').replace('silver.', '').replace('gold.', '')}"
        description = f"{dq_category} | {query_description}"
    else:
        rule_name = f"{rule_type}_{table_name.replace('.', '_').replace('silver.', '').replace('gold.', '')}"
        description = f"{dq_category} | {query_description}"

    # Extract table layer and clean name
    if "." in table_name:
        layer, clean_table = table_name.split(".", 1)
    else:
        layer = "gold"  # Default assumption
        clean_table = table_name

    # Generate thresholds
    min_threshold, max_threshold, avg_value = _generate_thresholds(
        rule_type, dq_category, threshold
    )

    # Map frequency to execution parameters
    mode, latency = _map_frequency_to_execution(frequency)

    # Build JSON rule structure
    json_rule = {
        "subject_area": subject_area.lower(),
        "layer": layer,
        "table": clean_table,
        "rule_name": rule_name,
        "rule_type": rule_type,
        "constraint": constraint,
        "frequency": frequency,
        "latency": latency,
        "load_type": "overwrite",
        "mode": mode,
        "sla": _generate_sla(frequency),
        "min_threshold": min_threshold,
        "max_threshold": max_threshold,
        "avg": avg_value,
        "alert_severity": _map_severity(severity),
        "is_active": True,
        "description": description,
    }

    # Generate alert configuration
    alert_name = f"PDP Alert | SEV3 | {dq_category} | JSON Rule | {subject_abbrev} | {description}"

    return {
        "json_rule": json_rule,
        "rule_type": f"DQ Framework {rule_type} Rule",
        "deployment_target": f"src/databricks/workspace/notebooks/DQFramework/RuleConfig/MetricCollector/{subject_area}/",
        "filename": f"{layer}.json",
        "alert_configuration": {
            "alert_name": alert_name,
            "rule_id": str(uuid.uuid4()),
            "frequency": frequency,
            "severity": severity,
        },
        "usage_guidance": [
            f"{rule_type} rules are ideal for {query_description.lower()} monitoring",
            "Deploy to DQ Framework MetricCollector for continuous monitoring",
            "Integrate with existing subject area JSON files",
            "Thresholds auto-calibrated based on rule type and category",
            "Consider custom_notebook rules for complex validation logic",
        ],
        "integration_notes": [
            "JSON rules integrate with existing DQ dashboard and alerting",
            "Metrics are automatically collected and visualized",
            "Alerts flow through standard notification channels",
            "Can run alongside PySpark tests for comprehensive coverage",
            f"Rule type '{rule_type}' follows established framework patterns",
        ],
    }


@mcp.tool(
    description="Generate advanced JSON DQ Framework rule with full customization options."
)
def generate_advanced_json_rule(
    test_type: str,
    subject_area: str,
    data_quality_category: str,
    table_name: str,
    field_name: str | None = None,
    rule_frequency: str = "hourly",
    threshold_value: float | None = None,
    severity_level: str = "warning",
    custom_constraint: list[str] | None = None,
) -> dict[str, Any]:
    """Generate advanced JSON DQ Framework rule with full control."""

    # Use custom constraint if provided, otherwise determine automatically
    if custom_constraint:
        rule_type = "custom_query"
        constraint = custom_constraint
        query_description = "Custom Query"
    else:
        rule_type, constraint, query_description = _determine_rule_type(
            data_quality_category, field_name, table_name, threshold_value
        )

    # Generate rule name
    if field_name:
        rule_name = f"{rule_type}_{field_name.lower()}_{table_name.replace('.', '_').replace('silver.', '').replace('gold.', '')}"
    else:
        rule_name = f"{rule_type}_{table_name.replace('.', '_').replace('silver.', '').replace('gold.', '')}"

    # Extract layer info
    if "." in table_name:
        layer, clean_table = table_name.split(".", 1)
    else:
        layer = "gold"
        clean_table = table_name

    # Generate thresholds and execution parameters
    min_threshold, max_threshold, avg_value = _generate_thresholds(
        rule_type, data_quality_category, threshold_value
    )
    mode, latency = _map_frequency_to_execution(rule_frequency)

    json_rule = {
        "subject_area": subject_area.lower(),
        "layer": layer,
        "table": clean_table,
        "rule_name": rule_name,
        "rule_type": rule_type,
        "constraint": constraint,
        "frequency": rule_frequency,
        "latency": latency,
        "load_type": "overwrite",
        "mode": mode,
        "sla": _generate_sla(rule_frequency),
        "min_threshold": min_threshold,
        "max_threshold": max_threshold,
        "avg": avg_value,
        "alert_severity": _map_severity(severity_level),
        "is_active": True,
        "description": f"{data_quality_category} | {query_description}",
    }

    return {
        "json_rule": json_rule,
        "rule_type": f"DQ Framework {rule_type} Rule",
        "deployment_target": f"src/databricks/workspace/notebooks/DQFramework/RuleConfig/MetricCollector/{subject_area}/",
        "filename": f"{layer}.json",
        "customization_applied": {
            "rule_type": rule_type,
            "constraint": "custom" if custom_constraint else "auto-generated",
            "thresholds": "calibrated" if threshold_value else "default",
        },
    }


@mcp.tool(
    description="Get comprehensive information about JSON DQ Framework rule types and their use cases."
)
def get_json_rule_types_info() -> dict[str, Any]:
    """Return detailed information about JSON DQ Framework rule types."""
    return {
        "available_rule_types": {
            "count": {
                "purpose": "Volume monitoring - tracks record counts",
                "use_cases": ["Daily transaction volume", "Table row count monitoring"],
                "constraint": "Empty list - counts all records",
                "threshold_type": "Percentage deviation from average",
            },
            "null_check": {
                "purpose": "Completeness - detects null/empty values in specific fields",
                "use_cases": [
                    "Critical field completeness",
                    "Required data validation",
                ],
                "constraint": "List of field names to check",
                "threshold_type": "Percentage of null values allowed",
            },
            "duplicate_check": {
                "purpose": "Accuracy - finds duplicate records based on key fields",
                "use_cases": ["Primary key uniqueness", "Transaction ID validation"],
                "constraint": "List of fields that should be unique",
                "threshold_type": "Number of duplicates allowed",
            },
            "sum": {
                "purpose": "Consistency - monitors sum/total values for amount fields",
                "use_cases": ["Total transaction amounts", "Financial reconciliation"],
                "constraint": "List of numeric fields to sum",
                "threshold_type": "Percentage deviation from expected sum",
            },
            "custom_query": {
                "purpose": "Flexible - custom SQL for complex validation logic",
                "use_cases": ["Complex business rules", "Multi-table validations"],
                "constraint": "SQL query returning count or metric",
                "threshold_type": "Based on query result interpretation",
            },
            "table_history": {
                "purpose": "Timeliness - monitors data processing and ingestion timing",
                "use_cases": ["Data freshness", "Processing delays"],
                "constraint": "Operation types to monitor (MERGE, INSERT, etc.)",
                "threshold_type": "Time-based thresholds",
            },
            "custom_notebook": {
                "purpose": "Complex validation - executes Databricks notebooks for advanced testing",
                "use_cases": ["Statistical analysis", "ML-based validation"],
                "constraint": "Notebook path and parameters",
                "threshold_type": "Notebook-defined metrics",
            },
        },
        "selection_guidance": {
            "Completeness": "Use null_check for field-level, count for table-level",
            "Accuracy": "Use duplicate_check for uniqueness, custom_query for validation",
            "Consistency": "Use sum for amounts, custom_query for cross-field validation",
            "Reliability": "Use count for volume, table_history for timeliness",
            "Timeliness": "Use table_history for processing delays",
        },
        "framework_integration": {
            "deployment_path": "DQFramework/RuleConfig/MetricCollector/",
            "execution_engine": "DQ Framework MetricCollector",
            "dashboard_integration": "Automatic metrics visualization",
            "alerting": "Standard notification channels",
        },
    }
