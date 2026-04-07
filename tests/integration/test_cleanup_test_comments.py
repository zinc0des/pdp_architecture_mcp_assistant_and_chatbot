"""
Unit tests for the test comment cleanup functionality.
"""

import pytest
from unittest.mock import Mock, patch

from .cleanup_test_comments import (
    TestCommentCleanupConfig,
    TestCommentCleaner,
    cleanup_integration_test_comments,
)

# Test constants
TEST_PR_ID = 123
TEST_THREAD_ID = 456
TEST_ORG = "test-org"
TEST_PROJECT = "test-project"
TEST_REPO = "test-repo"


class TestTestCommentCleanupConfig:
    """Test configuration for Azure DevOps integration test comment cleanup"""

    def test_developers_can_configure_test_comment_cleanup_with_default_patterns(self):
        """
        As a developer setting up integration tests
        When I create a cleanup configuration without specifying patterns
        Then I should get a comprehensive set of default patterns that identify test comments
        So that integration tests can automatically clean up their artifacts
        """
        # Given: A developer creates a cleanup configuration without custom patterns
        config = TestCommentCleanupConfig(
            org=TEST_ORG, project=TEST_PROJECT, repository=TEST_REPO, pr_id=TEST_PR_ID
        )

        # Then: Configuration should include comprehensive default patterns
        assert config.test_comment_patterns is not None, (
            "Default patterns should be automatically initialized"
        )
        assert len(config.test_comment_patterns) > 0, (
            "At least one default pattern should be provided"
        )

        # And: Should include key integration test markers
        expected_patterns = [
            "🧪 **INTEGRATION TEST**",
            "🔬 **MCP Tool Test**",
            "*Test ID:",
        ]
        for pattern in expected_patterns:
            assert pattern in config.test_comment_patterns, (
                f"Expected pattern '{pattern}' should be in default patterns. "
                f"Available patterns: {config.test_comment_patterns}"
            )

    def test_developers_can_override_default_patterns_for_custom_testing_scenarios(
        self,
    ):
        """
        As a developer with specific testing requirements
        When I provide custom test comment patterns during configuration
        Then the system should use my patterns instead of defaults
        So that I can customize cleanup behavior for specialized test scenarios
        """
        # Given: Developer defines custom patterns for their specific test scenario
        custom_patterns = ["custom-pattern", "another-pattern"]

        # When: Creating configuration with custom patterns
        config = TestCommentCleanupConfig(
            org=TEST_ORG,
            project=TEST_PROJECT,
            repository=TEST_REPO,
            pr_id=TEST_PR_ID,
            test_comment_patterns=custom_patterns,
        )

        # Then: Configuration should use exactly the custom patterns provided
        assert config.test_comment_patterns == custom_patterns, (
            f"Expected custom patterns {custom_patterns} but got {config.test_comment_patterns}"
        )


