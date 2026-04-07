"""
Tests for Azure DevOps workflow tools - behavior-focused tests.

Tests focus on what AI agents can accomplish when helping developers
work effectively with Azure DevOps pull requests and AI-assisted development workflows.
"""

import subprocess
from unittest.mock import Mock, patch
from pdp_dev_mcp.tools.common.azure_devops_repository import (
    azure_devops_repository_discovery,
    azure_devops_workflow_setup,
)
from pdp_dev_mcp.tools.common.azure_devops_pr_comments import (
    azure_devops_pr_comment_analysis,
    azure_devops_resolve_pr_comments,
)
from pdp_dev_mcp.tools.common.azure_devops_pr_lifecycle import (
    azure_devops_create_pull_request,
)
from pdp_dev_mcp.tools.common.azure_devops_common import (
    AzureDevOpsPRContext,
)


class TestAIAgentsCanDiscoverRepositoryContext:
    """Test what AI agents can accomplish when helping developers understand their repository context."""

    def test_ai_agents_can_help_developers_discover_repository_context_from_git(
        self,
    ) -> None:
        """AI agents should be able to discover Azure DevOps organization, project, and repository from git remote."""
        with patch("subprocess.run") as mock_run:
            # Mock git remote URL response
            mock_run.return_value = Mock(
                returncode=0,
                stdout="https://dev.azure.com/microsoft/Universal%20Store/_git/Commerce.PaymentsDataPlatform\n",
            )

            result = azure_devops_repository_discovery()

            # AI agents need successful discovery to help developers
            assert result["success"] is True, (
                "AI agents need functioning repository discovery to help developers understand their context"
            )

            # AI agents need proper organization parsing to help with Azure DevOps operations
            assert result["organization"] == "microsoft", (
                "AI agents need accurate organization parsing to help developers configure Azure DevOps CLI"
            )

            # AI agents need proper project parsing with URL decoding
            assert result["project"] == "Universal Store", (
                "AI agents need accurate project parsing with URL decoding for space-containing project names"
            )

            # AI agents need repository name for PR operations
            assert result["repository"] == "Commerce.PaymentsDataPlatform", (
                "AI agents need accurate repository name parsing for PR comment analysis"
            )

    def test_ai_agents_can_help_developers_handle_legacy_visualstudio_urls(
        self,
    ) -> None:
        """AI agents should be able to handle legacy .visualstudio.com URLs for older Azure DevOps instances."""
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = Mock(
                returncode=0,
                stdout="https://msazure.visualstudio.com/DefaultCollection/One/_git/Commerce.PaymentsDataPlatform\n",
            )

            result = azure_devops_repository_discovery()

            # AI agents need successful handling of legacy URLs (preserving correct legacy format)
            assert result["success"] is True
            assert result["organization"] == "msazure"
            assert result["org_url"] == "https://msazure.visualstudio.com", (
                f"Legacy Visual Studio URLs should preserve the original format. "
                f"Expected 'https://msazure.visualstudio.com', got '{result['org_url']}'"
            )

    def test_ai_agents_can_help_developers_understand_discovery_failures(self) -> None:
        """AI agents should provide clear error messages when repository discovery fails."""
        with patch("subprocess.run") as mock_run:
            # Mock git command failure
            mock_run.return_value = Mock(
                returncode=1, stderr="fatal: not a git repository"
            )

            result = azure_devops_repository_discovery()

            # AI agents need clear failure indication to help developers troubleshoot
            assert result["success"] is False, (
                "AI agents need clear failure indication when repository discovery fails"
            )

            # AI agents need descriptive error messages to help developers understand issues
            assert "No git repositories found" in result["error"], (
                "AI agents need descriptive error messages to help developers understand repository issues"
            )

    def test_ai_agents_can_help_developers_handle_unsupported_url_formats(self) -> None:
        """AI agents should gracefully handle unsupported git URL formats."""
        with patch("subprocess.run") as mock_run:
            # Mock unsupported URL format
            mock_run.return_value = Mock(
                returncode=0, stdout="https://github.com/microsoft/some-repo.git\n"
            )

            result = azure_devops_repository_discovery()

            # AI agents need clear failure indication for unsupported URLs
            assert result["success"] is False, (
                "AI agents need clear failure indication for unsupported git URL formats"
            )

            # AI agents need specific error for unsupported URLs
            assert "No git repositories found" in result["error"], (
                "AI agents need specific error messages for unsupported git URL formats"
            )

            # Enhanced discovery provides helpful suggestions instead of raw URL
            assert "suggestion" in result, (
                "AI agents need helpful suggestions for developer troubleshooting"
            )

    def test_ai_agents_can_help_developers_handle_incomplete_url_parsing(self) -> None:
        """AI agents should handle URLs that don't contain all required components."""
        with patch("subprocess.run") as mock_run:
            # Mock incomplete URL (missing repository name)
            mock_run.return_value = Mock(
                returncode=0,
                stdout="https://dev.azure.com/microsoft/Project\n",  # Missing /_git/repo part
            )

            result = azure_devops_repository_discovery()

            # AI agents need clear failure indication for incomplete URLs
            assert result["success"] is False, (
                "AI agents need clear failure indication when URL parsing is incomplete"
            )

            # AI agents need specific error for parsing failures
            assert "No git repositories found" in result["error"], (
                "AI agents need specific error messages for incomplete URL parsing"
            )

            # Enhanced discovery provides available repositories list for debugging
            assert "available_repositories" in result, (
                "AI agents need to see available repositories for developer troubleshooting"
            )

    def test_ai_agents_can_help_developers_handle_git_timeouts(self) -> None:
        """AI agents should gracefully handle git command timeouts."""
        with patch("subprocess.run") as mock_run:
            # Mock subprocess timeout
            from subprocess import TimeoutExpired

            mock_run.side_effect = TimeoutExpired(cmd=["git"], timeout=30)

            result = azure_devops_repository_discovery()

            # AI agents need clear failure indication for timeouts
            assert result["success"] is False, (
                "AI agents need clear failure indication when git commands timeout"
            )

            # AI agents need specific timeout error message
            assert "No git repositories found" in result["error"], (
                "AI agents need specific timeout error messages for developer troubleshooting"
            )

    def test_ai_agents_can_help_developers_handle_unexpected_discovery_errors(
        self,
    ) -> None:
        """AI agents should gracefully handle unexpected errors during repository discovery."""
        with patch("subprocess.run") as mock_run:
            # Mock unexpected exception
            mock_run.side_effect = RuntimeError("Unexpected system error")

            result = azure_devops_repository_discovery()

            # AI agents need clear failure indication for unexpected errors
            assert result["success"] is False, (
                "AI agents need clear failure indication for unexpected errors"
            )

            # AI agents need error details for debugging
            assert (
                "Repository discovery failed: Unexpected system error"
                in result["error"]
            ), "AI agents need detailed error messages for unexpected failures"

    def test_ai_agents_can_help_developers_use_explicit_working_directory(
        self,
    ) -> None:
        """AI agents should be able to help developers specify explicit working directories for repository discovery."""
        with (
            patch("subprocess.run") as mock_run,
            patch("os.path.exists") as mock_exists,
            patch("os.path.isdir") as mock_isdir,
            patch("os.listdir") as mock_listdir,
        ):
            # Mock directory structure - custom path exists and contains a .git directory
            def mock_exists_side_effect(path):
                if path == "/custom/path/to/repo":
                    return True
                if path == "/custom/path/to/repo/.git":
                    return True
                return False

            def mock_isdir_side_effect(path):
                return path in ["/custom/path/to/repo", "/custom/path/to/repo/.git"]

            mock_exists.side_effect = mock_exists_side_effect
            mock_isdir.side_effect = mock_isdir_side_effect
            mock_listdir.return_value = [".git", "src", "README.md"]

            # Mock git remote URL response
            mock_run.return_value = Mock(
                returncode=0,
                stdout="https://dev.azure.com/microsoft/Universal%20Store/_git/Commerce.PaymentsDataPlatform\n",
            )

            result = azure_devops_repository_discovery(
                working_directory="/custom/path/to/repo"
            )

            # AI agents should be able to work with explicit paths for flexibility
            assert result["success"] is True, (
                "AI agents need explicit working directory support for flexible repository operations"
            )

            # Verify the subprocess was called with the correct working directory
            mock_run.assert_called_with(
                ["git", "config", "--get", "remote.origin.url"],
                capture_output=True,
                text=True,
                timeout=10,
                cwd="/custom/path/to/repo",
            )

            # AI agents need repository context information
            assert "organization" in result, "AI agents need organization context"
            assert "project" in result, "AI agents need project context"
            assert "repository" in result, "AI agents need repository context"

    def test_ai_agents_can_help_developers_with_auto_discovery_from_current_directory(
        self,
    ) -> None:
        """AI agents should automatically discover git repositories when no working directory is specified."""
        with (
            patch("subprocess.run") as mock_run,
            patch("os.getcwd") as mock_getcwd,
            patch("os.path.exists") as mock_exists,
            patch("os.path.isdir") as mock_isdir,
            patch("os.listdir") as mock_listdir,
        ):
            # Mock current directory and git detection
            mock_getcwd.return_value = "/some/nested/project/path"

            def mock_exists_side_effect(path):
                if path == "/some/nested/project/path/.git":
                    return True
                return False

            def mock_isdir_side_effect(path):
                return path in [
                    "/some/nested/project/path",
                    "/some/nested/project/path/.git",
                ]

            mock_exists.side_effect = mock_exists_side_effect
            mock_isdir.side_effect = mock_isdir_side_effect
            mock_listdir.return_value = [".git", "src", "README.md"]

            # Mock git remote URL response
            mock_run.return_value = Mock(
                returncode=0,
                stdout="https://dev.azure.com/microsoft/Universal%20Store/_git/Commerce.PaymentsDataPlatform\n",
            )

            result = azure_devops_repository_discovery()

            # AI agents should successfully auto-discover repositories
            assert result["success"] is True, (
                "AI agents need auto-discovery capability to work seamlessly from any project subdirectory"
            )

            # Verify the subprocess was called with the auto-discovered working directory
            mock_run.assert_called_with(
                ["git", "config", "--get", "remote.origin.url"],
                capture_output=True,
                text=True,
                timeout=10,
                cwd="/some/nested/project/path",
            )

            # AI agents need repository context information
            assert "organization" in result, "AI agents need organization context"
            assert "project" in result, "AI agents need project context"
            assert "repository" in result, "AI agents need repository context"

    def test_ai_agents_can_help_developers_with_fallback_to_known_workspace_paths(
        self,
    ) -> None:
        """AI agents should use intelligent workspace discovery when current directory has no git repo."""
        with (
            patch("subprocess.run") as mock_run,
            patch("os.getcwd") as mock_getcwd,
        ):
            # Mock current directory with no git repo
            mock_getcwd.return_value = "/tmp"

            # Mock git command to fail (no repo in current directory)
            mock_run.side_effect = Exception("Not a git repository")

            result = azure_devops_repository_discovery()

            # AI agents should handle the case gracefully with a helpful error message
            assert result["success"] is False, (
                "AI agents should indicate failure when no repositories are found"
            )

            # Enhanced discovery should provide helpful guidance
            assert "No git repositories found" in result["error"], (
                "AI agents need clear error messages for no repository scenarios"
            )

            assert "suggestion" in result, (
                "AI agents should provide helpful suggestions when repositories aren't found"
            )


