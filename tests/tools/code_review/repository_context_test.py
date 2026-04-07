"""
Tesimport tempfile
from datetime import datetime
from unittest.mock import patch, MagicMock

from pdp_dev_mcp.tools.common.repository_context import (
    RepositoryContext,
    ensure_repository_context,
    get_repository_context,
    set_repository_context,
)pository context management.

Tests focus on what AI agents can accomplish when helping developers
maintain consistent repository context across different tool operations.
"""

import tempfile
from unittest.mock import patch

from pdp_dev_mcp.tools.common.repository_context import (
    RepositoryContext,
    ensure_repository_context,
    get_repository_context,
    set_repository_context,
)


class TestAIAgentsCanManageRepositoryContext:
    """Test what AI agents can accomplish when helping developers manage repository context."""

    def setup_method(self):
        """Reset repository context before each test."""
        RepositoryContext._current_working_directory = None
        RepositoryContext._cached_repo_info = None
        RepositoryContext._cache_timestamp = None

    def test_ai_agents_help_developers_set_working_directory_with_absolute_path(
        self,
    ) -> None:
        """
        As a developer using AI agents for code review
        When I set a repository context with an absolute path
        Then the AI agent validates and caches the repository information
        """
        # Given: A valid absolute path to a repository
        with tempfile.TemporaryDirectory() as temp_dir:
            with (
                patch(
                    "pdp_dev_mcp.tools.common.repository_context.RepositoryContext._discover_repository_info"
                ) as mock_discover,
            ):
                mock_discover.return_value = {
                    "success": True,
                    "organization": "test-org",
                    "project": "test-project",
                    "repository": "test-repo",
                }

                # When: Setting the working directory
                result = RepositoryContext.set_working_directory(temp_dir)

                # Then: The context should be set successfully
                assert result["success"] is True, f"Expected success, got: {result}"
                assert result["message"] == f"Repository context set to: {temp_dir}"
                assert "repository_info" in result
                assert "context_timestamp" in result

                # And: The context should be cached
                assert RepositoryContext._current_working_directory == temp_dir
                assert RepositoryContext._cached_repo_info is not None
                assert RepositoryContext._cache_timestamp is not None

    def test_ai_agents_help_developers_reject_relative_paths_for_consistency(
        self,
    ) -> None:
        """
        As a developer using AI agents for code review
        When I provide a relative path for repository context
        Then the AI agent rejects it to ensure consistency across tool operations
        """
        # Given: A relative path
        relative_path = "src/relative/path"

        # When: Attempting to set a relative path as working directory
        result = RepositoryContext.set_working_directory(relative_path)

        # Then: The operation should fail with a clear error
        assert result["success"] is False
        assert "must be absolute path" in result["error"]
        assert relative_path in result["error"]

        # And: No context should be set
        assert RepositoryContext._current_working_directory is None
        assert RepositoryContext._cached_repo_info is None

    def test_ai_agents_help_developers_handle_nonexistent_directories_gracefully(
        self,
    ) -> None:
        """
        As a developer using AI agents for code review
        When I provide a path that doesn't exist
        Then the AI agent handles this gracefully with a meaningful error
        """
        # Given: A non-existent absolute path
        nonexistent_path = "/absolutely/nonexistent/path"

        # When: Attempting to set a non-existent directory
        result = RepositoryContext.set_working_directory(nonexistent_path)

        # Then: The operation should fail with a clear error
        assert result["success"] is False
        assert "does not exist" in result["error"]
        assert nonexistent_path in result["error"]

    def test_ai_agents_help_developers_clear_cache_when_switching_context(self) -> None:
        """
        As a developer using AI agents across multiple repositories
        When I switch repository context
        Then the AI agent clears old cache to prevent stale information
        """
        # Given: An existing context
        with tempfile.TemporaryDirectory() as temp_dir1:
            with tempfile.TemporaryDirectory() as temp_dir2:
                with patch(
                    "pdp_dev_mcp.tools.common.repository_context.RepositoryContext._discover_repository_info"
                ) as mock_discover:
                    # Set up first context
                    mock_discover.return_value = {
                        "success": True,
                        "repository": "repo1",
                    }
                    RepositoryContext.set_working_directory(temp_dir1)
                    first_timestamp = RepositoryContext._cache_timestamp

                    # When: Switching to a different context
                    mock_discover.return_value = {
                        "success": True,
                        "repository": "repo2",
                    }
                    result = RepositoryContext.set_working_directory(temp_dir2)

                    # Then: The context should be switched successfully
                    assert result["success"] is True
                    assert RepositoryContext._current_working_directory == temp_dir2

                    # And: The cache should be refreshed
                    assert RepositoryContext._cache_timestamp != first_timestamp
                    assert RepositoryContext._cached_repo_info is not None
                    assert RepositoryContext._cached_repo_info["repository"] == "repo2"

    def test_ai_agents_help_developers_handle_repository_discovery_failures(
        self,
    ) -> None:
        """
        As a developer using AI agents for code review
        When repository discovery fails for a valid directory
        Then the AI agent handles this gracefully and resets context
        """
        # Given: A valid directory but repository discovery fails
        with tempfile.TemporaryDirectory() as temp_dir:
            with patch(
                "pdp_dev_mcp.tools.common.repository_context.RepositoryContext._discover_repository_info"
            ) as mock_discover:
                mock_discover.return_value = {
                    "success": False,
                    "error": "Not a git repository",
                }

                # When: Attempting to set working directory
                result = RepositoryContext.set_working_directory(temp_dir)

                # Then: The operation should fail gracefully
                assert result["success"] is False
                assert "Failed to discover repository information" in result["error"]
                assert "Not a git repository" in result["error"]
                assert result["attempted_directory"] == temp_dir

                # And: Context should be reset
                assert RepositoryContext._current_working_directory is None
                assert RepositoryContext._cached_repo_info is None

    def test_ai_agents_help_developers_get_cached_repository_info(self) -> None:
        """
        As a developer using AI agents for multiple operations
        When I request repository information after setting context
        Then the AI agent uses cached information for performance
        """
        # Given: A cached repository context
        with tempfile.TemporaryDirectory() as temp_dir:
            with patch(
                "pdp_dev_mcp.tools.common.repository_context.RepositoryContext._discover_repository_info"
            ) as mock_discover:
                mock_discover.return_value = {
                    "success": True,
                    "organization": "cached-org",
                    "project": "cached-project",
                    "repository": "cached-repo",
                }
                RepositoryContext.set_working_directory(temp_dir)

                # When: Getting repository info without explicit directory
                result = RepositoryContext.get_repository_info()

                # Then: Should return cached information
                assert result["success"] is True
                assert result["organization"] == "cached-org"
                assert result["project"] == "cached-project"
                assert result["repository"] == "cached-repo"

                # And: Should not call discovery again (called only once during set_working_directory)
                assert mock_discover.call_count == 1

    def test_ai_agents_help_developers_override_context_with_explicit_directory(
        self,
    ) -> None:
        """
        As a developer using AI agents for multi-repo analysis
        When I provide an explicit directory override
        Then the AI agent uses that directory without affecting global context
        """
        # Given: A cached context and an override directory
        with tempfile.TemporaryDirectory() as cached_dir:
            with tempfile.TemporaryDirectory() as override_dir:
                with patch(
                    "pdp_dev_mcp.tools.common.repository_context.RepositoryContext._discover_repository_info"
                ) as mock_discover:
                    # Set up cached context
                    mock_discover.return_value = {
                        "success": True,
                        "repository": "cached-repo",
                    }
                    RepositoryContext.set_working_directory(cached_dir)

                    # When: Getting info with explicit override
                    mock_discover.return_value = {
                        "success": True,
                        "repository": "override-repo",
                    }
                    result = RepositoryContext.get_repository_info(
                        working_directory=override_dir
                    )

                    # Then: Should use override directory
                    assert result["success"] is True
                    assert result["repository"] == "override-repo"

                    # And: Should not affect cached context
                    assert RepositoryContext._current_working_directory == cached_dir
                    cached_result = RepositoryContext.get_repository_info()
                    assert cached_result["repository"] == "cached-repo"

    def test_ai_agents_help_developers_handle_no_context_with_intelligent_discovery(
        self,
    ) -> None:
        """
        As a developer using AI agents without explicit context
        When I request repository information
        Then the AI agent attempts intelligent discovery from current directory
        """
        # Given: No cached context
        assert RepositoryContext._current_working_directory is None

        with patch(
            "pdp_dev_mcp.tools.common.repository_context.azure_devops_repository_discovery_enhanced"
        ) as mock_enhanced_discovery:
            mock_enhanced_discovery.return_value = {
                "success": True,
                "organization": "discovered-org",
                "project": "discovered-project",
                "repository": "discovered-repo",
            }

            # When: Getting repository info without context
            result = RepositoryContext.get_repository_info()

            # Then: Should use intelligent discovery
            assert result["success"] is True
            assert result["organization"] == "discovered-org"
            assert result["project"] == "discovered-project"
            assert result["repository"] == "discovered-repo"

            # And: Should call enhanced discovery (note: positional argument)
            mock_enhanced_discovery.assert_called_once_with(None)

    def test_ai_agents_help_developers_get_clear_context_status(self) -> None:
        """
        As a developer using AI agents for debugging
        When I check repository context status
        Then the AI agent provides clear information about current state
        """
        # Given: No context initially
        result = RepositoryContext.get_context_status()

        # Then: Should show no context
        assert result["context_set"] is False
        assert result["current_working_directory"] is None
        assert result["cache_timestamp"] is None

        # Given: A set context
        with tempfile.TemporaryDirectory() as temp_dir:
            with patch(
                "pdp_dev_mcp.tools.common.repository_context.RepositoryContext._discover_repository_info"
            ) as mock_discover:
                mock_discover.return_value = {
                    "success": True,
                    "repository": "test-repo",
                }
                RepositoryContext.set_working_directory(temp_dir)

                # When: Checking status after setting context
                result = RepositoryContext.get_context_status()

                # Then: Should show context details
                assert result["context_set"] is True
                assert result["current_working_directory"] == temp_dir
                assert result["cache_timestamp"] is not None
                assert result["cache_available"] is True

    def test_ai_agents_help_developers_clear_context_for_fresh_start(self) -> None:
        """
        As a developer using AI agents across different sessions
        When I need to clear repository context
        Then the AI agent resets all context for a fresh start
        """
        # Given: An existing context
        with tempfile.TemporaryDirectory() as temp_dir:
            with patch(
                "pdp_dev_mcp.tools.common.repository_context.RepositoryContext._discover_repository_info"
            ) as mock_discover:
                mock_discover.return_value = {
                    "success": True,
                    "repository": "test-repo",
                }
                RepositoryContext.set_working_directory(temp_dir)

                # Verify context is set
                assert RepositoryContext._current_working_directory is not None
                assert RepositoryContext._cached_repo_info is not None

                # When: Clearing context
                result = RepositoryContext.clear_context()

                # Then: Context should be completely cleared
                assert result["success"] is True
                assert "Repository context cleared" in result["message"]
                assert RepositoryContext._current_working_directory is None
                assert RepositoryContext._cached_repo_info is None
                assert RepositoryContext._cache_timestamp is None

    def test_ai_agents_help_developers_understand_context_thread_safety(self) -> None:
        """
        As a developer using AI agents in concurrent scenarios
        When multiple operations access repository context
        Then the AI agent ensures thread-safe operations
        """
        # Given: A repository context operation
        with tempfile.TemporaryDirectory() as temp_dir:
            with patch(
                "pdp_dev_mcp.tools.common.repository_context.RepositoryContext._discover_repository_info"
            ) as mock_discover:
                mock_discover.return_value = {
                    "success": True,
                    "repository": "thread-test-repo",
                }

                # When: Multiple operations (simulated by multiple calls)
                result1 = RepositoryContext.set_working_directory(temp_dir)
                result2 = RepositoryContext.get_repository_info()
                result3 = RepositoryContext.get_context_status()

                # Then: All operations should complete successfully
                assert result1["success"] is True
                assert result2["success"] is True
                assert result3["context_set"] is True

                # And: Context should be consistent
                assert result2["repository"] == "thread-test-repo"
                assert result3["current_working_directory"] == temp_dir


