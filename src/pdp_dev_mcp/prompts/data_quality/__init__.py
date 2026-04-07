"""
Data Quality MCP Prompts - Specialized prompts for data quality workflows.

This module contains prompt definitions that provide expert guidance for
specialized data quality prompts accessible to developers via MCP clients.
"""

# Import the module to register the MCP prompts via decorators
# Prompts are automatically registered when the module is imported
from . import dq_prompts

__all__ = [
    "dq_prompts",  # Module containing MCP prompt definitions
]