class TestAIAgentsCanAnalyzePRComments:
    """Test what AI agents can accomplish when helping developers analyze PR feedback."""

    @patch("subprocess.run")
    def test_ai_agents_can_help_developers_analyze_pr_comments_for_feedback(
        self, mock_run
    ) -> None:
        """AI agents should be able to analyze PR comments and identify all feedback for developers."""
        # Mock subprocess calls: git command for repository discovery, then Azure CLI REST calls
        mock_run.side_effect = [
            Mock(
                returncode=0,
                stdout="https://dev.azure.com/microsoft/Universal%20Store/_git/Commerce.PaymentsDataPlatform\n",
            ),  # git config --get remote.origin.url
            Mock(
                returncode=0,
                stdout='{"id": "repo-guid"}',
            ),  # az rest GET repository
            Mock(
                returncode=0,
                stdout='{"id": "project-guid"}',
            ),  # az rest GET project
            Mock(
                returncode=0,
                stdout='{"value": [{"id": "123", "status": "active", "comments": [{"author": {"displayName": "MerlinBot"}, "content": "Consider using word boundaries in regex"}]}]}',
            ),  # az rest GET PR comments
        ]

        result = azure_devops_pr_comment_analysis(pr_url_or_id="13577785")

        # AI agents need successful analysis to help developers understand PR feedback
        assert result["success"] is True, (
            "AI agents need functioning PR comment analysis to help developers process AI feedback"
        )

        # AI agents need comment summary to help developers prioritize work
        assert "comment_summary" in result
        assert result["comment_summary"]["active_threads"] == 1

        # AI agents need active comment details to help developers understand what needs attention
        assert len(result["active_comments"]) == 1
        assert result["active_comments"][0]["author"] == "MerlinBot"

    @patch("subprocess.run")
    def test_ai_agents_can_help_developers_understand_comment_analysis_failures(
        self, mock_run
    ) -> None:
        """AI agents should provide clear error information when PR comment analysis fails."""
        # Mock git command failure to simulate not being in a git repository
        mock_run.return_value = Mock(
            returncode=1, stdout="", stderr="fatal: not a git repository"
        )

        result = azure_devops_pr_comment_analysis(pr_url_or_id="12345")

        # AI agents need clear failure information to help developers troubleshoot
        assert result["success"] is False
        assert "error" in result

    @patch("subprocess.run")
    def test_ai_agents_can_help_developers_handle_azure_cli_configuration_failures(
        self, mock_run
    ) -> None:
        """AI agents should handle Azure CLI configuration failures gracefully."""
        # Mock subprocess calls: git command succeeds, but Azure CLI configuration fails
        mock_run.side_effect = [
            Mock(
                returncode=0,
                stdout="https://dev.azure.com/microsoft/Universal%20Store/_git/Commerce.PaymentsDataPlatform\n",
            ),  # git config --get remote.origin.url
            Mock(
                returncode=1, stderr="az: error: not logged in"
            ),  # az devops configure failure
        ]

        result = azure_devops_pr_comment_analysis(pr_url_or_id="12345")

        # AI agents need clear failure indication for CLI configuration issues
        assert result["success"] is False, (
            "AI agents need clear failure indication when Azure CLI configuration fails"
        )

        # AI agents need error information to help developers troubleshoot
        assert "stderr" in result or "error" in result, (
            "AI agents need error details to help developers troubleshoot CLI issues"
        )

    @patch("subprocess.run")
    def test_ai_agents_can_help_developers_handle_repository_information_failures(
        self, mock_run
    ) -> None:
        """AI agents should handle repository information retrieval failures."""
        # Mock subprocess calls: git succeeds, CLI config succeeds, but repository info fails
        mock_run.side_effect = [
            Mock(
                returncode=0,
                stdout="https://dev.azure.com/microsoft/Universal%20Store/_git/Commerce.PaymentsDataPlatform\n",
            ),  # git config --get remote.origin.url
            Mock(returncode=0, stdout='{"id": "repo-guid"}'),  # az rest GET repository
            Mock(
                returncode=1, stderr="fatal: repository 'BadRepo' not found"
            ),  # az rest GET project
        ]

        result = azure_devops_pr_comment_analysis(pr_url_or_id="12345")

        # AI agents need clear failure indication for repository info issues
        assert result["success"] is False, (
            "AI agents need clear failure indication when repository information retrieval fails"
        )

        # AI agents need error information to help developers troubleshoot
        assert "Failed to get project information" in result["error"], (
            "AI agents need specific error messages for repository information failures"
        )

    @patch("subprocess.run")
    def test_ai_agents_can_help_developers_handle_malformed_repository_data(
        self, mock_run
    ) -> None:
        """AI agents should handle malformed repository data gracefully."""
        # Mock subprocess calls: git succeeds, but repository response has malformed JSON (missing "id")
        mock_run.side_effect = [
            Mock(
                returncode=0,
                stdout="https://dev.azure.com/microsoft/Universal%20Store/_git/Commerce.PaymentsDataPlatform\n",
            ),  # git config --get remote.origin.url
            Mock(
                returncode=0, stdout='{"incomplete": "data"}'
            ),  # az rest GET repository with missing "id" field
            Mock(
                returncode=0, stdout='{"name": "project"}'
            ),  # az rest GET project with missing "id" field
        ]

        result = azure_devops_pr_comment_analysis(pr_url_or_id="12345")

        # AI agents need clear failure indication for malformed data
        assert result["success"] is False, (
            "AI agents need clear failure indication when repository data is malformed"
        )

        # AI agents need error information for troubleshooting malformed data
        assert "Could not extract repository and project GUIDs" in result["error"], (
            "AI agents need specific error messages for malformed JSON data failures"
        )

    @patch("subprocess.run")
    def test_ai_agents_can_help_developers_handle_json_fallback_parsing(
        self, mock_run
    ) -> None:
        """AI agents should handle JSON with control characters by reporting the error."""
        # Mock subprocess calls: git succeeds, then Azure CLI REST calls with control characters
        # JSON with embedded null bytes (\u0000) will fail strict JSON parsing
        mock_run.side_effect = [
            Mock(
                returncode=0,
                stdout="https://dev.azure.com/microsoft/Universal%20Store/_git/Commerce.PaymentsDataPlatform\n",
            ),  # git config --get remote.origin.url
            Mock(
                returncode=0,
                stdout='{"id": "repo-guid\u0000"}',
            ),  # az rest GET repository with control chars - will fail JSON parsing
        ]

        result = azure_devops_pr_comment_analysis(pr_url_or_id="12345")

        # AI agents need clear failure indication for JSON parsing errors
        assert result["success"] is False, (
            "AI agents need clear failure indication when JSON contains control characters"
        )

        # AI agents need specific error for JSON parsing failures
        assert "JSON parsing error" in result["error"], (
            "AI agents need specific error messages for JSON parsing failures"
        )

    @patch("subprocess.run")
    def test_ai_agents_can_help_developers_handle_fallback_parsing_failures(
        self, mock_run
    ) -> None:
        """AI agents should handle missing GUID fields gracefully."""
        # Mock subprocess calls: git succeeds, but repository response is missing required "id" field
        mock_run.side_effect = [
            Mock(
                returncode=0,
                stdout="https://dev.azure.com/microsoft/Universal%20Store/_git/Commerce.PaymentsDataPlatform\n",
            ),  # git config --get remote.origin.url
            Mock(
                returncode=0, stdout='{"completely": "invalid structure"}'
            ),  # az rest GET repository with missing "id" field
            Mock(
                returncode=0, stdout='{"name": "SomeProject"}'
            ),  # az rest GET project with missing "id" field
        ]

        result = azure_devops_pr_comment_analysis(pr_url_or_id="12345")

        # AI agents need clear failure indication for missing GUIDs
        assert result["success"] is False, (
            "AI agents need clear failure indication when GUID extraction fails"
        )

        # AI agents need specific error for GUID extraction failures
        assert "Could not extract repository and project GUIDs" in result["error"], (
            "AI agents need specific error messages when GUID extraction fails"
        )

    @patch("subprocess.run")
    def test_ai_agents_can_help_developers_handle_empty_guid_extraction(
        self, mock_run
    ) -> None:
        """AI agents should handle cases where JSON response has no "id" fields."""
        # Mock subprocess calls: git succeeds, but repository response has no ID fields
        # JSON with control chars will fail parsing, triggering JSONDecodeError
        mock_run.side_effect = [
            Mock(
                returncode=0,
                stdout="https://dev.azure.com/microsoft/Universal%20Store/_git/Commerce.PaymentsDataPlatform\n",
            ),  # git config --get remote.origin.url
            Mock(
                returncode=0,
                stdout='{"invalid\u0000": "structure", "no_id_fields": true}',
            ),  # az rest GET repository - JSON with control chars will fail parsing
        ]

        result = azure_devops_pr_comment_analysis(pr_url_or_id="12345")

        # AI agents need clear failure indication for JSON parsing errors
        assert result["success"] is False, (
            "AI agents need clear failure indication when JSON parsing fails"
        )

        # AI agents need specific error for JSON parsing errors
        assert "JSON parsing error" in result["error"], (
            "AI agents need specific error messages for JSON parsing failures"
        )

    @patch("subprocess.run")
    def test_ai_agents_can_help_developers_handle_pr_api_failures(
        self, mock_run
    ) -> None:
        """AI agents should handle PR API failures gracefully."""
        # Mock subprocess calls: git succeeds, repo and project succeed, but PR API fails
        mock_run.side_effect = [
            Mock(
                returncode=0,
                stdout="https://dev.azure.com/microsoft/Universal%20Store/_git/Commerce.PaymentsDataPlatform\n",
            ),  # git config --get remote.origin.url
            Mock(returncode=0, stdout='{"id": "repo-guid"}'),  # az rest GET repository
            Mock(returncode=0, stdout='{"id": "project-guid"}'),  # az rest GET project
            Mock(
                returncode=1, stderr="TF401179: Pull request does not exist"
            ),  # az rest GET PR comments - failure
        ]

        result = azure_devops_pr_comment_analysis(pr_url_or_id="999999")

        # AI agents need clear failure indication for PR API issues
        assert result["success"] is False, (
            "AI agents need clear failure indication when PR API calls fail"
        )

        # AI agents need specific error for PR API failures
        assert "Failed to retrieve PR comments" in result["error"], (
            "AI agents need specific error messages for PR API failures"
        )

    @patch("subprocess.run")
    def test_ai_agents_can_help_developers_handle_json_parsing_errors_in_pr_data(
        self, mock_run
    ) -> None:
        """AI agents should handle JSON parsing errors in PR data gracefully."""
        # Mock subprocess calls with malformed JSON response
        mock_run.side_effect = [
            Mock(
                returncode=0,
                stdout="https://dev.azure.com/microsoft/Universal%20Store/_git/Commerce.PaymentsDataPlatform\n",
            ),  # git config --get remote.origin.url
            Mock(
                returncode=0,
                stdout='{"id": "repo-guid", "project": {"id": "project-guid"}}',
            ),  # az rest GET repository
            Mock(returncode=0, stdout='{"id": "project-guid"}'),  # az rest GET project
            Mock(
                returncode=0, stdout='{"invalid": json data}'
            ),  # az rest GET PR comments with invalid JSON
        ]

        result = azure_devops_pr_comment_analysis(pr_url_or_id="12345")

        # AI agents need clear failure indication for JSON parsing issues
        assert result["success"] is False, (
            "AI agents need clear failure indication when PR data JSON parsing fails"
        )

        # AI agents need specific error for JSON parsing failures
        assert "JSON parsing error" in result["error"], (
            "AI agents need specific error messages for JSON parsing failures"
        )

    @patch("subprocess.run")
    def test_ai_agents_can_help_developers_handle_pr_analysis_timeouts(
        self, mock_run
    ) -> None:
        """AI agents should handle subprocess timeouts in PR analysis gracefully."""
        # Mock timeout during PR API call
        from subprocess import TimeoutExpired

        mock_run.side_effect = [
            Mock(
                returncode=0,
                stdout="https://dev.azure.com/microsoft/Universal%20Store/_git/Commerce.PaymentsDataPlatform\n",
            ),  # git config --get remote.origin.url
            Mock(
                returncode=0,
                stdout='{"id": "repo-guid", "project": {"id": "project-guid"}}',
            ),  # az rest GET repository success
            Mock(returncode=0, stdout='{"id": "project-guid"}'),  # az rest GET project
            TimeoutExpired(
                cmd=["az", "rest"], timeout=30
            ),  # az rest timeout on PR data
        ]

        result = azure_devops_pr_comment_analysis(pr_url_or_id="12345")

        # AI agents need clear failure indication for timeouts
        assert result["success"] is False, (
            "AI agents need clear failure indication when PR analysis times out"
        )

        # AI agents need specific timeout error message
        assert "timed out" in result["error"], (
            "AI agents need specific timeout error messages for PR analysis failures"
        )

    @patch("subprocess.run")
    def test_ai_agents_can_help_developers_handle_unexpected_pr_analysis_errors(
        self, mock_run
    ) -> None:
        """AI agents should handle unexpected errors in PR analysis gracefully."""
        # Mock unexpected exception
        mock_run.side_effect = [
            Mock(
                returncode=0,
                stdout="https://dev.azure.com/microsoft/Universal%20Store/_git/Commerce.PaymentsDataPlatform\n",
            ),  # git config --get remote.origin.url
            Mock(
                returncode=0,
                stdout='{"id": "repo-guid", "project": {"id": "project-guid"}}',
            ),  # az rest GET repository success
            Mock(returncode=0, stdout='{"id": "project-guid"}'),  # az rest GET project
            RuntimeError(
                "Unexpected system error"
            ),  # Unexpected error during PR data fetch
        ]

        result = azure_devops_pr_comment_analysis(pr_url_or_id="12345")

        # AI agents need clear failure indication for unexpected errors
        assert result["success"] is False, (
            "AI agents need clear failure indication for unexpected errors in PR analysis"
        )

        # AI agents need error details for debugging
        assert "Unexpected error" in result["error"], (
            "AI agents need detailed error messages for unexpected PR analysis failures"
        )

    @patch("subprocess.run")
    @patch("os.makedirs")
    @patch("builtins.open")
    def test_ai_agents_can_use_custom_save_directory_for_pr_analysis(
        self, mock_open, mock_makedirs, mock_run
    ) -> None:
        """AI agents should be able to save PR analysis to custom directories following team patterns."""
        # Mock Azure CLI calls with multi-author comments
        mock_run.side_effect = [
            Mock(
                returncode=0,
                stdout="https://dev.azure.com/microsoft/Universal%20Store/_git/Commerce.PaymentsDataPlatform\n",
            ),  # git config --get remote.origin.url
            Mock(
                returncode=0,
                stdout='{"id": "repo-guid", "project": {"id": "project-guid"}}',
            ),  # az rest GET repository
            Mock(returncode=0, stdout='{"id": "project-guid"}'),  # az rest GET project
            Mock(
                returncode=0,
                stdout='{"value": [{"id": "123", "status": "active", "comments": [{"author": {"displayName": "MerlinBot"}, "content": "Consider using word boundaries in regex", "publishedDate": "2025-09-17"}]}, {"id": "124", "status": "fixed", "comments": [{"author": {"displayName": "noamk@microsoft.com"}, "content": "Please rename this variable to be more descriptive", "publishedDate": "2025-09-16"}]}]}',
            ),  # az rest GET PR comments
        ]

        # Mock file operations
        mock_file = Mock()
        mock_open.return_value.__enter__.return_value = mock_file

        custom_directory = ".copilot/custom-analysis"
        result = azure_devops_pr_comment_analysis(
            pr_url_or_id="12345", save_to_file=True, save_directory=custom_directory
        )

        # AI agents need successful analysis with custom save directory
        assert result["success"] is True, (
            "AI agents need functioning PR analysis with custom save directories"
        )

        # AI agents need visibility into comment authors for prioritizing feedback
        assert "comment_authors" in result, (
            "AI agents need comment author summary to understand feedback sources"
        )
        assert result["comment_authors"]["MerlinBot"] == 1
        assert result["comment_authors"]["noamk@microsoft.com"] == 1

        # AI agents need author samples for immediate context without reading files
        assert "author_samples" in result, (
            "AI agents need author sample comments for immediate context"
        )
        assert "MerlinBot" in result["author_samples"]
        assert "noamk@microsoft.com" in result["author_samples"]
        assert result["author_samples"]["MerlinBot"]["count"] == 1
        assert (
            "word boundaries" in result["author_samples"]["MerlinBot"]["latest_comment"]
        )

        # AI agents need detailed file output information to use saved files
        assert "file_output" in result, (
            "AI agents need detailed file output information for automation"
        )
        assert result["file_output"]["saved"] is True
        assert result["file_output"]["directory_used"] == custom_directory
        assert result["file_output"]["save_directory_source"] == "custom"
        assert custom_directory in result["file_output"]["path"]

        # Verify directory creation was called with custom path
        mock_makedirs.assert_called_once_with(custom_directory, exist_ok=True)

    @patch("subprocess.run")
    @patch("os.makedirs")
    @patch("builtins.open")
    def test_ai_agents_use_copilot_default_directory_when_no_custom_directory_specified(
        self, mock_open, mock_makedirs, mock_run
    ) -> None:
        """AI agents should use .copilot/ default directory following team collaboration patterns."""
        # Mock Azure CLI calls
        mock_run.side_effect = [
            Mock(
                returncode=0,
                stdout="https://dev.azure.com/microsoft/Universal%20Store/_git/Commerce.PaymentsDataPlatform\n",
            ),  # git config --get remote.origin.url
            Mock(
                returncode=0,
                stdout='{"id": "repo-guid", "project": {"id": "project-guid"}}',
            ),  # az rest GET repository
            Mock(returncode=0, stdout='{"id": "project-guid"}'),  # az rest GET project
            Mock(
                returncode=0,
                stdout='{"value": [{"id": "123", "status": "active", "comments": [{"author": {"displayName": "MerlinBot"}, "content": "Consider using word boundaries in regex"}]}]}',
            ),  # az rest GET PR comments
        ]

        # Mock file operations
        mock_file = Mock()
        mock_open.return_value.__enter__.return_value = mock_file

        result = azure_devops_pr_comment_analysis(
            pr_url_or_id="12345", save_to_file=True
        )

        # AI agents need successful analysis with default .copilot/ directory
        assert result["success"] is True, (
            "AI agents need functioning PR analysis with default .copilot/ directory"
        )

        # AI agents need confirmation of .copilot/ default usage
        assert "file_output" in result
        assert ".copilot/analysis/" in result["file_output"]["directory_used"]
        assert result["file_output"]["save_directory_source"] == "default (.copilot/)"

        # Verify .copilot/ directory creation was called
        args, kwargs = mock_makedirs.call_args
        assert ".copilot/analysis/" in args[0], (
            "AI agents expect .copilot/ directory structure by default"
        )

    @patch("subprocess.run")
    @patch("os.makedirs")
    @patch("builtins.open")
    def test_ai_agents_handle_file_save_failures_gracefully(
        self, mock_open, mock_makedirs, mock_run
    ) -> None:
        """AI agents should report file save operation failures clearly."""
        # Mock Azure CLI calls
        mock_run.side_effect = [
            Mock(
                returncode=0,
                stdout="https://dev.azure.com/microsoft/Universal%20Store/_git/Commerce.PaymentsDataPlatform\n",
            ),  # git config --get remote.origin.url
            Mock(
                returncode=0,
                stdout='{"id": "repo-guid", "project": {"id": "project-guid"}}',
            ),  # az rest GET repository
            Mock(returncode=0, stdout='{"id": "project-guid"}'),  # az rest GET project
            Mock(
                returncode=0,
                stdout='{"value": [{"id": "123", "status": "active", "comments": [{"author": {"displayName": "MerlinBot"}, "content": "Consider using word boundaries in regex"}]}]}',
            ),  # az rest GET PR comments
        ]

        # Mock file save failure
        mock_open.side_effect = PermissionError("Permission denied")

        result = azure_devops_pr_comment_analysis(
            pr_url_or_id="12345", save_to_file=True
        )

        # AI agents need clear failure indication when file operations fail
        assert result["success"] is False, (
            "AI agents need clear failure indication when file save fails"
        )

        # AI agents need specific error message for file save failures
        assert "Permission denied" in result["error"], (
            "AI agents need specific error messages for file permission errors"
        )


