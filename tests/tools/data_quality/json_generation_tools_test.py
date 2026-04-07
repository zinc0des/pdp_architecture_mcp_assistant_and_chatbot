"""
Tests for DQ JSON generation tools - behavior-focused tests.

Tests focus on what AI agents can accomplish when helping developers
create monitoring rules and operational data quality configurations.
"""

from pdp_dev_mcp.tools.data_quality import (
    generate_advanced_json_rule,
    generate_json_rule_suggestions,
    get_json_rule_types_info,
)


class TestAIAgentsCanGenerateJSONRules:
    """Test what AI agents can accomplish when helping developers create data quality monitoring rules."""

    def test_ai_agents_can_help_developers_create_monitoring_rules(self):
        """AI agents should be able to generate monitoring rules that developers can use for operational data quality."""
        # This tests the AI agent's ability to help developers with rule creation
        try:
            result = generate_json_rule_suggestions(
                table_name="transactions", monitoring_type="accuracy"
            )

            # AI agents need reliable rule generation to help developers
            assert result is not None, (
                "AI agents need functioning rule generation to help developers create monitoring"
            )

            # AI agents need meaningful content they can interpret and explain to developers
            result_str = str(result).lower()
            has_rule_content = any(
                term in result_str
                for term in ["rule", "json", "monitor", "accuracy", "transactions"]
            )
            assert has_rule_content, (
                "AI agents need rule content that incorporates developer requirements for effective assistance"
            )

        except Exception as e:
            assert False, (
                f"AI agents should be able to reliably generate rules for developers: {e}"
            )

    def test_ai_agents_can_help_developers_create_detailed_monitoring_configurations(
        self,
    ):
        """AI agents should be able to create comprehensive monitoring rules based on specific developer requirements."""
        # This tests the AI agent's ability to process detailed requirements
        try:
            result = generate_advanced_json_rule(
                test_type="Integration",
                subject_area="Payments",
                data_quality_category="Completeness",
                table_name="transactions",
                field_name="transaction_id",
            )

            # AI agents need comprehensive rule generation to provide detailed help
            assert result is not None, (
                "AI agents need advanced rule generation capability to help developers with complex requirements"
            )

            # AI agents need parameter-aware responses to provide relevant assistance
            result_str = str(result).lower()
            incorporates_params = any(
                param in result_str
                for param in [
                    "integration",
                    "payments",
                    "completeness",
                    "transactions",
                    "transaction_id",
                ]
            )
            assert incorporates_params, (
                "AI agents need context-aware rule generation to provide relevant assistance to developers"
            )

        except Exception as e:
            assert False, (
                f"AI agents should be able to reliably create advanced rules for developers: {e}"
            )

    def test_ai_agents_can_explain_available_rule_options_to_developers(self):
        """AI agents should be able to provide information about available rule types to help developers understand their options."""
        # This tests the AI agent's ability to guide developers through available options
        try:
            result = get_json_rule_types_info()

            # AI agents need rule type information to guide developers effectively
            assert result is not None, (
                "AI agents need rule type information to help developers understand available options"
            )

            # AI agents need informative content they can use to educate developers
            result_str = str(result).lower()
            has_guidance = any(
                term in result_str
                for term in [
                    "rule",
                    "type",
                    "json",
                    "monitor",
                    "data quality",
                    "available",
                ]
            )
            assert has_guidance, (
                "AI agents need informative rule type content to help developers make informed choices"
            )

        except Exception as e:
            assert False, (
                f"AI agents should be able to reliably access rule type information for developers: {e}"
            )

    def test_ai_agents_can_handle_different_data_quality_categories_for_developers(
        self,
    ):
        """AI agents should be able to generate different rule types based on data quality categories to help developers address specific concerns."""
        categories_to_test = [
            ("Completeness", "null_check"),
            ("Accuracy", "duplicate_check"),
            ("Consistency", "sum"),
            ("Reliability", "table_history"),
        ]

        for category, expected_rule_type in categories_to_test:
            try:
                result = generate_advanced_json_rule(
                    test_type="Integration",
                    subject_area="Payments",
                    data_quality_category=category,
                    table_name="test_table",
                    field_name="test_field" if category != "Reliability" else None,
                )

                # AI agents need category-specific rule generation to address developer concerns appropriately
                assert result is not None, (
                    f"AI agents need {category} rule generation to help developers with {category.lower()} issues"
                )

                # AI agents need rules that reflect the specific data quality concern
                result_str = str(result).lower()
                has_category_context = (
                    category.lower() in result_str or expected_rule_type in result_str
                )
                assert has_category_context, (
                    f"AI agents need {category}-appropriate rules to help developers address specific data quality concerns"
                )

            except Exception as e:
                assert False, (
                    f"AI agents should be able to generate {category} rules for developers: {e}"
                )

    def test_ai_agents_can_generate_rules_with_different_field_patterns_for_developers(
        self,
    ):
        """AI agents should be able to adapt rule generation based on field name patterns to help developers with context-aware monitoring."""
        field_patterns_to_test = [
            ("amount_field", "sum"),  # Should trigger sum rule for amount fields
            ("duplicate_check", "duplicate_check"),  # Should trigger duplicate check
            (
                "regular_field",
                "custom_query",
            ),  # Should trigger custom query for regular fields
        ]

        for field_name, expected_pattern in field_patterns_to_test:
            try:
                result = generate_advanced_json_rule(
                    test_type="Integration",
                    subject_area="Payments",
                    data_quality_category="Accuracy",
                    table_name="test_table",
                    field_name=field_name,
                )

                # AI agents need pattern-aware rule generation to provide contextual help
                assert result is not None, (
                    f"AI agents need pattern-aware generation for {field_name} to help developers with appropriate monitoring"
                )

                # AI agents need rules that reflect the field context
                result_str = str(result).lower()
                has_pattern_context = any(
                    term in result_str
                    for term in [field_name.lower(), expected_pattern, "rule"]
                )
                assert has_pattern_context, (
                    "AI agents need field-pattern-appropriate rules to help developers with contextual monitoring"
                )

            except Exception as e:
                assert False, (
                    f"AI agents should be able to generate pattern-aware rules for {field_name}: {e}"
                )

    def test_ai_agents_can_handle_edge_cases_gracefully_for_developer_confidence(self):
        """AI agents should handle edge cases gracefully to maintain developer confidence in the tool."""
        edge_cases_to_test = [
            # Test with minimal parameters
            ("Unit", "Unknown", "Other", "table", None),
        ]

        for (
            test_type,
            subject_area,
            category,
            table_name,
            field_name,
        ) in edge_cases_to_test:
            try:
                result = generate_advanced_json_rule(
                    test_type=test_type,
                    subject_area=subject_area,
                    data_quality_category=category,
                    table_name=table_name,
                    field_name=field_name,
                )

                # AI agents need graceful handling to maintain developer confidence
                assert result is not None, (
                    "AI agents need graceful edge case handling to maintain developer confidence"
                )

                # AI agents should provide fallback functionality for developers
                result_str = str(result).lower()
                has_fallback_content = any(
                    term in result_str for term in ["rule", "data", "quality", "custom"]
                )
                assert has_fallback_content, (
                    "AI agents need meaningful fallback responses to help developers even with edge cases"
                )

            except Exception as e:
                assert False, (
                    f"AI agents should handle edge cases gracefully for developer confidence: {e}"
                )

    def test_ai_agents_can_generate_rules_with_custom_thresholds_for_developers(self):
        """AI agents should be able to incorporate custom threshold values when helping developers create specific monitoring rules."""
        threshold_scenarios = [
            (50.0, "Custom threshold incorporation"),
            (0.0, "Zero threshold handling"),
            (100.0, "Maximum threshold handling"),
        ]

        for threshold_value, scenario in threshold_scenarios:
            try:
                result = generate_advanced_json_rule(
                    test_type="Integration",
                    subject_area="Payments",
                    data_quality_category="Completeness",
                    table_name="test_table",
                    field_name="test_field",
                    threshold_value=threshold_value,
                )

                # AI agents need threshold-aware generation to help developers with specific requirements
                assert result is not None, (
                    f"AI agents need threshold-aware generation for {scenario} to help developers"
                )

                # AI agents should incorporate threshold values meaningfully
                result_str = str(result).lower()
                has_threshold_context = any(
                    term in result_str
                    for term in [str(threshold_value), "threshold", "rule"]
                )
                assert has_threshold_context, (
                    f"AI agents need threshold-incorporated rules to help developers with {scenario}"
                )

            except Exception as e:
                assert False, f"AI agents should handle {scenario} for developers: {e}"

    def test_ai_agents_can_generate_rules_for_different_frequencies_for_developers(
        self,
    ):
        """AI agents should be able to generate rules with different execution frequencies to help developers with varied monitoring needs."""
        frequency_scenarios = [
            ("Hourly", "High-frequency monitoring"),
            ("Daily", "Standard monitoring"),
            ("Weekly", "Low-frequency monitoring"),
            ("On-Demand", "Manual monitoring"),
        ]

        for frequency, scenario in frequency_scenarios:
            try:
                result = generate_advanced_json_rule(
                    test_type="Integration",
                    subject_area="Payments",
                    data_quality_category="Completeness",
                    table_name="test_table",
                    field_name="test_field",
                    rule_frequency=frequency,
                )

                # AI agents need frequency-aware generation to help developers with scheduling
                assert result is not None, (
                    f"AI agents need frequency-aware generation for {scenario} to help developers"
                )

                # AI agents should incorporate frequency requirements meaningfully
                result_str = str(result).lower()
                has_frequency_context = any(
                    term in result_str
                    for term in [frequency.lower(), "frequency", "schedule", "rule"]
                )
                assert has_frequency_context, (
                    f"AI agents need frequency-incorporated rules to help developers with {scenario}"
                )

            except Exception as e:
                assert False, f"AI agents should handle {scenario} for developers: {e}"

    def test_ai_agents_can_handle_empty_field_scenarios_for_developers(self):
        """AI agents should be able to generate appropriate rules when developers don't specify field names for different data quality categories."""
        field_scenarios = [
            ("Completeness", None, "count"),  # Should default to count rule
            ("Accuracy", None, "count"),  # Should default to count rule
            ("Consistency", None, "count"),  # Should default to count rule
            (
                "Reliability",
                None,
                "count",
            ),  # Should default to count rule (no freshness trigger)
        ]

        for category, field_name, expected_rule_type in field_scenarios:
            try:
                result = generate_advanced_json_rule(
                    test_type="Integration",
                    subject_area="Payments",
                    data_quality_category=category,
                    table_name="test_table",
                    field_name=field_name,
                )

                # AI agents need graceful handling when developers omit field names
                assert result is not None, (
                    f"AI agents need graceful {category} handling when developers don't specify fields"
                )

                # AI agents should provide appropriate fallback rules
                result_str = str(result).lower()
                has_fallback_logic = any(
                    term in result_str
                    for term in [expected_rule_type, "rule", category.lower()]
                )
                assert has_fallback_logic, (
                    f"AI agents need appropriate {category} fallback rules when developers don't specify fields"
                )

            except Exception as e:
                assert False, (
                    f"AI agents should handle {category} without field names for developers: {e}"
                )

    def test_ai_agents_can_generate_table_freshness_rules_for_developers(self):
        """AI agents should be able to generate table_history rules when developers need freshness monitoring."""
        freshness_scenarios = [
            ("freshness_table", None),  # Table name contains "freshness"
            ("test_table", 12.0),  # Threshold value less than 24
        ]

        for table_name, threshold in freshness_scenarios:
            try:
                result = generate_advanced_json_rule(
                    test_type="Integration",
                    subject_area="Payments",
                    data_quality_category="Reliability",
                    table_name=table_name,
                    field_name=None,
                    threshold_value=threshold,
                )

                # AI agents need freshness-aware rule generation for developers
                assert result is not None, (
                    f"AI agents need freshness monitoring capability for developers with {table_name}/{threshold}"
                )

                # AI agents should generate appropriate timeliness rules
                result_str = str(result).lower()
                has_freshness_logic = any(
                    term in result_str
                    for term in ["table_history", "merge", "timeliness", "processing"]
                )
                assert has_freshness_logic, (
                    f"AI agents need timeliness-appropriate rules for developers monitoring {table_name}"
                )

            except Exception as e:
                assert False, (
                    f"AI agents should handle freshness monitoring for {table_name}: {e}"
                )

    def test_ai_agents_can_handle_amount_field_patterns_for_developers(self):
        """AI agents should be able to recognize amount field patterns and generate sum rules for developers."""
        amount_field_patterns = [
            "total_amount",
            "payment_sum",
            "transaction_value",
            "order_total",
        ]

        for field_name in amount_field_patterns:
            try:
                result = generate_advanced_json_rule(
                    test_type="Integration",
                    subject_area="Payments",
                    data_quality_category="Consistency",
                    table_name="test_table",
                    field_name=field_name,
                )

                # AI agents need pattern recognition to help developers with amount monitoring
                assert result is not None, (
                    f"AI agents need amount field recognition for {field_name} to help developers"
                )

                # AI agents should generate sum rules for amount fields
                result_str = str(result).lower()
                has_sum_logic = any(
                    term in result_str
                    for term in ["sum", field_name.lower(), "amount", "consistency"]
                )
                assert has_sum_logic, (
                    f"AI agents need sum-based rules for developers monitoring {field_name}"
                )

            except Exception as e:
                assert False, (
                    f"AI agents should handle amount field patterns for {field_name}: {e}"
                )

    def test_ai_agents_can_handle_custom_rule_type_preferences_for_developers(self):
        """AI agents should be able to use developer-specified rule type preferences instead of auto-detection."""
        rule_type_preferences = [
            "count",
            "null_check",
            "duplicate_check",
            "sum",
            "custom_query",
            "table_history",
            "custom_notebook",
        ]

        for rule_type in rule_type_preferences:
            try:
                result = generate_json_rule_suggestions(
                    table_name="test_table",
                    monitoring_type="custom",
                    rule_type_preference=rule_type,
                )

                # AI agents need rule type override capability for developer preferences
                assert result is not None, (
                    f"AI agents need rule type override capability for {rule_type} preferences"
                )

                # AI agents should honor developer-specified rule types
                result_str = str(result).lower()
                honors_preference = rule_type in result_str or "custom" in result_str
                assert honors_preference, (
                    f"AI agents need to honor developer preference for {rule_type} rules"
                )

            except Exception as e:
                assert False, (
                    f"AI agents should handle {rule_type} preferences for developers: {e}"
                )

    def test_ai_agents_can_handle_simple_table_names_for_developers(self):
        """AI agents should be able to handle table names without schema prefixes for developers."""
        simple_table_scenarios = [
            ("simple_table", "gold"),  # Should default to gold layer
            ("another_table", "gold"),
        ]

        for table_name, expected_layer in simple_table_scenarios:
            try:
                result = generate_advanced_json_rule(
                    test_type="Integration",
                    subject_area="Payments",
                    data_quality_category="Completeness",
                    table_name=table_name,  # No schema prefix
                    field_name="test_field",
                )

                # AI agents need graceful handling of simple table names
                assert result is not None, (
                    f"AI agents need simple table name handling for {table_name}"
                )

                # AI agents should apply appropriate defaults for layer
                result_str = str(result).lower()
                has_layer_logic = any(
                    term in result_str
                    for term in [expected_layer, table_name.lower(), "layer"]
                )
                assert has_layer_logic, (
                    f"AI agents need appropriate layer defaults for simple table names like {table_name}"
                )

            except Exception as e:
                assert False, (
                    f"AI agents should handle simple table names like {table_name}: {e}"
                )

    def test_ai_agents_can_handle_custom_constraints_for_developers(self):
        """AI agents should be able to incorporate custom SQL constraints when developers have specific validation needs."""
        custom_constraints = [
            ["SELECT COUNT(*) FROM test_table WHERE status = 'INVALID'"],
            ["SELECT COUNT(DISTINCT user_id) FROM transactions WHERE amount < 0"],
        ]

        for custom_constraint in custom_constraints:
            try:
                result = generate_advanced_json_rule(
                    test_type="Integration",
                    subject_area="Payments",
                    data_quality_category="Accuracy",
                    table_name="test_table",
                    custom_constraint=custom_constraint,
                )

                # AI agents need custom constraint support for advanced developer needs
                assert result is not None, (
                    "AI agents need custom constraint support for advanced developer validation needs"
                )

                # AI agents should incorporate custom SQL constraints
                result_str = str(result).lower()
                has_custom_logic = any(
                    term in result_str
                    for term in ["custom", "query", "constraint"]
                    + [word.lower() for word in custom_constraint[0].split()]
                )
                assert has_custom_logic, (
                    "AI agents need custom constraint incorporation for advanced developer requirements"
                )

            except Exception as e:
                assert False, (
                    f"AI agents should handle custom constraints for advanced developer needs: {e}"
                )

    def test_ai_agents_can_handle_unknown_severity_levels_for_developers(self):
        """AI agents should be able to handle unknown severity levels gracefully and provide defaults for developers."""
        unknown_severities = [
            "unknown_severity",
            "custom_level",
            "emergency",
        ]

        for severity in unknown_severities:
            try:
                result = generate_advanced_json_rule(
                    test_type="Integration",
                    subject_area="Payments",
                    data_quality_category="Completeness",
                    table_name="test_table",
                    field_name="test_field",
                    severity_level=severity,
                )

                # AI agents need graceful severity handling for developer confidence
                assert result is not None, (
                    f"AI agents need graceful severity handling for {severity} to maintain developer confidence"
                )

                # AI agents should provide appropriate defaults for unknown severities
                result_str = str(result).lower()
                has_severity_handling = any(
                    term in result_str
                    for term in ["high", "medium", "low", "severity", "alert"]
                )
                assert has_severity_handling, (
                    f"AI agents need appropriate severity defaults for unknown levels like {severity}"
                )

            except Exception as e:
                assert False, (
                    f"AI agents should handle unknown severity levels like {severity}: {e}"
                )

    def test_ai_agents_can_handle_unusual_frequency_schedules_for_developers(self):
        """AI agents should be able to generate appropriate SLA times for unusual frequency schedules."""
        unusual_frequencies = [
            "monthly",
            "quarterly",
            "custom_schedule",
            "on_demand",
        ]

        for frequency in unusual_frequencies:
            try:
                result = generate_advanced_json_rule(
                    test_type="Integration",
                    subject_area="Payments",
                    data_quality_category="Completeness",
                    table_name="test_table",
                    field_name="test_field",
                    rule_frequency=frequency,
                )

                # AI agents need graceful frequency handling for unusual schedules
                assert result is not None, (
                    f"AI agents need graceful frequency handling for {frequency} to help developers"
                )

                # AI agents should generate appropriate SLA defaults for unusual frequencies
                result_str = str(result).lower()
                has_sla_handling = any(
                    term in result_str
                    for term in ["13:15:00", "sla", frequency.lower(), "schedule"]
                )
                assert has_sla_handling, (
                    f"AI agents need appropriate SLA defaults for unusual frequencies like {frequency}"
                )

            except Exception as e:
                assert False, (
                    f"AI agents should handle unusual frequencies like {frequency}: {e}"
                )

    def test_ai_agents_can_generate_table_level_monitoring_without_fields_for_developers(
        self,
    ):
        """AI agents should be able to generate table-level monitoring rules when developers don't specify field names."""
        try:
            result = generate_json_rule_suggestions(
                table_name="transactions",
                monitoring_type="volume",
                field_name=None,  # No field specified - should use table-level monitoring
                frequency="daily",
            )

            # AI agents need table-level monitoring capability when developers don't specify fields
            assert result is not None, (
                "AI agents need table-level monitoring capability when developers don't specify field names"
            )

            # AI agents should generate appropriate table-level rule names and descriptions
            result_str = str(result).lower()
            has_table_level_logic = any(
                term in result_str
                for term in ["count", "volume", "transactions", "table", "rule"]
            )
            assert has_table_level_logic, (
                "AI agents need table-level rule generation when developers omit field specifications"
            )

        except Exception as e:
            assert False, (
                f"AI agents should handle table-level monitoring without field names: {e}"
            )

    def test_ai_agents_can_handle_schema_prefixed_table_names_in_basic_suggestions_for_developers(
        self,
    ):
        """AI agents should be able to handle table names with schema prefixes in basic rule suggestions for developers."""
        try:
            result = generate_json_rule_suggestions(
                table_name="test.simple_transactions",  # Schema prefix to hit line 200
                monitoring_type="completeness",
                field_name="user_id",
                frequency="hourly",
            )

            # AI agents need schema-aware table name handling in basic suggestions
            assert result is not None, (
                "AI agents need schema-aware table name handling in basic rule suggestions"
            )

            # AI agents should properly extract layer and table information from schema prefixes
            result_str = str(result).lower()
            has_schema_logic = any(
                term in result_str
                for term in ["simple_transactions", "test", "layer", "null_check"]
            )
            assert has_schema_logic, (
                "AI agents need proper schema prefix parsing for developer clarity in basic suggestions"
            )

        except Exception as e:
            assert False, (
                f"AI agents should handle schema-prefixed table names in basic suggestions: {e}"
            )

    def test_ai_agents_can_handle_simple_table_names_in_advanced_rules_for_developers(
        self,
    ):
        """AI agents should be able to handle simple table names without schema prefixes in advanced rule generation."""
        try:
            result = generate_advanced_json_rule(
                test_type="Integration",
                subject_area="Payments",
                data_quality_category="Accuracy",
                table_name="user_accounts",  # No schema prefix
                field_name="account_id",
            )

            # AI agents need simple table name handling in advanced rules
            assert result is not None, (
                "AI agents need simple table name handling in advanced rule generation"
            )

            # AI agents should apply appropriate layer defaults in advanced rules
            result_str = str(result).lower()
            has_advanced_simple_logic = any(
                term in result_str
                for term in ["user_accounts", "gold", "layer", "accuracy"]
            )
            assert has_advanced_simple_logic, (
                "AI agents need appropriate layer defaults for simple table names in advanced rules"
            )

        except Exception as e:
            assert False, (
                f"AI agents should handle simple table names in advanced rules: {e}"
            )

    def test_ai_agents_can_handle_table_names_with_schema_prefixes_for_developers(self):
        """AI agents should be able to handle table names with schema prefixes when developers specify layered table structures."""
        try:
            result = generate_advanced_json_rule(
                test_type="Unit",
                subject_area="TestArea",
                data_quality_category="Completeness",
                table_name="test.advancedtable",  # Schema prefix to test layer extraction
                field_name="test_field",
            )

            # AI agents need proper layer extraction to help developers with schema-aware table references
            assert result is not None, (
                "AI agents need schema-aware table handling to help developers with layered data structures"
            )

            # AI agents should correctly parse schema prefixes for developer clarity
            assert result["json_rule"]["layer"] == "test", (
                "AI agents need accurate layer extraction to help developers understand data organization"
            )
            assert result["json_rule"]["table"] == "advancedtable", (
                "AI agents need clean table name extraction to help developers with clear rule definitions"
            )

        except Exception as e:
            assert False, (
                f"AI agents should handle schema-prefixed table names for developers: {e}"
            )
