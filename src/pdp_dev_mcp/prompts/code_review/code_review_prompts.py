"""
MCP Prompts for Code Review Workflows
Contains prompts for AI-assisted code review processes specific to payment platform development.
"""

from pathlib import Path

from mcp.server.fastmcp.prompts import base

from pdp_dev_mcp.common import load_prompt_content
from pdp_dev_mcp.mcp_instance import mcp


def _load_prompt_content(prompt_file: str) -> str:
    """Load prompt content from the code_review prompts directory."""
    current_dir = Path(__file__).parent
    prompt_path = current_dir / prompt_file
    return load_prompt_content(prompt_path)


@mcp.prompt()
def code_review_tools_guide() -> list[base.Message]:
    """
    Comprehensive guide to MCP code review tools for AI-assisted payment platform reviews.

    Provides detailed information about:
    - AI-enabling analysis tools for context and quality signals
    - Comment posting tools for delivering feedback
    - Payment domain-specific analysis tools
    - Best practices for using tools in AI-assisted workflows
    """
    return [
        base.UserMessage(_load_prompt_content("code_review_tools_guide.md")),
        base.AssistantMessage(
            "I'm ready to assist with AI-enabled code reviews using the MCP tools! 🔍\n\n"
            "I have access to 10 specialized code review tools organized into:\n\n"
            "📊 **AI-Enabling Tools** (Context & Quality Assessment):\n"
            "   • get_code_analysis_context - Comprehensive PR analysis framework\n"
            "   • get_payments_change_context - Payment domain context extraction\n"
            "   • get_code_quality_signals - Static analysis and pattern detection\n\n"
            "💬 **Comment Posting Tools** (Feedback Delivery):\n"
            "   • post_ai_comments_by_pr_url - Post comments using PR URL (recommended)\n"
            "   • post_ai_generated_comments - Post comments with explicit parameters\n\n"
            "🔍 **Payment Domain Tools** (Deep Domain Analysis):\n"
            "   • get_payments_domain_context - Domain knowledge analysis\n"
            "   • analyze_payment_code_compliance - PCI DSS compliance checking\n"
            "   • analyze_payment_provider_patterns - Provider integration analysis\n"
            "   • analyze_payment_architecture_constraints - Architecture validation\n"
            "   • analyze_payment_historical_issues - Historical incident analysis\n\n"
            "What type of code review assistance would you like help with?"
        ),
    ]