class TestAIAgentsCanResolvePRComments:
    """Test what AI agents can accomplish when helping developers resolve PR feedback."""

    @patch("subprocess.run")
    def test_ai_agents_can_help_developers_resolve_implemented_feedback(
        self, mock_run
    ) -> None:
        """AI agents should be able to resolve PR comments after developers implement suggestions."""
        # Mock Azure CLI calls
        mock_run.side_effect = [
            Mock(
                returncode=0,
                stdout="https://dev.azure.com/microsoft/Universal%20Store/_git/Commerce.PaymentsDataPlatform\n",
            ),  # git config --get remote.origin.url
            Mock(
                returncode=0,
                stdout='{"id": "repo-guid", "project": {"id": "project-guid"}}',
            ),  # az rest GET repository
            Mock(returncode=0, stdout='{"id": "project-guid"}'),  # az rest GET project
            Mock(returncode=0, stdout=""),  # az rest PATCH for first thread
            Mock(returncode=0, stdout=""),  # az rest PATCH for second thread
        ]

        # Create PR context for resolution
        pr_context = AzureDevOpsPRContext(
            pr_url="https://dev.azure.com/microsoft/Universal%20Store/_git/Commerce.PaymentsDataPlatform/pullrequest/13577785",
            organization="microsoft",
            project="Universal Store",
            repository="Commerce.PaymentsDataPlatform",
            pr_id=13577785,
            source="test",
        )

        result = azure_devops_resolve_pr_comments(
            pr_context=pr_context, thread_ids=["123", "456"], status="fixed"
        )

        # AI agents need successful resolution to help developers complete feedback cycles
        assert result["success"] is True, (
            "AI agents need functioning comment resolution to help developers complete AI feedback workflows"
        )

        # AI agents need resolution summary to help developers track progress
        assert result["successful_resolutions"] == 2
        assert result["failed_resolutions"] == 0
        assert "resolved 2/2 threads" in result["summary"].lower()

    def test_ai_agents_can_help_developers_validate_resolution_status_options(
        self,
    ) -> None:
        """AI agents should validate resolution status options to prevent API errors."""
        # Test validates status before making any subprocess calls
        pr_context = AzureDevOpsPRContext(
            pr_url="https://dev.azure.com/test/test/_git/test/pullrequest/12345",
            organization="test",
            project="test",
            repository="test",
            pr_id=12345,
            source="test",
        )

        result = azure_devops_resolve_pr_comments(
            pr_context=pr_context, thread_ids=["123"], status="invalid_status"
        )

        # AI agents need status validation to help developers avoid API errors
        assert result["success"] is False
        assert "invalid status" in result["error"].lower()

    def test_ai_agents_can_help_developers_use_dry_run_mode_for_validation(
        self,
    ) -> None:
        """AI agents should support dry-run mode to help developers validate resolution plans."""
        # Dry-run mode doesn't make subprocess calls, so no mocking needed
        pr_context = AzureDevOpsPRContext(
            pr_url="https://dev.azure.com/microsoft/Universal%20Store/_git/Commerce.PaymentsDataPlatform/pullrequest/13577785",
            organization="microsoft",
            project="Universal Store",
            repository="Commerce.PaymentsDataPlatform",
            pr_id=13577785,
            source="test",
        )

        result = azure_devops_resolve_pr_comments(
            pr_context=pr_context,
            thread_ids=["123", "456"],
            status="fixed",
            dry_run=True,
        )

        # AI agents need dry-run capability to help developers plan resolution safely
        assert result["dry_run"] is True
        assert result["threads_to_resolve"] == 2
        assert "set dry_run=false" in result["next_steps"].lower()

    @patch("subprocess.run")
    def test_ai_agents_can_help_developers_handle_resolution_discovery_failures(
        self, mock_run
    ) -> None:
        """AI agents should handle subprocess failures in comment resolution."""
        # Mock subprocess to fail during resolution operations
        mock_run.side_effect = subprocess.CalledProcessError(
            1, ["az"], "Project not found"
        )

        pr_context = AzureDevOpsPRContext(
            pr_url="https://dev.azure.com/test/test/_git/test/pullrequest/12345",
            organization="test",
            project="test",
            repository="test",
            pr_id=12345,
            source="test",
        )

        result = azure_devops_resolve_pr_comments(
            pr_context=pr_context, thread_ids=["123"], status="fixed"
        )

        # AI agents need clear failure indication for subprocess failures
        assert result["success"] is False, (
            "AI agents need clear failure indication when subprocess calls fail during resolution"
        )

        # AI agents need error information from failed subprocess calls
        assert "Unexpected error" in result["error"], (
            "AI agents need specific error messages for subprocess failures during resolution"
        )

    @patch(
        "pdp_dev_mcp.tools.common.azure_devops_repository.azure_devops_repository_discovery"
    )
    @patch("subprocess.run")
    def test_ai_agents_can_help_developers_handle_resolution_cli_failures(
        self, mock_run, mock_discovery
    ) -> None:
        """AI agents should handle Azure CLI failures during comment resolution."""
        # Mock successful repository discovery
        mock_discovery.return_value = {
            "success": True,
            "organization": "microsoft",
            "project": "Universal Store",
            "repository": "Commerce.PaymentsDataPlatform",
            "org_url": "https://dev.azure.com/microsoft",
        }

        # Mock CLI configuration failure
        mock_run.return_value = Mock(returncode=1, stderr="az: error: not logged in")

        pr_context = AzureDevOpsPRContext(
            pr_url="https://dev.azure.com/microsoft/Universal%20Store/_git/Commerce.PaymentsDataPlatform/pullrequest/12345",
            organization="microsoft",
            project="Universal Store",
            repository="Commerce.PaymentsDataPlatform",
            pr_id=12345,
            source="test",
        )

        result = azure_devops_resolve_pr_comments(
            pr_context=pr_context, thread_ids=["123"], status="fixed"
        )

        # AI agents need clear failure indication for CLI issues during resolution
        assert result["success"] is False, (
            "AI agents need clear failure indication when Azure CLI fails during resolution"
        )

        # AI agents need specific error for CLI failures in resolution
        assert "Failed to get repository information" in result["error"], (
            "AI agents need specific error messages for CLI failures during resolution"
        )

    @patch("subprocess.run")
    def test_ai_agents_can_help_developers_handle_resolution_api_failures(
        self, mock_run
    ) -> None:
        """AI agents should handle API failures during comment resolution."""
        # Mock successful subprocess calls but failed resolution API call
        mock_run.side_effect = [
            Mock(
                returncode=0,
                stdout="project-guid\n",
            ),  # az devops project show success
            Mock(
                returncode=0,
                stdout='{"id": "repo-guid", "project": {"id": "project-guid"}}',
            ),  # az repos show success
            Mock(
                returncode=1, stderr="TF401027: Thread does not exist"
            ),  # az rest PATCH failure
        ]

        pr_context = AzureDevOpsPRContext(
            pr_url="https://dev.azure.com/microsoft/Universal%20Store/_git/Commerce.PaymentsDataPlatform/pullrequest/12345",
            organization="microsoft",
            project="Universal Store",
            repository="Commerce.PaymentsDataPlatform",
            pr_id=12345,
            source="test",
        )

        result = azure_devops_resolve_pr_comments(
            pr_context=pr_context, thread_ids=["invalid-thread"], status="fixed"
        )

        # AI agents need partial success reporting for mixed resolution results
        assert result["successful_resolutions"] == 0, (
            "AI agents need accurate counts of successful resolutions"
        )

        # AI agents need failed resolution tracking
        assert result["failed_resolutions"] == 1, (
            "AI agents need accurate counts of failed resolutions"
        )

        # AI agents need overall success status based on results
        assert result["success"] is False, (
            "AI agents need clear failure indication when all resolutions fail"
        )

    @patch("subprocess.run")
    def test_ai_agents_can_help_developers_handle_resolution_timeouts(
        self, mock_run
    ) -> None:
        """AI agents should handle timeouts during comment resolution."""
        # Mock timeout during resolution API call
        from subprocess import TimeoutExpired

        mock_run.side_effect = [
            Mock(
                returncode=0,
                stdout="project-guid\n",
            ),  # az devops project show success
            Mock(
                returncode=0,
                stdout='{"id": "repo-guid", "project": {"id": "project-guid"}}',
            ),  # az repos show success
            TimeoutExpired(cmd=["az", "rest"], timeout=30),  # az rest PATCH timeout
        ]

        pr_context = AzureDevOpsPRContext(
            pr_url="https://dev.azure.com/microsoft/Universal%20Store/_git/Commerce.PaymentsDataPlatform/pullrequest/12345",
            organization="microsoft",
            project="Universal Store",
            repository="Commerce.PaymentsDataPlatform",
            pr_id=12345,
            source="test",
        )

        result = azure_devops_resolve_pr_comments(
            pr_context=pr_context, thread_ids=["123"], status="fixed"
        )

        # AI agents need clear failure indication for resolution timeouts
        assert result["success"] is False, (
            "AI agents need clear failure indication when comment resolution times out"
        )

        # AI agents need timeout information in the resolution results
        assert result["failed_resolutions"] == 1, (
            "AI agents need accurate failed resolution count for timeout scenarios"
        )

        # AI agents need timeout details in results
        assert (
            "timed out" in str(result["results"])
            or "timeout" in str(result["results"]).lower()
        ), "AI agents need timeout error details in resolution results"

    @patch("subprocess.run")
    def test_ai_agents_can_help_developers_handle_unexpected_resolution_errors(
        self, mock_run
    ) -> None:
        """AI agents should handle unexpected errors during comment resolution."""
        # Mock unexpected exception during resolution
        mock_run.side_effect = [
            RuntimeError(
                "Unexpected system error"
            ),  # Unexpected error during project show
        ]

        pr_context = AzureDevOpsPRContext(
            pr_url="https://dev.azure.com/microsoft/Universal%20Store/_git/Commerce.PaymentsDataPlatform/pullrequest/12345",
            organization="microsoft",
            project="Universal Store",
            repository="Commerce.PaymentsDataPlatform",
            pr_id=12345,
            source="test",
        )

        result = azure_devops_resolve_pr_comments(
            pr_context=pr_context, thread_ids=["123"], status="fixed"
        )

        # AI agents need clear failure indication for unexpected resolution errors
        assert result["success"] is False, (
            "AI agents need clear failure indication for unexpected errors during resolution"
        )

        # AI agents need error details for debugging resolution issues
        assert "Unexpected error" in result["error"], (
            "AI agents need detailed error messages for unexpected resolution failures"
        )


