"""
Tests for Enhanced Repository Discovery - behavior-focused tests.

Tests focus on what AI agents can accomplish when helping developers
work effectively with both single-repo and multi-repo workspaces.
"""

from unittest.mock import Mock, patch
import pytest

from pdp_dev_mcp.tools.common.enhanced_repository_discovery import (
    azure_devops_repository_discovery_enhanced,
    find_git_repositories,
    parse_azure_devops_url,
    infer_target_repository,
)


class TestAIAgentsCanDiscoverRepositoriesInSingleRepoWorkspaces:
    """Test what AI agents can accomplish when helping developers in traditional single-repo workspaces."""

    def test_ai_agents_can_help_developers_discover_current_repository_context(
        self,
    ) -> None:
        """AI agents should discover repository info when working directory is within a git repository."""
        with (
            patch("subprocess.run") as mock_run,
            patch("os.path.exists") as mock_exists,
            patch("os.getcwd") as mock_getcwd,
            patch("os.listdir") as mock_listdir,
            patch("os.path.dirname") as mock_dirname,
        ):
            # Given: Developer is working in a git repository
            mock_getcwd.return_value = "/path/to/project"
            mock_exists.side_effect = lambda path: path == "/path/to/project/.git"
            mock_listdir.return_value = ["src", "tests", ".git", "README.md"]
            mock_dirname.return_value = "/path/to"

            mock_run.return_value = Mock(
                returncode=0,
                stdout="https://dev.azure.com/microsoft/Universal%20Store/_git/Commerce.PaymentsDataPlatform\n",
            )

            # When: AI agent discovers repository context
            result = azure_devops_repository_discovery_enhanced()

            # Then: AI agent gets complete repository information for developer assistance
            assert result["success"] is True, (
                "AI agents need successful discovery to help developers with Azure DevOps operations"
            )
            assert result["organization"] == "microsoft", (
                "AI agents need organization info for Azure DevOps CLI configuration"
            )
            assert result["project"] == "Universal Store", (
                "AI agents need project info with proper URL decoding for space-containing names"
            )
            assert result["repository"] == "Commerce.PaymentsDataPlatform", (
                "AI agents need repository name for PR and code analysis operations"
            )

    def test_ai_agents_can_help_developers_discover_repository_from_subdirectory(
        self,
    ) -> None:
        """AI agents should walk up directory tree to find git repository root."""
        with (
            patch("subprocess.run") as mock_run,
            patch("os.path.exists") as mock_exists,
            patch("os.getcwd") as mock_getcwd,
            patch("os.path.dirname") as mock_dirname,
            patch("os.listdir") as mock_listdir,
        ):
            # Given: Developer is in a subdirectory of a git repository
            mock_getcwd.return_value = "/path/to/project/src/components"
            mock_listdir.return_value = ["src", "tests", ".git", "README.md"]

            # Mock directory tree walking
            mock_dirname.side_effect = lambda x: {
                "/path/to/project/src/components": "/path/to/project/src",
                "/path/to/project/src": "/path/to/project",
                "/path/to/project": "/path/to",
                "/path/to": "/path",
                "/path": "/",
                "/": "/",  # Filesystem root
            }.get(x, "/")

            # Mock .git existence only at project root
            mock_exists.side_effect = lambda path: path == "/path/to/project/.git"

            mock_run.return_value = Mock(
                returncode=0,
                stdout="https://dev.azure.com/microsoft/Universal%20Store/_git/Commerce.PaymentsDataPlatform\n",
            )

            # When: AI agent discovers repository context from subdirectory
            result = azure_devops_repository_discovery_enhanced()

            # Then: AI agent finds repository root and gets complete information
            assert result["success"] is True, (
                "AI agents need to find repository root from any subdirectory for flexible operations"
            )

    def test_ai_agents_can_help_developers_with_explicit_working_directory(
        self,
    ) -> None:
        """AI agents should respect explicit working directory specifications from developers."""
        with (
            patch("subprocess.run") as mock_run,
            patch("os.path.exists") as mock_exists,
            patch("os.listdir") as mock_listdir,
            patch("os.path.dirname") as mock_dirname,
        ):
            # Given: Developer specifies explicit working directory
            explicit_path = "/custom/project/path"
            mock_exists.side_effect = lambda path: path == f"{explicit_path}/.git"
            mock_listdir.return_value = ["src", "tests", ".git", "README.md"]
            mock_dirname.return_value = "/custom/project"
            mock_run.return_value = Mock(
                returncode=0,
                stdout="https://dev.azure.com/microsoft/TestProject/_git/TestRepo\n",
            )

            # When: AI agent uses explicit working directory
            result = azure_devops_repository_discovery_enhanced(
                working_directory=explicit_path
            )

            # Then: AI agent respects explicit path and discovers repository info
            assert result["success"] is True, (
                "AI agents need to respect explicit working directory for targeted repository operations"
            )
            assert result["repository"] == "TestRepo", (
                "AI agents need to discover correct repository from explicit path"
            )