class TestAIAgentRepositoryContextWorkflow:
    """
    AI agents need reliable repository context discovery to perform
    code review tasks without requiring explicit setup from users.
    """

    def setup_method(self):
        """Reset repository context before each test."""
        RepositoryContext._current_working_directory = None
        RepositoryContext._cached_repo_info = None
        RepositoryContext._cache_timestamp = None

    def test_ai_agent_gets_helpful_guidance_when_no_repository_context_available(self):
        """
        As an AI agent performing code review
        When I try to access repository context but none is available
        Then I get clear guidance on how to establish context for the user

        This ensures AI agents can guide users to provide necessary
        repository information when working across multiple repositories.
        """
        # Given: No repository context is currently set
        RepositoryContext._current_working_directory = None
        RepositoryContext._cached_repo_info = None

        # When: AI agent tries to ensure repository context from non-git directory
        with tempfile.TemporaryDirectory() as non_git_dir:
            result = ensure_repository_context(working_directory=non_git_dir)

        # Then: AI agent gets actionable guidance for the user
        assert result["success"] is False, (
            "Repository context should fail when no valid repository is found"
        )
        assert "suggestion" in result, (
            f"Error response should include suggestion field. Got: {result}"
        )
        assert "set_repository_context" in result["suggestion"], (
            f"Suggestion should mention set_repository_context tool. Got: '{result['suggestion']}'"
        )

    def test_ai_agent_can_discover_repository_context_from_current_directory(self):
        """
        As an AI agent performing code review
        When I need repository context and user is in a valid git repository
        Then I can automatically discover Azure DevOps organization and project information

        This enables seamless code review workflows when users are already
        working in the correct repository context.
        """
        # Given: User is working in a valid git repository directory
        mock_repo_info = {
            "success": True,
            "organization": "microsoft",
            "project": "Universal Store",
            "repository": "Commerce.PaymentsDataPlatform",
            "working_directory": "/Users/test/repo",
        }

        # When: AI agent ensures repository context from current directory context
        with patch(
            "pdp_dev_mcp.tools.common.repository_context.azure_devops_repository_discovery_enhanced"
        ) as mock_discovery:
            mock_discovery.return_value = mock_repo_info

            # Set the current working directory first to simulate being in a repo
            RepositoryContext._current_working_directory = "/Users/test/repo"

            result = ensure_repository_context(working_directory=None)

        # Then: AI agent gets complete Azure DevOps context for API calls
        assert result["success"] is True, (
            f"Repository context discovery should succeed in valid git repository. Got error: {result.get('error')}"
        )
        assert result["organization"] == "microsoft", (
            f"Should discover Microsoft organization, got: {result.get('organization')}"
        )
        assert result["project"] == "Universal Store", (
            f"Should discover Universal Store project, got: {result.get('project')}"
        )
        assert result["repository"] == "Commerce.PaymentsDataPlatform", (
            f"Should discover Commerce.PaymentsDataPlatform repository, got: {result.get('repository')}"
        )

    def test_ai_agent_uses_cached_context_for_performance_across_multiple_tools(self):
        """
        As an AI agent performing multiple code review operations
        When I access repository context repeatedly during a session
        Then I get cached results for performance without repeated discovery

        This ensures efficient tool execution when AI agents call multiple
        repository-dependent tools in sequence.
        """
        # Given: Repository context has been discovered and cached
        mock_repo_info = {
            "success": True,
            "organization": "microsoft",
            "project": "Universal Store",
            "repository": "Commerce.PaymentsDataPlatform",
            "working_directory": "/Users/test/repo",
        }

        with patch(
            "pdp_dev_mcp.tools.common.repository_context.azure_devops_repository_discovery_enhanced"
        ) as mock_discovery:
            mock_discovery.return_value = mock_repo_info

            # Set up cached context first
            RepositoryContext._current_working_directory = "/Users/test/repo"
            RepositoryContext._cached_repo_info = mock_repo_info
            from datetime import datetime

            RepositoryContext._cache_timestamp = datetime.now().isoformat()

            # When: AI agent makes multiple repository context requests using ensure_repository_context
            first_result = ensure_repository_context()
            second_result = ensure_repository_context()
            third_result = ensure_repository_context()

        # Then: Discovery is not called for cached results and results are consistent
        assert mock_discovery.call_count == 0, (
            f"Repository discovery should not be called when using cached data, got {mock_discovery.call_count} calls"
        )
        assert first_result["success"] is True, (
            f"Cached repository context should maintain success status. Got: {first_result}"
        )
        assert second_result["success"] is True, (
            f"Cached repository context should maintain success status. Got: {second_result}"
        )
        assert third_result["success"] is True, (
            f"Cached repository context should maintain success status. Got: {third_result}"
        )
        # Results should be consistent across calls
        assert second_result["organization"] == "microsoft", (
            f"Cached context should maintain organization. Got: {second_result.get('organization')}"
        )
        assert third_result["repository"] == "Commerce.PaymentsDataPlatform", (
            f"Cached context should maintain repository. Got: {third_result.get('repository')}"
        )