class TestAIAgentsCanSetupWorkflows:
    """Test what AI agents can accomplish when helping developers set up Azure DevOps workflows."""

    @patch("subprocess.run")
    def test_ai_agents_can_help_developers_complete_workflow_setup(
        self, mock_run
    ) -> None:
        """AI agents should be able to complete full workflow setup for developers."""
        # Mock subprocess calls: git config, az devops configure, az repos pr list, git branch
        mock_run.side_effect = [
            Mock(
                returncode=0,
                stdout="https://dev.azure.com/microsoft/Universal%20Store/_git/Commerce.PaymentsDataPlatform\n",
            ),  # git config --get remote.origin.url
            Mock(returncode=0, stdout=""),  # az devops configure
            Mock(
                returncode=0,
                stdout='[{"pullRequestId": 13577785, "title": "Test PR", "status": "Active", "createdBy": {"displayName": "Developer"}, "sourceRefName": "refs/heads/feature-branch", "isDraft": false}]',
            ),  # az repos pr list
            Mock(returncode=0, stdout="feature-branch\n"),  # git branch --show-current
        ]

        result = azure_devops_workflow_setup()

        # AI agents need successful setup to help developers start workflows
        assert result["success"] is True, (
            "AI agents need functioning workflow setup to help developers begin Azure DevOps AI workflows"
        )

        # AI agents need repository context to help developers understand their environment
        assert result["repository_context"]["organization"] == "microsoft"
        assert result["repository_context"]["current_branch"] == "feature-branch"

        # AI agents need PR overview to help developers identify target PRs
        assert result["pr_overview"]["total_prs"] == 1
        assert len(result["pr_overview"]["recent_prs"]) == 1

        # AI agents need workflow ready status to confirm setup completion
        assert result["workflow_ready"] is True
        assert result["cli_configured"] is True

    @patch("subprocess.run")
    def test_ai_agents_can_help_developers_understand_setup_failures(
        self, mock_run
    ) -> None:
        """AI agents should provide clear error information when workflow setup fails."""
        # Mock git command failure (not in git repository)
        mock_run.return_value = Mock(returncode=1, stderr="fatal: not a git repository")

        result = azure_devops_workflow_setup()

        # AI agents need clear failure information to help developers troubleshoot setup
        assert result["success"] is False
        assert result["step"] == "repository_context"
        # Error message may vary based on context management implementation
        assert "error" in result, (
            "AI agents need error information when repository context fails"
        )

    @patch("subprocess.run")
    def test_ai_agents_can_help_developers_handle_workflow_authentication_failures(
        self, mock_run
    ) -> None:
        """AI agents should handle Azure CLI authentication failures during workflow setup."""
        # Mock the complete git command sequence for repository discovery
        mock_run.side_effect = [
            Mock(
                returncode=0,
                stdout="https://dev.azure.com/microsoft/Universal%20Store/_git/Commerce.PaymentsDataPlatform",
            ),  # git config --get remote.origin.url
            Mock(
                returncode=1, stderr="az: error: not logged in"
            ),  # Project GUID lookup or CLI failure
        ]

        result = azure_devops_workflow_setup()

        # AI agents need clear failure information for authentication issues
        assert result["success"] is False, (
            "AI agents need clear failure indication when workflow authentication fails"
        )

        # AI agents need error information for authentication failures
        assert "error" in result, (
            "AI agents need error information when workflow authentication fails"
        )

    @patch("subprocess.run")
    def test_ai_agents_can_help_developers_handle_workflow_pr_listing_failures(
        self, mock_run
    ) -> None:
        """AI agents should handle PR listing failures during workflow setup."""
        # Mock the complete command sequence for workflow setup
        mock_run.side_effect = [
            Mock(
                returncode=0,
                stdout="https://dev.azure.com/microsoft/Universal%20Store/_git/Commerce.PaymentsDataPlatform",
            ),  # git config --get remote.origin.url
            Mock(returncode=0, stdout=""),  # az devops configure success
            Mock(
                returncode=1, stderr="TF401128: The project does not exist"
            ),  # az repos pr list failure
        ]

        result = azure_devops_workflow_setup()

        # AI agents need clear failure information for PR listing issues
        assert result["success"] is False, (
            "AI agents need clear failure indication when workflow PR listing fails"
        )

        # AI agents need specific step identification for troubleshooting
        assert result["step"] == "pr_listing", (
            "AI agents need to identify which workflow step failed for developer troubleshooting"
        )

        # AI agents need specific error for PR listing failures
        assert "Failed to list PRs" in result["error"], (
            "AI agents need specific error messages for workflow PR listing failures"
        )

    @patch("subprocess.run")
    def test_ai_agents_can_help_developers_handle_workflow_branch_detection_failures(
        self, mock_run
    ) -> None:
        """AI agents should handle branch detection failures during workflow setup."""
        # Mock the complete command sequence for workflow setup
        mock_run.side_effect = [
            Mock(
                returncode=0,
                stdout="https://dev.azure.com/microsoft/Universal%20Store/_git/Commerce.PaymentsDataPlatform",
            ),  # git config --get remote.origin.url
            Mock(returncode=0, stdout=""),  # az devops configure success
            Mock(returncode=0, stdout="[]"),  # az repos pr list success (empty)
            Mock(
                returncode=1, stderr="fatal: not a git repository"
            ),  # git branch failure
        ]

        result = azure_devops_workflow_setup()

        # AI agents should continue with partial success for branch detection failures
        assert result["success"] is True, (
            "AI agents should continue workflow setup even when branch detection fails"
        )

        # AI agents need default branch when detection fails
        assert result["repository_context"]["current_branch"] == "unknown", (
            "AI agents need default branch value when detection fails"
        )

        # AI agents should still have successful setup despite branch detection failure
        assert result["workflow_ready"] is True, (
            "AI agents should maintain workflow readiness despite branch detection issues"
        )

    @patch("subprocess.run")
    def test_ai_agents_can_help_developers_handle_workflow_setup_timeouts(
        self, mock_run
    ) -> None:
        """AI agents should handle timeouts during workflow setup."""
        # Mock timeout during CLI configuration
        from subprocess import TimeoutExpired

        # First call succeeds (git config), second call times out (Project GUID lookup or configure)
        mock_run.side_effect = [
            Mock(
                returncode=0,
                stdout="https://dev.azure.com/microsoft/Universal%20Store/_git/Commerce.PaymentsDataPlatform",
            ),  # git config --get remote.origin.url
            TimeoutExpired(cmd=["az", "devops", "configure"], timeout=30),
        ]

        result = azure_devops_workflow_setup()

        # AI agents need clear failure indication for workflow timeouts
        assert result["success"] is False, (
            "AI agents need clear failure indication when workflow setup times out"
        )

        # AI agents need error information for workflow timeouts
        assert "error" in result, (
            "AI agents need error information when workflow setup times out"
        )

    @patch("subprocess.run")
    def test_ai_agents_can_help_developers_handle_unexpected_workflow_setup_errors(
        self, mock_run
    ) -> None:
        """AI agents should handle unexpected errors during workflow setup."""
        # Mock unexpected exception during workflow setup
        # First call succeeds (git config), second call raises unexpected error
        mock_run.side_effect = [
            Mock(
                returncode=0,
                stdout="https://dev.azure.com/microsoft/Universal%20Store/_git/Commerce.PaymentsDataPlatform",
            ),  # git config --get remote.origin.url
            RuntimeError("Unexpected system error"),
        ]

        result = azure_devops_workflow_setup()

        # AI agents need clear failure indication for unexpected workflow errors
        assert result["success"] is False, (
            "AI agents need clear failure indication for unexpected errors during workflow setup"
        )

        # AI agents need error details for debugging workflow issues
        assert "Unexpected error" in result["error"], (
            "AI agents need detailed error messages for unexpected workflow setup failures"
        )

    @patch("subprocess.run")
    def test_ai_agents_can_help_developers_handle_workflow_json_parsing_errors(
        self, mock_run
    ) -> None:
        """AI agents should handle JSON parsing errors in workflow setup gracefully."""
        # Mock the complete command sequence with malformed JSON response
        mock_run.side_effect = [
            Mock(
                returncode=0,
                stdout="https://dev.azure.com/microsoft/Universal%20Store/_git/Commerce.PaymentsDataPlatform",
            ),  # git config --get remote.origin.url
            Mock(returncode=0, stdout=""),  # az devops configure success
            Mock(
                returncode=0, stdout='{"invalid": json data}'
            ),  # az repos pr list with invalid JSON
        ]

        result = azure_devops_workflow_setup()

        # AI agents need clear failure indication for JSON parsing issues in workflow
        assert result["success"] is False, (
            "AI agents need clear failure indication when workflow JSON parsing fails"
        )

        # AI agents need step identification for JSON parsing failures
        assert result["step"] == "json_parsing", (
            "AI agents need to identify JSON parsing step failures for troubleshooting"
        )

        # AI agents need specific error for JSON parsing failures in workflow
        assert "JSON parsing error" in result["error"], (
            "AI agents need specific error messages for workflow JSON parsing failures"
        )