class TestTestCommentCleaner:
    """Test cleanup functionality for Azure DevOps integration test comments"""

    def setup_method(self):
        """Set up test fixtures for comment cleanup testing"""
        self.config = TestCommentCleanupConfig(
            org=TEST_ORG,
            project=TEST_PROJECT,
            repository=TEST_REPO,
            pr_id=TEST_PR_ID,
            dry_run=True,  # Default to dry run for safety
        )
        self.cleaner = TestCommentCleaner(self.config)

    def test_integration_test_developers_can_identify_their_test_comments_for_cleanup(
        self,
    ):
        """
        As an integration test developer
        When I post comments with standard integration test markers
        Then the cleanup system should correctly identify them as test comments
        So that automated cleanup can remove them after test completion
        """
        # Given: A comment thread containing an integration test marker
        comment_thread = {
            "comments": [
                {
                    "content": f"🧪 **INTEGRATION TEST** - Test Comment\n\nThis is a test comment.\n\n*Test ID: test-{TEST_PR_ID}*"
                }
            ]
        }

        # When: Checking if the comment is a test comment
        is_test_comment = self.cleaner.is_test_comment(comment_thread)

        # Then: System should correctly identify it as a test comment
        assert is_test_comment is True, (
            "Integration test comments with standard markers should be identified for cleanup"
        )

    def test_mcp_tool_developers_can_identify_their_test_comments_for_cleanup(self):
        """
        As an MCP tool developer testing comment functionality
        When I post comments with MCP-specific test markers
        Then the cleanup system should identify them as test comments
        So that MCP integration tests don't clutter PR discussions
        """
        # Given: A comment thread containing an MCP test marker
        comment_thread = {
            "comments": [
                {"content": "🔬 **MCP Tool Test**\n\nThis is an MCP test comment."}
            ]
        }

        # When: Checking if the comment is a test comment
        is_test_comment = self.cleaner.is_test_comment(comment_thread)

        # Then: System should correctly identify it as a test comment
        assert is_test_comment is True, (
            "MCP tool test comments should be identified for automatic cleanup"
        )

    def test_code_reviewers_have_their_regular_comments_preserved_during_cleanup(self):
        """
        As a code reviewer providing legitimate feedback
        When I post normal code review comments without test markers
        Then the cleanup system should not identify them as test comments
        So that real review feedback is never accidentally removed
        """
        # Given: A regular code review comment without test markers
        comment_thread = {
            "comments": [
                {
                    "content": "This is a regular code review comment about the implementation."
                }
            ]
        }

        # When: Checking if the comment is a test comment
        is_test_comment = self.cleaner.is_test_comment(comment_thread)

        # Then: System should correctly preserve regular comments
        assert is_test_comment is False, (
            "Regular code review comments should never be identified as test comments to prevent accidental deletion"
        )

    def test_system_administrators_get_robust_handling_of_empty_comment_threads(self):
        """
        As a system administrator managing Azure DevOps integration
        When the system encounters empty or malformed comment threads
        Then the cleanup system should handle them gracefully without errors
        So that edge cases don't break the automated cleanup process
        """
        # Given: Various edge cases of empty comment data
        test_cases = [
            {"comments": []},  # Empty comments array
            {},  # Missing comments key entirely
        ]

        for case_index, comment_thread in enumerate(test_cases):
            # When: Checking if empty thread is a test comment
            is_test_comment = self.cleaner.is_test_comment(comment_thread)

            # Then: System should handle gracefully without errors
            assert is_test_comment is False, (
                f"Empty comment thread case {case_index + 1} should return False safely: {comment_thread}"
            )

    def test_developers_get_case_insensitive_pattern_matching_for_flexibility(self):
        """
        As a developer writing integration tests
        When I use test markers with different capitalization
        Then the cleanup system should still identify them correctly
        So that minor formatting variations don't prevent proper cleanup
        """
        # Given: A comment with mixed-case test pattern
        comment_thread = {
            "comments": [{"content": "this comment contains INTEGRATION-TEST tag"}]
        }

        # When: Checking pattern matching with case variations
        is_test_comment = self.cleaner.is_test_comment(comment_thread)

        # Then: System should identify test patterns regardless of case
        assert is_test_comment is True, (
            "Test pattern matching should be case-insensitive to handle formatting variations"
        )

    @patch("subprocess.run")
    def test_system_administrators_can_perform_complete_cleanup_operations(
        self, mock_subprocess
    ):
        """
        As a system administrator managing test environment hygiene
        When I execute a complete test comment cleanup operation
        Then all test comments should be identified and removed successfully
        So that the PR remains clean for subsequent testing cycles
        """
        # Given: Azure DevOps API returns no test comments (simplest successful case)
        mock_subprocess.return_value = Mock(
            returncode=0,
            stdout='{"value": []}',  # No comments found
        )

        # When: Executing complete cleanup operation
        result = self.cleaner.cleanup_test_comments()

        # Then: Should successfully complete cleanup even with no test comments
        assert result["success"] is True, (
            "Complete cleanup operation should succeed when API calls are successful"
        )
        assert result["resolved_count"] == 0, (
            "Should report zero resolved comments when no test comments exist"
        )
        assert result["failed_count"] == 0, (
            "No failed deletions should be reported for successful cleanup operations"
        )
        assert mock_subprocess.call_count == 1, (
            "Should make exactly one API call to list comments when no test comments exist"
        )

    @patch("subprocess.run")
    def test_azure_devops_integrators_handle_api_authentication_failures_gracefully(
        self, mock_run
    ):
        """
        As an Azure DevOps integrator managing authentication issues
        When the Azure REST API returns authentication failures
        Then the system should handle the error gracefully and return empty results
        So that cleanup operations don't crash when credentials are invalid
        """
        # Given: Azure DevOps API returns authentication failure
        mock_run.return_value = Mock(returncode=1, stderr="Authentication failed")

        # When: Attempting to retrieve comments with invalid credentials
        comments = self.cleaner.get_all_comments()

        # Then: Should return empty list gracefully without crashing
        assert comments == [], (
            f"Expected empty list for authentication failure but got {comments}"
        )

    @patch("subprocess.run")
    def test_developers_get_safe_dry_run_mode_to_preview_cleanup_operations(
        self, mock_run
    ):
        """
        As a developer testing comment cleanup functionality
        When I run cleanup operations in dry-run mode
        Then no actual API calls should be made to Azure DevOps
        So that I can safely test cleanup logic without affecting real PR comments
        """
        # Given: Cleanup system configured for dry-run mode (default in setup)

        # When: Attempting to delete a comment thread in dry-run mode
        result = self.cleaner.delete_comment_thread(TEST_THREAD_ID)

        # Then: Should succeed without making any API calls
        assert result is True, (
            "Dry-run mode should always return success without actual operations"
        )
        mock_run.assert_not_called()  # Dry-run mode should not make API calls

    @patch("subprocess.run")
    def test_azure_devops_integrators_can_delete_comment_threads_when_authorized(
        self, mock_run
    ):
        """
        As an Azure DevOps integrator with proper permissions
        When I delete comment threads through the Azure REST API
        Then the deletion should succeed and return confirmation
        So that automated cleanup can remove test comments from PRs
        """
        # Given: System configured for actual operations (not dry-run)
        self.config.dry_run = False

        # And: Azure DevOps API will return successful deletion
        mock_run.return_value = Mock(returncode=0, stdout='{"value": []}')

        # When: Deleting a comment thread
        result = self.cleaner.delete_comment_thread(TEST_THREAD_ID)

        # Then: Operation should succeed
        assert result is True, (
            "Comment thread deletion should succeed when API returns success"
        )
        assert mock_run.call_count >= 1, (
            "At least one API call should be made for thread deletion"
        )

    @patch("subprocess.run")
    def test_azure_devops_integrators_handle_deletion_failures_gracefully(
        self, mock_run
    ):
        """
        As an Azure DevOps integrator handling API failures
        When comment thread deletion fails due to permissions or network issues
        Then the system should return failure status without crashing
        So that cleanup operations can continue processing other comments
        """
        # Given: System configured for actual operations (not dry-run)
        self.config.dry_run = False

        # And: Azure DevOps API will return deletion failure
        mock_run.return_value = Mock(returncode=1)

        # When: Attempting to delete a comment thread
        result = self.cleaner.delete_comment_thread(TEST_THREAD_ID)

        # Then: Should return failure status gracefully
        assert result is False, (
            "Comment thread deletion should return False when API returns failure"
        )
        assert mock_run.call_count >= 1, (
            "At least one API call should be attempted even if it fails"
        )


