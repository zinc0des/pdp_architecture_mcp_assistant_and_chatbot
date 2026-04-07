"""
Tests for DQ prompts.

Tests focus on developer capabilities - what developers can accomplish
by accessing specialized prompts through the MCP prompt interface.
"""

from pdp_dev_mcp.prompts.data_quality import dq_prompts


class TestDevelopersCanAccessSpecializedDataQualityPrompts:
    """Test what developers can accomplish by accessing specialized data quality prompts through MCP prompt selection."""

    def test_ai_agents_help_engineers_access_targeted_test_generation_guidance_via_prompt_selection(
        self,
    ):
        """
        As a data engineer
        When I ask an AI agent to help with PySpark data quality test generation
        Then the agent provides specialized prompts I can use to create effective tests
        """
        # This tests what engineers can access through MCP prompt selection
        result = dq_prompts.test_suggestion_generator()

        # Engineers need structured, actionable prompt content they can use directly
        assert isinstance(result, list), (
            "Engineers need structured prompt guidance they can select and use"
        )
        assert len(result) > 0, (
            "Engineers need actual prompt content, not empty responses"
        )

        # Engineers need accessible prompt content they can paste into their workflow
        assert result[0].content is not None, (
            "Engineers need accessible prompt content for their workflows"
        )
        assert hasattr(result[0].content, "text"), (
            "Engineers need readable prompt text they can use"
        )
        assert len(result[0].content.text) > 0, (
            "Engineers need substantive guidance content for effective prompting"
        )

        # Engineers should get comprehensive structured guidance with clear sections for test generation
        content_text = result[0].content.text

        # Verify engineers get the key structural sections they need for effective test generation
        expected_guidance_sections = [
            "# Test Suggestion Generator Agent",
            "## Responsibilities:",
            "## Workflow:",
            "## 🚀 AI-Assisted Development Integration",
            "## Best Practices Integration:",
        ]

        for section in expected_guidance_sections:
            assert section in content_text, (
                f"Engineers need structured test generation guidance with clear '{section}' for effective development"
            )

        # The prompt should provide practical guidance engineers can send to AI agents
        content_text_lower = content_text.lower()
        test_generation_keywords = [
            "test",
            "pyspark",
            "data quality",
            "suggestion",
            "generation",
        ]
        assert any(
            keyword in content_text_lower for keyword in test_generation_keywords
        ), (
            "Prompt should provide engineers with effective guidance for data quality test creation"
        )

    def test_ai_agents_help_analysts_access_specialized_data_quality_expertise_via_prompt_selection(
        self,
    ):
        """
        As a data quality analyst
        When I ask an AI agent for expert-level analytical guidance
        Then the agent provides specialized prompts and methodologies I can apply
        """
        # This tests what analysts can access through MCP prompt selection
        result = dq_prompts.data_quality_analyst()

        # Analysts need expert-level prompt content they can use directly
        assert isinstance(result, list), (
            "Analysts need structured expert prompts they can select and use"
        )
        assert len(result) > 0, (
            "Analysts need substantive expertise prompts, not empty responses"
        )

        # Analysts need accessible expert content they can paste into their analytical workflows
        assert result[0].content is not None, (
            "Analysts need accessible expert prompt content"
        )
        assert hasattr(result[0].content, "text"), (
            "Analysts need readable analytical prompts"
        )
        assert len(result[0].content.text) > 0, (
            "Analysts need comprehensive expert prompt content"
        )

        # The prompt should provide analytical expertise analysts can send to AI agents
        content_text = result[0].content.text.lower()
        assert any(
            keyword in content_text
            for keyword in ["data quality", "analyst", "analysis", "dq"]
        ), (
            "Prompt should provide analysts with expert-level data quality analytical guidance"
        )

    def test_ai_agents_help_teams_access_dual_approach_strategy_guidance_via_prompt_selection(
        self,
    ):
        """
        As a data quality team
        When I ask an AI agent for strategic guidance on PySpark tests vs JSON rules
        Then the agent provides prompts to help me make informed decisions
        """
        # This tests what teams can access through MCP prompt selection
        result = dq_prompts.dual_path_dq_guidance()
        print(result)

        # Teams need clear strategic prompt content they can use for decision-making
        assert isinstance(result, list), (
            "Teams need structured strategic prompt guidance they can select and use"
        )
        assert len(result) > 0, (
            "Teams need actual strategic prompt content, not empty guidance"
        )

        # Teams need accessible strategic content they can paste into their workflow
        assert result[0].content is not None, (
            "Teams need accessible strategic prompt content for decision-making"
        )
        assert hasattr(result[0].content, "text"), (
            "Teams need readable strategic prompts for approach selection"
        )
        assert len(result[0].content.text) > 0, (
            "Teams need comprehensive strategic prompt content"
        )

        # Teams should get comprehensive structured guidance with clear sections for decision-making
        content_lower = result[0].content.text.lower()

        # Verify teams get the key structural sections they need for making informed decisions
        expected_sections = [
            "## 📊 json dq framework rules - when to use:",
            "## 🔬 pyspark tests - when to use:",
            "## 🎯 decision matrix:",
            "## 🚀 ai-assisted development best practices",
        ]

        for section in expected_sections:
            assert section in content_lower, (
                f"Teams need structured guidance with clear '{section}' section for informed decision-making"
            )

        # Teams need decision-support content that helps them choose the right approach
        decision_keywords = ["pyspark", "json", "data quality", "guidance", "approach"]
        assert any(keyword in content_lower for keyword in decision_keywords), (
            "Prompt should help teams understand both PySpark and JSON DQ approaches"
        )