class TestAIAgentsCanDiscoverRepositoriesInMultiRepoWorkspaces:
    """Test what AI agents can accomplish when helping developers in multi-repo VS Code workspaces."""

    def test_ai_agents_can_help_developers_discover_multiple_repositories(self) -> None:
        """AI agents should discover all available repositories in multi-repo workspaces."""
        with (
            patch("os.listdir") as mock_listdir,
            patch("os.path.isdir") as mock_isdir,
            patch("os.path.exists") as mock_exists,
            patch("subprocess.run") as mock_run,
        ):
            # Given: Multi-repo workspace with several repositories
            mock_listdir.return_value = [
                "CFS-Payments-DataPlatform-PMT",
                "Commerce.PaymentsDataPlatform",
                "some-other-folder",
                "CFS-Payments-DataPlatform-BIN",
            ]

            # Mock directory structure
            mock_isdir.side_effect = lambda path: any(
                path.endswith(repo)
                for repo in [
                    "CFS-Payments-DataPlatform-PMT",
                    "Commerce.PaymentsDataPlatform",
                    "some-other-folder",
                    "CFS-Payments-DataPlatform-BIN",
                ]
            )

            # Mock .git existence for repo directories only
            mock_exists.side_effect = lambda path: (
                "/.git" in path
                and any(
                    repo in path
                    for repo in [
                        "CFS-Payments-DataPlatform-PMT",
                        "Commerce.PaymentsDataPlatform",
                        "CFS-Payments-DataPlatform-BIN",
                    ]
                )
                and "some-other-folder" not in path
            )

            # Mock git remote responses for different repos
            def mock_git_response(cmd, **kwargs):
                cwd = kwargs.get("cwd", "")
                if "PMT" in cwd:
                    return Mock(
                        returncode=0,
                        stdout="https://dev.azure.com/microsoft/PMT/_git/CFS-Payments-DataPlatform-PMT\n",
                    )
                elif "Commerce.PaymentsDataPlatform" in cwd:
                    return Mock(
                        returncode=0,
                        stdout="https://dev.azure.com/microsoft/Universal%20Store/_git/Commerce.PaymentsDataPlatform\n",
                    )
                elif "BIN" in cwd:
                    return Mock(
                        returncode=0,
                        stdout="https://dev.azure.com/microsoft/BIN/_git/CFS-Payments-DataPlatform-BIN\n",
                    )
                return Mock(returncode=1, stderr="Not a git repository")

            mock_run.side_effect = mock_git_response

            # When: AI agent searches for repositories from workspace root
            repositories = find_git_repositories("/workspace/root")

            # Then: AI agent discovers all valid repositories
            assert len(repositories) == 3, (
                "AI agents need to discover all valid repositories in multi-repo workspaces"
            )

            repo_names = [repo["name"] for repo in repositories]
            assert "CFS-Payments-DataPlatform-PMT" in repo_names, (
                "AI agents need to find PMT repository for PaymentsJournal operations"
            )
            assert "Commerce.PaymentsDataPlatform" in repo_names, (
                "AI agents need to find main PDP repository for comparative operations"
            )
            assert "CFS-Payments-DataPlatform-BIN" in repo_names, (
                "AI agents need to find BIN repository for cross-repo analysis"
            )

    def test_ai_agents_can_help_developers_with_intelligent_repository_inference(
        self,
    ) -> None:
        """AI agents should intelligently infer target repository in multi-repo scenarios."""
        with (
            patch("os.getcwd") as mock_getcwd,
            patch("os.listdir") as mock_listdir,
            patch("os.path.isdir") as mock_isdir,
            patch("os.path.exists") as mock_exists,
            patch("subprocess.run") as mock_run,
        ):
            # Given: Developer is working within one repository in multi-repo workspace
            mock_getcwd.return_value = "/workspace/CFS-Payments-DataPlatform-PMT/src"
            mock_listdir.return_value = [
                "CFS-Payments-DataPlatform-PMT",
                "Commerce.PaymentsDataPlatform",
            ]
            mock_isdir.return_value = True

            # Mock .git existence for both repos
            mock_exists.side_effect = lambda path: "/.git" in path

            # Mock git responses
            def mock_git_response(cmd, **kwargs):
                cwd = kwargs.get("cwd", "")
                if "PMT" in cwd:
                    return Mock(
                        returncode=0,
                        stdout="https://dev.azure.com/microsoft/PMT/_git/CFS-Payments-DataPlatform-PMT\n",
                    )
                else:
                    return Mock(
                        returncode=0,
                        stdout="https://dev.azure.com/microsoft/Universal%20Store/_git/Commerce.PaymentsDataPlatform\n",
                    )

            mock_run.side_effect = mock_git_response

            # When: AI agent discovers repository context
            result = azure_devops_repository_discovery_enhanced()

            # Then: AI agent intelligently selects the repository developer is working in
            assert result["success"] is True, (
                "AI agents need successful inference for seamless multi-repo operations"
            )
            assert result["repository"] == "CFS-Payments-DataPlatform-PMT", (
                "AI agents should infer PMT repository when developer is working in PMT subdirectory"
            )

    def test_ai_agents_can_help_developers_handle_ambiguous_multi_repo_scenarios(
        self,
    ) -> None:
        """AI agents should provide clear guidance when repository selection is ambiguous."""
        with (
            patch("os.getcwd") as mock_getcwd,
            patch("os.listdir") as mock_listdir,
            patch("os.path.isdir") as mock_isdir,
            patch("os.path.exists") as mock_exists,
            patch("os.path.dirname") as mock_dirname,
            patch("subprocess.run") as mock_run,
        ):
            # Given: Developer is in workspace root with multiple repositories, no clear preference
            mock_getcwd.return_value = "/workspace"  # Not inside any specific repo
            mock_listdir.return_value = ["repo1", "repo2", "repo3"]
            mock_isdir.return_value = True

            # Mock directory walking to show we're not in a git repo at current level
            mock_dirname.side_effect = lambda x: "/" if x == "/workspace" else x

            # Mock .git existence only for subdirectories, not workspace root
            mock_exists.side_effect = lambda path: (
                "/.git" in path
                and any(repo in path for repo in ["repo1", "repo2", "repo3"])
                and "/workspace/.git" not in path
            )

            # Mock git responses for all repos with different names
            def mock_git_response(cmd, **kwargs):
                cwd = kwargs.get("cwd", "")
                if "repo1" in cwd:
                    return Mock(
                        returncode=0,
                        stdout="https://dev.azure.com/microsoft/Project1/_git/TestRepo1\n",
                    )
                elif "repo2" in cwd:
                    return Mock(
                        returncode=0,
                        stdout="https://dev.azure.com/microsoft/Project2/_git/TestRepo2\n",
                    )
                elif "repo3" in cwd:
                    return Mock(
                        returncode=0,
                        stdout="https://dev.azure.com/microsoft/Project3/_git/TestRepo3\n",
                    )
                return Mock(returncode=1, stderr="Not a git repository")

            mock_run.side_effect = mock_git_response

            # When: AI agent encounters ambiguous scenario
            result = azure_devops_repository_discovery_enhanced()

            # Then: AI agent provides clear guidance about ambiguity
            assert result["success"] is False, (
                "AI agents should indicate failure when repository selection is ambiguous"
            )
            assert "Multiple repositories" in result["error"], (
                "AI agents should explain the ambiguity to help developers understand the issue"
            )
            assert "available_repositories" in result, (
                "AI agents should list available repositories for developer selection"
            )
            assert len(result["available_repositories"]) > 1, (
                "AI agents should provide the list of discovered repositories for developer choice"
            )


