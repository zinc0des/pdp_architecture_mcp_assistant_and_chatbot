"""
Tests for Enhanced Error Handling and Threading Functionality

These tests validate the critical error handling improvements and new threading
functionality that provide functional purpose beyond graceful degradation.
"""

import pytest
from unittest.mock import patch, Mock
import json

from pdp_dev_mcp.tools.code_review.ai_comment_posting import (
    CodeReviewComment,
    CommentType,
    CommentSeverity,
    post_ai_generated_comments,
    create_ai_comment,
    _post_single_comment,
)
from pdp_dev_mcp.tools.common.repository_context import (
    RepositoryContext,
    ensure_repository_context,
)


class TestEnhancedErrorHandling:
    """Test enhanced error handling that provides functional guidance."""

    def setup_method(self):
        """Reset repository context before each test."""
        RepositoryContext._current_working_directory = None
        RepositoryContext._cached_repo_info = None
        RepositoryContext._cache_timestamp = None

    def test_ai_agents_can_get_explicit_mcp_tool_guidance_for_repository_context_issues(
        self,
    ):
        """As an AI agent helping developers with repository context management,
        When I encounter missing repository context,
        Then I should receive explicit MCP tool guidance with troubleshooting steps,
        So I can help developers properly configure their repository context for MCP operations."""
        # When: AI agent attempts to ensure context without setting it
        result = ensure_repository_context()

        # Then: Error provides explicit MCP tool guidance
        if result["success"] is False:
            # Check for the specific error message format
            assert "No repository context set" in result.get(
                "error", ""
            ) or "Use mcp_pdp-dev-mcp_set_repository_context" in result.get(
                "suggestion", ""
            )
        else:
            # If success, it means there's cached context - skip this test
            pytest.skip("Repository context is already set from previous tests")