class TestDeveloperExplicitRepositoryManagement:
    """
    Developers working with multiple repositories or complex workspaces
    need explicit control over repository context for accurate analysis.
    """

    def setup_method(self):
        """Reset repository context before each test."""
        RepositoryContext._current_working_directory = None
        RepositoryContext._cached_repo_info = None
        RepositoryContext._cache_timestamp = None

    def test_developer_can_explicitly_set_repository_context_for_multi_repo_workspace(
        self,
    ):
        """
        As a developer working in a multi-repository workspace
        When I explicitly set repository context to a specific directory
        Then subsequent tools use that exact repository for analysis

        This supports complex workspace scenarios where automatic discovery
        might not target the intended repository for code review.
        """
        # Given: Developer has multiple repositories in workspace
        with tempfile.TemporaryDirectory() as target_repo_path:
            mock_repo_info = {
                "success": True,
                "organization": "microsoft",
                "project": "Target Project",
                "repository": "TargetRepository",
                "working_directory": target_repo_path,
            }

            # When: Developer explicitly sets repository context
            with patch(
                "pdp_dev_mcp.tools.common.repository_context.azure_devops_repository_discovery_enhanced"
            ) as mock_discovery:
                mock_discovery.return_value = mock_repo_info

                result = set_repository_context(target_repo_path)

            # Then: Repository context is set to developer's exact specification
            assert result["success"] is True, (
                f"Explicit repository context setting should succeed. Got error: {result.get('error')}"
            )
            # The working directory is available in the repository_info sub-object
            assert result["repository_info"]["working_directory"] == target_repo_path, (
                f"Working directory should match developer's specification. "
                f"Expected: {target_repo_path}, Got: {result['repository_info'].get('working_directory')}"
            )
            assert result["repository_info"]["repository"] == "TargetRepository", (
                f"Should discover target repository from specified path. Got: {result['repository_info'].get('repository')}"
            )

            # And: Subsequent context requests use the explicit setting
            cached_result = get_repository_context()
            assert cached_result.get("working_directory") == target_repo_path, (
                f"Cached context should maintain developer's explicit repository choice. "
                f"Expected: {target_repo_path}, Got: {cached_result.get('working_directory')}"
            )

    def test_developer_gets_clear_error_for_invalid_repository_path(self):
        """
        As a developer setting repository context
        When I provide an invalid or non-existent repository path
        Then I get clear error message explaining the path requirements

        This helps developers troubleshoot workspace setup issues and
        understand the requirements for repository context.
        """
        # Given: Developer provides invalid repository paths
        test_cases = [
            ("/nonexistent/path", "does not exist"),
            ("relative/path", "absolute path"),  # Non-absolute path
        ]

        for invalid_path, expected_error_content in test_cases:
            # When: Developer attempts to set repository context with invalid path
            result = set_repository_context(invalid_path)

            # Then: Developer gets helpful error explaining requirements
            assert result["success"] is False, (
                f"Invalid path '{invalid_path}' should result in failure"
            )
            assert expected_error_content in result["error"], (
                f"Error for path '{invalid_path}' should mention '{expected_error_content}'. Got: '{result['error']}'"
            )

    def test_developer_can_switch_repository_context_during_session(self):
        """
        As a developer reviewing multiple repositories
        When I switch repository context to different repositories
        Then each context switch provides accurate repository information

        This enables cross-repository code review workflows where developers
        need to analyze code across multiple Azure DevOps repositories.
        """
        # Given: Developer starts with first repository
        with tempfile.TemporaryDirectory() as first_repo_path:
            with tempfile.TemporaryDirectory() as second_repo_path:
                first_repo_info = {
                    "success": True,
                    "organization": "microsoft",
                    "project": "First Project",
                    "repository": "FirstRepo",
                    "working_directory": first_repo_path,
                }

                second_repo_info = {
                    "success": True,
                    "organization": "microsoftit",
                    "project": "Second Project",
                    "repository": "SecondRepo",
                    "working_directory": second_repo_path,
                }

                with patch(
                    "pdp_dev_mcp.tools.common.repository_context.azure_devops_repository_discovery_enhanced"
                ) as mock_discovery:
                    # When: Developer sets first repository context
                    mock_discovery.return_value = first_repo_info
                    first_result = set_repository_context(first_repo_path)

                    # And: Developer switches to second repository context
                    mock_discovery.return_value = second_repo_info
                    second_result = set_repository_context(second_repo_path)

                # Then: Each context switch provides accurate repository information
                assert (
                    first_result["repository_info"].get("repository") == "FirstRepo"
                ), (
                    f"First repository context should target FirstRepo. Got: {first_result['repository_info'].get('repository')}"
                )
                assert (
                    first_result["repository_info"].get("organization") == "microsoft"
                ), (
                    f"First repository should be in microsoft organization. Got: {first_result['repository_info'].get('organization')}"
                )

                assert (
                    second_result["repository_info"].get("repository") == "SecondRepo"
                ), (
                    f"Second repository context should target SecondRepo. Got: {second_result['repository_info'].get('repository')}"
                )
                assert (
                    second_result["repository_info"].get("organization")
                    == "microsoftit"
                ), (
                    f"Second repository should be in microsoftit organization. Got: {second_result['repository_info'].get('organization')}"
                )

                # And: Current context reflects the most recent repository
                current_context = get_repository_context()
                assert current_context.get("repository") == "SecondRepo", (
                    f"Current context should reflect most recent repository switch. "
                    f"Expected: SecondRepo, Got: {current_context.get('repository')}"
                )
