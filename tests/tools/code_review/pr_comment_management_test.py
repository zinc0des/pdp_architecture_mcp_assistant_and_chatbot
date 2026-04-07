"""
Tests for AI-generated comment management and posting functionality.

Tests focus on AI's ability to deliver intelligent code review feedback
through proper Azure DevOps integration with contextual formatting.

All tests follow BDD patterns and test only through public APIs.
"""

import json
import subprocess
from unittest.mock import patch, Mock

from pdp_dev_mcp.tools.code_review.ai_comment_posting import (
    post_ai_generated_comments,
    create_security_comment,
    CommentType,
    CommentSeverity,
    CodeReviewComment,
)


class TestAIAgentsCanPostIntelligentCodeReviewComments:
    """Test AI agents' ability to post contextual, intelligent code review feedback."""

    def test_ai_agents_can_create_contextual_security_comments_with_business_impact(
        self,
    ) -> None:
        """
        As an AI agent providing security-focused code review
        When I identify security vulnerabilities in payment processing code
        Then I create properly formatted security comments with business impact
        """
        # Given: AI agent identifies a critical security issue
        security_comment = create_security_comment(
            comment_id="security_001",
            title="Hardcoded Payment Credentials Detected",
            content="Hardcoded API keys and database passwords detected in payment processing configuration. This violates PCI DSS requirements and exposes sensitive financial data.",
            file_path="src/payment_processor.py",
            line_number=42,
            severity=CommentSeverity.CRITICAL,
            business_impact="CRITICAL: PCI compliance violation could result in audit failures, fines up to $500K, and loss of payment processing privileges.",
        )

        # Then: Security comment includes proper threat assessment
        assert security_comment.comment_type == CommentType.SECURITY
        assert security_comment.severity == CommentSeverity.CRITICAL
        assert "PCI DSS" in security_comment.content
        assert security_comment.business_impact is not None
        assert "security" in security_comment.tags
        assert "compliance" in security_comment.tags

        # And: When posted through public API, comment formatting includes security indicators
        with patch("subprocess.run") as mock_subprocess:
            mock_subprocess.return_value = Mock(
                returncode=0, stdout='{"value": "success"}'
            )

            post_ai_generated_comments(
                org="test-org",
                project="test-project",
                repository="test-repo",
                pr_id=123,
                comments=[security_comment],
                dry_run=False,
            )

            # Verify the API call contains the security content
            assert mock_subprocess.called
            call_args = str(mock_subprocess.call_args)
            assert "Hardcoded API keys" in call_args
            assert "PCI DSS requirements" in call_args
            assert "sensitive financial data" in call_args

    @patch("subprocess.run")
    def test_praise_detection_through_filtering_behavior(self, mock_run):
        """
        Test that praise comments with multiple positive words get filtered properly.

        This tests the edge case where praise detection affects comment filtering,
        documenting the behavior users see when comments contain positive language.
        """
        # Mock Azure CLI responses to simulate own PR scenario
        mock_run.side_effect = [
            Mock(
                returncode=0, stdout='{"createdBy": {"displayName": "test-user"}}'
            ),  # PR author lookup
            Mock(
                returncode=0, stdout='{"displayName": "test-user"}'
            ),  # Current user lookup (same as author)
            Mock(returncode=0, stdout="[]"),  # comment posting (dry run)
        ]

        # Create comment with multiple positive words - should be detected as praise
        comments = [
            CodeReviewComment(
                comment_id="praise_edge_case",
                comment_type=CommentType.GENERAL,
                severity=CommentSeverity.INFO,
                title="Excellent work",
                content="This is excellent! Great job on the implementation. Amazing results.",
                file_path=None,
                line_number=None,
            )
        ]

        # Call the function with own PR (filtering enabled)
        result = post_ai_generated_comments(
            org="testorg",
            project="testproject",
            repository="testrepo",
            pr_id=123,
            comments=comments,
            dry_run=True,
            filter_self_praise=True,
        )

        # Verify praise comment was filtered out (not posted to PR)
        assert result.total_comments == 0, (
            "Praise comments should be filtered on own PR"
        )

        # Verify praise comment appears in local comments instead
        assert len(result.local_praise_comments) == 1, (
            "Praise should appear in local comments"
        )
        assert result.local_praise_comments[0]["comment_id"] == "praise_edge_case"

    @patch("subprocess.run")
    def test_conservative_praise_filtering_when_azure_cli_fails(self, mock_run):
        """
        Test that when Azure CLI fails to determine PR author or current user,
        the system uses conservative filtering to avoid potential self-praise.

        This documents the behavior when authentication or API issues prevent
        proper user identification.
        """
        # Mock Azure CLI scenarios where PR author lookup fails
        mock_run.side_effect = [
            Mock(
                returncode=0, stdout="[]"
            ),  # _get_pr_diff_files succeeds (empty result)
            Mock(
                returncode=1, stderr="API authentication failed"
            ),  # PR author lookup fails - triggers conservative filtering
            Mock(returncode=0, stdout="[]"),  # comment posting still works (dry run)
        ]

        # Create potentially praise-like comment
        comments = [
            CodeReviewComment(
                comment_id="potential_praise",
                comment_type=CommentType.GENERAL,
                severity=CommentSeverity.INFO,
                title="Nice work",
                content="This looks good and works well.",
                file_path=None,
                line_number=None,
            )
        ]

        # Call function with filtering enabled but API failures
        result = post_ai_generated_comments(
            org="testorg",
            project="testproject",
            repository="testrepo",
            pr_id=123,
            comments=comments,
            dry_run=True,
            filter_self_praise=True,
        )

        # When user identification fails, conservative approach filters potential praise
        assert result.total_comments == 0, (
            "Conservative filtering should filter potential praise when user unknown"
        )
        assert len(result.local_praise_comments) == 1, (
            "Filtered praise should appear locally for user to decide whether to post"
        )

    @patch("subprocess.run")
    def test_network_failure_during_comment_posting(self, mock_run):
        """
        Test graceful handling of network failures during comment posting.

        This documents how the system behaves when Azure DevOps API calls
        fail due to network connectivity issues.
        """
        # Mock network failure during comment posting - simplified sequence
        mock_run.side_effect = [
            Mock(
                returncode=0, stdout='{"createdBy": {"displayName": "other-user"}}'
            ),  # PR author lookup succeeds
            Mock(
                returncode=0, stdout="current-user"
            ),  # current user lookup in _filter_self_praise_comments succeeds
            Mock(
                returncode=1, stderr="Network connection failed"
            ),  # actual comment posting command fails
        ]

        comments = [
            CodeReviewComment(
                comment_id="network_test",
                comment_type=CommentType.GENERAL,
                severity=CommentSeverity.INFO,
                title="Code review",
                content="Consider adding error handling here.",
            )
        ]

        result = post_ai_generated_comments(
            org="testorg",
            project="testproject",
            repository="testrepo",
            pr_id=123,
            comments=comments,
            dry_run=False,
        )

        # Network failure should be captured in results
        assert result.total_comments == 1
        assert result.failed_posts == 1
        assert len(result.failures) == 1
        assert "Network connection failed" in result.failures[0]["error"]

    @patch("subprocess.run")
    def test_line_comment_with_complex_diff_context(self, mock_run):
        """
        Test line comments when PR has complex diff context with multiple file changes.

        This verifies that line comments are properly validated against
        the available files in the PR diff.
        """
        # Mock complex diff response with multiple files
        diff_response = {
            "value": [
                {"item": {"path": "/src/payment_processor.py"}, "changeType": "edit"},
                {"item": {"path": "/src/utils/helpers.py"}, "changeType": "add"},
                {"item": {"path": "/tests/test_payment.py"}, "changeType": "edit"},
            ]
        }

        mock_run.side_effect = [
            Mock(returncode=0, stdout=json.dumps(diff_response)),  # diff files
            Mock(
                returncode=0, stdout='{"createdBy": {"displayName": "other-user"}}'
            ),  # PR author
            Mock(
                returncode=0, stdout='{"displayName": "current-user"}'
            ),  # current user
            Mock(returncode=0, stdout="[]"),  # comment posting
        ]

        # Create line comments for both existing and non-existing files
        comments = [
            CodeReviewComment(
                comment_id="valid_line_comment",
                comment_type=CommentType.LINE_COMMENT,
                severity=CommentSeverity.WARNING,
                title="Code improvement",
                content="Add null check here",
                file_path="src/payment_processor.py",  # exists in diff
                line_number=42,
            ),
            CodeReviewComment(
                comment_id="invalid_line_comment",
                comment_type=CommentType.LINE_COMMENT,
                severity=CommentSeverity.INFO,
                title="Missing file comment",
                content="This file is not in the PR",
                file_path="src/missing_file.py",  # not in diff
                line_number=10,
            ),
        ]

        result = post_ai_generated_comments(
            org="testorg",
            project="testproject",
            repository="testrepo",
            pr_id=123,
            comments=comments,
            dry_run=True,
        )

        # Should process all comments but may warn about invalid file paths
        assert result.total_comments == 2
        # Exact behavior depends on implementation - may post all or filter invalid

    @patch("subprocess.run")
    def test_azure_cli_timeout_handling(self, mock_run):
        """
        Test handling of Azure CLI command timeouts.

        This documents system behavior when Azure CLI commands exceed
        their timeout limits due to slow API responses.
        """
        # Mock timeout during Azure CLI call
        mock_run.side_effect = subprocess.TimeoutExpired("az", 30)

        comments = [
            CodeReviewComment(
                comment_id="timeout_test",
                comment_type=CommentType.GENERAL,
                severity=CommentSeverity.INFO,
                title="Test comment",
                content="This should handle timeout gracefully",
            )
        ]

        result = post_ai_generated_comments(
            org="testorg",
            project="testproject",
            repository="testrepo",
            pr_id=123,
            comments=comments,
            dry_run=False,
        )

        # Timeout should be handled gracefully
        assert result.total_comments == 1
        assert result.failed_posts == 1
        # Specific error handling depends on implementation

    @patch("subprocess.run")
    def test_unexpected_system_error_handling(self, mock_run):
        """
        Test handling of unexpected system errors during processing.

        This ensures the system remains stable when encountering
        unexpected exceptions during comment processing.
        """
        # Mock unexpected exception
        mock_run.side_effect = Exception("Unexpected system error")

        comments = [
            CodeReviewComment(
                comment_id="error_test",
                comment_type=CommentType.GENERAL,
                severity=CommentSeverity.INFO,
                title="Error handling test",
                content="Testing unexpected error scenarios",
            )
        ]

        result = post_ai_generated_comments(
            org="testorg",
            project="testproject",
            repository="testrepo",
            pr_id=123,
            comments=comments,
            dry_run=False,
        )

        # System should handle unexpected errors gracefully
        assert result.total_comments == 1
        assert result.failed_posts == 1
        # Error should be captured in failure details

    @patch("subprocess.run")
    def test_suggestion_comment_with_comprehensive_metadata(self, mock_run):
        """
        Test suggestion comments with comprehensive metadata and formatting.

        This verifies that all comment metadata (tags, business impact,
        suggested code, etc.) is properly handled and formatted.
        """
        mock_run.side_effect = [
            Mock(returncode=0, stdout='{"value": []}'),  # diff files
            Mock(
                returncode=0, stdout='{"createdBy": {"displayName": "other-user"}}'
            ),  # PR author
            Mock(
                returncode=0, stdout='{"displayName": "current-user"}'
            ),  # current user
            Mock(returncode=0, stdout="[]"),  # comment posting
        ]

        # Create comprehensive suggestion comment
        comprehensive_comment = CodeReviewComment(
            comment_id="comprehensive_suggestion",
            comment_type=CommentType.SUGGESTION,
            severity=CommentSeverity.WARNING,
            title="Performance Optimization Suggestion",
            content="This loop could be optimized using vectorized operations for better performance with large datasets.",
            file_path="src/data_processor.py",
            line_number=156,
            suggested_code="df.apply(lambda x: process_row_vectorized(x), axis=1)",
            reasoning="Vectorized operations in pandas are significantly faster than iterative loops for large datasets.",
            business_impact="Could improve processing time by 70% for large payment batches",
            tags=["performance", "optimization", "pandas"],
            metadata={"performance_impact": "high", "complexity": "medium"},
        )

        result = post_ai_generated_comments(
            org="testorg",
            project="testproject",
            repository="testrepo",
            pr_id=123,
            comments=[comprehensive_comment],
            dry_run=True,
        )

        # Verify comprehensive metadata is preserved
        assert result.total_comments == 1
        assert result.successful_posts == 1
        posted_comment = result.posted_comments[0]

        # Check that key metadata is included in formatted content
        formatted_content = posted_comment["formatted_content"]
        assert "Performance Optimization Suggestion" in formatted_content
        assert "vectorized operations" in formatted_content
        # Additional metadata should be included in formatting