class TestCleanupIntegrationTestComments:
    """Test the convenience function using black-box testing principles"""

    @patch("subprocess.run")
    def test_developers_can_use_convenience_function_for_simplified_cleanup(
        self, mock_subprocess
    ):
        """
        As a developer needing quick test comment cleanup
        When I use the convenience function with basic parameters
        Then I get proper cleanup results without managing configuration objects
        So that I can clean up test comments with minimal code
        """
        # Given: Azure DevOps API returns no test comments (successful empty case)
        mock_subprocess.return_value = Mock(returncode=0, stdout='{"value": []}')

        # When: Developer uses convenience function for cleanup
        result = cleanup_integration_test_comments(
            org=TEST_ORG,
            project=TEST_PROJECT,
            repository=TEST_REPO,
            pr_id=TEST_PR_ID,
            dry_run=True,
            additional_patterns=["custom-pattern"],
        )

        # Then: Should return successful cleanup results
        assert result["success"] is True, (
            "Convenience function should provide successful cleanup results"
        )
        assert result["resolved_count"] == 0, (
            "Should correctly report zero resolved comments when no test comments exist"
        )
        assert result["failed_count"] == 0, (
            "Should report zero failures for successful empty cleanup"
        )

        # And: Should make appropriate API call to list comments
        assert mock_subprocess.call_count == 1, (
            "Should make exactly one API call to list comments"
        )


