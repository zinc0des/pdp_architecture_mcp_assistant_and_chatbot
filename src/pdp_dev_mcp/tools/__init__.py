"""
PDP Development MCP Tools - AI-accessible functions for platform development workflows.

This module contains @mcp.tool decorated functions that AI agents can call
to help developers with various aspects of Payments Data Platform development.

Currently organized into:
- architecture: PDP architecture knowledge base retrieval tools
- grafana: Grafana alert analysis and resolution tools
- knowledge_harvester: Knowledge harvesting and repo scanning tools
- research_notes: Personal research vault management tools
- data_quality: Data quality analysis, test generation, and compliance tools
- common: Cross-cutting tools including Azure DevOps workflow automation
- code_review: AI-enabled code review and PR analysis tools
"""

# Import architecture knowledge base tools (self-registering via @mcp.tool)
from .architecture import (  # noqa: F401
    list_architecture_topics,
    get_architecture_topic,
    search_architecture,
    get_layer_detail,
    get_domain_schema,
    get_data_flow,
)

# Import Grafana alert tools (self-registering via @mcp.tool)
from .grafana import (  # noqa: F401
    grafana_get_alert_resolution_guidance,
    grafana_get_upstream_check_guidance,
    grafana_diagnose_network_issues,
    grafana_get_alert_best_practices,
    grafana_analyze_alert_pattern,
)

# Import knowledge harvester tools (self-registering via @mcp.tool)
from .knowledge_harvester import (  # noqa: F401
    harvest_pdp_learnings,
    validate_pdp_relevance,
    search_learnings,
    list_learnings,
    get_learning,
    verify_learning,
    scan_repos_for_knowledge,
    get_file_diff_summary,
)

# Import research notes tools (self-registering via @mcp.tool)
from .research_notes import (  # noqa: F401
    capture_research_notes,
    tag_research_notes,
    list_research_notes,
    get_research_note,
)

# Import data quality tools
from .data_quality import (
    analyze_test_file,
    analyze_multiple_files,
    get_analysis_standards,
    get_dq_architecture_guidance,
    get_dq_approach_examples,
    recommend_dq_approach,
    compare_dq_approaches,
    generate_json_rule_suggestions,
    generate_advanced_json_rule,
    get_json_rule_types_info,
    generate_test_suggestions,
    get_pyspark_test_guidance,
)

# Import common tools
from .common import (
    # Repository context management
    azure_devops_repository_discovery,
    azure_devops_workflow_setup,
    set_repository_context,
    get_repository_context_status,
    clear_repository_context,
    # PR comment management
    azure_devops_pr_comment_analysis,
    azure_devops_resolve_pr_comments,
    # PR review status and reminders
    azure_devops_get_pr_review_status,
    azure_devops_send_pr_review_reminders,
    # PR lifecycle management
    azure_devops_create_pull_request,
)

# Import code review tools
from .code_review import (
    get_payments_change_context,
    get_payments_domain_context,
    analyze_payment_code_compliance,
    analyze_payment_provider_patterns,
    analyze_payment_architecture_constraints,
    analyze_payment_historical_issues,
    get_code_analysis_context,
    get_code_quality_signals,
    post_ai_generated_comments,
    post_ai_comments_by_pr_url,
    # Enhanced prescriptive comment functions (modern MCP tool architecture)
    azure_devops_establish_pr_context,
    get_pr_file_changes_with_context,
    get_file_contents_with_context,
    generate_change_summary_with_context,
    analyze_test_coverage_with_context,
    # Key dataclasses for external use
    AzureDevOpsPRContext,
    PRDetails,
    DependencyInfo,
    PRCodeContextResult,
)

__all__ = [
    # Architecture Knowledge Base tools
    "list_architecture_topics",
    "get_architecture_topic",
    "search_architecture",
    "get_layer_detail",
    "get_domain_schema",
    "get_data_flow",
    # Grafana Alert tools
    "grafana_get_alert_resolution_guidance",
    "grafana_get_upstream_check_guidance",
    "grafana_diagnose_network_issues",
    "grafana_get_alert_best_practices",
    "grafana_analyze_alert_pattern",
    # Knowledge Harvester tools
    "harvest_pdp_learnings",
    "validate_pdp_relevance",
    "search_learnings",
    "list_learnings",
    "get_learning",
    "verify_learning",
    "scan_repos_for_knowledge",
    "get_file_diff_summary",
    # Research Notes tools
    "capture_research_notes",
    "tag_research_notes",
    "list_research_notes",
    "get_research_note",
    # Data Quality Analysis tools
    "analyze_test_file",
    "analyze_multiple_files",
    "get_analysis_standards",
    # Data Quality Architecture guidance tools
    "get_dq_architecture_guidance",
    "get_dq_approach_examples",
    "recommend_dq_approach",
    "compare_dq_approaches",
    # Data Quality JSON generation tools
    "generate_json_rule_suggestions",
    "generate_advanced_json_rule",
    "get_json_rule_types_info",
    # Data Quality PySpark generation tools
    "generate_test_suggestions",
    "get_pyspark_test_guidance",
    # Azure DevOps Workflow tools
    "azure_devops_repository_discovery",
    "azure_devops_workflow_setup",
    "set_repository_context",
    "get_repository_context_status",
    "clear_repository_context",
    "azure_devops_pr_comment_analysis",
    "azure_devops_resolve_pr_comments",
    "azure_devops_get_pr_review_status",
    "azure_devops_send_pr_review_reminders",
    "azure_devops_create_pull_request",
    # Code Review tools
    "get_payments_change_context",
    # Payment Domain Knowledge tools
    "get_payments_domain_context",
    "analyze_payment_code_compliance",
    "analyze_payment_provider_patterns",
    "analyze_payment_architecture_constraints",
    "analyze_payment_historical_issues",
    # AI-Enabling Code Review tools
    "get_code_analysis_context",
    "get_code_quality_signals",
    "post_ai_generated_comments",
    "post_ai_comments_by_pr_url",
    # Enhanced Prescriptive Comment Functions (Modern MCP Tool Architecture)
    "azure_devops_establish_pr_context",
    "get_pr_file_changes_with_context",
    "get_file_contents_with_context",
    "generate_change_summary_with_context",
    "analyze_test_coverage_with_context",
    # Key Dataclasses
    "AzureDevOpsPRContext",
    "PRDetails",
    "DependencyInfo",
    "PRCodeContextResult",
]
