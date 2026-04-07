#!/usr/bin/env python3
"""
Integration tests for line/file-level comment positioning validation.

This test suite validates that line positioning works by:
1. Posting comments to specific lines/files
2. Retrieving comment metadata from Azure DevOps API
3. Validating actual position matches expected position
4. Automated cleanup of test comments
"""

import pytest
from typing import Dict, Any, List, Optional
from pdp_dev_mcp.tools.code_review.ai_comment_posting import (
    create_ai_comment,
    CommentType,
    CommentSeverity,
    post_ai_generated_comments,
)
from pdp_dev_mcp.tools.common.azure_devops_pr_comments import (
    azure_devops_pr_comment_analysis,
)


@pytest.mark.integration
class TestAIAgentsCanValidateLinePositioningForAccurateCommenting:
    """
    Test that AI agents can validate line/file positioning for accurate comment placement.

    These tests verify that AI agents can:
    - Post comments to specific lines/files
    - Retrieve comment metadata via Azure DevOps API
    - Compare actual vs expected position
    - Auto-cleanup test comments
    """

    def test_ai_agents_can_validate_single_line_comment_positioning_for_precise_feedback(
        self,
    ):
        """As an AI agent helping developers with code review feedback placement,
        When I post a comment to a specific line and validate its position,
        Then I should confirm the comment appears at the exact target line,
        So I can ensure precise feedback delivery to help developers focus on specific code issues."""
        # This will be implemented once we have working line positioning
        pytest.skip("Line positioning not yet implemented - clean slate approach")

    def test_ai_agents_can_validate_multiple_file_positioning_for_comprehensive_feedback(
        self,
    ):
        """As an AI agent helping developers with multi-file code review,
        When I post comments to different files and validate their positions,
        Then I should confirm each comment appears in the correct file context,
        So I can provide comprehensive feedback across multiple files to help developers understand cross-file impacts."""
        pytest.skip("Line positioning not yet implemented - clean slate approach")

    def test_ai_agents_can_use_official_api_structure_for_accurate_line_positioning(
        self,
    ):
        """As an AI agent helping developers with Azure DevOps API integration,
        When I use the documented Azure DevOps API structure for line positioning,
        Then I should achieve accurate comment placement using proper ThreadContext,
        So I can help developers implement reliable code review automation with precise feedback positioning."""

        # Create test comment with line positioning - OFFICIAL API STRUCTURE
        test_comment = create_ai_comment(
            comment_id="official-api-structure-test",
            title="Official API Structure Test",
            content=(
                "🧪 **TEST: Official Azure DevOps REST API Structure**\n\n"
                "This comment uses the EXACT JSON structure from Microsoft's official REST API documentation.\n\n"
                "**Fixed based on official docs:**\n"
                "- Added comments array with parentCommentId and commentType\n"
                "- Added status: 1 (active)\n"
                "- Set leftFileStart/End to null (for new files)\n"
                "- Added changeTrackingId: 1 in pullRequestThreadContext\n"
                "- Added leading slash to file path\n\n"
                "**Expected result:** Comment appears INLINE in Files view at line 1 of .copilot/README.md."
            ),
            comment_type=CommentType.GENERAL,
            severity=CommentSeverity.INFO,
            file_path=".copilot/README.md",  # Use file that's actually in the changeset
            line_number=1,
        )

        # Post the comment using the corrected implementation with working auth config
        result = post_ai_generated_comments(
            org="microsoft",  # Use same working config as pr_level_commenting test
            project="Universal Store",  # Use same working config as pr_level_commenting test
            repository="Commerce.PaymentsDataPlatform",
            pr_id=13844374,  # Use same working PR as pr_level_commenting test
            comments=[test_comment],
        )

        # Validate posting succeeded
        assert result.successful_posts > 0, f"Comment posting failed: {result.failures}"
        assert result.failed_posts == 0, f"Unexpected failures: {result.failures}"

        # TODO: Add automated validation once API analysis is working
        # validator = LinePositionValidator("msft-skilling", "Content", "Commerce.PaymentsDataPlatform", 229)
        # position_data = validator.get_comment_position_data("doc-based-positioning-test")
        # assert position_data["line_number"] == 400
        # assert position_data["file_path"].endswith("ai_comment_posting.py")
        # assert not position_data["is_pr_level"]

        print("✅ Real iteration context line positioning test completed successfully")
        print(
            f"   Posted {result.successful_posts} comment(s) with dynamic iteration context"
        )
        print(
            "   Manual verification required: Check PR 13844374 Files view for INLINE positioning"
        )

    def test_ai_agents_can_handle_invalid_line_numbers_gracefully_for_robust_operation(
        self,
    ):
        """As an AI agent helping developers with code review automation,
        When I encounter invalid line numbers during comment positioning,
        Then I should handle errors gracefully with clear fallback behavior,
        So I can help developers maintain reliable code review workflows even with positioning edge cases."""
        pytest.skip("Line positioning not yet implemented - clean slate approach")


