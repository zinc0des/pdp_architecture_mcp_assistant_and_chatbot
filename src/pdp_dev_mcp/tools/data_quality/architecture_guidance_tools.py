"""
Dual-Path Architecture Guidance Tools

Provides guidance on choosing between PySpark tests and JSON DQ Framework rules
based on specific use cases and requirements.
"""

from typing import Any

from pdp_dev_mcp.mcp_instance import mcp


@mcp.tool(
    description="Get comprehensive guidance on dual-path data quality architecture: when to use PySpark tests vs JSON DQ Framework rules."
)
def get_dq_architecture_guidance() -> list[str]:
    """Return guidance on dual-path DQ architecture."""
    return [
        "# Dual-Path Data Quality Architecture",
        "",
        "Choose the optimal approach based on your specific needs:",
        "",
        "## PySpark Tests - Use When:",
        "- Detailed investigation and debugging required",
        "- Statistical analysis needed (z-scores, anomaly detection)",
        "- Complex validation logic with custom business rules",
        "- Development/investigation of data patterns",
        "- Rich debugging output needed for troubleshooting",
        "- Azure Monitor integration for alerts and dashboards preferred",
        "",
        "## JSON DQ Framework Rules - Use When:",
        "- Standardized rule types sufficient for validation needs",
        "- DQ Framework dashboard integration desired",
        "- Lightweight execution without full Databricks compute overhead",
        "- Built-in DQ Framework metrics, monitoring, and alerting preferred",
        "",
        "## Available JSON Rule Types:",
        "- count: Volume monitoring (record counts)",
        "- null_check: Completeness validation (field nulls)",
        "- duplicate_check: Accuracy validation (uniqueness)",
        "- sum: Consistency validation (amount totals)",
        "- custom_query: Custom SQL validation logic",
        "- table_history: Timeliness monitoring (processing delays)",
        "- custom_notebook: Complex validation via notebooks",
        "",
        "## Strategic Implementation:",
        "1. Choose JSON rules for DQ Framework-native monitoring and metrics",
        "2. Choose PySpark tests for custom validation with Azure Monitor integration",
        "3. Both approaches support operational monitoring through different mechanisms",
        "",
        "Both approaches work together for optimal data quality coverage!",
    ]


