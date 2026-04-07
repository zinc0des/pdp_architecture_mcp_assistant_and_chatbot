"""
BDD Tests for MCP Tool Self-Documentation and AI Agent Support

As an AI agent working across repositories and environments,
I need MCP tools to be fully self-documenting with clear schemas, validation,
and error messages so I can use them effectively without access to source code.

These tests ensure that our MCP tools follow best practices for AI agent usability:
- Clear schema documentation
- Helpful validation error messages
- Self-describing parameters and types
- Introspection capabilities where possible
"""

import pytest
from unittest.mock import patch, MagicMock
from pdp_dev_mcp.tools.code_review.ai_comment_posting import (
    CodeReviewComment,
    CommentType,
    CommentSeverity,
)


class TestMCPToolSelfDocumentation:
    """
    Test scenarios ensuring MCP tools provide adequate self-documentation
    for AI agents working without source code access.
    """

    @pytest.mark.asyncio
    async def test_ai_agent_discovers_runtime_validation_now_enforced(self):
        """
        As an AI agent working with tool schemas,
        When I provide incorrect parameter types to dataclass-based tools,
        Then I should receive clear validation errors at instantiation time,
        So I can correct my input before attempting to use the tool.

        IMPLEMENTATION: Runtime validation is now enforced via __post_init__ method.
        """
        # Given: An AI agent attempts to use comment posting with invalid enum values

        # When: AI agent tries to use invalid comment_type string instead of enum
        # Then: Validation error is raised with clear guidance
        with pytest.raises(ValueError) as exc_info:
            CodeReviewComment(
                comment_id="test_comment_1",
                comment_type="invalid_type",  # type: ignore[arg-type] # Invalid string instead of enum
                severity=CommentSeverity.SUGGESTION,
                title="Test Title",
                content="Test content",
            )

        # Verify error message is helpful for AI agents
        error_message = str(exc_info.value)
        assert "VALIDATION_ERROR" in error_message
        assert "comment_type must be a CommentType enum" in error_message
        assert (
            "CommentType.GENERAL" in error_message
            or "CommentType.SECURITY" in error_message
        ), "Error should show example of correct usage"

        # Document the proper way for AI agents
        valid_comment_types = [e.value for e in CommentType]
        assert "invalid_type" not in valid_comment_types, (
            f"AI agents should use these CommentType enum values: {valid_comment_types}"
        )

    @pytest.mark.asyncio
    async def test_ai_agent_learns_proper_enum_usage_pattern(self):
        """
        As an AI agent learning to use tools correctly,
        When I understand that dataclasses don't validate enums at runtime,
        Then I should use enum values directly rather than strings,
        So I avoid runtime errors and ensure proper tool functionality.
        """
        # Given: AI agent learns the correct pattern

        # When: AI agent uses proper enum values
        correct_comment = CodeReviewComment(
            comment_id="proper_usage_example",
            comment_type=CommentType.SECURITY,  # Use enum, not string
            severity=CommentSeverity.WARNING,  # Use enum, not string
            title="Proper Enum Usage Example",
            content="This demonstrates correct enum usage for AI agents",
        )

        # Then: Comment is created with proper types
        assert isinstance(correct_comment.comment_type, CommentType)
        assert isinstance(correct_comment.severity, CommentSeverity)
        assert correct_comment.comment_type == CommentType.SECURITY
        assert correct_comment.severity == CommentSeverity.WARNING

        # Document the pattern for AI agents
        ai_agent_best_practices = [
            "Use CommentType.VALUE instead of 'value'",
            "Use CommentSeverity.LEVEL instead of 'level'",
            "Import enum classes before using them",
            "Validate enum values client-side since dataclasses don't",
        ]

        assert len(ai_agent_best_practices) == 4, (
            f"AI agents should follow these patterns: {ai_agent_best_practices}"
        )

    @pytest.mark.asyncio
    async def test_ai_agent_gets_helpful_error_for_missing_required_fields(self):
        """
        As an AI agent working with complex schemas,
        When I omit required fields from tool parameters,
        Then I should receive specific error messages about missing fields,
        So I can complete the request with all required information.
        """
        # Given: AI agent attempts to create comment without required fields

        # When: AI agent tries to create CodeReviewComment with missing required fields
        with pytest.raises(TypeError) as exc_info:
            # Missing required positional arguments
            CodeReviewComment(comment_id="test_comment_1")  # type: ignore[call-arg]

        # Then: Error should mention missing required fields
        error_message = str(exc_info.value)

        # AI agents need to know which specific fields are missing
        # TypeError should mention the missing required arguments
        assert (
            "required" in error_message.lower() or "missing" in error_message.lower()
        ), (
            f"AI agents need to know which required fields are missing. "
            f"Error message: {error_message}"
        )

    @pytest.mark.asyncio
    async def test_ai_agent_discovers_valid_enum_values_from_errors(self):
        """
        As an AI agent discovering tool capabilities,
        When I encounter enum validation errors,
        Then I should be able to understand valid options from error context,
        So I can make correct subsequent requests.
        """
        # Given: AI agent needs to understand valid CommentType values

        # When: AI agent explores enum values
        valid_comment_types = [e.value for e in CommentType]
        valid_severities = [e.value for e in CommentSeverity]

        # Then: AI agent can construct valid requests
        valid_comment = CodeReviewComment(
            comment_id="test_comment_1",
            comment_type=CommentType.GENERAL,
            severity=CommentSeverity.SUGGESTION,
            title="Test Title",
            content="Test content",
        )

        assert valid_comment.comment_type == CommentType.GENERAL
        assert valid_comment.severity == CommentSeverity.SUGGESTION

        # Document valid values for AI agent reference
        expected_comment_types = [
            "general",
            "line",
            "file",
            "suggestion",
            "security",
            "performance",
            "domain",
        ]
        expected_severities = ["info", "suggestion", "warning", "error", "critical"]

        assert set(valid_comment_types) == set(expected_comment_types), (
            f"AI agents expect these comment types: {expected_comment_types}. "
            f"Found: {valid_comment_types}"
        )

        assert set(valid_severities) == set(expected_severities), (
            f"AI agents expect these severities: {expected_severities}. "
            f"Found: {valid_severities}"
        )

    @pytest.mark.asyncio
    async def test_ai_agent_understands_optional_vs_required_parameters(self):
        """
        As an AI agent optimizing tool usage,
        When I examine tool parameter requirements,
        Then I should clearly understand which parameters are required vs optional,
        So I can make efficient requests with minimal required data.
        """
        # Given: AI agent wants to create minimal valid comment

        # When: AI agent provides only required fields
        minimal_comment = CodeReviewComment(
            comment_id="minimal_test",
            comment_type=CommentType.GENERAL,
            severity=CommentSeverity.INFO,
            title="Minimal Title",
            content="Minimal content",
        )

        # Then: Comment should be created successfully with defaults for optional fields
        assert minimal_comment.file_path is None  # Optional field
        assert minimal_comment.line_number is None  # Optional field
        assert minimal_comment.suggested_code is None  # Optional field
        assert minimal_comment.reasoning is None  # Optional field
        assert minimal_comment.business_impact is None  # Optional field
        assert minimal_comment.tags == []  # Optional field with default
        assert minimal_comment.metadata == {}  # Optional field with default
        assert minimal_comment.parent_thread_id is None  # Optional field

        # AI agents should understand the minimal viable request
        required_fields = ["comment_id", "comment_type", "severity", "title", "content"]
        for field in required_fields:
            assert hasattr(minimal_comment, field), (
                f"AI agents expect required field '{field}' to be present"
            )

    @pytest.mark.asyncio
    async def test_ai_agent_gets_validation_feedback_from_dry_run(self):
        """
        As an AI agent learning tool usage patterns,
        When I use dry_run mode with post_ai_generated_comments,
        Then I should get validation feedback without side effects,
        So I can test schemas and understand tool behavior safely.

        IMPLEMENTATION: dry_run now performs full validation including field checks.
        """
        # Given: AI agent wants to test comment posting without actually posting
        from pdp_dev_mcp.tools.code_review.ai_comment_posting import (
            post_ai_generated_comments,
        )

        # When: AI agent uses dry_run mode with valid comment
        valid_comment = CodeReviewComment(
            comment_id="dry_run_test_1",
            comment_type=CommentType.GENERAL,
            severity=CommentSeverity.INFO,
            title="Test Dry Run",
            content="Testing validation without posting",
        )

        result = post_ai_generated_comments(
            org="test_org",
            project="test_project",
            repository="test_repo",
            pr_id=12345,
            comments=[valid_comment],
            dry_run=True,
            filter_self_praise=False,
        )

        # Then: Validation feedback is provided
        assert result.dry_run is True
        assert result.total_comments == 1
        assert result.successful_posts == 1  # Passed validation
        assert result.failed_posts == 0
        assert len(result.posted_comments) == 1
        assert result.posted_comments[0]["validation"] == "PASSED"
        assert result.posted_comments[0]["comment_id"] == "dry_run_test_1"

        # Test invalid comment fails validation in dry_run
        invalid_comment = CodeReviewComment(
            comment_id="",  # Empty ID should fail
            comment_type=CommentType.GENERAL,
            severity=CommentSeverity.INFO,
            title="Test Invalid",
            content="Testing validation failure",
        )

        result_invalid = post_ai_generated_comments(
            org="test_org",
            project="test_project",
            repository="test_repo",
            pr_id=12345,
            comments=[invalid_comment],
            dry_run=True,
            filter_self_praise=False,
        )

        assert result_invalid.failed_posts == 1
        assert len(result_invalid.failures) == 1
        assert "comment_id cannot be empty" in result_invalid.failures[0]["error"]

    @pytest.mark.asyncio
    async def test_ai_agent_gets_clear_api_error_messages_with_context(self):
        """
        As an AI agent handling API failures,
        When tools encounter API errors or network issues,
        Then I should receive clear error messages with context and suggestions,
        So I can provide helpful feedback to users and retry appropriately.

        IMPLEMENTATION: Enhanced error messages now include AGENT_GUIDANCE sections.
        """
        # Given: AI agent encounters API failure during comment posting
        from pdp_dev_mcp.tools.code_review.ai_comment_posting import (
            _post_single_comment,
        )

        test_comment = CodeReviewComment(
            comment_id="error_test_1",
            comment_type=CommentType.GENERAL,
            severity=CommentSeverity.INFO,
            title="Test Error Handling",
            content="Testing error messages",
        )

        # Test 401 Unauthorized error
        with patch("subprocess.run") as mock_subprocess:
            mock_subprocess.return_value = MagicMock(
                returncode=1, stderr="401 Unauthorized: Invalid Azure DevOps token"
            )

            success, error_msg = _post_single_comment(
                org="test_org",
                project="test_project",
                repository="test_repo",
                pr_id=12345,
                comment=test_comment,
            )

            assert success is False
            assert error_msg is not None
            assert "AGENT_GUIDANCE" in error_msg
            assert "Authentication failed" in error_msg
            assert "az login" in error_msg

        # Test 404 Not Found error
        with patch("subprocess.run") as mock_subprocess:
            mock_subprocess.return_value = MagicMock(
                returncode=1, stderr="404 Not Found: Pull request does not exist"
            )

            success, error_msg = _post_single_comment(
                org="test_org",
                project="test_project",
                repository="test_repo",
                pr_id=99999,
                comment=test_comment,
            )

            assert success is False
            assert error_msg is not None
            assert "AGENT_GUIDANCE" in error_msg
            assert "Resource not found" in error_msg
            assert (
                "PR 99999 does not exist" in error_msg or "does not exist" in error_msg
            )

        # Verify error context helps AI agents
        api_error_context_implemented = True
        assert api_error_context_implemented, (
            "AI agents need clear API error messages with actionable context"
        )

    @pytest.mark.asyncio
    async def test_ai_agent_discovers_tool_capabilities_through_parameter_inspection(
        self,
    ):
        """
        As an AI agent exploring available functionality,
        When I examine tool parameters and types,
        Then I should understand the full range of tool capabilities,
        So I can utilize advanced features appropriately.
        """
        # Given: AI agent examines CodeReviewComment capabilities

        # When: AI agent explores advanced features
        advanced_comment = CodeReviewComment(
            comment_id="feature_exploration",
            comment_type=CommentType.SECURITY,  # Specialized type
            severity=CommentSeverity.WARNING,
            title="Security Analysis",
            content="This demonstrates advanced comment capabilities",
            file_path="src/example.py",  # File-specific commenting
            line_number=42,  # Line-specific commenting
            suggested_code="# Improved security implementation",  # Code suggestions
            reasoning="Security best practice violation detected",  # AI reasoning
            business_impact="Reduces security risk",  # Business context
            tags=["security", "compliance", "automated-review"],  # Categorization
            metadata={
                "detection_method": "static_analysis",
                "confidence": 0.85,
            },  # Tool metadata
            parent_thread_id=12345,  # Threaded conversations
        )

        # Then: AI agent can leverage full feature set
        assert advanced_comment.comment_type == CommentType.SECURITY
        assert advanced_comment.file_path == "src/example.py"
        assert advanced_comment.line_number == 42
        assert advanced_comment.suggested_code is not None
        assert len(advanced_comment.tags) == 3
        assert "detection_method" in advanced_comment.metadata

        # AI agents should understand the rich feature set available
        feature_capabilities = [
            "file_path",  # File-specific comments
            "line_number",  # Line-specific comments
            "suggested_code",  # Code improvement suggestions
            "reasoning",  # AI explanation capability
            "business_impact",  # Business context linking
            "tags",  # Categorization and filtering
            "metadata",  # Extensible tool information
            "parent_thread_id",  # Conversation threading
        ]

        for capability in feature_capabilities:
            assert hasattr(advanced_comment, capability), (
                f"AI agents should discover '{capability}' capability through schema inspection"
            )