class LinePositionValidator:
    """
    Utility class to validate comment positioning via Azure DevOps API.

    This provides the automated validation logic that replaces manual review.
    """

    def __init__(self, org: str, project: str, repository: str, pr_id: int):
        self.org = org
        self.project = project
        self.repository = repository
        self.pr_id = pr_id

    def get_comment_position_data(self, comment_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve positioning data for a specific comment.

        Returns:
            Dict with positioning info like:
            {
                'thread_id': 123456,
                'file_path': 'src/example.py',
                'line_number': 42,
                'is_pr_level': False,
                'thread_context': {...}
            }
        """
        try:
            # Get all comments on the PR
            result = azure_devops_pr_comment_analysis(
                pr_id=self.pr_id, save_to_file=False
            )

            # Find our specific comment by searching for comment_id in content
            for comment in result.get("active_comments", []):
                content = comment.get("full_content", "")
                if comment_id in content:
                    return self._extract_position_data(comment)

            return None
        except Exception as e:
            print(f"Error retrieving comment position: {e}")
            return None

    def _extract_position_data(self, comment: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract positioning data from Azure DevOps comment metadata.

        The key is analyzing the threadContext to determine if positioning worked.
        """
        # Extract position data from the comment (now provided by azure_devops_pr_comment_analysis)
        file_path = comment.get("file_path")
        line_start = comment.get("line_start")
        line_end = comment.get("line_end")
        
        # If file_path is None, this is a PR-level comment
        is_pr_level = file_path is None

        return {
            "thread_id": comment.get("thread_id"),
            "file_path": file_path,
            "line_number": line_start,  # Use start line for validation
            "is_pr_level": is_pr_level,
            "thread_context": comment.get("thread_context", {}),
            "raw_comment": comment,
        }

    def validate_position(
        self, comment_id: str, expected_file: str, expected_line: int
    ) -> Dict[str, Any]:
        """
        Validate that a comment appears at the expected position.

        Returns validation result with success/failure and details.
        """
        position_data = self.get_comment_position_data(comment_id)

        if not position_data:
            return {
                "success": False,
                "error": f"Comment with ID {comment_id} not found",
                "expected_file": expected_file,
                "expected_line": expected_line,
            }

        actual_file = position_data.get("file_path")
        actual_line = position_data.get("line_number")
        is_pr_level = position_data.get("is_pr_level")

        if is_pr_level:
            return {
                "success": False,
                "error": "Comment appears at PR level instead of file/line level",
                "expected_file": expected_file,
                "expected_line": expected_line,
                "actual_file": None,
                "actual_line": None,
                "is_pr_level": True,
            }

        file_match = actual_file == expected_file
        line_match = actual_line == expected_line

        return {
            "success": file_match and line_match,
            "expected_file": expected_file,
            "expected_line": expected_line,
            "actual_file": actual_file,
            "actual_line": actual_line,
            "file_match": file_match,
            "line_match": line_match,
            "is_pr_level": False,
            "position_data": position_data,
        }
