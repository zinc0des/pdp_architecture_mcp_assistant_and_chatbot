"""
MCP Tools - AI-accessible functions for common development workflows.

Common tools and utilities for the PDP Development MCP server.
This module provides shared functionality that can be used across different domains,
including Azure DevOps workflow automation and other cross-cutting concerns.
"""

# Import Azure DevOps tools from domain-specific modules to register them with the MCP server
# Repository context management
from .azure_devops_repository import (
    azure_devops_repository_discovery,
    azure_devops_workflow_setup,
    set_repository_context,
    get_repository_context_status,
    clear_repository_context,
)

# PR comment management
from .azure_devops_pr_comments import (
    azure_devops_establish_pr_context,
    azure_devops_pr_comment_analysis,
    azure_devops_post_pr_comment,
    azure_devops_reply_to_pr_comment,
    azure_devops_resolve_pr_comments,
)

# PR review status and reminders
from .azure_devops_pr_review import (
    azure_devops_get_pr_review_status,
    azure_devops_send_pr_review_reminders,
)

# PR lifecycle management
from .azure_devops_pr_lifecycle import (
    azure_devops_create_pull_request,
)

__all__ = [
    # Repository context management
    "azure_devops_repository_discovery",
    "azure_devops_workflow_setup",
    "set_repository_context",
    "get_repository_context_status",
    "clear_repository_context",
    # PR comment management
    "azure_devops_establish_pr_context",
    "azure_devops_pr_comment_analysis",
    "azure_devops_post_pr_comment",
    "azure_devops_reply_to_pr_comment",
    "azure_devops_resolve_pr_comments",
    # PR review status and reminders
    "azure_devops_get_pr_review_status",
    "azure_devops_send_pr_review_reminders",
    # PR lifecycle management
    "azure_devops_create_pull_request",
]