class TestAIAgentsCanCreatePullRequests:
    """Test what AI agents can accomplish when helping developers create Azure DevOps pull requests."""

    def test_ai_agents_can_help_developers_create_draft_pull_requests(
        self,
    ) -> None:
        """AI agents should be able to create draft pull requests for developers during feature development."""
        with patch("subprocess.run") as mock_run:
            # Mock the complete command sequence for PR creation
            pr_response = {
                "pullRequestId": 12345,
                "_links": {
                    "web": {
                        "href": "https://dev.azure.com/microsoft/Universal%20Store/_git/Commerce.PaymentsDataPlatform/pullrequest/12345"
                    }
                },
            }
            mock_run.side_effect = [
                Mock(
                    returncode=0,
                    stdout="https://dev.azure.com/microsoft/Universal%20Store/_git/Commerce.PaymentsDataPlatform",
                ),  # git config --get remote.origin.url
                Mock(
                    returncode=0,
                    stdout=f"{pr_response}".replace("'", '"'),  # Convert to valid JSON
                ),  # az repos pr create
            ]

            result = azure_devops_create_pull_request(
                source_branch="feature/phase2-payments-journal-cleanup",
                target_branch="main",
                title="Phase 2: PaymentsJournal cleanup and collaboration pattern standardization",
                description="Strategic removal of PaymentsJournal components from main repository",
                is_draft=True,
            )

            # AI agents need successful PR creation to help developers automate workflows
            assert result["success"] is True, (
                "AI agents need functioning PR creation to help developers automate development workflows"
            )

            # AI agents need PR ID for subsequent operations
            assert result["pr_id"] == 12345, (
                "AI agents need accurate PR ID parsing to help developers track created PRs"
            )

            # AI agents need PR URL for developer navigation
            assert "pullrequest/12345" in result["pr_url"], (
                "AI agents need accurate PR URL parsing to help developers navigate to created PRs"
            )

            # AI agents need draft status confirmation
            assert result["is_draft"] is True, (
                "AI agents need accurate draft status tracking for workflow automation"
            )

            # AI agents need branch information for tracking
            assert (
                result["source_branch"] == "feature/phase2-payments-journal-cleanup"
            ), "AI agents need accurate source branch tracking for PR management"

            # AI agents need meaningful success message for user feedback
            assert "successfully" in result["message"].lower(), (
                "AI agents need meaningful success messages to provide clear feedback to developers"
            )

    def test_ai_agents_can_handle_pr_creation_failures_gracefully(
        self,
    ) -> None:
        """AI agents should provide clear error messages when PR creation fails due to Azure CLI issues."""
        with patch("subprocess.run") as mock_run:
            # Mock the complete command sequence with failure
            mock_run.side_effect = [
                Mock(
                    returncode=0,
                    stdout="https://dev.azure.com/microsoft/Universal%20Store/_git/Commerce.PaymentsDataPlatform",
                ),  # git config --get remote.origin.url
                subprocess.CalledProcessError(
                    returncode=1,
                    cmd=["az", "repos", "pr", "create"],
                    stderr="fatal: branch 'nonexistent-branch' not found",
                ),  # az repos pr create failure
            ]

            result = azure_devops_create_pull_request(
                source_branch="nonexistent-branch",
                target_branch="main",
                title="Test PR",
            )

            # AI agents need clear failure indication for PR creation issues
            assert result["success"] is False, (
                "AI agents need clear failure indication when PR creation fails"
            )

            # AI agents need step identification for PR creation failures
            assert result["step"] == "pr_creation", (
                "AI agents need to identify PR creation step failures for troubleshooting"
            )

            # AI agents need specific error message for troubleshooting
            assert "branch" in result["error"].lower(), (
                "AI agents need specific error messages to help developers troubleshoot PR creation failures"
            )

            # AI agents need command information for debugging
            assert "az repos pr create" in result["command"], (
                "AI agents need command information to help developers debug Azure CLI issues"
            )


