"""
MCP Prompts for Data Quality (DQ) tools
Contains prompts for test suggestion generation and data quality analysis.
"""

from pathlib import Path

from mcp.server.fastmcp.prompts import base

from pdp_dev_mcp.common import load_prompt_content
from pdp_dev_mcp.mcp_instance import mcp


def _load_prompt_content(prompt_file: str) -> str:
    """Load prompt content from the prompts directory."""
    current_dir = Path(__file__).parent
    prompt_path = current_dir / prompt_file
    return load_prompt_content(prompt_path)


@mcp.prompt()
def test_suggestion_generator() -> list[base.Message]:
    """
    Expert Test Suggestion Generator prompt for creating compliant data quality tests.
    Supports both PySpark test templates and JSON DQ Framework rules.
    """
    return [
        base.UserMessage(_load_prompt_content("test_suggestion_generator_prompt.md")),
        base.AssistantMessage(
            "I'm ready to help you create compliant data quality tests! 🧪\n\n"
            "I can help with:\n\n"
            "🔬 **PySpark Test Templates** (detailed investigation, debugging, statistical analysis)\n"
            "📊 **JSON DQ Framework Rules** (continuous monitoring, dashboard integration, automated alerting)\n"
            "🎯 **Architecture Guidance** (choosing the optimal approach for your needs)\n"
            "📁 **Directory Structure** (proper file placement and organization)\n"
            "🐛 **Debugging Patterns** (best practices for troubleshooting DQ tests)\n\n"
            "What type of data quality test or monitoring rule would you like to create today?"
        ),
    ]


@mcp.prompt()
def data_quality_analyst() -> list[base.Message]:
    """
    Expert Data Quality Analysis prompt for analyzing test files and compliance.
    """
    return [
        base.UserMessage(_load_prompt_content("data_quality_analysis_prompt.md")),
        base.AssistantMessage(
            "I'm ready to analyze your data quality tests for compliance and effectiveness! 📋\n\n"
            "I can help with:\n\n"
            "✅ **Standards Compliance** (review files against PDP data quality standards)\n"
            "📝 **Batch Analysis** (analyze multiple test files simultaneously)\n"
            "🔍 **Pattern Recognition** (identify good practices and anti-patterns)\n"
            "📈 **Gap Analysis** (highlight missing test coverage and improvements)\n"
            "🛠️ **Framework Validation** (ensure proper use of both PySpark and JSON DQ patterns)\n\n"
            "Would you like me to analyze a specific test file, multiple files, or provide guidance on data quality standards?"
        ),
    ]


@mcp.prompt()
def dual_path_dq_guidance() -> list[base.Message]:
    """
    Comprehensive guidance on the dual-path data quality architecture.
    Helps users choose between PySpark tests and JSON DQ Framework rules.
    """
    return [
        base.UserMessage(_load_prompt_content("dual_path_architecture_guidance.md")),
        base.AssistantMessage(
            "I'm ready to help you choose the optimal data quality approach! 🎯\n\n"
            "I can guide you through:\n\n"
            "📊 **JSON DQ Framework Rules** (operational monitoring, dashboard integration, standard checks)\n"
            "🔬 **PySpark Tests** (complex validation, statistical analysis, debugging capabilities)\n"
            "⚖️ **Decision Matrix** (choosing the right approach based on your specific needs)\n"
            "🚀 **Implementation Best Practices** (getting started with either approach)\n"
            "🔄 **Hybrid Strategies** (using both approaches strategically)\n\n"
            "What type of data quality validation are you looking to implement?"
        ),
    ]