@mcp.tool(
    description="Analyze specific requirements and recommend the optimal DQ approach (PySpark vs JSON rules)."
)
def recommend_dq_approach(
    use_case: str,
    complexity_level: str = "medium",
    monitoring_frequency: str = "daily",
    debugging_needs: str = "basic",
    integration_requirements: str = "dashboard",
) -> dict[str, Any]:
    """Recommend the optimal DQ approach based on requirements.

    Args:
        use_case: Description of the data quality use case
        complexity_level: One of ["low", "medium", "high"]
        monitoring_frequency: One of ["hourly", "real-time", "daily", "weekly", "monthly"]
        debugging_needs: One of ["basic", "moderate", "extensive", "statistical"]
        integration_requirements: One of ["dashboard", "alerts", "both", "custom"]

    Returns:
        Dictionary with recommendation, scores, reasoning, and implementation strategy

    Raises:
        ValueError: If any parameter has an invalid value
    """

    # Define allowed values for validation
    allowed_complexity = {"low", "medium", "high"}
    allowed_frequency = {"hourly", "real-time", "daily", "weekly", "monthly"}
    allowed_debugging = {"basic", "moderate", "extensive", "statistical"}
    allowed_integration = {"dashboard", "alerts", "both", "custom"}

    # Validate inputs
    if complexity_level not in allowed_complexity:
        raise ValueError(
            f"complexity_level must be one of {sorted(allowed_complexity)}, got: {complexity_level}"
        )

    if monitoring_frequency not in allowed_frequency:
        raise ValueError(
            f"monitoring_frequency must be one of {sorted(allowed_frequency)}, got: {monitoring_frequency}"
        )

    if debugging_needs not in allowed_debugging:
        raise ValueError(
            f"debugging_needs must be one of {sorted(allowed_debugging)}, got: {debugging_needs}"
        )

    if integration_requirements not in allowed_integration:
        raise ValueError(
            f"integration_requirements must be one of {sorted(allowed_integration)}, got: {integration_requirements}"
        )

    pyspark_score = 0
    json_score = 0

    # Scoring based on use case patterns
    use_case_lower = use_case.lower()

    # JSON rules favor operational monitoring patterns
    json_patterns = [
        "volume",
        "monitoring",
        "alerting",
        "operational",
        "continuous",
        "real-time",
        "threshold",
        "sla",
        "compliance",
        "dashboard",
    ]

    # PySpark tests favor analytical/investigation patterns
    pyspark_patterns = [
        "validation",
        "analysis",
        "investigation",
        "statistical",
        "complex",
        "data quality",
        "anomaly",
        "profiling",
        "exploration",
        "debugging",
    ]

    import re

    # Normalize separators in use_case to handle variants (e.g., 'real-time', 'real time', 'realtime')
    normalized_use_case = re.sub(r"[-_\s]+", " ", use_case_lower)

    json_matches = sum(
        1
        for pattern in json_patterns
        if re.search(rf"\b{pattern}\b", normalized_use_case)
    )
    pyspark_matches = sum(
        1
        for pattern in pyspark_patterns
        if re.search(rf"\b{pattern}\b", normalized_use_case)
    )

    # Apply use case scoring (moderate weight: 1-2 points)
    if json_matches > pyspark_matches:
        json_score += 2
    elif pyspark_matches > json_matches:
        pyspark_score += 2
    elif json_matches > 0 or pyspark_matches > 0:
        # Mixed signals, slight boost to both
        json_score += 1
        pyspark_score += 1

    # Scoring based on complexity
    if complexity_level == "high":
        pyspark_score += 3
    elif complexity_level == "medium":
        pyspark_score += 1
        json_score += 1
    else:  # low
        json_score += 3

    # Scoring based on frequency
    if monitoring_frequency in ["hourly", "real-time"]:
        json_score += 3
    elif monitoring_frequency == "daily":
        json_score += 2
        pyspark_score += 1
    else:  # weekly or less frequent
        pyspark_score += 2

    # Scoring based on debugging needs
    if debugging_needs in ["extensive", "statistical"]:
        pyspark_score += 4
    elif debugging_needs == "moderate":
        pyspark_score += 2
        json_score += 1
    else:  # basic
        json_score += 2

    # Scoring based on integration
    if integration_requirements in ["dashboard", "alerts"]:
        json_score += 3
    elif integration_requirements == "both":
        json_score += 2
        pyspark_score += 1
    else:  # custom
        pyspark_score += 2

    # Determine recommendation with use case context
    use_case_insight = ""
    if json_matches > pyspark_matches:
        use_case_insight = (
            f"Use case '{use_case}' suggests operational monitoring focus"
        )
    elif pyspark_matches > json_matches:
        use_case_insight = (
            f"Use case '{use_case}' suggests analytical/investigation focus"
        )
    elif json_matches > 0 or pyspark_matches > 0:
        use_case_insight = (
            f"Use case '{use_case}' has mixed operational and analytical elements"
        )

    # Calculate score difference for recommendation strength
    score_diff = abs(pyspark_score - json_score)

    if pyspark_score > json_score:
        primary_recommendation = "PySpark Tests"
        secondary_recommendation = "JSON Rules"
        reasoning = [
            "Complex validation logic needs PySpark flexibility",
            "Debugging requirements favor rich PySpark output",
            "Statistical analysis capabilities important",
        ]
        if use_case_insight:
            reasoning.insert(0, use_case_insight)

        # Strong preference for PySpark - recommend single approach
        if score_diff >= 3:
            implementation_strategy = [
                "Focus on PySpark tests for this use case",
                "Rich debugging and analysis capabilities are essential",
                "JSON rules not needed for this specific requirement",
            ]
        else:
            implementation_strategy = [
                f"Start with {primary_recommendation.lower()} for immediate needs",
                f"Consider adding {secondary_recommendation.lower()} if operational monitoring becomes important",
            ]

    elif json_score > pyspark_score:
        primary_recommendation = "JSON DQ Framework Rules"
        secondary_recommendation = "PySpark Tests"
        reasoning = [
            "DQ Framework-native metrics publishing and monitoring",
            "Standardized rule types align with validation requirements",
            "Built-in framework dashboards and notification channels",
        ]
        if use_case_insight:
            reasoning.insert(0, use_case_insight)

        # Strong preference for JSON - recommend single approach
        if score_diff >= 3:
            implementation_strategy = [
                "Focus on JSON DQ Framework rules for this use case",
                "DQ Framework-native monitoring and standardized rule types are optimal",
                "PySpark tests not needed for this specific requirement",
            ]
        else:
            implementation_strategy = [
                f"Start with {primary_recommendation.lower()} for immediate needs",
                f"Consider adding {secondary_recommendation.lower()} if custom validation logic becomes important",
            ]

    else:
        primary_recommendation = "Hybrid Approach"
        secondary_recommendation = "Both methods equally valuable"
        reasoning = [
            "Requirements suggest both approaches have value",
            "Consider JSON rules for operational monitoring",
            "Add PySpark tests for detailed investigation",
        ]
        if use_case_insight:
            reasoning.insert(0, use_case_insight)

        implementation_strategy = [
            "Both approaches recommended due to balanced requirements",
            "Start with JSON rules for operational monitoring",
            "Add PySpark tests for comprehensive investigation capabilities",
        ]

    return {
        "primary_recommendation": primary_recommendation,
        "secondary_recommendation": secondary_recommendation,
        "scores": {"pyspark_score": pyspark_score, "json_score": json_score},
        "reasoning": reasoning,
        "implementation_strategy": implementation_strategy,
        "analysis_inputs": {
            "use_case": use_case,
            "complexity_level": complexity_level,
            "monitoring_frequency": monitoring_frequency,
            "debugging_needs": debugging_needs,
            "integration_requirements": integration_requirements,
        },
    }