class TestAIAgentsCanHandleRepositoryDiscoveryEdgeCases:
    """Test what AI agents can accomplish when helping developers handle discovery edge cases."""

    def test_ai_agents_can_help_developers_handle_non_azure_devops_repositories(
        self,
    ) -> None:
        """AI agents should gracefully handle non-Azure DevOps git repositories."""
        with (
            patch("subprocess.run") as mock_run,
            patch("os.path.exists") as mock_exists,
            patch("os.getcwd") as mock_getcwd,
        ):
            # Given: Repository with non-Azure DevOps remote
            mock_getcwd.return_value = "/path/to/project"
            mock_exists.side_effect = lambda path: path == "/path/to/project/.git"
            mock_run.return_value = Mock(
                returncode=0,
                stdout="https://github.com/microsoft/some-repo.git\n",
            )

            # When: AI agent attempts discovery
            result = azure_devops_repository_discovery_enhanced()

            # Then: AI agent handles non-Azure DevOps repositories gracefully
            assert result["success"] is False, (
                "AI agents should clearly indicate when repository is not Azure DevOps compatible"
            )

    def test_ai_agents_can_help_developers_handle_git_command_failures(self) -> None:
        """AI agents should provide clear guidance when git commands fail."""
        with (
            patch("subprocess.run") as mock_run,
            patch("os.path.exists") as mock_exists,
            patch("os.getcwd") as mock_getcwd,
        ):
            # Given: Git command fails (e.g., corrupted repository)
            mock_getcwd.return_value = "/path/to/project"
            mock_exists.side_effect = lambda path: path == "/path/to/project/.git"
            mock_run.return_value = Mock(
                returncode=1,
                stderr="fatal: not a git repository",
            )

            # When: AI agent attempts discovery
            result = azure_devops_repository_discovery_enhanced()

            # Then: AI agent provides clear error information
            assert result["success"] is False, (
                "AI agents should clearly indicate git command failures"
            )
            assert "error" in result, (
                "AI agents should provide error details for developer troubleshooting"
            )

    def test_ai_agents_can_help_developers_handle_permission_errors(self) -> None:
        """AI agents should gracefully handle permission errors during repository discovery."""
        with (
            patch("os.listdir") as mock_listdir,
            patch("os.getcwd") as mock_getcwd,
        ):
            # Given: Permission error when listing directories
            mock_getcwd.return_value = "/restricted/workspace"
            mock_listdir.side_effect = PermissionError("Permission denied")

            # When: AI agent attempts discovery
            result = azure_devops_repository_discovery_enhanced()

            # Then: AI agent handles permission errors gracefully
            assert result["success"] is False, (
                "AI agents should handle permission errors gracefully"
            )
            assert "error" in result, (
                "AI agents should provide clear error information for permission issues"
            )


