"""
Tests for DQ PySpark generation tools.

Tests focus on what AI agents can accomplish when helping data engineers
generate and implement PySpark data quality tests.
"""

from pdp_dev_mcp.tools.data_quality import (
    generate_test_suggestions,
    get_pyspark_test_guidance,
)


class TestAIAgentsCanHelpEngineersGeneratePySparkTests:
    """Test what AI agents can accomplish when helping data engineers with PySpark test generation."""

    def test_ai_agents_can_help_engineers_create_targeted_completeness_tests(self):
        """AI agents should be able to generate specific completeness test templates that data engineers can implement immediately."""
        result = generate_test_suggestions(
            test_type="Integration",
            subject_area="Payments",
            data_quality_category="Completeness",
            table_name="gold_transactions",
        )

        # AI agents need complete, usable templates to provide immediate value to engineers
        assert "test_template" in result, (
            "AI agents need actual test code templates to help engineers implement tests immediately"
        )

        # AI agents need file management guidance to help engineers organize their work
        assert "filename" in result, (
            "AI agents need filename suggestions to help engineers organize their test files properly"
        )
        assert "target_directory" in result, (
            "AI agents need directory guidance to help engineers place tests in correct locations"
        )

        # AI agents need context-aware responses to provide relevant assistance
        assert "completeness" in result["filename"].lower(), (
            "AI agents should generate context-aware filenames reflecting the completeness focus"
        )
        assert "payments" in result["filename"].lower(), (
            "AI agents should generate domain-specific filenames reflecting the payments context"
        )

    def test_ai_agents_can_provide_engineers_comprehensive_testing_guidance(self):
        """AI agents should be able to access and provide comprehensive PySpark testing guidance to help engineers follow best practices."""
        guidance = get_pyspark_test_guidance()

        # AI agents need structured guidance they can interpret and communicate to engineers
        assert isinstance(guidance, list), (
            "AI agents need structured guidance format to effectively communicate best practices to engineers"
        )
        assert len(guidance) > 0, (
            "AI agents need substantial guidance content to provide meaningful help to engineers"
        )

        # AI agents need meaningful content to avoid providing empty responses to engineers
        meaningful_content = [item for item in guidance if item.strip()]
        assert len(meaningful_content) > 0, (
            "AI agents need substantive guidance content to provide valuable assistance to engineers"
        )

        # AI agents need practical, actionable content they can explain to engineers
        guidance_text = " ".join(guidance).lower()
        assert any(
            keyword in guidance_text
            for keyword in ["test", "debug", "practice", "structure"]
        ), (
            "AI agents need practical testing guidance they can communicate to help engineers improve their testing practices"
        )

    def test_ai_agents_can_help_engineers_with_different_test_types_for_specialized_scenarios(
        self,
    ):
        """AI agents should be able to generate different test types to help engineers with specialized testing scenarios."""
        test_type_scenarios = [
            ("Functional", "Regression"),  # Should trigger line 52
            ("Diff", "Data Mismatch"),  # Should trigger line 54
            ("Integration", "Empty Field"),  # Default case
        ]

        for test_type, expected_issue_type in test_type_scenarios:
            try:
                result = generate_test_suggestions(
                    test_type=test_type,
                    subject_area="Payments",
                    data_quality_category="Completeness",
                    table_name="test_table",
                    field_name="test_field",
                )

                # AI agents need test type awareness to help engineers with specialized scenarios
                assert result is not None, (
                    f"AI agents need {test_type} test generation capability to help engineers with specialized scenarios"
                )

                # AI agents should generate context-appropriate alert names and classifications
                result_str = str(result).lower()
                has_test_type_context = any(
                    term in result_str
                    for term in [test_type.lower(), expected_issue_type.lower()]
                )
                assert has_test_type_context, (
                    f"AI agents need {test_type}-appropriate classifications to help engineers understand test purposes"
                )

            except Exception as e:
                assert False, (
                    f"AI agents should handle {test_type} test generation for engineers: {e}"
                )

    def test_ai_agents_can_handle_table_level_tests_without_specific_fields_for_engineers(
        self,
    ):
        """AI agents should be able to generate table-level tests when engineers don't specify particular fields."""
        try:
            result = generate_test_suggestions(
                test_type="Integration",
                subject_area="Payments",
                data_quality_category="Completeness",
                table_name="test_table",
                field_name=None,  # No specific field - should trigger line 63
            )

            # AI agents need table-level test generation to help engineers with comprehensive validation
            assert result is not None, (
                "AI agents need table-level test generation capability when engineers don't specify fields"
            )

            # AI agents should generate appropriate descriptions for table-level tests
            assert (
                "test_table has completeness issues"
                in result["test_classification"]["description"]
            ), (
                "AI agents need appropriate table-level descriptions to help engineers understand test scope"
            )

        except Exception as e:
            assert False, (
                f"AI agents should handle table-level test generation for engineers: {e}"
            )

    def test_ai_agents_can_generate_accuracy_tests_for_engineers(self):
        """AI agents should be able to generate accuracy test templates to help engineers validate data correctness."""
        try:
            result = generate_test_suggestions(
                test_type="Integration",
                subject_area="Payments",
                data_quality_category="Accuracy",  # Should trigger accuracy template generation
                table_name="test_table",
                field_name="accuracy_field",
            )

            # AI agents need accuracy test generation to help engineers with data validation
            assert result is not None, (
                "AI agents need accuracy test generation capability to help engineers validate data correctness"
            )

            # AI agents should generate accuracy-specific test templates
            assert "accuracy_validation" in result["test_template"], (
                "AI agents need accuracy-specific test templates to help engineers implement proper validation logic"
            )

        except Exception as e:
            assert False, (
                f"AI agents should handle accuracy test generation for engineers: {e}"
            )

    def test_ai_agents_can_generate_other_data_quality_category_tests_for_engineers(
        self,
    ):
        """AI agents should be able to generate tests for various data quality categories to help engineers with comprehensive validation."""
        other_categories = [
            "Consistency",
            "Timeliness",
            "Validity",
            "Uniqueness",
        ]

        for category in other_categories:
            try:
                result = generate_test_suggestions(
                    test_type="Integration",
                    subject_area="Payments",
                    data_quality_category=category,  # Should trigger else branch for template generation
                    table_name="test_table",
                    field_name="test_field",
                )

                # AI agents need diverse category support to help engineers with comprehensive data quality
                assert result is not None, (
                    f"AI agents need {category} test generation capability to help engineers with comprehensive validation"
                )

                # AI agents should generate appropriate templates for all categories
                result_str = str(result).lower()
                has_category_context = category.lower() in result_str
                assert has_category_context, (
                    f"AI agents need {category}-appropriate content to help engineers understand validation focus"
                )

            except Exception as e:
                assert False, (
                    f"AI agents should handle {category} test generation for engineers: {e}"
                )

    def test_ai_agents_can_generate_filename_variations_for_engineer_organization(self):
        """AI agents should be able to generate appropriate filenames with and without field names to help engineers organize tests."""
        filename_scenarios = [
            ("test_field", True),  # With field name - should trigger line 225
            (None, False),  # Without field name - should trigger else branch
        ]

        for field_name, has_field in filename_scenarios:
            try:
                result = generate_test_suggestions(
                    test_type="Integration",
                    subject_area="Payments",
                    data_quality_category="Completeness",
                    table_name="test_table",
                    field_name=field_name,
                )

                # AI agents need filename generation flexibility to help engineers organize tests
                assert result is not None, (
                    f"AI agents need filename generation capability for field scenario: {field_name}"
                )

                # AI agents should generate appropriate filenames based on field presence
                filename = result["filename"]
                if has_field:
                    assert "test_field" in filename, (
                        "AI agents need field-specific filenames when engineers specify fields"
                    )
                else:
                    assert "completeness" in filename, (
                        "AI agents need category-based filenames when engineers don't specify fields"
                    )

            except Exception as e:
                assert False, (
                    f"AI agents should handle filename generation for field scenario {field_name}: {e}"
                )

    def test_ai_agents_can_handle_invalid_test_types_gracefully_for_engineer_guidance(
        self,
    ):
        """AI agents should provide clear error messages when engineers specify invalid test types."""
        try:
            # This should trigger line 250 - the validation error case
            generate_test_suggestions(
                test_type="InvalidTestType",  # Invalid type
                subject_area="Payments",
                data_quality_category="Completeness",
                table_name="test_table",
            )
            assert False, (
                "AI agents should validate test types and provide helpful error messages to engineers"
            )

        except ValueError as e:
            # AI agents need informative error messages to guide engineers
            error_message = str(e)
            assert "Invalid test_type" in error_message, (
                "AI agents need clear error messages to help engineers understand valid options"
            )
            assert "Integration" in error_message, (
                "AI agents need to show valid options in error messages to guide engineers"
            )

        except Exception as e:
            assert False, (
                f"AI agents should handle validation errors appropriately for engineers: {e}"
            )

    def test_ai_agents_can_help_developers_generate_tests_with_minimal_information(
        self,
    ):
        """AI agents should be able to help developers generate useful tests even when developers provide minimal details."""
        # This tests the AI agent's ability to assist developers with incomplete information
        result = generate_test_suggestions(
            test_type="Integration",
            subject_area="",  # Developer might not know their subject area yet
            data_quality_category="Completeness",
            table_name="",  # Developer might not have finalized table name
        )

        # AI agents need robust generation capability to help developers with incomplete specifications
        assert isinstance(result, dict), (
            "AI agents need structured output they can provide to developers"
        )
        assert "test_template" in result, (
            "AI agents need actual test code to help developers even with minimal input"
        )

        # AI agents need meaningful content to provide valuable developer assistance
        template = result["test_template"]
        assert len(template) > 0, (
            "AI agents need meaningful test content they can help developers customize"
        )
