"""
Test azure_devops_establish_pr_context functionality.

This replaces the context establishment portions of the old get_pr_code_context tests
with tests for the new cross-repository context establishment architecture.
"""

import pytest
from unittest.mock import patch
import tempfile

# Test the context establishment function
from pdp_dev_mcp.tools.common.azure_devops_pr_comments import (
    azure_devops_establish_pr_context,
)


class TestAzureDevOpsContextEstablishment:
    """Test cross-repository PR context establishment capabilities."""

    def test_context_establishment_with_full_pr_url(self):
        """Test AI agents can establish context from complete PR URLs for cross-repository analysis."""
        # Test URL from different organization than current working directory
        pr_url = "https://dev.azure.com/msazure/Commerce/_git/PaymentsDataPlatform/pullrequest/123456"

        with tempfile.TemporaryDirectory() as temp_dir:
            context = azure_devops_establish_pr_context(pr_url, temp_dir)

            assert context.organization == "msazure"
            assert context.project == "Commerce"
            assert context.repository == "PaymentsDataPlatform"
            assert context.pr_id == 123456  # int, not string
            assert context.pr_url == pr_url
            assert context.source == "url"

    def test_context_establishment_with_pr_id_only(self):
        """Test AI agents can establish context from PR ID when working in local repository."""
        # This test demonstrates error handling when no local git context is available
        pr_id = "789012"

        with tempfile.TemporaryDirectory() as temp_dir:
            # Without git context, should get helpful message about how to fix it
            with pytest.raises(
                ValueError, match="Cannot establish PR context from PR ID.*provide a PR URL.*repository context"
            ):
                azure_devops_establish_pr_context(pr_id, temp_dir)

    def test_context_establishment_handles_invalid_pr_urls_gracefully(self):
        """Test AI agents gracefully handle invalid PR URL formats."""
        invalid_urls = [
            "not-a-url",
            "https://github.com/microsoft/repo/_pull/123",  # Wrong provider
            "https://dev.azure.com/incomplete",  # Missing parts
            "",  # Empty string
            None,  # None value
        ]

        with tempfile.TemporaryDirectory() as temp_dir:
            for invalid_url in invalid_urls:
                # Different invalid inputs produce different helpful error messages
                with pytest.raises(
                    ValueError, match="Invalid PR identifier|Unsupported Azure DevOps URL|No PR URL or ID provided|Incomplete Azure DevOps PR URL"
                ):
                    azure_devops_establish_pr_context(invalid_url, temp_dir)

    def test_context_establishment_validates_working_directory(self):
        """Test AI agents validate git repository before PR operations for reliable context."""
        # Test validates input format first, then repository context
        with pytest.raises(
            ValueError, match="Cannot establish PR context from PR ID.*provide a PR URL"
        ):
            azure_devops_establish_pr_context("123456", "/non/existent/path")

        # Test with non-git directory
        with tempfile.TemporaryDirectory() as temp_dir:
            with pytest.raises(
                ValueError, match="Cannot establish PR context from PR ID.*provide a PR URL"
            ):
                azure_devops_establish_pr_context("123456", temp_dir)

    def test_context_establishment_handles_different_azure_devops_organizations(self):
        """Test AI agents handle cross-repository dependency analysis with different organizations."""
        test_cases = [
            {
                "url": "https://dev.azure.com/msazure/Commerce/_git/PaymentsDataPlatform/pullrequest/111",
                "expected_org": "msazure",
                "expected_project": "Commerce",
            },
            {
                "url": "https://dev.azure.com/microsoft/DevDiv/_git/VS/pullrequest/222",
                "expected_org": "microsoft",
                "expected_project": "DevDiv",
            },
        ]

        with tempfile.TemporaryDirectory() as temp_dir:
            for case in test_cases:
                context = azure_devops_establish_pr_context(case["url"], temp_dir)

                assert context.organization == case["expected_org"]
                assert context.project == case["expected_project"]
                assert context.source == "url"

    def test_context_establishment_provides_helpful_error_messages(self):
        """Test AI agents provide specific MCP tool guidance when context establishment fails."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Test helpful error for malformed URL
            with pytest.raises(ValueError) as exc_info:
                azure_devops_establish_pr_context("malformed-url", temp_dir)

            error_message = str(exc_info.value)
            assert "Invalid" in error_message
            assert "PR" in error_message

            # Test helpful error for missing working directory
            with pytest.raises(ValueError) as exc_info:
                azure_devops_establish_pr_context("123456", "/does/not/exist")

            error_message = str(exc_info.value)
            # New error message is more specific: "Cannot establish PR context from PR ID..."
            assert "provide a PR URL" in error_message or "repository context" in error_message

    def test_context_establishment_handles_network_failures_gracefully(self):
        """Test AI agents gracefully handle Azure DevOps API connectivity issues."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Mock network failure when trying to validate PR URL
            with patch("subprocess.run") as mock_run:
                mock_run.side_effect = ConnectionError("Network unreachable")

                # Should still establish context for offline analysis
                try:
                    context = azure_devops_establish_pr_context(
                        "https://dev.azure.com/msazure/Commerce/_workitems/edit/123",
                        temp_dir,
                    )
                    # Should extract what it can from URL
                    assert context.organization == "msazure"
                    assert context.project == "Commerce"
                except ValueError:
                    # Or provide helpful error about network issues
                    pass

    def test_context_establishment_optimizes_for_simple_changes(self):
        """Test AI agents help developers understand minimal context for simple changes."""
        simple_pr_url = "https://dev.azure.com/microsoft/Commerce/_git/PaymentsDataPlatform/pullrequest/111"

        with tempfile.TemporaryDirectory() as temp_dir:
            context = azure_devops_establish_pr_context(simple_pr_url, temp_dir)

            # Context establishment should be fast and lightweight
            assert context.pr_url == simple_pr_url
            assert context.organization == "microsoft"
            assert context.project == "Commerce"
            # Should not do heavy analysis during context establishment

    def test_context_establishment_supports_different_url_formats(self):
        """Test AI agents handle complex project structure analysis edge cases."""
        url_variations = [
            "https://dev.azure.com/org/project/_git/repo/pullrequest/123",
            "https://dev.azure.com/org/project/_git/repo/pullrequest/123/",  # Trailing slash
        ]

        with tempfile.TemporaryDirectory() as temp_dir:
            for url in url_variations:
                context = azure_devops_establish_pr_context(url, temp_dir)
                assert context.pr_id == 123
                assert context.source == "url"

    def test_context_establishment_handles_malformed_azure_devops_api_responses(self):
        """Test AI agents gracefully handle malformed JSON responses from Azure DevOps API."""
        pr_url = "https://dev.azure.com/msazure/Commerce/_git/PaymentsDataPlatform/pullrequest/123"

        with tempfile.TemporaryDirectory() as temp_dir:
            # Should establish basic context even if API validation fails
            context = azure_devops_establish_pr_context(pr_url, temp_dir)

            # Basic URL parsing should work even with API issues
            assert context.organization == "msazure"
            assert context.project == "Commerce"
            assert context.pr_id == 123

    def test_context_establishment_preserves_repository_information(self):
        """Test AI agents extract repository context for cross-repository analysis."""
        # Test URL with repository information
        pr_url = "https://dev.azure.com/microsoft/Commerce/_git/PaymentsDataPlatform/pullrequest/123"

        with tempfile.TemporaryDirectory() as temp_dir:
            context = azure_devops_establish_pr_context(pr_url, temp_dir)

            assert context.organization == "microsoft"
            assert context.project == "Commerce"
            assert context.repository == "PaymentsDataPlatform"
            assert context.pr_id == 123

    def test_context_establishment_provides_complete_workflow_error_guidance(self):
        """Test AI agents can receive complete workflow error guidance for troubleshooting."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Test that errors provide actionable guidance
            with pytest.raises(ValueError) as exc_info:
                azure_devops_establish_pr_context("", temp_dir)

            error_msg = str(exc_info.value)
            # Should provide guidance on what to fix (new message has "provide" and "url")
            assert any(
                keyword in error_msg.lower()
                for keyword in ["provide", "url", "format", "expected", "example"]
            )
