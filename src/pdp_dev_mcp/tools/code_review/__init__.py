"""
Code Review AI-Assisted Tools

These tools help AI agents provide intelligent code review assistance by gathering
comprehensive context about pull requests, dependencies, and test coverage.

Designed to enable AI agents to:
- Understand the full context of code changes
- Identify critical dependencies and downstream impacts
- Analyze test coverage and suggest improvements
- Provide domain-specific guidance for payment processing code

Following established BDD patterns for behavior-driven development.
"""

from .change_context import get_payments_change_context
from .static_analysis import (
    get_payments_domain_context,
    analyze_payment_code_compliance,
    analyze_payment_provider_patterns,
    analyze_payment_architecture_constraints,
    analyze_payment_historical_issues,
)

from .ai_enabling_analysis import get_code_analysis_context
from .code_quality_signals import get_code_quality_signals
from .ai_comment_posting import post_ai_generated_comments, post_ai_comments_by_pr_url

# Import enhanced prescriptive comment functions
from .prescriptive_comments import (
    azure_devops_establish_pr_context,
    get_pr_file_changes_with_context,
    get_file_contents_with_context,
    generate_change_summary_with_context,
    analyze_test_coverage_with_context,
    # Import key dataclasses for external use
    AzureDevOpsPRContext,
    PRDetails,
    DependencyInfo,
    PRCodeContextResult,
)

__all__ = [
    "get_payments_change_context",
    "get_payments_domain_context",
    "analyze_payment_code_compliance",
    "analyze_payment_provider_patterns",
    "analyze_payment_architecture_constraints",
    "analyze_payment_historical_issues",
    "get_code_analysis_context",
    "get_code_quality_signals",
    "post_ai_generated_comments",
    "post_ai_comments_by_pr_url",
    # Enhanced prescriptive comment functions (modern MCP tool architecture)
    "azure_devops_establish_pr_context",
    "get_pr_file_changes_with_context",
    "get_file_contents_with_context",
    "generate_change_summary_with_context",
    "analyze_test_coverage_with_context",
    # Key dataclasses for external use
    "AzureDevOpsPRContext",
    "PRDetails",
    "DependencyInfo",
    "PRCodeContextResult",
]