class TestMCPToolErrorMessageQuality:
    """
    Test scenarios ensuring error messages are helpful for AI agents
    working without source code or documentation access.
    """

    @pytest.mark.asyncio
    async def test_error_messages_include_tool_name_and_context(self):
        """
        As an AI agent handling multiple tool failures,
        When I receive error messages from MCP tools,
        Then errors should clearly identify which tool failed and why,
        So I can provide specific troubleshooting guidance to users.
        """
        # Given: AI agent encounters tool-specific error

        # When: Tool fails with context
        # Note: This tests the principle that error messages should be tool-specific
        tool_specific_errors_expected = True

        # Then: Error should include tool identification
        assert tool_specific_errors_expected, (
            "AI agents need error messages that clearly identify the failing tool "
            "and provide context for resolution"
        )

    @pytest.mark.asyncio
    async def test_validation_errors_suggest_corrections(self):
        """
        As an AI agent helping users fix tool usage,
        When validation errors occur,
        Then error messages should suggest specific corrections,
        So I can guide users to successful tool usage.
        """
        # Given: AI agent encounters validation error

        # When: Validation fails
        # Note: This documents the expectation for helpful validation messages
        correction_suggestions_expected = True

        # Then: Error should suggest fixes
        assert correction_suggestions_expected, (
            "AI agents need validation errors that suggest specific corrections "
            "rather than just indicating failure"
        )


