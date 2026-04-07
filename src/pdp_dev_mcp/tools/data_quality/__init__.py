"""
MCP Tools - AI-accessible functions for data quality workflows.

This module contains @mcp.tool decorated functions that AI agents can call
to help developers with data quality analysis, generation, and guidance.
"""

from .analysis_tools import (
    analyze_test_file,
    analyze_multiple_files,
    get_analysis_standards,
)
from .architecture_guidance_tools import (
    get_dq_architecture_guidance,
    get_dq_approach_examples,
    recommend_dq_approach,
    compare_dq_approaches,
)
from .json_generation_tools import (
    generate_json_rule_suggestions,
    generate_advanced_json_rule,
    get_json_rule_types_info,
)
from .pyspark_generation_tools import (
    generate_test_suggestions,
    get_pyspark_test_guidance,
)

__all__ = [
    # Analysis tools
    "analyze_test_file",
    "analyze_multiple_files",
    "get_analysis_standards",
    # Architecture guidance tools
    "get_dq_architecture_guidance",
    "get_dq_approach_examples",
    "recommend_dq_approach",
    "compare_dq_approaches",
    # JSON generation tools
    "generate_json_rule_suggestions",
    "generate_advanced_json_rule",
    "get_json_rule_types_info",
    # PySpark generation tools
    "generate_test_suggestions",
    "get_pyspark_test_guidance",
]