@mcp.tool(
    description="Get detailed comparison of PySpark tests vs JSON DQ Framework rules across different dimensions."
)
def compare_dq_approaches() -> dict[str, Any]:
    """Return detailed comparison of both DQ approaches."""
    return {
        "comparison_matrix": {
            "Implementation Speed": {
                "pyspark": "Medium - Requires test code development",
                "json": "Fast - Configuration-based setup",
            },
            "Debugging Capabilities": {
                "pyspark": "Excellent - Rich output, statistical analysis, sample data",
                "json": "Basic - Threshold-based alerts only",
            },
            "Operational Monitoring": {
                "pyspark": "Azure Monitor integration - Automated alert generation and dashboards",
                "json": "DQ Framework integration - Built-in metrics publishing and monitoring",
            },
            "Dashboard Integration": {
                "pyspark": "Azure Monitor dashboards - Integrated monitoring and visualization",
                "json": "DQ Framework dashboards - Native framework visualization and metrics",
            },
            "Alerting": {
                "pyspark": "Azure Monitor alerts - Automated alert generation from test metadata",
                "json": "Framework notifications - Built-in DQ Framework alerting capabilities",
            },
            "Maintenance Overhead": {
                "pyspark": "Higher - Code maintenance required",
                "json": "Lower - Configuration updates only",
            },
            "Flexibility": {
                "pyspark": "High - Full programming capabilities",
                "json": "Medium - Framework rule types",
            },
            "Performance": {
                "pyspark": "Higher overhead - Full Databricks execution",
                "json": "Lower overhead - Lightweight framework",
            },
        },
        "use_case_matrix": {
            "Volume Monitoring": {
                "recommended": "JSON Rules",
                "reason": "Simple threshold monitoring ideal for JSON count rules",
            },
            "Data Freshness": {
                "recommended": "JSON Rules",
                "reason": "table_history rules perfect for timeliness monitoring",
            },
            "Complex Business Logic": {
                "recommended": "PySpark Tests",
                "reason": "Custom validation logic requires programming flexibility",
            },
            "Statistical Analysis": {
                "recommended": "PySpark Tests",
                "reason": "Z-scores, anomaly detection need full compute capabilities",
            },
            "Field Completeness": {
                "recommended": "Both",
                "reason": "JSON null_check for monitoring, PySpark for investigation",
            },
            "Data Investigation": {
                "recommended": "PySpark Tests",
                "reason": "Rich debugging output essential for root cause analysis",
            },
            "Operational Dashboards": {
                "recommended": "Both",
                "reason": "JSON provides DQ Framework dashboards, PySpark enables Azure Monitor dashboards",
            },
        },
        "decision_framework": [
            "1. Start with validation complexity: can standardized rules handle your needs or do you need custom logic?",
            "2. Consider execution requirements: lightweight validation vs full Databricks compute",
            "3. Evaluate debugging needs: detailed analysis favors PySpark",
            "4. Assess development approach: declarative rules vs programmatic tests",
            "5. Consider maintenance approach: framework rule updates vs pytest test code maintenance",
            "6. Remember: both approaches support operational monitoring through different mechanisms",
        ],
    }


