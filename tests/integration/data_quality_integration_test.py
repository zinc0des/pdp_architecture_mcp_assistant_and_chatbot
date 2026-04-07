"""
Data Quality tools integration tests.

Tests focus on AI agent workflow capabilities - how AI agents can help developers combine
different DQ tools to accomplish their data quality goals in real-world scenarios.

These integration tests verify end-to-end workflows across multiple DQ tools rather than
individual tool functionality (which is covered by unit tests).
"""

import pytest
from pdp_dev_mcp.tools.data_quality import (
    analyze_test_file,
    generate_json_rule_suggestions,
    generate_test_suggestions,
)


@pytest.mark.integration
class TestDataQualityAIAgentWorkflowIntegration:
    """Test how AI agents can help developers combine different tools for end-to-end data quality workflows."""

    def test_ai_agents_can_help_developers_analyze_existing_tests_then_generate_new_ones(
        self, sample_test_file: str
    ) -> None:
        """AI agents should be able to help developers analyze their current tests and then generate additional tests based on insights."""
        # This tests the AI agent's ability to support multi-step developer workflows

        # First, AI agents help developers analyze what they currently have
        analysis_result = analyze_test_file(sample_test_file)

        # Then AI agents help developers generate new tests to fill gaps
        generation_result = generate_test_suggestions(
            test_type="Integration",
            subject_area="PaymentTransactions",
            data_quality_category="Completeness",
            table_name="gold_transactions",
        )

        # AI agents need comprehensive analysis capability to help developers understand their current state
        assert analysis_result["total_tests"] >= 1, (
            "AI agents should help developers see their existing test coverage"
        )
        # AI agents need generation capability to help developers implement improvements
        assert "test_template" in generation_result, (
            "AI agents should provide developers with new test code they can implement"
        )

    def test_ai_agents_can_help_developers_implement_comprehensive_monitoring_strategy(
        self,
    ) -> None:
        """AI agents should be able to help developers generate both immediate testing and ongoing monitoring for the same data quality concern."""
        # This tests the AI agent's ability to support comprehensive developer monitoring strategies

        # AI agents help developers with immediate validation (PySpark tests) and ongoing monitoring (JSON rules)
        pyspark_result = generate_test_suggestions(
            test_type="Integration",
            subject_area="PaymentTransactions",
            data_quality_category="Accuracy",
            table_name="transactions",
        )

        json_result = generate_json_rule_suggestions(
            table_name="transactions", monitoring_type="accuracy"
        )

        # AI agents need both test and monitoring generation to help developers with comprehensive coverage
        assert "test_template" in pyspark_result, (
            "AI agents should provide developers with immediate test validation capabilities"
        )
        assert "json_rule" in json_result, (
            "AI agents should provide developers with ongoing monitoring rule capabilities"
        )

        # AI agents need coherent output to help developers address their specific concerns
        pyspark_content = str(pyspark_result.get("test_template", "")).lower()
        json_content = str(json_result.get("json_rule", "")).lower()
        assert "accuracy" in pyspark_content or "valid" in pyspark_content, (
            "AI agents should help developers with PySpark tests that address accuracy validation"
        )
        assert "accuracy" in json_content or any(
            term in json_content for term in ["valid", "correct", "match"]
        ), (
            "AI agents should help developers with JSON rules that address accuracy monitoring"
        )
