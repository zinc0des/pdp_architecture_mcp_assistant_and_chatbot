"""
MCP Prompts for Common Development Workflows
Contains prompts for general development workflows that apply across all domains.
"""

from pathlib import Path

from mcp.server.fastmcp.prompts import base

from pdp_dev_mcp.common import load_prompt_content
from pdp_dev_mcp.mcp_instance import mcp


def _load_prompt_content(prompt_file: str) -> str:
    """Load prompt content from the common prompts directory."""
    current_dir = Path(__file__).parent
    prompt_path = current_dir / prompt_file
    return load_prompt_content(prompt_path)


@mcp.prompt()
def azure_devops_ai_workflow_guide() -> list[base.Message]:
    """
    Comprehensive guide for Azure DevOps AI-assisted development workflows.
    Provides best practices for integrating AI assistance in development pipelines.
    """
    return [
        base.UserMessage(_load_prompt_content("azure_devops_ai_workflow_guide.md")),
        base.AssistantMessage(
            "I'm ready to help you implement Azure DevOps AI-assisted development workflows! 🚀\n\n"
            "I can guide you through:\n\n"
            "🔄 **AI-Assisted Development Workflow** (MCP tools + MerlinBot enhancement cycle)\n"
            "📋 **Pull Request Best Practices** (creating PRs that get quality AI feedback)\n"
            "🤖 **MerlinBot Integration** (leveraging AI code review for all development)\n"
            "⚙️ **CI/CD Pipeline Setup** (automating validation and deployment)\n"
            "📈 **Team Workflow Enhancement** (proven patterns for AI-human collaboration)\n\n"
            "What aspect of the Azure DevOps AI workflow would you like to explore?"
        ),
    ]


@mcp.prompt()
def copilot_instructions_reminder() -> list[base.Message]:
    """
    Prompt to re-establish GitHub Copilot instructions context.

    Use this when the AI may have lost context of project-specific guidelines
    including tool preferences, security requirements, testing standards, and
    development patterns defined in .github/instructions/*.
    """
    return [
        base.UserMessage("Please always refer to `.github/instructions/*`."),
        base.AssistantMessage(
            "I recognize and will comply with the patterns and guidance outlined in "
            "`.github/instructions/*`. I'll now read those instructions to ensure "
            "I'm following the established tool preferences, security guidelines, "
            "testing standards, and development patterns for this project.\n"
        ),
    ]