class TestAzureDevOpsUrlParsing:
    """Test Azure DevOps URL parsing functionality for AI agents."""

    def test_ai_agents_can_parse_modern_azure_devops_urls(self) -> None:
        """AI agents should correctly parse modern dev.azure.com URLs."""
        # Given: Modern Azure DevOps URL
        url = "https://dev.azure.com/microsoft/Universal%20Store/_git/Commerce.PaymentsDataPlatform"

        # When: AI agent parses URL
        org, project, repository = parse_azure_devops_url(url)

        # Then: AI agent correctly extracts all components
        assert org == "microsoft", (
            "AI agents need accurate organization parsing for Azure DevOps operations"
        )
        assert project == "Universal Store", (
            "AI agents need proper URL decoding for project names with spaces"
        )
        assert repository == "Commerce.PaymentsDataPlatform", (
            "AI agents need accurate repository name for PR and code operations"
        )

    def test_ai_agents_can_parse_legacy_visualstudio_urls(self) -> None:
        """AI agents should correctly parse legacy .visualstudio.com URLs."""
        # Given: Legacy Azure DevOps URL
        url = "https://msazure.visualstudio.com/DefaultCollection/One/_git/Commerce.PaymentsDataPlatform"

        # When: AI agent parses URL
        org, project, repository = parse_azure_devops_url(url)

        # Then: AI agent correctly extracts all components
        assert org == "msazure", (
            "AI agents need accurate organization parsing for legacy URLs"
        )
        assert project == "One", (
            "AI agents need accurate project parsing for legacy URLs"
        )
        assert repository == "Commerce.PaymentsDataPlatform", (
            "AI agents need accurate repository parsing for legacy URLs"
        )

    def test_ai_agents_can_handle_unsupported_url_formats(self) -> None:
        """AI agents should gracefully handle unsupported URL formats."""
        # Given: Unsupported URL format
        url = "https://github.com/microsoft/some-repo.git"

        # When: AI agent parses URL
        org, project, repository = parse_azure_devops_url(url)

        # Then: AI agent returns empty components for unsupported URLs
        assert org == "", (
            "AI agents should return empty organization for unsupported URLs"
        )
        assert project == "", (
            "AI agents should return empty project for unsupported URLs"
        )
        assert repository == "", (
            "AI agents should return empty repository for unsupported URLs"
        )