if __name__ == "__main__":
    pytest.main([__file__])


class TestSystemReliabilityAndEdgeCases:
    """Test edge cases and exception handling for reliable system operation"""

    def setup_method(self):
        """Set up test fixtures for edge case testing"""
        self.config = TestCommentCleanupConfig(
            org=TEST_ORG,
            project=TEST_PROJECT,
            repository=TEST_REPO,
            pr_id=TEST_PR_ID,
            dry_run=False,  # Test actual operations
        )
        self.cleaner = TestCommentCleaner(self.config)

    @patch("subprocess.run")
    def test_system_administrators_get_resilient_handling_of_subprocess_exceptions(
        self, mock_run
    ):
        """
        As a system administrator managing API integrations
        When subprocess operations raise unexpected exceptions during comment retrieval
        Then the system should handle them gracefully and return empty results
        So that integration failures don't crash the cleanup process
        """
        # Given: Subprocess.run raises an unexpected exception
        mock_run.side_effect = Exception("Network timeout during API call")

        # When: Attempting to get all comments with exception occurring
        comments = self.cleaner.get_all_comments()

        # Then: Should return empty list gracefully without crashing
        assert comments == [], (
            "Exception handling should return empty list when subprocess operations fail"
        )

    @patch("subprocess.run")
    def test_content_validation_systems_handle_empty_comment_content_gracefully(
        self, mock_run
    ):
        """
        As a content validation system processing comment threads
        When comment threads contain entries with missing or None content
        Then the system should skip them safely without errors
        So that malformed API responses don't break pattern matching
        """
        # Given: Comment thread with None/empty content (edge case from API)
        comment_thread = {
            "comments": [
                {"content": None},  # None content case
                {"content": ""},  # Empty string case
                {"content": "🧪 **INTEGRATION TEST**"},  # Valid test comment
            ]
        }

        # When: Checking if thread contains test comments
        is_test_comment = self.cleaner.is_test_comment(comment_thread)

        # Then: Should correctly identify test patterns despite empty content entries
        assert is_test_comment is True, (
            "System should handle None/empty content gracefully and still identify valid test patterns"
        )

    def test_deletion_command_builders_generate_proper_azure_rest_api_calls(self):
        """
        As an Azure DevOps integrator building REST API commands
        When I need to delete specific comments from threads
        Then the system should generate properly formatted Azure CLI commands
        So that comment deletion operations use correct API endpoints and parameters
        """
        # Given: Specific thread and comment IDs for deletion
        thread_id = 12345
        comment_id = 67890

        # When: Building the delete comment command
        delete_cmd = self.cleaner._build_delete_comment_command(thread_id, comment_id)

        # Then: Should generate correct Azure CLI command structure
        expected_uri_pattern = f"https://dev.azure.com/{TEST_ORG}/{TEST_PROJECT}/_apis/git/repositories/{TEST_REPO}/pullRequests/{TEST_PR_ID}/threads/{thread_id}/comments/{comment_id}?api-version=7.1"

        assert "az" in delete_cmd, "Command should use Azure CLI"
        assert "rest" in delete_cmd, "Command should use REST API interface"
        assert "--method" in delete_cmd, "Command should specify HTTP method"
        assert "DELETE" in delete_cmd, (
            "Command should use DELETE method for comment removal"
        )
        assert "--uri" in delete_cmd, "Command should specify target URI"
        assert expected_uri_pattern in delete_cmd, (
            f"Command should target correct API endpoint: {expected_uri_pattern}"
        )

    @patch("subprocess.run")
    def test_comment_deletion_workflows_handle_actual_comment_processing(
        self, mock_run
    ):
        """
        As a comment cleanup system processing real comment threads
        When I need to delete all comments from a thread that actually contains comments
        Then the system should execute the complete deletion workflow
        So that test comment threads are properly removed from PRs
        """
        # Given: System configured for actual operations (not dry-run)
        # And: Thread get operation returns actual comments to delete
        mock_get_response = Mock(
            returncode=0,
            stdout='{"value": [{"id": 1, "content": "First comment"}, {"id": 2, "content": "Second comment"}]}',
        )
        # And: Delete operations succeed
        mock_delete_response = Mock(returncode=0, stdout="{}")

        # Configure subprocess.run to return different responses based on call
        def mock_run_side_effect(cmd, **kwargs):
            if "--method" in cmd and "GET" in cmd:
                return mock_get_response
            elif "--method" in cmd and "DELETE" in cmd:
                return mock_delete_response
            else:
                return Mock(returncode=1)

        mock_run.side_effect = mock_run_side_effect

        # When: Executing thread deletion for thread with actual comments
        result = self.cleaner.delete_comment_thread(12345)

        # Then: Should successfully complete deletion workflow
        assert result is True, (
            "Thread deletion should succeed when API calls are successful"
        )

        # And: Should make appropriate API calls (1 GET + 2 DELETEs for 2 comments)
        assert mock_run.call_count == 3, (
            f"Expected 3 API calls (1 GET + 2 DELETE) but got {mock_run.call_count}"
        )

    @patch("subprocess.run")
    def test_complete_cleanup_workflows_process_discovered_test_comments(
        self, mock_run
    ):
        """
        As an integration test cleanup system
        When I discover actual test comments that need to be removed
        Then I should execute the complete cleanup workflow including deletion
        So that test artifacts are properly cleaned up from PR discussions
        """
        # Given: API returns test comments that need cleanup
        mock_comments_response = Mock(
            returncode=0,
            stdout='{"value": [{"id": 123, "comments": [{"content": "🧪 **INTEGRATION TEST** - Test comment to clean up"}]}]}',
        )

        # And: Thread get operation returns comments to delete
        mock_thread_response = Mock(
            returncode=0, stdout='{"value": [{"id": 1, "content": "Test comment"}]}'
        )

        # And: Delete operations succeed
        mock_delete_response = Mock(returncode=0, stdout="{}")

        # Configure subprocess responses based on API endpoint
        def mock_run_side_effect(cmd, **kwargs):
            if "/threads?api-version=6.0" in " ".join(cmd):
                return mock_comments_response  # List all threads
            elif (
                "/threads/" in " ".join(cmd)
                and "/comments" in " ".join(cmd)
                and "--method" in cmd
                and "GET" in cmd
            ):
                return mock_thread_response  # Get thread comments
            elif "--method" in cmd and "DELETE" in cmd:
                return mock_delete_response  # Delete comment
            else:
                return Mock(returncode=1)

        mock_run.side_effect = mock_run_side_effect

        # When: Executing complete cleanup operation
        result = self.cleaner.cleanup_test_comments()

        # Then: Should successfully process test comments for cleanup
        assert result["success"] is True, (
            "Complete cleanup should succeed when test comments are found and deleted successfully"
        )
        assert result["test_comments_found"] == 1, (
            "Should correctly identify one test comment thread for cleanup"
        )
        assert result["resolved_count"] == 1, (
            "Should successfully resolve one test comment thread"
        )
        assert result["failed_count"] == 0, (
            "Should have no failed deletions when API calls succeed"
        )

        # And: Should make appropriate API calls for discovery and deletion
        assert mock_run.call_count >= 3, (
            f"Expected at least 3 API calls (list, get thread, delete) but got {mock_run.call_count}"
        )


if __name__ == "__main__":
    pytest.main([__file__])
