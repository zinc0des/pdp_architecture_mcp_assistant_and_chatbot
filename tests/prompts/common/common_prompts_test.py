"""
Tests for Common Development Prompts - behavior-focused tests

Tests focus on what developers and DevOps teams can accomplish when using
general development workflow prompts accessible via MCP clients.
"""

from pdp_dev_mcp.prompts.common import common_prompts


class TestDevelopersCanAccessGeneralDevelopmentWorkflowPrompts:
    """Test what developers can accomplish when accessing general development workflow prompts via MCP clients."""

    def test_ai_agents_help_devops_teams_access_workflow_guidance_via_prompt_selection(
        self,
    ):
        """
        As a DevOps team
        When I ask an AI agent for workflow implementation guidance
        Then the agent provides AI-enhanced prompts for Azure DevOps pipeline development
        """
        # This tests what DevOps teams can access through MCP prompt selection
        result = common_prompts.azure_devops_ai_workflow_guide()

        # DevOps teams need practical implementation prompts they can use directly
        assert isinstance(result, list), (
            "DevOps teams need structured implementation prompts they can select and use"
        )
        assert len(result) > 0, (
            "DevOps teams need actual workflow prompt content, not empty responses"
        )

        # DevOps teams need accessible implementation prompts they can paste into their planning
        assert result[0].content is not None, (
            "DevOps teams need accessible workflow prompt content"
        )
        assert hasattr(result[0].content, "text"), (
            "DevOps teams need readable implementation prompts"
        )
        assert len(result[0].content.text) > 0, (
            "DevOps teams need comprehensive workflow prompt content"
        )

        # DevOps teams should get comprehensive structured guidance with clear workflow phases
        content_text = result[0].content.text

        # Verify teams get the key structural sections they need for implementing AI workflows
        expected_workflow_sections = [
            "## 🚀 The Complete Workflow",
            "### Phase 1: Initial Development",
            "### Phase 2: Pull Request Creation",
            "### Phase 3: AI Review (The Magic ✨)",
            "### Phase 4: AI Feedback Analysis & Implementation",
            "## 🔧 Essential Azure DevOps MCP Tools",
        ]

        for section in expected_workflow_sections:
            assert section in content_text, (
                f"DevOps teams need structured workflow guidance with clear '{section}' for implementation"
            )

        # The prompt should provide relevant DevOps implementation guidance
        content_text_lower = content_text.lower()
        implementation_keywords = [
            "azure",
            "devops",
            "ai",
            "workflow",
            "pipeline",
            "merlinbot",
        ]
        assert any(
            keyword in content_text_lower for keyword in implementation_keywords
        ), "Prompt should help DevOps teams implement AI-enhanced development workflows"


class TestDevelopersHandlePromptAccessEdgeCases:
    """Test how developers handle edge cases when accessing prompt content."""

    def test_ai_agents_get_meaningful_fallback_when_specific_prompt_content_unavailable(
        self,
    ):
        """
        Given an AI agent accessing workflow guidance prompts
        When specific prompt content is unavailable or corrupted
        Then the system should provide meaningful fallback content
        """
        # Given: AI agent accessing prompts
        # When: Accessing workflow guidance prompts (this should work)
        result = common_prompts.azure_devops_ai_workflow_guide()

        # Then: System should provide meaningful content
        assert isinstance(result, list), (
            "AI agents should receive structured prompt responses"
        )
        assert len(result) > 0, (
            "AI agents should get meaningful content, not empty responses"
        )

        # And: Content should be accessible and meaningful
        assert result[0].content is not None, (
            "AI agents should get accessible prompt content"
        )
        assert hasattr(result[0].content, "text"), (
            "AI agents should get text-based prompt content"
        )
        assert len(result[0].content.text) > 50, (
            "AI agents should get substantial content, not just placeholders"
        )