@mcp.tool(
    description="Get real-world examples of when to use each DQ approach based on actual scenarios."
)
def get_dq_approach_examples() -> dict[str, Any]:
    """Return real-world examples of DQ approach selection."""
    return {
        "pyspark_examples": {
            "BingAds Volume Analysis": {
                "scenario": "Investigating transaction volume anomalies",
                "why_pyspark": [
                    "Statistical analysis needed (z-scores, standard deviation)",
                    "Sample failure records required for investigation",
                    "Complex filtering logic for BillingSource",
                    "Rich debugging output for pattern identification",
                ],
                "outcome": "Identified -0.12 z-score (normal variation) vs suspected anomaly",
            },
            "PaymentNetworkName Mapping": {
                "scenario": "Validating complex mapping logic with exceptions",
                "why_pyspark": [
                    "Custom UDF validation required",
                    "Statistical breakdown by provider needed",
                    "Sample failure records essential for debugging",
                    "Complex business rules for special cases",
                ],
                "outcome": "Found 91.15% valid mappings, identified 3.5M empty string issue",
            },
            "ResponseCode Validation": {
                "scenario": "Comprehensive validation with detailed categorization",
                "why_pyspark": [
                    "24 detailed categories → 10 normalized values mapping",
                    "Provider-level breakdown analysis",
                    "Statistical validation across multiple dimensions",
                    "Rich debugging for edge cases",
                ],
                "outcome": "100% data quality validation with comprehensive analysis",
            },
        },
        "json_examples": {
            "Gold Transactions Volume": {
                "scenario": "Daily transaction count monitoring",
                "why_json": [
                    "Simple count rule sufficient",
                    "Dashboard integration needed",
                    "Automated alerting required",
                    "Continuous monitoring without overhead",
                ],
                "implementation": "count rule with 60% deviation threshold",
            },
            "Data Freshness Monitoring": {
                "scenario": "Processing delay detection",
                "why_json": [
                    "table_history rule perfect fit",
                    "Timeliness monitoring built-in",
                    "Real-time alerting needed",
                    "Operations team dashboard integration",
                ],
                "implementation": "table_history rule with MERGE operation tracking",
            },
            "Critical Field Completeness": {
                "scenario": "ResponseCode null monitoring",
                "why_json": [
                    "null_check rule ideal for field monitoring",
                    "Threshold-based alerting sufficient",
                    "Continuous monitoring required",
                    "Dashboard trend analysis needed",
                ],
                "implementation": "null_check rule with 25% threshold",
            },
        },
        "hybrid_examples": {
            "Comprehensive Transaction Monitoring": {
                "scenario": "Complete gold.transactions data quality coverage",
                "approach": [
                    "JSON count rules for daily volume monitoring",
                    "JSON null_check rules for critical field completeness",
                    "PySpark tests for complex business logic validation",
                    "PySpark tests for detailed investigation when alerts fire",
                ],
                "benefits": "Operational monitoring + investigation capabilities",
            }
        },
        "selection_guidance": [
            "Operational monitoring → JSON Rules",
            "Investigation & debugging → PySpark Tests",
            "Simple thresholds → JSON Rules",
            "Complex validation → PySpark Tests",
            "Dashboard integration → JSON Rules",
            "Statistical analysis → PySpark Tests",
            "Comprehensive coverage → Both approaches",
        ],
    }
