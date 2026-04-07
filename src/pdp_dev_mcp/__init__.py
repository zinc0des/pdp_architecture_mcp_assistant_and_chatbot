"""
Payments Data Platform Development MCP Server

Development tools for the Payments Data Platform with domain-specific capabilities:

Data Quality:
- PySpark test generation for detailed investigation
- JSON DQ Framework rules for operational monitoring
- Test analysis and standards compliance checking
- Architecture guidance and best practices

AI-Enabling Code Review:
- Comprehensive context analysis for intelligent AI reviews
- Quality signal detection to focus on genuine concerns
- Contextual comment posting to Azure DevOps PRs
- Payment domain expertise integration

Future domains could include infrastructure automation, deployment tooling,
monitoring capabilities, and security analysis.
"""

# Always read version from pyproject.toml for local development
# This ensures the running code version matches the source, not the installed package
try:
    import tomllib
except ImportError:
    import tomli as tomllib
from pathlib import Path

try:
    pyproject_path = Path(__file__).parent.parent.parent / "pyproject.toml"
    with open(pyproject_path, "rb") as f:
        pyproject_data = tomllib.load(f)
        __version__ = pyproject_data["project"]["version"]
except Exception:
    # Fallback to installed package version if pyproject.toml not found
    try:
        from importlib.metadata import version
        __version__ = version("pdp-dev-mcp")
    except Exception:
        __version__ = "0.0.0.dev0"

# Import modules to register MCP tools and prompts
# The @mcp.tool and @mcp.prompt decorators execute during import, registering functionality
# This ensures all tools are available regardless of the entry point used
from pdp_dev_mcp.prompts import (
    dq_prompts as dq_prompts,  # MCP prompts for data quality workflows
)
from pdp_dev_mcp.tools import (
    # Data quality analysis tools
    analyze_test_file as analyze_test_file,
    analyze_multiple_files as analyze_multiple_files,
    get_analysis_standards as get_analysis_standards,
    # Data quality architecture guidance tools
    get_dq_architecture_guidance as get_dq_architecture_guidance,
    get_dq_approach_examples as get_dq_approach_examples,
    recommend_dq_approach as recommend_dq_approach,
    compare_dq_approaches as compare_dq_approaches,
    # JSON DQ Framework generation tools
    generate_json_rule_suggestions as generate_json_rule_suggestions,
    generate_advanced_json_rule as generate_advanced_json_rule,
    get_json_rule_types_info as get_json_rule_types_info,
    # PySpark test generation tools
    generate_test_suggestions as generate_test_suggestions,
    get_pyspark_test_guidance as get_pyspark_test_guidance,
    # Code review tools
    get_payments_change_context as get_payments_change_context,
    # Payment domain knowledge tools
    get_payments_domain_context as get_payments_domain_context,
    analyze_payment_code_compliance as analyze_payment_code_compliance,
    analyze_payment_provider_patterns as analyze_payment_provider_patterns,
    analyze_payment_architecture_constraints as analyze_payment_architecture_constraints,
    analyze_payment_historical_issues as analyze_payment_historical_issues,
    # AI-enabling code review tools
    get_code_analysis_context as get_code_analysis_context,
    get_code_quality_signals as get_code_quality_signals,
    post_ai_generated_comments as post_ai_generated_comments,
)