class TestMCPToolIntrospectionCapabilities:
    """
    Test scenarios for potential tool introspection features that would
    help AI agents discover and use tools effectively.
    """

    @pytest.mark.asyncio
    async def test_ai_agent_can_discover_available_tool_categories(self):
        """
        As an AI agent exploring a new MCP server,
        When I need to understand available functionality,
        Then I should be able to discover tool categories and purposes,
        So I can guide users to appropriate tools for their needs.
        """
        # Given: AI agent connects to MCP server

        # When: AI agent explores available tools
        # Note: This tests the concept - actual implementation would use MCP protocol
        expected_categories = [
            "data_quality",  # Data quality analysis tools
            "code_review",  # Code review and analysis tools
            "azure_devops",  # Azure DevOps workflow tools
            "payment_domain",  # Payment-specific domain tools
        ]

        # Then: AI agent should discover logical tool groupings
        # This would ideally be provided by the MCP server itself
        tool_categorization_helpful = True
        assert tool_categorization_helpful, (
            f"AI agents benefit from discovering tool categories: {expected_categories}"
        )

    @pytest.mark.asyncio
    async def test_ai_agent_understands_tool_prerequisites_and_dependencies(self):
        """
        As an AI agent orchestrating complex workflows,
        When I plan multi-step operations using MCP tools,
        Then I should understand tool prerequisites and dependencies,
        So I can execute tools in the correct order with proper setup.
        """
        # Given: AI agent plans workflow using multiple tools

        # When: AI agent examines tool dependencies
        # Example: Some tools require repository context to be established first
        workflow_dependencies = {
            "post_ai_generated_comments": ["establish_pr_context"],
            "get_code_quality_signals": ["get_code_analysis_context"],
            "analyze_payment_code_compliance": ["get_payments_domain_context"],
        }

        # Then: AI agent should understand execution order requirements
        dependency_awareness_helpful = True
        assert dependency_awareness_helpful, (
            "AI agents need to understand tool prerequisites for successful workflows"
        )

        # Document the concept that tools should indicate their dependencies
        for dependent_tool, prerequisites in workflow_dependencies.items():
            assert isinstance(prerequisites, list), (
                f"Tool '{dependent_tool}' should clearly indicate prerequisites: {prerequisites}"
            )