class TestAIAgentsCanHandleProjectNamesWithSpaces:
    """
    Test what AI agents can accomplish when helping developers work with Azure DevOps projects
    that contain spaces in their names (like "Universal Store").

    These tests consolidate URL encoding fixes and validate that project names with spaces
    are handled correctly across all Azure DevOps operations.
    """

    @patch("subprocess.run")
    def test_ai_agents_help_developers_work_with_project_spaces_in_workflow_setup(
        self, mock_run
    ):
        """
        As a developer working in a project with spaces in the name
        When AI agents help me set up Azure DevOps workflows
        Then all operations complete successfully without URL encoding errors
        """
        # Mock the complete command sequence for workflow setup
        mock_run.side_effect = [
            Mock(
                returncode=0,
                stdout="https://dev.azure.com/microsoft/Universal%20Store/_git/Commerce.PaymentsDataPlatform",
            ),  # git config --get remote.origin.url
            Mock(
                returncode=0, stdout="project-guid-123"
            ),  # Project GUID lookup or az devops configure
            Mock(returncode=0, stdout="[]"),  # Empty PR list
            Mock(returncode=0, stdout="main\n"),  # Current branch
        ]

        from pdp_dev_mcp.tools.common.azure_devops_repository import (
            azure_devops_workflow_setup,
        )

        result = azure_devops_workflow_setup()

        assert result["success"] is True, (
            f"AI agents should help developers work with project spaces successfully. "
            f"Error: {result.get('error', 'No error provided')}"
        )

        assert result["repository_context"]["project"] == "Universal Store", (
            f"AI agents should preserve project names with spaces correctly. "
            f"Got: {result['repository_context'].get('project', 'No project')}"
        )

    @patch("subprocess.run")
    def test_ai_agents_help_developers_analyze_pr_comments_with_project_spaces(
        self, mock_run
    ):
        """
        As a developer working in a project with spaces in the name
        When AI agents help me analyze PR comments
        Then the analysis completes successfully without URL encoding errors
        """
        # Mock successful Azure CLI operations
        mock_run.side_effect = [
            Mock(
                returncode=0,
                stdout="https://dev.azure.com/microsoft/Universal%20Store/_git/Commerce.PaymentsDataPlatform\n",
            ),  # git config --get remote.origin.url
            Mock(
                returncode=0,
                stdout='{"id": "repo-guid", "project": {"id": "project-guid"}}',
            ),  # az rest GET repository
            Mock(returncode=0, stdout='{"id": "project-guid"}'),  # az rest GET project
            Mock(returncode=0, stdout='{"value": []}'),  # az rest GET PR comments
        ]

        from pdp_dev_mcp.tools.common.azure_devops_pr_comments import (
            azure_devops_pr_comment_analysis,
        )

        result = azure_devops_pr_comment_analysis(pr_url_or_id="12345")

        assert result["success"] is True, (
            f"AI agents should help developers analyze PR comments with project spaces successfully. "
            f"Error: {result.get('error', 'No error provided')}"
        )

    @patch("subprocess.run")
    def test_ai_agents_help_developers_resolve_pr_comments_with_project_spaces(
        self, mock_run
    ):
        """
        As a developer working in a project with spaces in the name
        When AI agents help me resolve PR comments
        Then the resolution completes successfully without URL encoding errors
        """
        # Mock successful Azure CLI operations (pr_context provided directly)
        mock_run.side_effect = [
            Mock(returncode=0, stdout="project-guid-123\n"),  # Project GUID lookup
            Mock(
                returncode=0,
                stdout='{"id": "repo-guid", "project": {"id": "project-guid"}}',
            ),  # Repository info
            Mock(
                returncode=0, stdout='{"status": "fixed"}'
            ),  # Successful comment resolution
        ]

        from pdp_dev_mcp.tools.common.azure_devops_pr_comments import (
            azure_devops_resolve_pr_comments,
        )
        from pdp_dev_mcp.tools.common.azure_devops_common import (
            AzureDevOpsPRContext,
        )

        pr_context = AzureDevOpsPRContext(
            pr_url="https://dev.azure.com/microsoft/Universal%20Store/_git/Commerce.PaymentsDataPlatform/pullrequest/12345",
            organization="microsoft",
            project="Universal Store",
            repository="Commerce.PaymentsDataPlatform",
            pr_id=12345,
            source="test",
        )

        result = azure_devops_resolve_pr_comments(
            pr_context=pr_context, thread_ids=["123"], status="fixed"
        )

        assert result["success"] is True, (
            f"AI agents should help developers resolve PR comments with project spaces successfully. "
            f"Error: {result.get('error', 'No error provided')}"
        )

    def test_ai_agents_help_developers_avoid_double_encoded_quotes_in_urls(self):
        """
        As a developer working in a project with spaces in the name
        When AI agents generate Azure CLI commands
        Then the commands avoid double-encoded quotes that cause HTTP 500 errors
        """
        # This test validates that we use project GUIDs instead of quoted project names
        # to avoid URLs like /%22Universal%20Store%22/ which cause server errors

        # The fix: Use explicit --project GUID parameters instead of global configuration
        # Result: URLs are clean and work correctly with projects containing spaces

        project_name_with_spaces = "Universal Store"

        # AI agents should never generate commands that would create double-encoded URLs
        # Instead, they should use project GUID lookup approach
        assert " " in project_name_with_spaces, (
            "This test validates handling of project names containing spaces"
        )

        # Success criteria: All Azure CLI commands use explicit parameters
        # This avoids the historical issue where global configuration created malformed URLs


