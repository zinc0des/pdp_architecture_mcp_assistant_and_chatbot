"""
Tests for DQ architecture guidance tools - behavior-focused tests.

Tests focus on what AI agents can accomplish when helping developers
with data quality architecture decisions and guidance.
"""

import pytest

from pdp_dev_mcp.tools.data_quality import (
    compare_dq_approaches,
    get_dq_approach_examples,
    get_dq_architecture_guidance,
    recommend_dq_approach,
)


class TestAIAgentsCanProvideArchitectureGuidance:
    """Test what AI agents can accomplish when helping developers with DQ architecture decisions."""

    def test_ai_agents_can_provide_comprehensive_architecture_guidance_to_developers(
        self,
    ) -> None:
        """AI agents should be able to access and provide comprehensive data quality architecture guidance to developers."""
        # This tests the AI agent's ability to help developers with architectural decisions
        try:
            result = get_dq_architecture_guidance()

            # AI agents need reliable, structured guidance they can interpret and relay
            assert result is not None, (
                "AI agents need accessible architecture guidance to help developers"
            )

            # AI agents need guidance content they can understand and communicate
            result_str = str(result).lower()
            has_guidance = any(
                term in result_str
                for term in [
                    "architecture",
                    "guidance",
                    "approach",
                    "pattern",
                    "design",
                    "data quality",
                    "dq",
                    "framework",
                    "solution",
                ]
            )
            assert has_guidance, (
                "AI agents need meaningful architectural content to provide helpful guidance to developers"
            )

        except Exception as e:
            assert False, (
                f"AI agents should be able to reliably access architecture guidance: {e}"
            )

    def test_ai_agents_can_explain_approach_tradeoffs_to_developers(self) -> None:
        """AI agents should be able to compare DQ approaches and explain tradeoffs to developers."""
        # This tests the AI agent's ability to help developers understand options
        try:
            result = compare_dq_approaches()

            # AI agents need comparative information they can interpret and explain
            assert result is not None, (
                "AI agents need comparison data to help developers choose approaches"
            )

            # AI agents need content that allows them to explain tradeoffs effectively
            result_str = str(result).lower()
            has_comparison = any(
                term in result_str
                for term in [
                    "compare",
                    "vs",
                    "versus",
                    "difference",
                    "advantage",
                    "benefit",
                    "pyspark",
                    "json",
                    "approach",
                    "framework",
                ]
            )
            assert has_comparison, (
                "AI agents need comparative content to explain approach differences to developers"
            )

        except Exception as e:
            assert False, (
                f"AI agents should be able to reliably access approach comparisons: {e}"
            )

    def test_ai_agents_can_provide_tailored_recommendations_based_on_developer_context(
        self,
    ) -> None:
        """AI agents should be able to generate tailored recommendations based on specific developer requirements."""
        # This tests the AI agent's ability to process context and provide relevant advice
        try:
            result = recommend_dq_approach(
                use_case="volume monitoring",
                complexity_level="low",
                debugging_needs="basic",
            )

            # AI agents need tailored recommendations they can explain to developers
            assert result is not None, (
                "AI agents need recommendation capability to help developers choose appropriate approaches"
            )

            # AI agents need context-aware responses they can use to advise developers
            result_str = str(result).lower()
            incorporates_context = any(
                term in result_str
                for term in [
                    "volume",
                    "monitoring",
                    "low",
                    "basic",
                    "recommend",
                    "suggest",
                ]
            )
            assert incorporates_context, (
                "AI agents need context-aware recommendations to provide relevant advice to developers"
            )

        except Exception as e:
            assert False, (
                f"AI agents should be able to reliably generate tailored recommendations: {e}"
            )

    def test_ai_agents_can_access_practical_examples_for_developers(self) -> None:
        """AI agents should be able to provide practical examples that help developers understand DQ approaches."""
        # This tests the AI agent's ability to provide concrete examples to developers
        try:
            result = get_dq_approach_examples()

            # AI agents need practical examples they can share with developers
            assert result is not None, (
                "AI agents need example content to help developers understand implementation options"
            )

            # AI agents need example content that demonstrates real-world application
            result_str = str(result).lower()
            has_examples = any(
                term in result_str
                for term in [
                    "example",
                    "sample",
                    "case",
                    "scenario",
                    "use case",
                    "implementation",
                    "practice",
                    "real",
                ]
            )
            assert has_examples, (
                "AI agents need practical examples to help developers understand how to apply DQ approaches"
            )

        except Exception as e:
            assert False, f"AI agents should be able to reliably access examples: {e}"

    def test_ai_agents_handle_parameter_validation_gracefully_for_developer_experience(
        self,
    ) -> None:
        """AI agents should handle invalid parameters gracefully and provide helpful feedback to developers."""
        # This tests the AI agent's ability to recover from errors and guide developers
        try:
            # Test with minimal parameters - AI agents should handle gracefully
            result = recommend_dq_approach(use_case="testing")
            assert result is not None, (
                "AI agents should be able to provide recommendations even with minimal developer input"
            )

            # Test with empty parameters - AI agents need graceful handling
            result2 = recommend_dq_approach(use_case="")
            assert result2 is not None, (
                "AI agents should handle empty parameters gracefully to maintain developer workflow"
            )

        except Exception as e:
            # AI agents need clear validation feedback to help guide developers
            error_str = str(e).lower()
            is_validation_error = any(
                term in error_str
                for term in ["invalid", "required", "missing", "parameter", "argument"]
            )
            if not is_validation_error:
                assert False, (
                    f"AI agents should get clear parameter validation feedback to help developers: {e}"
                )

    def test_ai_agents_can_handle_parameter_validation_errors_for_developer_guidance(
        self,
    ) -> None:
        """AI agents should receive clear validation errors that they can use to guide developers toward correct parameter usage."""
        validation_test_cases = [
            (
                "invalid_complexity",
                {"complexity_level": "invalid_level"},
                "complexity_level",
            ),
            (
                "invalid_frequency",
                {"monitoring_frequency": "invalid_freq"},
                "monitoring_frequency",
            ),
            (
                "invalid_debugging",
                {"debugging_needs": "invalid_debug"},
                "debugging_needs",
            ),
            (
                "invalid_integration",
                {"integration_requirements": "invalid_integration"},
                "integration_requirements",
            ),
        ]

        for test_name, kwargs, expected_param in validation_test_cases:
            with pytest.raises(ValueError) as exc_info:
                recommend_dq_approach(use_case="test", **kwargs)

            # AI agents need clear error messages to help guide developers
            error_message = str(exc_info.value).lower()
            assert expected_param.lower() in error_message, (
                f"AI agents need clear {expected_param} validation errors for developer guidance"
            )
            assert "must be one of" in error_message, (
                f"AI agents need specific valid option guidance for {test_name}"
            )

    def test_ai_agents_can_provide_recommendations_across_different_complexity_levels_for_developers(
        self,
    ) -> None:
        """AI agents should be able to provide appropriate recommendations for different complexity levels to help developers at various skill levels."""
        complexity_scenarios = [
            ("low", "Simple monitoring needs"),
            ("medium", "Moderate complexity requirements"),
            ("high", "Advanced data quality needs"),
        ]

        for complexity, scenario in complexity_scenarios:
            try:
                result = recommend_dq_approach(
                    use_case="data monitoring",
                    complexity_level=complexity,
                    debugging_needs="basic",
                )

                # AI agents need complexity-appropriate recommendations to help developers
                assert result is not None, (
                    f"AI agents need {complexity} complexity recommendations for developers with {scenario}"
                )

                # AI agents should provide level-appropriate guidance
                result_str = str(result).lower()
                has_complexity_guidance = any(
                    term in result_str
                    for term in [complexity, "recommend", "approach", "data"]
                )
                assert has_complexity_guidance, (
                    f"AI agents need {complexity}-level appropriate guidance for developers"
                )

            except Exception as e:
                assert False, (
                    f"AI agents should handle {complexity} complexity scenarios for developers: {e}"
                )

    def test_ai_agents_can_handle_different_monitoring_frequencies_for_developer_scenarios(
        self,
    ) -> None:
        """AI agents should be able to provide frequency-appropriate recommendations to help developers with different monitoring needs."""
        frequency_scenarios = [
            ("real-time", "Immediate response requirements"),
            ("hourly", "Regular monitoring needs"),
            ("daily", "Standard operational monitoring"),
            ("weekly", "Periodic review requirements"),
        ]

        for frequency, scenario in frequency_scenarios:
            try:
                result = recommend_dq_approach(
                    use_case="quality monitoring",
                    monitoring_frequency=frequency,
                    debugging_needs="basic",
                )

                # AI agents need frequency-appropriate recommendations to help developers
                assert result is not None, (
                    f"AI agents need {frequency} frequency recommendations for developers with {scenario}"
                )

                # AI agents should provide frequency-aware guidance
                result_str = str(result).lower()
                has_frequency_context = any(
                    term in result_str
                    for term in [frequency.replace("-", ""), "recommend", "monitoring"]
                )
                assert has_frequency_context, (
                    f"AI agents need {frequency}-appropriate guidance for developers"
                )

            except Exception as e:
                assert False, (
                    f"AI agents should handle {frequency} frequency scenarios for developers: {e}"
                )

    def test_ai_agents_can_provide_debugging_level_appropriate_recommendations_for_developers(
        self,
    ) -> None:
        """AI agents should be able to provide debugging-level appropriate recommendations to help developers with different troubleshooting needs."""
        debugging_scenarios = [
            ("basic", "Simple troubleshooting needs"),
            ("extensive", "Complex debugging requirements"),
            ("moderate", "Standard debugging needs"),
            ("statistical", "Statistical analysis debugging"),
        ]

        for debugging_level, scenario in debugging_scenarios:
            try:
                result = recommend_dq_approach(
                    use_case="data validation",
                    debugging_needs=debugging_level,
                    complexity_level="medium",
                )

                # AI agents need debugging-level appropriate recommendations to help developers
                assert result is not None, (
                    f"AI agents need {debugging_level} debugging recommendations for developers with {scenario}"
                )

                # AI agents should provide debugging-aware guidance
                result_str = str(result).lower()
                has_debugging_context = any(
                    term in result_str
                    for term in [debugging_level, "recommend", "approach"]
                )
                assert has_debugging_context, (
                    f"AI agents need {debugging_level}-level appropriate guidance for developers"
                )

            except Exception as e:
                assert False, (
                    f"AI agents should handle {debugging_level} debugging scenarios for developers: {e}"
                )

    def test_ai_agents_can_handle_different_integration_requirements_for_developer_environments(
        self,
    ) -> None:
        """AI agents should be able to provide integration-appropriate recommendations to help developers with different operational environments."""
        integration_scenarios = [
            ("dashboard", "Dashboard integration needs"),
            ("alerts", "Alerting system requirements"),
            ("both", "Comprehensive integration needs"),
            ("custom", "Custom integration requirements"),
        ]

        for integration, scenario in integration_scenarios:
            try:
                result = recommend_dq_approach(
                    use_case="operational monitoring",
                    integration_requirements=integration,
                    complexity_level="medium",
                )

                # AI agents need integration-appropriate recommendations to help developers
                assert result is not None, (
                    f"AI agents need {integration} integration recommendations for developers with {scenario}"
                )

                # AI agents should provide integration-aware guidance
                result_str = str(result).lower()
                has_integration_context = any(
                    term in result_str
                    for term in [integration, "recommend", "integration"]
                )
                assert has_integration_context, (
                    f"AI agents need {integration}-appropriate guidance for developers"
                )

            except Exception as e:
                assert False, (
                    f"AI agents should handle {integration} integration scenarios for developers: {e}"
                )

    def test_ai_agents_can_provide_use_case_specific_recommendations_for_developers(
        self,
    ) -> None:
        """AI agents should be able to provide use-case-specific recommendations to help developers with various data quality scenarios."""
        use_case_scenarios = [
            ("operational monitoring", "Operational environment needs"),
            ("data investigation", "Investigation and analysis needs"),
            ("compliance validation", "Regulatory compliance requirements"),
            ("performance tracking", "Performance measurement needs"),
        ]

        for use_case, scenario in use_case_scenarios:
            try:
                result = recommend_dq_approach(
                    use_case=use_case,
                    complexity_level="medium",
                    debugging_needs="basic",
                )

                # AI agents need use-case-specific recommendations to help developers
                assert result is not None, (
                    f"AI agents need {use_case} recommendations for developers with {scenario}"
                )

                # AI agents should provide contextual guidance
                use_case_terms = use_case.split()
                result_str = str(result).lower()
                has_use_case_context = any(
                    term in result_str
                    for term in use_case_terms + ["recommend", "approach"]
                )
                assert has_use_case_context, (
                    f"AI agents need {use_case}-specific guidance for developers"
                )

            except Exception as e:
                assert False, (
                    f"AI agents should handle {use_case} scenarios for developers: {e}"
                )

    def test_ai_agents_can_recommend_hybrid_approach_when_both_methods_equally_valuable_for_developers(
        self,
    ) -> None:
        """AI agents should recommend hybrid approach when JSON and PySpark scores are equal, helping developers leverage both methods."""
        # This tests the AI agent's ability to handle balanced scenarios where both approaches have equal merit

        try:
            # Create a scenario where both JSON and PySpark get equal scores
            # Using medium complexity (+1 each), daily frequency (+2 JSON, +1 PySpark),
            # moderate debugging (+2 PySpark, +1 JSON), both integration (+2 JSON, +1 PySpark)
            # This should result in: JSON: 1+2+1+2=6, PySpark: 1+1+2+1=5
            # Let's try a different balance: medium complexity, weekly frequency, moderate debugging, custom integration
            # JSON: 1(medium) + 0(weekly) + 1(moderate) + 0(custom) = 2
            # PySpark: 1(medium) + 2(weekly) + 2(moderate) + 2(custom) = 7
            # That's not equal. Let me try: low complexity, daily frequency, basic debugging, both integration
            # JSON: 3(low) + 2(daily) + 2(basic) + 2(both) = 9
            # PySpark: 0(low) + 1(daily) + 0(basic) + 1(both) = 2
            # Still not equal. Let me try: medium complexity, daily frequency, basic debugging, custom integration
            # JSON: 1(medium) + 2(daily) + 2(basic) + 0(custom) = 5
            # PySpark: 1(medium) + 1(daily) + 0(basic) + 2(custom) = 4
            # Close! Let me try: medium complexity, weekly frequency, basic debugging, both integration
            # JSON: 1(medium) + 0(weekly) + 2(basic) + 2(both) = 5
            # PySpark: 1(medium) + 2(weekly) + 0(basic) + 1(both) = 4
            # Almost! Let me try: low complexity, hourly frequency, extensive debugging, custom integration
            # JSON: 3(low) + 3(hourly) + 0(extensive) + 0(custom) = 6
            # PySpark: 0(low) + 0(hourly) + 4(extensive) + 2(custom) = 6
            # Perfect! That should give equal scores

            result = recommend_dq_approach(
                use_case="balanced data quality monitoring",
                complexity_level="low",  # +3 JSON, +0 PySpark
                monitoring_frequency="hourly",  # +3 JSON, +0 PySpark
                debugging_needs="extensive",  # +0 JSON, +4 PySpark
                integration_requirements="custom",  # +0 JSON, +2 PySpark
            )

            # AI agents need hybrid recommendations when both approaches have equal value
            assert result is not None, (
                "AI agents need hybrid approach recommendations when both methods are equally valuable for developers"
            )

            # AI agents should identify this as a hybrid scenario for developer guidance
            assert result["primary_recommendation"] == "Hybrid Approach", (
                "AI agents need to recommend hybrid approach when scores are equal for balanced developer guidance"
            )

            # AI agents should explain the equal value to developers
            assert (
                result["secondary_recommendation"] == "Both methods equally valuable"
            ), (
                "AI agents need to communicate equal value to help developers understand balanced scenarios"
            )

            # AI agents should provide reasoning for the hybrid approach
            reasoning_text = " ".join(result["reasoning"]).lower()
            hybrid_indicators = any(
                term in reasoning_text
                for term in ["both", "hybrid", "value", "consider", "add"]
            )
            assert hybrid_indicators, (
                "AI agents need to explain hybrid approach reasoning to help developers understand when to use both methods"
            )

            # AI agents should mention both JSON and PySpark in the reasoning
            mentions_json = "json" in reasoning_text
            mentions_pyspark = "pyspark" in reasoning_text
            assert mentions_json and mentions_pyspark, (
                "AI agents need to reference both approaches in hybrid recommendations for developer clarity"
            )

        except Exception as e:
            assert False, (
                f"AI agents should recommend hybrid approach when both methods are equally valuable for developers: {e}"
            )

    def test_ai_agents_should_strongly_favor_json_for_simple_operational_monitoring_scenarios(
        self,
    ) -> None:
        """AI agents should strongly recommend JSON for simple operational monitoring since JSON simplicity enables straightforward Kusto investigation."""
        # This tests the architectural principle that simple JSON rules inherently provide simple debugging paths

        try:
            # Create a scenario that represents simple operational monitoring:
            # - Low complexity (simple rules)
            # - Frequent monitoring (operational focus)
            # - Basic debugging (simple Kusto queries suffice)
            # - Dashboard integration (operational display)
            # Expected: JSON should win decisively
            # JSON: 3(low) + 3(hourly) + 2(basic) + 3(dashboard) = 11
            # PySpark: 0(low) + 0(hourly) + 0(basic) + 0(dashboard) = 0

            result = recommend_dq_approach(
                use_case="operational monitoring dashboard",
                complexity_level="low",  # +3 JSON, simple rules
                monitoring_frequency="hourly",  # +3 JSON, operational cadence
                debugging_needs="basic",  # +2 JSON, Kusto queries suffice
                integration_requirements="dashboard",  # +3 JSON, operational display
            )

            # AI agents should recognize that simple operational scenarios favor JSON decisively
            assert result is not None, (
                "AI agents need clear recommendations for simple operational monitoring scenarios"
            )

            # AI agents should recommend JSON for simple operational monitoring
            assert result["primary_recommendation"] == "JSON DQ Framework Rules", (
                "AI agents should strongly favor JSON when simplicity enables straightforward Kusto investigation"
            )

            # AI agents should recognize PySpark as secondary for simple scenarios
            assert result["secondary_recommendation"] == "PySpark Tests", (
                "AI agents should position PySpark as secondary for simple operational monitoring"
            )

            # AI agents should emphasize operational benefits in reasoning
            reasoning_text = " ".join(result["reasoning"]).lower()
            operational_indicators = any(
                term in reasoning_text
                for term in ["operational", "monitoring", "dashboard", "streamlined"]
            )
            assert operational_indicators, (
                "AI agents should emphasize operational monitoring benefits for simple JSON scenarios"
            )

            # AI agents should NOT suggest this needs complex debugging (the architectural insight)
            complex_debugging_terms = [
                "extensive",
                "statistical",
                "complex",
                "investigation",
            ]
            suggests_complex_debugging = any(
                term in reasoning_text for term in complex_debugging_terms
            )
            assert not suggests_complex_debugging, (
                "AI agents should recognize that simple JSON rules don't require complex debugging since Kusto investigation is straightforward"
            )

        except Exception as e:
            assert False, (
                f"AI agents should strongly favor JSON for simple operational monitoring scenarios: {e}"
            )

    def test_ai_agents_should_recognize_when_pyspark_complexity_is_actually_needed(
        self,
    ) -> None:
        """AI agents should recommend PySpark when complexity genuinely requires sophisticated debugging beyond simple Kusto queries."""
        # This tests the contrast - when PySpark's debugging capabilities are actually necessary

        try:
            # Create a scenario where PySpark debugging is genuinely needed:
            # - High complexity (sophisticated logic requiring detailed investigation)
            # - Less frequent monitoring (investigation-focused, not operational)
            # - Statistical debugging (beyond simple Kusto capabilities)
            # - Custom integration (flexibility needed)
            # Expected: PySpark should win decisively
            # JSON: 0(high) + 0(weekly) + 0(statistical) + 0(custom) = 0
            # PySpark: 3(high) + 2(weekly) + 4(statistical) + 2(custom) = 11

            result = recommend_dq_approach(
                use_case="complex data investigation and analysis",
                complexity_level="high",  # +3 PySpark, needs sophisticated logic
                monitoring_frequency="weekly",  # +2 PySpark, investigation cadence
                debugging_needs="statistical",  # +4 PySpark, beyond Kusto capabilities
                integration_requirements="custom",  # +2 PySpark, flexibility needed
            )

            # AI agents should recognize when PySpark complexity is genuinely required
            assert result is not None, (
                "AI agents need clear recommendations for complex investigation scenarios"
            )

            # AI agents should recommend PySpark for genuinely complex scenarios
            assert result["primary_recommendation"] == "PySpark Tests", (
                "AI agents should favor PySpark when complexity genuinely requires sophisticated debugging"
            )

            # AI agents should recognize JSON as secondary for complex scenarios
            assert result["secondary_recommendation"] == "JSON Rules", (
                "AI agents should position JSON as secondary for complex investigation needs"
            )

            # AI agents should emphasize investigation and analysis benefits
            reasoning_text = " ".join(result["reasoning"]).lower()
            investigation_indicators = any(
                term in reasoning_text
                for term in [
                    "complex",
                    "validation",
                    "debugging",
                    "statistical",
                    "analysis",
                ]
            )
            assert investigation_indicators, (
                "AI agents should emphasize investigation and analysis capabilities for complex PySpark scenarios"
            )

        except Exception as e:
            assert False, (
                f"AI agents should recognize when PySpark complexity is actually needed: {e}"
            )