class TestRepositoryInference:
    """Test intelligent repository inference functionality for AI agents."""

    def test_ai_agents_can_infer_repository_from_working_directory(self) -> None:
        """AI agents should prefer repository that contains the working directory."""
        # Given: Multiple repositories and working directory hint
        repositories = [
            {"path": "/workspace/repo1", "name": "repo1"},
            {"path": "/workspace/repo2", "name": "repo2"},
            {"path": "/workspace/repo3", "name": "repo3"},
        ]
        working_directory = "/workspace/repo2/src/components"

        # When: AI agent infers target repository
        result = infer_target_repository(repositories, working_directory)

        # Then: AI agent selects repository containing working directory
        assert result is not None, (
            "AI agents should successfully infer repository from working directory context"
        )
        assert result["name"] == "repo2", (
            "AI agents should select repository that contains the working directory"
        )

    def test_ai_agents_can_handle_single_repository_scenarios(self) -> None:
        """AI agents should automatically select when only one repository is available."""
        # Given: Single repository
        repositories = [{"path": "/workspace/repo1", "name": "repo1"}]

        # When: AI agent infers target repository
        result = infer_target_repository(repositories)

        # Then: AI agent selects the single available repository
        assert result is not None, (
            "AI agents should select single repository automatically"
        )
        assert result["name"] == "repo1", (
            "AI agents should return the single available repository"
        )

    def test_ai_agents_can_detect_ambiguous_scenarios(self) -> None:
        """AI agents should detect when repository selection is ambiguous."""
        # Given: Multiple repositories without clear preference
        repositories = [
            {"path": "/workspace/repo1", "name": "repo1"},
            {"path": "/workspace/repo2", "name": "repo2"},
            {"path": "/workspace/repo3", "name": "repo3"},
        ]
        working_directory = "/different/path"  # Not related to any repository

        # When: AI agent attempts inference
        result = infer_target_repository(repositories, working_directory)

        # Then: AI agent detects ambiguity
        assert result is None, (
            "AI agents should return None when repository selection is ambiguous"
        )
