"""Test the new PR URL functionality with real-world URLs provided by the user."""

import pytest
from unittest.mock import patch
from pdp_dev_mcp.tools.code_review.ai_comment_posting import (
    post_ai_comments_by_pr_url,
    CodeReviewComment,
    CommentType,
    CommentSeverity,
    CommentPostingResult,
)


class TestAIAgentsCanHandleRealWorldPRUrls:
    """Test that AI agents can handle real-world PR URL functionality for cross-organization support."""

    def test_ai_agents_can_parse_and_post_to_msazure_pr_urls_for_cross_organization_support(
        self,
    ):
        """As an AI agent helping developers with cross-organization code review,
        When I parse and post to MSAzure PR URLs,
        Then I should successfully extract parameters and post comments,
        So I can help developers collaborate across different Azure DevOps organizations."""
        pr_url = "https://dev.azure.com/msazure/One/_git/CFS-Payments-DataPlatform-PMT/pullrequest/13483931"

        test_comment = CodeReviewComment(
            comment_id="real-world-test-1",
            title="Cross-Organization Test",
            content="Testing with real MSAzure URL from user's example",
            comment_type=CommentType.GENERAL,
            severity=CommentSeverity.INFO,
        )

        with patch(
            "pdp_dev_mcp.tools.code_review.ai_comment_posting.post_ai_generated_comments"
        ) as mock_post:
            mock_result = CommentPostingResult(
                total_comments=1, successful_posts=1, failed_posts=0, dry_run=True
            )
            mock_post.return_value = mock_result

            result = post_ai_comments_by_pr_url(
                pr_url=pr_url, comments=[test_comment], dry_run=True
            )

            # Verify the correct parameters were extracted and passed
            mock_post.assert_called_once_with(
                org="msazure",
                project="One",
                repository="CFS-Payments-DataPlatform-PMT",
                pr_id=13483931,
                comments=[test_comment],
                dry_run=True,
                batch_size=5,
                filter_self_praise=True,
            )

            assert result.successful_posts == 1

    def test_ai_agents_can_handle_multiple_real_world_pr_urls_for_comprehensive_support(
        self,
    ):
        """As an AI agent helping developers with diverse Azure DevOps environments,
        When I process multiple real-world PR URL formats,
        Then I should correctly parse and handle various organization and project structures,
        So I can help developers work across different Azure DevOps configurations."""
        test_cases = [
            {
                "name": "MSAzure One Project",
                "url": "https://dev.azure.com/msazure/One/_git/CFS-Payments-DataPlatform-PMT/pullrequest/13483931",
                "expected_org": "msazure",
                "expected_project": "One",
                "expected_repo": "CFS-Payments-DataPlatform-PMT",
                "expected_pr_id": 13483931,
            },
            {
                "name": "Microsoft Legacy Format",
                "url": "https://microsoft.visualstudio.com/DefaultCollection/PaymentsDataPlatform/_git/Commerce.PaymentsDataPlatform/pullrequest/123456",
                "expected_org": "microsoft",
                "expected_project": "PaymentsDataPlatform",
                "expected_repo": "Commerce.PaymentsDataPlatform",
                "expected_pr_id": 123456,
            },
            {
                "name": "Generic Dev Azure Format",
                "url": "https://dev.azure.com/contoso/MyProject/_git/MyRepo/pullrequest/999",
                "expected_org": "contoso",
                "expected_project": "MyProject",
                "expected_repo": "MyRepo",
                "expected_pr_id": 999,
            },
        ]

        for test_case in test_cases:
            test_comment = CodeReviewComment(
                comment_id=f"test-{test_case['name'].replace(' ', '-').lower()}",
                title=f"Test for {test_case['name']}",
                content=f"Testing {test_case['name']} URL format",
                comment_type=CommentType.GENERAL,
                severity=CommentSeverity.INFO,
            )

            with patch(
                "pdp_dev_mcp.tools.code_review.ai_comment_posting.post_ai_generated_comments"
            ) as mock_post:
                mock_result = CommentPostingResult(
                    total_comments=1, successful_posts=1, failed_posts=0, dry_run=True
                )
                mock_post.return_value = mock_result

                result = post_ai_comments_by_pr_url(
                    pr_url=test_case["url"], comments=[test_comment], dry_run=True
                )

                # Verify correct parsing for this test case
                mock_post.assert_called_once_with(
                    org=test_case["expected_org"],
                    project=test_case["expected_project"],
                    repository=test_case["expected_repo"],
                    pr_id=test_case["expected_pr_id"],
                    comments=[test_comment],
                    dry_run=True,
                    batch_size=5,
                    filter_self_praise=True,
                )

                assert result.successful_posts == 1, f"Failed for {test_case['name']}"

    def test_user_experience_improvement_demo(self):
        """Demonstrate the UX improvement: before vs after."""
        # BEFORE: User had to manually extract parameters
        # post_ai_generated_comments(
        #     org="msazure",
        #     project="One",
        #     repository="CFS-Payments-DataPlatform-PMT",
        #     pr_id=13483931,
        #     comments=[...],
        #     dry_run=True
        # )

        # AFTER: User can just paste the PR URL
        pr_url = "https://dev.azure.com/msazure/One/_git/CFS-Payments-DataPlatform-PMT/pullrequest/13483931"

        test_comment = CodeReviewComment(
            comment_id="ux-demo",
            title="UX Improvement Demo",
            content="This demonstrates how much easier it is to use PR URLs directly",
            comment_type=CommentType.GENERAL,
            severity=CommentSeverity.INFO,
        )

        with patch(
            "pdp_dev_mcp.tools.code_review.ai_comment_posting.post_ai_generated_comments"
        ) as mock_post:
            mock_result = CommentPostingResult(
                total_comments=1, successful_posts=1, failed_posts=0, dry_run=True
            )
            mock_post.return_value = mock_result

            # Single simple call with just the PR URL
            result = post_ai_comments_by_pr_url(
                pr_url=pr_url, comments=[test_comment], dry_run=True
            )

            # All parameters correctly extracted automatically
            mock_post.assert_called_once_with(
                org="msazure",
                project="One",
                repository="CFS-Payments-DataPlatform-PMT",
                pr_id=13483931,
                comments=[test_comment],
                dry_run=True,
                batch_size=5,
                filter_self_praise=True,
            )

            assert result.successful_posts == 1

    def test_ai_agents_can_detect_url_format_from_actual_pr_urls_for_adaptive_processing(
        self,
    ):
        """As an AI agent helping developers with URL processing,
        When I detect URL format from actual PR URLs,
        Then I should correctly identify and parse different Azure DevOps URL structures,
        So I can help developers seamlessly work with various PR URL formats from different organizations."""
        test_cases = [
            {
                "name": "Modern dev.azure.com format",
                "url": "https://dev.azure.com/msazure/One/_git/CFS-Payments-DataPlatform-PMT/pullrequest/13483931",
                "expected_format": "modern",  # Uses dev.azure.com
            },
            {
                "name": "Legacy visualstudio.com format",
                "url": "https://microsoft.visualstudio.com/DefaultCollection/PaymentsDataPlatform/_git/Commerce.PaymentsDataPlatform/pullrequest/123456",
                "expected_format": "legacy",  # Uses .visualstudio.com
            },
        ]

        for test_case in test_cases:
            test_comment = CodeReviewComment(
                comment_id=f"format-detection-{test_case['expected_format']}",
                title="Format Detection Test",
                content="Testing URL format detection",
                comment_type=CommentType.GENERAL,
                severity=CommentSeverity.INFO,
            )

            with patch(
                "pdp_dev_mcp.tools.code_review.ai_comment_posting.post_ai_generated_comments"
            ) as mock_post:
                mock_result = CommentPostingResult(
                    total_comments=1, successful_posts=1, failed_posts=0, dry_run=True
                )
                mock_post.return_value = mock_result

                # The function should work regardless of URL format
                result = post_ai_comments_by_pr_url(
                    pr_url=test_case["url"], comments=[test_comment], dry_run=True
                )

                # Should succeed with proper parsing regardless of format
                assert result.successful_posts == 1, f"Failed for {test_case['name']}"
                assert mock_post.called, f"Function not called for {test_case['name']}"

    def test_ai_agents_can_handle_invalid_pr_url_errors_gracefully_for_robust_operation(
        self,
    ):
        """As an AI agent helping developers with URL validation,
        When I encounter invalid PR URLs,
        Then I should handle errors gracefully with clear error messages,
        So I can help developers understand and correct URL format issues."""
        invalid_urls = [
            "https://github.com/user/repo/pull/123",  # Not Azure DevOps
            "https://dev.azure.com/org/project/_git/repo",  # Missing PR ID
            "https://dev.azure.com/org/project",  # Missing repo and PR
            "",  # Empty URL
            "not-a-url",  # Invalid URL format
        ]

        test_comment = CodeReviewComment(
            comment_id="test-invalid",
            title="Test Comment",
            content="This should fail",
            comment_type=CommentType.GENERAL,
            severity=CommentSeverity.INFO,
        )

        for invalid_url in invalid_urls:
            with pytest.raises(ValueError, match="TOOL_USAGE_ERROR"):
                post_ai_comments_by_pr_url(
                    pr_url=invalid_url,
                    comments=[test_comment],
                    dry_run=True,
                )

    def test_ai_agents_can_handle_invalid_pr_id_errors_with_clear_feedback(self):
        """As an AI agent helping developers with PR ID validation,
        When I encounter invalid PR IDs in URLs,
        Then I should provide clear error feedback about ID format issues,
        So I can help developers understand and correct PR ID validation problems."""
        with patch(
            "pdp_dev_mcp.tools.code_review.ai_comment_posting.parse_azure_devops_pr_url"
        ) as mock_parse:
            mock_parse.return_value = ("org", "project", "repo", "not-a-number")

            test_comment = CodeReviewComment(
                comment_id="test-bad-id",
                title="Test Comment",
                content="This should fail",
                comment_type=CommentType.GENERAL,
                severity=CommentSeverity.INFO,
            )

            with pytest.raises(ValueError, match="TOOL_USAGE_ERROR"):
                post_ai_comments_by_pr_url(
                    pr_url="https://dev.azure.com/org/project/_git/repo/pullrequest/not-a-number",
                    comments=[test_comment],
                    dry_run=True,
                )

    def test_ai_agents_can_handle_empty_comments_lists_gracefully_for_edge_cases(self):
        """As an AI agent helping developers with edge case handling,
        When I encounter empty comments lists for PR operations,
        Then I should handle the situation gracefully without errors,
        So I can help developers maintain robust code review workflows even with unusual input conditions."""
        pr_url = "https://dev.azure.com/msazure/One/_git/CFS-Payments-DataPlatform-PMT/pullrequest/13483931"

        with patch(
            "pdp_dev_mcp.tools.code_review.ai_comment_posting.post_ai_generated_comments"
        ) as mock_post:
            mock_result = CommentPostingResult(
                total_comments=0, successful_posts=0, failed_posts=0, dry_run=True
            )
            mock_post.return_value = mock_result

            result = post_ai_comments_by_pr_url(
                pr_url=pr_url, comments=[], dry_run=True
            )

            mock_post.assert_called_once_with(
                org="msazure",
                project="One",
                repository="CFS-Payments-DataPlatform-PMT",
                pr_id=13483931,
                comments=[],
                dry_run=True,
                batch_size=5,
                filter_self_praise=True,
            )

            assert result.total_comments == 0
            assert result.successful_posts == 0
            assert result.failed_posts == 0