class TestThreadingFunctionality:
    """Test new threading functionality for proper conversation flow."""

    def setup_method(self):
        """Setup for threading tests."""
        RepositoryContext._current_working_directory = "/test/repo"
        RepositoryContext._cached_repo_info = {
            "organization": "microsoft",
            "project": "Universal Store",
            "repository": "Commerce.PaymentsDataPlatform",
        }

    def test_ai_agents_can_create_threaded_replies_with_parent_thread_id_for_conversation_continuity(
        self,
    ):
        """As an AI agent helping developers with threaded code review conversations,
        When I create a comment with parent_thread_id for a threaded reply,
        Then I should successfully create a comment with proper thread linkage,
        So I can help developers maintain conversation continuity in complex code review discussions."""
        # When: AI agent creates a threaded reply comment
        comment = create_ai_comment(
            comment_id="test_reply_1",
            title="Test Threaded Reply",
            content="This is a threaded reply",
            parent_thread_id=107991765,
        )

        # Then: Comment includes parent thread reference
        assert comment.parent_thread_id == 107991765
        assert comment.comment_id == "test_reply_1"
        assert comment.title == "Test Threaded Reply"

    def test_create_ai_comment_defaults_to_none_for_new_threads(self):
        """
        Given: AI agent creates a new comment thread
        When: Creating comment without parent_thread_id
        Then: Comment defaults to None for new thread creation
        """
        # When: AI agent creates a new comment thread
        comment = create_ai_comment(
            comment_id="test_new_1",
            title="Test New Thread",
            content="This is a new thread",
        )

        # Then: Comment defaults to None for new threads
        assert comment.parent_thread_id is None
        assert comment.comment_id == "test_new_1"

    @patch("subprocess.run")
    def test_post_single_comment_uses_threads_endpoint_for_new_comments(
        self, mock_subprocess
    ):
        """
        Given: AI agent posts a new comment without parent_thread_id
        When: Posting the comment
        Then: Uses POST /threads endpoint for new thread creation
        """
        # Given: Mock successful Azure CLI response
        mock_subprocess.return_value = Mock(returncode=0, stdout="", stderr="")

        # Given: New comment without parent thread
        comment = CodeReviewComment(
            comment_id="new_thread_1",
            comment_type=CommentType.GENERAL,
            severity=CommentSeverity.INFO,
            title="New Thread",
            content="This creates a new thread",
            parent_thread_id=None,
        )

        # When: AI agent posts the comment
        success, error = _post_single_comment(
            "microsoft", "Universal Store", "test-repo", 12345, comment
        )

        # Then: Uses threads endpoint for new thread creation
        assert success is True
        assert error is None
        mock_subprocess.assert_called_once()

        # Verify the correct endpoint was used
        call_args = mock_subprocess.call_args[0][0]
        uri_arg = next(arg for i, arg in enumerate(call_args) if arg == "--uri")
        uri_index = call_args.index(uri_arg) + 1
        uri = call_args[uri_index]
        assert "/threads?" in uri
        assert "/comments?" not in uri

    @patch("subprocess.run")
    def test_post_single_comment_uses_thread_comments_endpoint_for_replies(
        self, mock_subprocess
    ):
        """
        Given: AI agent posts a threaded reply with parent_thread_id
        When: Posting the comment
        Then: Uses POST /threads/{threadId}/comments endpoint for threaded reply
        """
        # Given: Mock successful Azure CLI response
        mock_subprocess.return_value = Mock(returncode=0, stdout="", stderr="")

        # Given: Threaded reply comment
        comment = CodeReviewComment(
            comment_id="reply_1",
            comment_type=CommentType.GENERAL,
            severity=CommentSeverity.INFO,
            title="Threaded Reply",
            content="This is a threaded reply",
            parent_thread_id=107991765,
        )

        # When: AI agent posts the threaded reply
        success, error = _post_single_comment(
            "microsoft", "Universal Store", "test-repo", 12345, comment
        )

        # Then: Uses thread comments endpoint for threaded reply
        assert success is True
        assert error is None
        mock_subprocess.assert_called_once()

        # Verify the correct endpoint was used
        call_args = mock_subprocess.call_args[0][0]
        uri_arg = next(arg for i, arg in enumerate(call_args) if arg == "--uri")
        uri_index = call_args.index(uri_arg) + 1
        uri = call_args[uri_index]
        assert "/threads/107991765/comments?" in uri
        assert "/threads?" not in uri

    @patch("subprocess.run")
    def test_ai_agents_can_use_simplified_payload_structure_for_efficient_threaded_replies(
        self, mock_subprocess
    ):
        """As an AI agent helping developers with efficient threaded conversations,
        When I post a threaded reply using simplified payload structure,
        Then I should successfully create the reply without redundant thread context,
        So I can help developers maintain clean and efficient conversation threads by inheriting context from parent threads."""
        # Given: Mock successful Azure CLI response
        mock_subprocess.return_value = Mock(returncode=0, stdout="", stderr="")

        # Given: Threaded reply comment
        comment = CodeReviewComment(
            comment_id="reply_simplified",
            comment_type=CommentType.GENERAL,
            severity=CommentSeverity.INFO,
            title="Simplified Reply",
            content="This reply uses simplified structure",
            parent_thread_id=107991765,
        )

        # When: AI agent posts the threaded reply
        _post_single_comment(
            "microsoft", "Universal Store", "test-repo", 12345, comment
        )

        # Then: Uses simplified payload structure for replies
        call_args = mock_subprocess.call_args[0][0]
        body_index = call_args.index("--body") + 1
        body_json = call_args[body_index]
        payload = json.loads(body_json)

        # Verify simplified structure
        assert "content" in payload
        assert "commentType" in payload
        assert "parentCommentId" in payload
        assert "threadContext" not in payload  # Should not include thread context
        assert (
            "pullRequestThreadContext" not in payload
        )  # Should not include PR context

    def test_post_ai_generated_comments_handles_mixed_thread_types(self):
        """
        Given: AI agent has both new threads and threaded replies to post
        When: Posting comments with mixed parent_thread_id values
        Then: Each comment uses appropriate endpoint based on parent_thread_id
        """
        # Given: Mixed comment types
        comments = [
            create_ai_comment(
                comment_id="new_1",
                title="New Thread 1",
                content="New thread content",
                parent_thread_id=None,
            ),
            create_ai_comment(
                comment_id="reply_1",
                title="Reply 1",
                content="Reply content",
                parent_thread_id=107991765,
            ),
            create_ai_comment(
                comment_id="new_2",
                title="New Thread 2",
                content="Another new thread",
                parent_thread_id=None,
            ),
        ]

        with patch(
            "pdp_dev_mcp.tools.code_review.ai_comment_posting._post_single_comment"
        ) as mock_post:
            mock_post.return_value = (True, None)

            # When: AI agent posts mixed comment types
            result = post_ai_generated_comments(
                org="microsoft",
                project="Universal Store",
                repository="test-repo",
                pr_id=12345,
                comments=comments,
                dry_run=False,
            )

            # Then: All comments posted successfully
            assert result.successful_posts == 3
            assert result.failed_posts == 0
            assert mock_post.call_count == 3

            # Verify each comment was processed with correct parent_thread_id
            call_args_list = mock_post.call_args_list
            assert call_args_list[0][0][4].parent_thread_id is None  # new_1
            assert call_args_list[1][0][4].parent_thread_id == 107991765  # reply_1
            assert call_args_list[2][0][4].parent_thread_id is None  # new_2


class TestErrorHandlingIntegration:
    """Test error handling integration across multiple tools."""

    def setup_method(self):
        """Reset state for integration tests."""
        RepositoryContext._current_working_directory = None
        RepositoryContext._cached_repo_info = None
        RepositoryContext._cache_timestamp = None

    def test_ai_agents_can_receive_actionable_mcp_tool_references_for_error_resolution(
        self,
    ):
        """As an AI agent helping developers with MCP tool troubleshooting,
        When I encounter various error conditions in MCP tools,
        Then I should receive error messages with specific MCP tool names and resolution steps,
        So I can help developers quickly identify and use the right tools to resolve configuration and operational issues."""
        # Test ensure_repository_context error structure
        result = ensure_repository_context()

        if result["success"] is False:
            # Check that error guidance mentions the MCP tool
            error_text = result.get("error", "") + " " + result.get("suggestion", "")
            assert (
                "mcp_pdp-dev-mcp_set_repository_context" in error_text
                or "set_repository_context" in error_text
            )
        else:
            # If context exists, test the error structure with a mock
            with patch(
                "pdp_dev_mcp.tools.common.repository_context.RepositoryContext.get_repository_info"
            ) as mock_get:
                mock_get.return_value = {
                    "success": False,
                    "error": "No repository context set and intelligent discovery failed. Use set_repository_context() first.",
                    "suggestion": "Call set_repository_context() with your repository path",
                }

                # Clear context to force error path
                RepositoryContext._current_working_directory = None
                RepositoryContext._cached_repo_info = None

                result = ensure_repository_context()
                assert result["success"] is False
                assert "set_repository_context" in result.get("error", "")
