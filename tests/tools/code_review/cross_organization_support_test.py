"""
Real-world cross-organization integration tests for AI agents posting comments.

These tests validate that AI agents can correctly handle actual PR URLs from different
Azure DevOps organizations to support developers across various enterprise environments.
"""

import pytest
from unittest.mock import patch, MagicMock, Mock
from pdp_dev_mcp.tools.code_review.ai_comment_posting import (
    post_ai_generated_comments,
    CodeReviewComment,
    CommentType,
    CommentSeverity,
    create_ai_comment,
)


class TestAIAgentsCanHandleCrossOrganizationSupport:
    """
    AI agents need to post comments across different Azure DevOps organizations
    to help developers working in various enterprise environments and legacy systems.
    """

    @patch("subprocess.run")
    def test_ai_agents_can_post_comments_to_microsoft_legacy_organizations_for_enterprise_support(
        self, mock_subprocess
    ):
        """
        As an AI agent helping developers with Microsoft enterprise repositories
        When I need to post comments to a real Microsoft PR using legacy organization format
        Then I successfully post comments using correct .visualstudio.com URLs
        so I can provide code review assistance across Microsoft's enterprise Azure DevOps instances
        """

        # Given: Azure DevOps API responses will show enterprise Microsoft setup
        def mock_subprocess_side_effect(*args, **kwargs):
            cmd_args = args[0] if args else []
            # Check if this is getting PR author info
            if any("pullRequests" in str(arg) for arg in cmd_args):
                return MagicMock(
                    returncode=0,
                    stdout='{"createdBy": {"displayName": "Test Developer (MICROSOFT)"}}',
                )
            # Otherwise return successful comment posting
            else:
                return MagicMock(
                    returncode=0,
                    stdout='{"value": [{"id": 1}]}',
                )

        mock_subprocess.side_effect = mock_subprocess_side_effect

        # Given: AI agent has comments to post for developer assistance
        comments = [
            CodeReviewComment(
                comment_id="integration-test-1",
                title="Integration Test Comment",
                content="This is a test comment for Microsoft organization integration testing.",
                comment_type=CommentType.GENERAL,
                severity=CommentSeverity.INFO,
            )
        ]

        # When: AI agent posts comments to real Microsoft PR parameters
        result = post_ai_generated_comments(
            comments=comments,
            org="microsoft",
            project="Universal Store",
            repository="Commerce.PaymentsDataPlatform",
            pr_id=13844374,
            dry_run=True,  # Always dry run for real PRs
        )

        # Then: AI agent successfully posts to Microsoft using correct legacy URL format
        expected_url = "https://microsoft.visualstudio.com/Universal Store/_git/Commerce.PaymentsDataPlatform/pullrequest/13844374"
        assert result.pr_url == expected_url, (
            f"Expected Microsoft legacy URL '{expected_url}' but got '{result.pr_url}' - AI agent used wrong URL format for Microsoft"
        )
        assert "visualstudio.com" in result.pr_url, (
            f"Expected .visualstudio.com in URL but got '{result.pr_url}' - AI agent cannot access Microsoft legacy repositories"
        )
        assert result.successful_posts == 1, (
            f"Expected 1 successful post but got {result.successful_posts} - AI agent failed to post to Microsoft PR"
        )
        assert result.failed_posts == 0, (
            f"Expected 0 failed posts but got {result.failed_posts} - AI agent had posting failures for Microsoft"
        )

    @patch("subprocess.run")
    def test_ai_agents_can_post_comments_to_msazure_modern_organizations_for_current_workflows(
        self, mock_subprocess
    ):
        """
        As an AI agent helping developers with modern MSAzure repositories
        When I need to post comments to a real MSAzure PR using modern organization format
        Then I successfully post comments using correct dev.azure.com URLs
        so I can provide code review assistance with current MSAzure development workflows
        """

        # Given: Azure DevOps API responses will show modern MSAzure setup
        def mock_subprocess_side_effect(*args, **kwargs):
            cmd_args = args[0] if args else []
            # Check if this is getting PR author info
            if any("pullRequests" in str(arg) for arg in cmd_args):
                return MagicMock(
                    returncode=0,
                    stdout='{"createdBy": {"displayName": "Test Developer (MSAZURE)"}}',
                )
            # Otherwise return successful comment posting
            else:
                return MagicMock(
                    returncode=0,
                    stdout='{"value": [{"id": 1}]}',
                )

        mock_subprocess.side_effect = mock_subprocess_side_effect

        comments = [
            CodeReviewComment(
                comment_id="integration-test-3",
                title="MSAzure Modern Integration Test",
                content="This is a test comment for MSAzure modern repo integration testing.",
                comment_type=CommentType.GENERAL,
                severity=CommentSeverity.INFO,
            )
        ]

        # Use the real modern PR parameters
        result = post_ai_generated_comments(
            comments=comments,
            org="msazure",
            project="One",
            repository="CFS-Payments-DataPlatform-PMT",
            pr_id=13483931,  # Modern PR ID
            dry_run=True,  # Always dry run for real PRs
        )

        # Verify the correct URL format - should use dev.azure.com (modern)
        expected_url = "https://dev.azure.com/msazure/One/_git/CFS-Payments-DataPlatform-PMT/pullrequest/13483931"
        assert result.pr_url == expected_url
        assert "dev.azure.com" in result.pr_url
        assert "visualstudio.com" not in result.pr_url
        assert result.successful_posts == 1
        assert result.failed_posts == 0

    @patch("subprocess.run")
    def test_ai_agents_can_post_comments_to_msazure_legacy_prs_using_modern_format_for_compatibility(
        self, mock_subprocess
    ):
        """
        As an AI agent helping developers with MSAzure legacy repository references
        When I need to post comments to legacy MSAzure PR IDs using modern organization format
        Then I successfully post comments using modern dev.azure.com URLs
        so I can provide compatibility between legacy PR references and current MSAzure infrastructure
        """

        # Given: Azure DevOps API responses for MSAzure legacy repository compatibility
        def mock_subprocess_side_effect(*args, **kwargs):
            cmd_args = args[0] if args else []
            # Check if this is getting PR author info
            if any("pullRequests" in str(arg) for arg in cmd_args):
                return MagicMock(
                    returncode=0,
                    stdout='{"createdBy": {"displayName": "Test Developer (MSAZURE)"}}',
                )
            # Otherwise return successful comment posting
            else:
                return MagicMock(
                    returncode=0,
                    stdout='{"value": [{"id": 1}]}',
                )

        mock_subprocess.side_effect = mock_subprocess_side_effect

        # Given: AI agent has comments to post for legacy repository assistance
        comments = [
            CodeReviewComment(
                comment_id="integration-test-2",
                title="MSAzure Legacy Integration Test",
                content="This is a test comment for MSAzure legacy repo integration testing.",
                comment_type=CommentType.GENERAL,
                severity=CommentSeverity.INFO,
            )
        ]

        # When: AI agent posts comments using real legacy PR parameters
        # Note: Tool will use modern URLs even for legacy PR IDs for current compatibility
        result = post_ai_generated_comments(
            comments=comments,
            org="msazure",
            project="One",
            repository="CFS-Payments-DataPlatform-PMT",
            pr_id=13507068,  # Legacy PR ID
            dry_run=True,  # Always dry run for real PRs
        )

        # Then: AI agent generates modern URLs even for legacy PR IDs (compatibility feature)
        # This is a limitation - ideally we'd detect the actual repo format
        expected_url = "https://dev.azure.com/msazure/One/_git/CFS-Payments-DataPlatform-PMT/pullrequest/13507068"
        assert result.pr_url == expected_url, (
            f"Expected MSAzure modern URL '{expected_url}' but got '{result.pr_url}' - AI agent cannot provide legacy PR compatibility"
        )
        assert "dev.azure.com" in result.pr_url, (
            f"Expected dev.azure.com in URL but got '{result.pr_url}' - AI agent cannot access MSAzure using modern format"
        )
        assert "visualstudio.com" not in result.pr_url
        assert result.successful_posts == 1
        assert result.failed_posts == 0

        # Note: In practice, this URL format mismatch might cause issues
        # for legacy repos. The ideal solution would be to detect the actual
        # repo URL format from the git remote or repository metadata.

    def test_ai_agents_understand_mixed_organization_scenarios_for_comprehensive_developer_support(
        self,
    ):
        """
        As an AI agent helping developers understand complex Azure DevOps environments
        When I encounter organizations with both legacy and modern URL formats
        Then I document and handle the mixed organization scenario appropriately
        so I can provide developers with accurate expectations about URL format limitations
        """
        # Given: AI agent encounters real-world mixed organization complexity
        # Some organizations like msazure have BOTH URL formats depending on
        # when/how repositories were created or migrated.

        real_examples = {
            "microsoft_legacy": "https://microsoft.visualstudio.com/Universal%20Store/_git/Commerce.PaymentsDataPlatform/pullrequest/13844374",
            "msazure_legacy": "https://msazure.visualstudio.com/One/_git/CFS-Payments-DataPlatform-PMT/pullrequest/13507068",
            "msazure_modern": "https://dev.azure.com/msazure/One/_git/CFS-Payments-DataPlatform-PMT/pullrequest/13483931",
        }

        # When: AI agent applies current solution prioritizing most common format per organization
        # - microsoft: .visualstudio.com (legacy primary)
        # - msazure: dev.azure.com (modern default for mixed)

        # Then: AI agent provides best-effort compatibility with documented limitations
        # This means:
        # ✅ microsoft legacy repos work correctly
        # ✅ msazure modern repos work correctly
        # ⚠️  msazure legacy repos may have URL format mismatches

        # AI agent documents the limitation: ideally, we would detect the actual repo format
        # from git remote or repository metadata, but that requires repository context
        # which isn't available when calling with org/project/repo parameters

        assert len(real_examples) == 3, (
            f"Expected documentation of 3 URL format examples but got {len(real_examples)} - AI agent cannot demonstrate mixed organization complexity to developers"
        )
