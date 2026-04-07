"""
MCP Tools - AI-accessible functions for Grafana alert monitoring and resolution workflows.

This module contains @mcp.tool decorated functions that AI agents can call
to help developers understand, diagnose, and resolve Grafana DQ alerts for
the Payments Data Platform.

Tools provided:
- grafana_get_alert_resolution_guidance: Get resolution recommendations for specific alerts
- grafana_get_upstream_check_guidance: Get guidance on checking upstream data sources
- grafana_diagnose_network_issues: Diagnose potential network-related data issues
- grafana_get_alert_best_practices: Get best practices for alert investigation
"""

from .grafana_alert_tools import (
    grafana_get_alert_resolution_guidance,
    grafana_get_upstream_check_guidance,
    grafana_diagnose_network_issues,
    grafana_get_alert_best_practices,
    grafana_analyze_alert_pattern,
)

__all__ = [
    "grafana_get_alert_resolution_guidance",
    "grafana_get_upstream_check_guidance",
    "grafana_diagnose_network_issues",
    "grafana_get_alert_best_practices",
    "grafana_analyze_alert_pattern",
]