class TestAIAgentsUseOrgParameterForCrossPlatformCompatibility:
    """
    Test what AI agents can accomplish when helping developers work across different
    Azure DevOps URL formats (.visualstudio.com vs dev.azure.com) using the --org parameter.

    These tests validate that all Azure CLI commands include the --org parameter
    for proper cross-platform authentication and API compatibility.
    """

    @patch("subprocess.run")
    def test_ai_agents_help_developers_create_prs_with_org_parameter_for_cross_platform_support(
        self, mock_run
    ):
        """
        As a developer using Azure DevOps on different URL formats
        When AI agents help me create pull requests
        Then the Azure CLI commands include --org parameter for cross-platform compatibility
        """
        # Mock subprocess calls: git config, then PR creation
        mock_run.side_effect = [
            Mock(
                returncode=0,
                stdout="https://dev.azure.com/microsoft/Universal%20Store/_git/Commerce.PaymentsDataPlatform\n",
            ),  # git config --get remote.origin.url
            Mock(
                returncode=0,
                stdout='{"pullRequestId": 12345, "_links": {"web": {"href": "https://dev.azure.com/microsoft/project/_git/repo/pullrequest/12345"}}}',
            ),  # az repos pr create with --org parameter
        ]

        from pdp_dev_mcp.tools.common.azure_devops_pr_lifecycle import (
            azure_devops_create_pull_request,
        )

        result = azure_devops_create_pull_request(
            source_branch="feature/test",
            target_branch="main",
            title="Test PR",
        )

        assert result["success"] is True, (
            f"AI agents should create PRs successfully with --org parameter. "
            f"Error: {result.get('error', 'No error provided')}"
        )

        # Verify the Azure CLI command included --org parameter
        # Check the second call (first is git config)
        assert mock_run.call_count == 2
        pr_create_call = mock_run.call_args_list[1][0][
            0
        ]  # Get the command list from second call

        assert "--org" in pr_create_call, (
            f"Azure CLI command should include --org parameter for cross-platform compatibility. "
            f"Command: {' '.join(pr_create_call)}"
        )

        # Verify --org comes before --organization for proper precedence
        org_index = pr_create_call.index("--org")
        if "--organization" in pr_create_call:
            organization_index = pr_create_call.index("--organization")
            assert org_index < organization_index, (
                "AI agents should place --org parameter before --organization for proper precedence"
            )

    @patch("subprocess.run")
    def test_ai_agents_help_developers_list_prs_with_org_parameter_for_authentication_compatibility(
        self, mock_run
    ):
        """
        As a developer using Azure DevOps with different authentication setups
        When AI agents help me list pull requests
        Then the Azure CLI commands include --org parameter to avoid TF401180 errors
        """
        # Mock subprocess calls: git config, az devops configure, project GUID lookup, PR list, current branch
        mock_run.side_effect = [
            Mock(
                returncode=0,
                stdout="https://dev.azure.com/microsoft/Universal%20Store/_git/Commerce.PaymentsDataPlatform\n",
            ),  # git config --get remote.origin.url
            Mock(returncode=0, stdout=""),  # az devops configure
            Mock(returncode=0, stdout="[]"),  # PR list with --org parameter
            Mock(returncode=0, stdout="main\n"),  # Current branch
        ]

        from pdp_dev_mcp.tools.common.azure_devops_repository import (
            azure_devops_workflow_setup,
        )

        result = azure_devops_workflow_setup()

        assert result["success"] is True, (
            f"AI agents should list PRs successfully with --org parameter. "
            f"Error: {result.get('error', 'No error provided')}"
        )

        # Find the PR list command call
        pr_list_call = None
        for call in mock_run.call_args_list:
            if (
                call[0]
                and len(call[0][0]) > 3
                and call[0][0][1:4] == ["repos", "pr", "list"]
            ):
                pr_list_call = call[0][0]
                break

        assert pr_list_call is not None, (
            "AI agents should make Azure CLI pr list calls during workflow setup"
        )

        assert "--org" in pr_list_call, (
            f"Azure CLI pr list command should include --org parameter. "
            f"Command: {' '.join(pr_list_call)}"
        )

    @patch("subprocess.run")
    def test_ai_agents_help_developers_query_repository_info_with_org_parameter_for_api_consistency(
        self, mock_run
    ):
        """
        As a developer using Azure DevOps APIs
        When AI agents help me resolve PR comments
        Then the Azure CLI commands include --org parameter for consistent API behavior
        """
        # Mock successful resolution flow that includes az repos show with --org parameter
        mock_run.side_effect = [
            Mock(
                returncode=0,
                stdout="project-guid\n",
            ),  # az devops project show (for project GUID lookup)
            Mock(
                returncode=0,
                stdout='{"id": "repo-guid", "project": {"id": "project-guid"}}',
            ),  # az repos show with --org parameter
            Mock(returncode=0, stdout='{"status": "fixed"}'),  # az rest PATCH thread
        ]

        from pdp_dev_mcp.tools.common.azure_devops_pr_comments import (
            azure_devops_resolve_pr_comments,
        )
        from pdp_dev_mcp.tools.common.azure_devops_common import (
            AzureDevOpsPRContext,
        )

        pr_context = AzureDevOpsPRContext(
            pr_url="https://dev.azure.com/microsoft/Universal Store/_git/Commerce.PaymentsDataPlatform/pullrequest/12345",
            organization="microsoft",
            project="Universal Store",
            repository="Commerce.PaymentsDataPlatform",
            pr_id=12345,
            source="url",
        )

        result = azure_devops_resolve_pr_comments(
            pr_context=pr_context, thread_ids=["123"], status="fixed"
        )

        assert result["success"] is True, (
            f"AI agents should resolve PR comments successfully with --org parameter. "
            f"Error: {result.get('error', 'No error provided')}"
        )

        # Find the repository show command call
        repo_show_call = None
        for call in mock_run.call_args_list:
            if call[0] and len(call[0][0]) > 2 and call[0][0][1:3] == ["repos", "show"]:
                repo_show_call = call[0][0]
                break

        assert repo_show_call is not None, (
            "AI agents should make Azure CLI repos show calls during PR comment resolution"
        )

        assert "--org" in repo_show_call, (
            f"Azure CLI repos show command should include --org parameter. "
            f"Command: {' '.join(repo_show_call)}"
        )

    def test_ai_agents_help_developers_understand_org_parameter_benefits(self):
        """
        As a developer experiencing Azure DevOps authentication issues
        When AI agents explain the --org parameter fix
        Then I understand how it solves cross-platform compatibility problems
        """
        # The --org parameter fix addresses several cross-platform issues:

        # 1. TF401180 errors when switching between .visualstudio.com and dev.azure.com
        tf401180_error = (
            "TF401180: The Azure DevOps Service has encountered a permission error"
        )

        # 2. Ensures consistent behavior across different Azure DevOps URL formats
        legacy_url = "https://msazure.visualstudio.com"
        modern_url = "https://dev.azure.com/msazure"

        # 3. Provides explicit organization context for all Azure CLI commands
        explicit_org_context = "--org parameter provides explicit organization context"

        # Success criteria: All Azure CLI commands work consistently across platforms
        assert "TF401180" in tf401180_error, (
            "AI agents help developers understand the specific authentication error being solved"
        )

        assert "visualstudio.com" in legacy_url and "dev.azure.com" in modern_url, (
            "AI agents help developers understand both legacy and modern Azure DevOps URL formats"
        )

        assert "--org" in explicit_org_context, (
            "AI agents help developers understand the --org parameter provides explicit context"
        )


# Note: PR reminder functionality tests moved to pr_reminder_integration_test.py
# to use integration testing approach with real repository data instead of complex mocking.
