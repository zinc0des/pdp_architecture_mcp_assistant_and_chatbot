"""
PDP Development MCP Prompts - Specialized prompts for platform development workflows.

This module contains prompt definitions that provide expert guidance for
specialized platform development prompts accessible to developers via MCP clients.

Currently organized into:
- common: General development workflow guides and prompts
- code_review: AI-assisted code review tools and workflows
- data_quality: Data quality analysis, testing, and architectural guidance prompts
"""

# Import domain-specific prompts to register them
from .code_review import code_review_prompts
from .common import common_prompts
from .data_quality import dq_prompts

__all__ = [
    "common_prompts",  # MCP prompts for general development workflows
    "code_review_prompts",  # MCP prompts for AI-assisted code reviews
    "dq_prompts",  # MCP prompts for data quality workflows
]
