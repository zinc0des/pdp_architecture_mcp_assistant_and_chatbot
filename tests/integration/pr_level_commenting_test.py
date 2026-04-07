#!/usr/bin/env python3
"""
Simple integration test for PR-level comment posting.
This validates that PR-level comments work correctly without line positioning.
"""

import pytest
from pdp_dev_mcp.tools.code_review.ai_comment_posting import (
    post_ai_generated_comments,
    create_ai_comment,
    CommentType,
    CommentSeverity,
)


@pytest.mark.integration
class TestAIAgentsCanPostPRLevelCommentsForCodeReview:
    """Test that AI agents can post PR-level comments for comprehensive code review."""

    def test_ai_agents_can_post_pr_level_comments_successfully_for_general_feedback(
        self,
    ):
        """As an AI agent helping developers with code review,
        When I post a PR-level comment for general feedback,
        Then I should successfully create and post the comment without line positioning,
        So I can provide comprehensive PR-level insights to help developers understand overall code quality."""
        # Create a simple PR-level comment
        comment = create_ai_comment(
            comment_id="pr-level-test-001",
            title="✅ PR-Level Comment Test",
            content=(
                "**PR-Level Comment Integration Test**\n\n"
                "This is a test comment that should appear at the PR level.\n\n"
                "**Validation Points:**\n"
                "- ✅ Posted successfully via Azure DevOps API\n"
                "- ✅ Appears at PR level (not attached to file/line)\n"
                "- ✅ No line positioning attempted\n"
                "- ✅ Clean foundation for future line positioning implementation\n\n"
                "**Tags:** `integration-test` `pr-level` `clean-slate`"
            ),
            comment_type=CommentType.GENERAL,
            severity=CommentSeverity.INFO,
            # NOTE: These are ignored in current implementation
            file_path=None,  # Explicitly None for PR-level comment
            line_number=None,  # Explicitly None for PR-level comment
        )

        # Post the comment
        result = post_ai_generated_comments(
            org="microsoft",
            project="Universal Store",
            repository="Commerce.PaymentsDataPlatform",
            pr_id=13844374,
            comments=[comment],
        )

        # Validate successful posting
        assert result.successful_posts == 1, (
            f"Expected 1 successful post, got {result.successful_posts}"
        )
        assert result.total_comments == 1, (
            f"Expected 1 total comment, got {result.total_comments}"
        )
        assert len(result.failures) == 0, f"Expected no failures, got {result.failures}"
        assert len(result.posted_comments) == 1, (
            f"Expected 1 posted comment, got {len(result.posted_comments)}"
        )

        # Validate comment details
        posted_comment = result.posted_comments[0]
        assert posted_comment["comment_id"] == "pr-level-test-001"
        assert posted_comment["title"] == "✅ PR-Level Comment Test"
        assert posted_comment["type"] == "general"
        assert posted_comment["severity"] == "info"
        assert posted_comment["posted"] is True

        print("✅ PR-level comment posted successfully!")
        print(f"📝 Comment ID: {posted_comment['comment_id']}")
        print("🎯 Posted to PR: 13844374")

    def test_ai_agents_can_post_multiple_pr_level_comments_efficiently_for_batch_feedback(
        self,
    ):
        """As an AI agent helping developers with comprehensive code review,
        When I post multiple PR-level comments in a batch operation,
        Then I should successfully create and post all comments efficiently,
        So I can provide developers with structured batch feedback for complex pull requests."""

        comments = [
            create_ai_comment(
                comment_id="batch-test-001",
                title="🧪 Batch Test Comment 1",
                content="First comment in batch test",
                comment_type=CommentType.GENERAL,
            ),
            create_ai_comment(
                comment_id="batch-test-002",
                title="🧪 Batch Test Comment 2",
                content="Second comment in batch test",
                comment_type=CommentType.GENERAL,
            ),
        ]

        result = post_ai_generated_comments(
            org="microsoft",
            project="Universal Store",
            repository="Commerce.PaymentsDataPlatform",
            pr_id=13844374,
            comments=comments,
        )

        # Validate batch posting
        assert result.successful_posts == 2, (
            f"Expected 2 successful posts, got {result.successful_posts}"
        )
        assert result.total_comments == 2, (
            f"Expected 2 total comments, got {result.total_comments}"
        )
        assert len(result.failures) == 0, f"Expected no failures, got {result.failures}"

        print("✅ Batch PR-level comments posted successfully!")
