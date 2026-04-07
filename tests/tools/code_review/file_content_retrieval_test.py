"""
Tests for file content retrieval tools - behavior-focused tests.

Tests focus on what AI agents can accomplish when retrieving actual file contents
from pull requests for code review analysis.
"""

import pytest
from unittest.mock import Mock, patch
from pdp_dev_mcp.tools.common.azure_devops_common import AzureDevOpsPRContext
from pdp_dev_mcp.tools.code_review.prescriptive_comments import (
    get_pr_file_changes_with_context,
    get_file_contents_with_context,
    FileChangesResult,
    FileChange,
    FileChangeItem,
)


class TestAIAgentsCanRetrieveFileChangesMetadata:
    """Test what AI agents can accomplish when fetching file change metadata from PRs."""

    @patch("subprocess.run")
    def test_ai_agents_can_fetch_file_changes_from_pull_requests(
        self, mock_run
    ) -> None:
        """AI agents should be able to retrieve file change metadata from Azure DevOps PRs."""
        # Mock subprocess calls for file changes retrieval
        mock_run.side_effect = [
            Mock(
                returncode=0,
                stdout='{"value": [{"id": 1}]}',  # PR iterations
            ),
            Mock(
                returncode=0,
                stdout='{"changeEntries": [{"item": {"path": "/src/payment_processor.py"}, "changeType": "edit"}]}',
            ),  # File changes
        ]

        # Create PR context
        context = AzureDevOpsPRContext(
            pr_url="https://dev.azure.com/microsoft/Universal%20Store/_git/Commerce.PaymentsDataPlatform/pullrequest/12345",
            organization="microsoft",
            project="Universal Store",
            repository="Commerce.PaymentsDataPlatform",
            pr_id=12345,
            source="test",
        )

        result = get_pr_file_changes_with_context(context)

        # AI agents need successful file change retrieval
        assert result.success is True, (
            "AI agents need functioning file change retrieval to understand what files changed in a PR"
        )

        # AI agents need the list of changed files
        assert len(result.changes) == 1, (
            "AI agents need accurate file change lists to know which files to analyze"
        )

        # AI agents need file path information
        assert result.changes[0].item.path == "/src/payment_processor.py", (
            "AI agents need correct file paths to fetch file contents"
        )

        # AI agents need change type information
        assert result.changes[0].change_type == "edit", (
            "AI agents need to know if files were added, edited, or deleted"
        )

    @patch("subprocess.run")
    def test_ai_agents_can_handle_multiple_file_changes_in_prs(self, mock_run) -> None:
        """AI agents should handle PRs with multiple file changes."""
        # Mock multiple file changes
        mock_run.side_effect = [
            Mock(returncode=0, stdout='{"value": [{"id": 1}]}'),
            Mock(
                returncode=0,
                stdout='{"changeEntries": ['
                '{"item": {"path": "/src/payment.py"}, "changeType": "edit"},'
                '{"item": {"path": "/src/refund.py"}, "changeType": "add"},'
                '{"item": {"path": "/src/legacy.py"}, "changeType": "delete"}'
                "]}",
            ),
        ]

        context = AzureDevOpsPRContext(
            pr_url="https://dev.azure.com/microsoft/project/_git/repo/pullrequest/123",
            organization="microsoft",
            project="project",
            repository="repo",
            pr_id=123,
            source="test",
        )

        result = get_pr_file_changes_with_context(context)

        # AI agents need all file changes
        assert result.success is True
        assert len(result.changes) == 3, (
            "AI agents need complete file change lists for comprehensive reviews"
        )

        # AI agents need different change types identified
        change_types = {change.change_type for change in result.changes}
        assert change_types == {"edit", "add", "delete"}, (
            "AI agents need to distinguish between edits, additions, and deletions"
        )

    @patch("subprocess.run")
    def test_ai_agents_can_handle_file_change_retrieval_failures(
        self, mock_run
    ) -> None:
        """AI agents should handle failures when retrieving file changes gracefully."""
        # Mock API failure
        mock_run.return_value = Mock(
            returncode=1, stderr="TF401179: Pull request does not exist"
        )

        context = AzureDevOpsPRContext(
            pr_url="https://dev.azure.com/microsoft/project/_git/repo/pullrequest/99999",
            organization="microsoft",
            project="project",
            repository="repo",
            pr_id=99999,
            source="test",
        )

        result = get_pr_file_changes_with_context(context)

        # AI agents need clear failure indication
        assert result.success is False, (
            "AI agents need clear failure status when file changes can't be retrieved"
        )

        # AI agents need error details for troubleshooting
        assert "Failed to get PR iterations" in result.error, (
            "AI agents need specific error messages to understand what went wrong"
        )

    @patch("subprocess.run")
    def test_ai_agents_can_handle_malformed_json_in_file_changes(
        self, mock_run
    ) -> None:
        """AI agents should handle malformed JSON responses gracefully."""
        # Mock malformed JSON
        mock_run.side_effect = [
            Mock(returncode=0, stdout='{"value": [{"id": 1}]}'),
            Mock(returncode=0, stdout='{"invalid json'),  # Malformed
        ]

        context = AzureDevOpsPRContext(
            pr_url="https://dev.azure.com/microsoft/project/_git/repo/pullrequest/123",
            organization="microsoft",
            project="project",
            repository="repo",
            pr_id=123,
            source="test",
        )

        result = get_pr_file_changes_with_context(context)

        # AI agents need clear error indication
        assert result.success is False
        assert "Invalid JSON response" in result.error, (
            "AI agents need specific error messages for JSON parsing failures"
        )


class TestAIAgentsCanRetrieveActualFileContents:
    """Test what AI agents can accomplish when fetching actual file contents for code review."""

    @pytest.mark.asyncio
    @patch("subprocess.run")
    async def test_ai_agents_can_fetch_actual_file_contents_from_prs(
        self, mock_run
    ) -> None:
        """AI agents should be able to retrieve actual source code contents from PR files."""
        # Mock API response with actual file content
        mock_run.return_value = Mock(
            returncode=0,
            stdout='{"content": "def process_payment():\\n    return True\\n"}',
        )

        # Create file changes result
        file_changes = FileChangesResult(
            success=True,
            changes=[
                FileChange(
                    item=FileChangeItem(path="/src/payment.py"),
                    change_type="edit",
                )
            ],
        )

        context = AzureDevOpsPRContext(
            pr_url="https://dev.azure.com/microsoft/project/_git/repo/pullrequest/123",
            organization="microsoft",
            project="project",
            repository="repo",
            pr_id=123,
            source="test",
        )

        result = await get_file_contents_with_context(file_changes, context)

        # AI agents need successful content retrieval
        assert result.success is True, (
            "AI agents need functioning content retrieval to analyze actual code"
        )

        # AI agents need actual file contents
        assert len(result.files) == 1, (
            "AI agents need file contents to perform code review"
        )

        # AI agents need the actual source code
        assert "def process_payment()" in result.files[0].content, (
            "AI agents need actual source code content to analyze code quality"
        )

        # AI agents need file path mapping
        assert result.files[0].path == "/src/payment.py", (
            "AI agents need to know which file each content belongs to"
        )

    @pytest.mark.asyncio
    @patch("subprocess.run")
    async def test_ai_agents_can_fetch_multiple_file_contents(self, mock_run) -> None:
        """AI agents should be able to fetch contents of multiple changed files."""
        # Mock responses - first PR details, then each file
        mock_run.side_effect = [
            Mock(
                returncode=0,
                stdout='{"sourceRefName": "refs/heads/feature", "targetRefName": "refs/heads/main"}',
            ),
            Mock(
                returncode=0,
                stdout='{"content": "class Payment:\\n    pass\\n"}',
            ),
            Mock(
                returncode=0,
                stdout='{"content": "class Refund:\\n    pass\\n"}',
            ),
        ]

        file_changes = FileChangesResult(
            success=True,
            changes=[
                FileChange(
                    item=FileChangeItem(path="/src/payment.py"), change_type="edit"
                ),
                FileChange(
                    item=FileChangeItem(path="/src/refund.py"), change_type="add"
                ),
            ],
        )

        context = AzureDevOpsPRContext(
            pr_url="https://dev.azure.com/microsoft/project/_git/repo/pullrequest/123",
            organization="microsoft",
            project="project",
            repository="repo",
            pr_id=123,
            source="test",
        )

        result = await get_file_contents_with_context(file_changes, context)

        # AI agents need all file contents
        assert result.success is True
        assert len(result.files) == 2, (
            "AI agents need contents of all changed files for comprehensive review"
        )

        # AI agents need to identify each file's content
        file_paths = {f.path for f in result.files}
        assert file_paths == {"/src/payment.py", "/src/refund.py"}, (
            "AI agents need all file contents properly mapped to their paths"
        )

    @pytest.mark.asyncio
    async def test_ai_agents_can_optimize_fetching_with_context_depth_minimal(
        self,
    ) -> None:
        """AI agents should skip non-code files when using minimal context depth."""
        # Create file changes with various file types
        file_changes = FileChangesResult(
            success=True,
            changes=[
                FileChange(
                    item=FileChangeItem(path="/src/payment.py"), change_type="edit"
                ),
                FileChange(
                    item=FileChangeItem(path="/config/settings.json"),
                    change_type="edit",
                ),
                FileChange(
                    item=FileChangeItem(path="/config/app.yaml"), change_type="edit"
                ),
            ],
        )

        context = AzureDevOpsPRContext(
            pr_url="https://dev.azure.com/microsoft/project/_git/repo/pullrequest/123",
            organization="microsoft",
            project="project",
            repository="repo",
            pr_id=123,
            source="test",
        )

        result = await get_file_contents_with_context(
            file_changes, context, context_depth="minimal"
        )

        # AI agents should skip config files in minimal mode
        assert len(result.skipped_files) >= 2, (
            "AI agents need minimal context depth to skip config files for performance"
        )

        # AI agents need to know which files were skipped
        assert "/config/settings.json" in result.skipped_files, (
            "AI agents need transparency about which files were skipped"
        )

    @pytest.mark.asyncio
    async def test_ai_agents_can_optimize_fetching_with_context_depth_standard(
        self,
    ) -> None:
        """AI agents should skip binary/temp files when using standard context depth."""
        file_changes = FileChangesResult(
            success=True,
            changes=[
                FileChange(
                    item=FileChangeItem(path="/src/payment.py"), change_type="edit"
                ),
                FileChange(
                    item=FileChangeItem(path="/dist/bundle.pyc"), change_type="add"
                ),
                FileChange(
                    item=FileChangeItem(path="/logs/debug.log"), change_type="edit"
                ),
            ],
        )

        context = AzureDevOpsPRContext(
            pr_url="https://dev.azure.com/microsoft/project/_git/repo/pullrequest/123",
            organization="microsoft",
            project="project",
            repository="repo",
            pr_id=123,
            source="test",
        )

        result = await get_file_contents_with_context(
            file_changes, context, context_depth="standard"
        )

        # AI agents should skip binary/temp files in standard mode
        assert (
            "/dist/bundle.pyc" in result.skipped_files
            or "/logs/debug.log" in result.skipped_files
        ), "AI agents need standard context depth to skip binary/temp files"

    @pytest.mark.asyncio
    @patch("subprocess.run")
    @patch("builtins.open")
    async def test_ai_agents_can_fallback_to_local_files_when_api_fails(
        self, mock_open, mock_run
    ) -> None:
        """AI agents should gracefully fallback to local file access when API fails."""
        # Mock API failure
        mock_run.return_value = Mock(returncode=1, stderr="API error")

        # Mock local file access
        mock_open.return_value.__enter__.return_value.read.return_value = (
            "def local_function():\n    pass\n"
        )

        file_changes = FileChangesResult(
            success=True,
            changes=[
                FileChange(
                    item=FileChangeItem(path="/src/payment.py"), change_type="edit"
                ),
            ],
        )

        context = AzureDevOpsPRContext(
            pr_url="https://dev.azure.com/microsoft/project/_git/repo/pullrequest/123",
            organization="microsoft",
            project="project",
            repository="repo",
            pr_id=123,
            source="test",
        )

        result = await get_file_contents_with_context(file_changes, context)

        # AI agents should get content even when API fails
        if len(result.files) > 0:
            assert "def local_function()" in result.files[0].content, (
                "AI agents need fallback to local files when API is unavailable"
            )

    @pytest.mark.asyncio
    async def test_ai_agents_can_handle_failures_without_valid_file_changes(
        self,
    ) -> None:
        """AI agents should handle attempts to fetch contents without valid file changes."""
        # Empty file changes
        file_changes = FileChangesResult(success=False, error="No changes found")

        context = AzureDevOpsPRContext(
            pr_url="https://dev.azure.com/microsoft/project/_git/repo/pullrequest/123",
            organization="microsoft",
            project="project",
            repository="repo",
            pr_id=123,
            source="test",
        )

        result = await get_file_contents_with_context(file_changes, context)

        # AI agents need clear failure indication
        assert result.success is False, (
            "AI agents need clear failure status when file changes are invalid"
        )

        # AI agents need error message explaining the issue with workflow guidance
        assert "File changes result indicates failure" in result.error, (
            "AI agents need specific error messages to understand prerequisites"
        )
        assert "Check the file_changes object for errors" in result.error, (
            "AI agents need actionable guidance on what to do when file changes are invalid"
        )

    @pytest.mark.asyncio
    @patch("subprocess.run")
    async def test_ai_agents_can_track_files_that_failed_to_retrieve(
        self, mock_run
    ) -> None:
        """AI agents should track which files couldn't be retrieved."""
        # Mock API failure for file retrieval
        mock_run.return_value = Mock(returncode=1, stderr="File not found")

        file_changes = FileChangesResult(
            success=True,
            changes=[
                FileChange(
                    item=FileChangeItem(path="/src/missing.py"), change_type="delete"
                ),
            ],
        )

        context = AzureDevOpsPRContext(
            pr_url="https://dev.azure.com/microsoft/project/_git/repo/pullrequest/123",
            organization="microsoft",
            project="project",
            repository="repo",
            pr_id=123,
            source="test",
        )

        result = await get_file_contents_with_context(file_changes, context)

        # AI agents should still succeed even if some files fail
        assert result.success is True, (
            "AI agents should handle partial failures gracefully"
        )

        # AI agents need to know which files failed
        assert "/src/missing.py" in result.error_files, (
            "AI agents need tracking of files that couldn't be retrieved"
        )


class TestAIAgentsCanPerformCompleteCodeReviewWorkflow:
    """Test the complete workflow from PR context to file contents."""

    @pytest.mark.asyncio
    @patch("subprocess.run")
    async def test_ai_agents_can_complete_full_file_retrieval_workflow(
        self, mock_run
    ) -> None:
        """AI agents should be able to execute the complete workflow from context to contents."""
        # Mock file changes API - includes PR details for new branch-aware fetching
        mock_run.side_effect = [
            Mock(returncode=0, stdout='{"value": [{"id": 1}]}'),  # Iterations
            Mock(
                returncode=0,
                stdout='{"changeEntries": [{"item": {"path": "/src/payment.py"}, "changeType": "edit"}]}',
            ),  # Changes
            Mock(
                returncode=0,
                stdout='{"sourceRefName": "refs/heads/feature", "targetRefName": "refs/heads/main"}',
            ),  # PR details
            Mock(
                returncode=0,
                stdout='{"content": "def process_payment():\\n    return True\\n"}',
            ),  # Content
        ]

        # Step 1: Establish PR context (would use azure_devops_establish_pr_context in real usage)
        context = AzureDevOpsPRContext(
            pr_url="https://dev.azure.com/microsoft/project/_git/repo/pullrequest/123",
            organization="microsoft",
            project="project",
            repository="repo",
            pr_id=123,
            source="test",
        )

        # Step 2: Get file changes
        changes = get_pr_file_changes_with_context(context)

        # AI agents need successful file change retrieval
        assert changes.success is True, (
            "AI agents need file changes before fetching contents"
        )

        # Step 3: Get actual file contents
        contents = await get_file_contents_with_context(changes, context)

        # AI agents need successful content retrieval
        assert contents.success is True, (
            "AI agents need actual file contents to perform code review"
        )

        # AI agents need the actual code
        assert len(contents.files) > 0, (
            "AI agents need at least one file's contents for analysis"
        )

        assert "def process_payment()" in contents.files[0].content, (
            "AI agents need actual source code to analyze"
        )

        # AI agents can now perform code review with actual content!
        assert contents.files[0].path == "/src/payment.py", (
            "AI agents need file path mapping to provide line-specific feedback"
        )

    @pytest.mark.asyncio
    @patch("subprocess.run")
    async def test_api_call_includes_include_content_parameter_for_actual_content(
        self, mock_run
    ) -> None:
        """
        As a developer debugging content retrieval
        When the tool calls Azure DevOps API
        Then it must include includeContent=true parameter
        So the API returns actual file content instead of just metadata
        """
        # Given: Mock API responses - first for PR details, then for file content
        mock_run.side_effect = [
            Mock(
                returncode=0,
                stdout='{"sourceRefName": "refs/heads/feature", "targetRefName": "refs/heads/main"}',
            ),
            Mock(
                returncode=0,
                stdout='{"content": "def calculate_fee():\\n    return 0.029\\n"}',
            ),
        ]

        # And: File changes for a single file
        file_changes = FileChangesResult(
            success=True,
            changes=[
                FileChange(
                    item=FileChangeItem(path="/src/pricing.py"),
                    change_type="edit",
                )
            ],
        )

        context = AzureDevOpsPRContext(
            pr_url="https://dev.azure.com/org/project/_git/repo/pullrequest/456",
            organization="org",
            project="project",
            repository="repo",
            pr_id=456,
            source="test",
        )

        # When: AI agent fetches file contents
        result = await get_file_contents_with_context(file_changes, context)

        # Then: API calls must include PR details call and file content call
        assert mock_run.call_count == 2, (
            "Should call PR details API and file content API"
        )
        api_call_args = mock_run.call_args_list[1][0][0]

        assert "--query-parameters" in api_call_args, (
            "API call must include query parameters to get actual content"
        )

        query_param_index = api_call_args.index("--query-parameters")
        query_params = api_call_args[query_param_index + 1]

        assert "includeContent=true" in query_params, (
            "API call must include includeContent=true to get actual file content instead of metadata"
        )

        # And: Result contains actual content
        assert result.success is True
        assert len(result.files) == 1
        assert "def calculate_fee()" in result.files[0].content, (
            "Content should contain actual source code, not API metadata"
        )

    @pytest.mark.asyncio
    @patch("subprocess.run")
    async def test_visualstudio_url_with_encoded_spaces_fetches_content_correctly(
        self, mock_run
    ) -> None:
        """
        As an AI agent working with visualstudio.com repositories
        When given a PR URL with URL-encoded project names
        Then file contents are fetched correctly using the decoded project name
        So developers using legacy visualstudio.com URLs get working content retrieval
        """
        # Given: Mock API responses - first for PR details, then for file content
        mock_run.side_effect = [
            Mock(
                returncode=0,
                stdout='{"sourceRefName": "refs/heads/feature-provider-selection", "targetRefName": "refs/heads/main"}',
            ),
            Mock(
                returncode=0,
                stdout='{"content": "class ProviderSelector:\\n    def select(self):\\n        pass\\n"}',
            ),
        ]

        # And: File changes from a visualstudio.com PR
        file_changes = FileChangesResult(
            success=True,
            changes=[
                FileChange(
                    item=FileChangeItem(
                        path="/src/databricks/workspace/notebooks/PaymentTransactions/Gold/PaymentsJournal/Modules/ProviderSelectionUtils.py"
                    ),
                    change_type="add",
                )
            ],
        )

        # And: Context from modern visualstudio.com URL with encoded spaces
        context = AzureDevOpsPRContext(
            pr_url="https://microsoft.visualstudio.com/Universal%20Store/_git/Commerce.PaymentsDataPlatform/pullrequest/13903594",
            organization="microsoft",
            project="Universal Store",  # Decoded from "Universal%20Store"
            repository="Commerce.PaymentsDataPlatform",
            pr_id=13903594,
            source="url",
        )

        # When: AI agent fetches file contents
        result = await get_file_contents_with_context(file_changes, context)

        # Then: API calls include PR details and file content
        assert mock_run.call_count == 2, (
            "Should call PR details API and file content API"
        )
        api_call_args = mock_run.call_args_list[1][0][0]

        # Verify project parameter uses decoded name
        assert "project=Universal Store" in api_call_args, (
            "API call must use decoded project name 'Universal Store' not 'Universal%20Store'"
        )

        # And: Content is retrieved successfully
        assert result.success is True, (
            "Content retrieval should succeed with visualstudio.com URLs"
        )
        assert len(result.files) == 1
        assert "class ProviderSelector" in result.files[0].content, (
            "Should retrieve actual Python source code"
        )
        assert (
            result.files[0].path
            == "/src/databricks/workspace/notebooks/PaymentTransactions/Gold/PaymentsJournal/Modules/ProviderSelectionUtils.py"
        ), "Should maintain full file path"

    @pytest.mark.asyncio
    @patch("subprocess.run")
    async def test_new_files_fetched_from_source_branch_with_version_descriptor(
        self, mock_run
    ) -> None:
        """
        As an AI agent reviewing a PR that adds new files
        When fetching file contents for files with change_type="add"
        Then the API call must include versionDescriptor parameters to specify source branch
        So new files that only exist in the source branch can be retrieved

        Background: New files (change_type="add") don't exist in the target/merge branch yet.
        Without versionDescriptor, the API looks in the default branch and returns 404.
        With versionDescriptor.versionType=branch&versionDescriptor.version=source-branch,
        the API looks in the source branch where the new file actually exists.
        """
        # Given: Mock PR details with source branch
        mock_run.side_effect = [
            Mock(
                returncode=0,
                stdout='{"sourceRefName": "refs/heads/feature-provider-selection", "targetRefName": "refs/heads/main"}',
            ),
            Mock(
                returncode=0,
                stdout='{"content": "def new_feature():\\n    return \\"implemented\\"\\n"}',
            ),
        ]

        # And: A file change with change_type="add" (new file in PR)
        file_changes = FileChangesResult(
            success=True,
            changes=[
                FileChange(
                    item=FileChangeItem(path="/src/new_module.py"),
                    change_type="add",
                )
            ],
        )

        context = AzureDevOpsPRContext(
            pr_url="https://dev.azure.com/org/project/_git/repo/pullrequest/789",
            organization="org",
            project="project",
            repository="repo",
            pr_id=789,
            source="test",
        )

        # When: AI agent fetches file contents
        result = await get_file_contents_with_context(file_changes, context)

        # Then: The file content API call must include versionDescriptor parameters
        assert mock_run.call_count == 2, (
            "Should call PR details API then file content API"
        )

        # First call is PR details
        pr_call_args = mock_run.call_args_list[0][0][0]
        assert "az" in pr_call_args
        assert "repos" in pr_call_args
        assert "pr" in pr_call_args
        assert "show" in pr_call_args

        # Second call is file content with versionDescriptor for new files
        file_call_args = mock_run.call_args_list[1][0][0]

        # Must include versionDescriptor parameters for new files
        assert "--query-parameters" in file_call_args, (
            "API call must include query parameters for new file retrieval"
        )

        query_param_index = file_call_args.index("--query-parameters")
        query_params = file_call_args[query_param_index + 1]

        assert "includeContent=true" in query_params, (
            "Must include includeContent=true to get file content"
        )

        assert "versionDescriptor.versionType=branch" in query_params, (
            "New files must specify versionType=branch to look in source branch"
        )

        assert "versionDescriptor.version=feature-provider-selection" in query_params, (
            "New files must specify source branch name to find the new file"
        )

        # And: Content retrieval succeeds with new file content
        assert result.success is True, (
            "New file content retrieval should succeed with versionDescriptor"
        )
        assert len(result.files) == 1, "Should retrieve the new file"
        assert "def new_feature()" in result.files[0].content, (
            "Should retrieve actual source code of new file from source branch"
        )
        assert result.files[0].path == "/src/new_module.py"

        # And: No errors for the new file
        assert len(result.error_files) == 0, (
            "New files should not be in error_files when versionDescriptor is used"
        )

    @pytest.mark.asyncio
    @patch("subprocess.run")
    async def test_edited_files_fetched_from_source_branch_with_changes(
        self, mock_run
    ) -> None:
        """
        As an AI agent reviewing a PR with edited files
        When fetching file contents for files with change_type="edit"
        Then the API call must include versionDescriptor to fetch from source branch
        So edited files show the NEW version with PR changes, not the old target branch version

        Background: This is a CRITICAL bug - without versionDescriptor for edited files,
        we fetch the OLD version from the target branch (before changes), making code
        review completely useless since we're analyzing the wrong code.

        The bug was discovered when reviewing PR #13903594:
        - New file (ProviderSelectionUtils.py) was retrieved correctly ✅
        - Edited files showed OLD versions WITHOUT the changes ❌
        - For example: PaymentsJournalCoreTable.py didn't show the new
          .addColumn("ProviderSelectionResponse", provider_selection_schema) line

        Fix: Apply versionDescriptor to BOTH "add" AND "edit" change types.
        """
        # Given: Mock PR details with source branch containing changes
        mock_run.side_effect = [
            Mock(
                returncode=0,
                stdout='{"sourceRefName": "refs/heads/users/jackpines/provider-selection-schema", "targetRefName": "refs/heads/main"}',
            ),
            Mock(
                returncode=0,
                stdout='{"content": "class PaymentsTable:\\n    def schema(self):\\n        return schema.addColumn(\\"ProviderSelectionResponse\\", provider_selection_schema)\\n"}',
            ),
        ]

        # And: A file change with change_type="edit" (modified file in PR)
        file_changes = FileChangesResult(
            success=True,
            changes=[
                FileChange(
                    item=FileChangeItem(
                        path="/src/databricks/workspace/notebooks/PaymentTransactions/Gold/PaymentsJournal/PaymentsJournalCoreTable.py"
                    ),
                    change_type="edit",
                )
            ],
        )

        context = AzureDevOpsPRContext(
            pr_url="https://microsoft.visualstudio.com/Universal%20Store/_git/Commerce.PaymentsDataPlatform/pullrequest/13903594",
            organization="microsoft",
            project="Universal Store",
            repository="Commerce.PaymentsDataPlatform",
            pr_id=13903594,
            source="test",
        )

        # When: AI agent fetches file contents
        result = await get_file_contents_with_context(file_changes, context)

        # Then: The file content API call must include versionDescriptor for edited files
        assert mock_run.call_count == 2, (
            "Should call PR details API then file content API"
        )

        # First call is PR details
        pr_call_args = mock_run.call_args_list[0][0][0]
        assert "az" in pr_call_args
        assert "repos" in pr_call_args

        # Second call is file content with versionDescriptor for edited files
        file_call_args = mock_run.call_args_list[1][0][0]

        # Must include versionDescriptor parameters for edited files to get PR changes
        assert "--query-parameters" in file_call_args, (
            "API call must include query parameters for edited file retrieval"
        )

        query_param_index = file_call_args.index("--query-parameters")
        query_params = file_call_args[query_param_index + 1]

        assert "includeContent=true" in query_params, (
            "Must include includeContent=true to get file content"
        )

        assert "versionDescriptor.versionType=branch" in query_params, (
            "CRITICAL: Edited files must specify versionType=branch to get PR changes from source branch, "
            "not the old version from target branch"
        )

        assert (
            "versionDescriptor.version=users/jackpines/provider-selection-schema"
            in query_params
        ), (
            "CRITICAL: Edited files must specify source branch to fetch the NEW version with changes, "
            "not the OLD version from target branch"
        )

        # And: Content retrieval succeeds with the CHANGED version
        assert result.success is True, (
            "Edited file content retrieval should succeed with versionDescriptor"
        )
        assert len(result.files) == 1, "Should retrieve the edited file"

        # CRITICAL: Verify we got the NEW version with changes
        assert "ProviderSelectionResponse" in result.files[0].content, (
            "CRITICAL BUG FIX VERIFICATION: Should retrieve NEW version with PR changes, "
            "not old target branch version. The new .addColumn line must be present."
        )
        assert "provider_selection_schema" in result.files[0].content, (
            "Should see the actual changes made in the PR"
        )

        # And: No errors for edited files
        assert len(result.error_files) == 0, (
            "Edited files should not be in error_files when versionDescriptor is used"
        )

    @pytest.mark.asyncio
    @patch("subprocess.run")
    async def test_completed_pr_fetches_from_merge_commit_not_deleted_source_branch(
        self, mock_run
    ) -> None:
        """
        As an AI agent reviewing a completed/merged PR
        When the source branch has been deleted (common after merge)
        Then the tool must use the merge commit ID instead of the source branch name
        So file contents can still be retrieved even after branch cleanup

        Background: This bug was discovered with PR #13903594:
        - PR was completed at 2025-10-10 21:41:32 UTC
        - Source branch "baldini/add_provider_selection_response" was deleted
        - Tool tried to fetch from deleted branch and failed
        - All files ended up in error_files list

        Root cause: After PR completion, Azure DevOps often deletes the source branch
        to keep the repository clean. The tool must detect PR status="completed" and
        use the merge commit ID instead of the (now deleted) source branch.

        Fix: Check PR status and use appropriate version descriptor:
        - Active PR: Use source branch name (branch still exists)
        - Completed PR: Use merge commit ID (branch may be deleted)
        """
        # Given: Mock PR details showing COMPLETED status with merge commit
        mock_run.side_effect = [
            Mock(
                returncode=0,
                stdout='{"status": "completed", "sourceRefName": "refs/heads/baldini/add_provider_selection_response", "targetRefName": "refs/heads/main", "lastMergeCommit": {"commitId": "b57ff98707abffe28e017b27d3dc06de50488bee"}}',
            ),
            Mock(
                returncode=0,
                stdout='{"content": "class PaymentsTable:\\n    def schema(self):\\n        return schema.addColumn(\\"ProviderSelectionResponse\\", provider_selection_schema)\\n"}',
            ),
        ]

        # And: File changes from the completed PR
        file_changes = FileChangesResult(
            success=True,
            changes=[
                FileChange(
                    item=FileChangeItem(
                        path="/src/databricks/workspace/notebooks/PaymentTransactions/Gold/PaymentsJournal/PaymentsJournalCoreTable.py"
                    ),
                    change_type="edit",
                )
            ],
        )

        context = AzureDevOpsPRContext(
            pr_url="https://microsoft.visualstudio.com/Universal%20Store/_git/Commerce.PaymentsDataPlatform/pullrequest/13903594",
            organization="microsoft",
            project="Universal Store",
            repository="Commerce.PaymentsDataPlatform",
            pr_id=13903594,
            source="test",
        )

        # When: AI agent fetches file contents from completed PR
        result = await get_file_contents_with_context(file_changes, context)

        # Then: Must use merge commit, not source branch
        assert mock_run.call_count == 2, (
            "Should call PR details API then file content API"
        )

        # Second call must use commit ID (not branch name that's deleted)
        file_call_args = mock_run.call_args_list[1][0][0]
        query_param_index = file_call_args.index("--query-parameters")
        query_params = file_call_args[query_param_index + 1]

        # CRITICAL: For completed PRs, must use commit version descriptor
        assert "versionDescriptor.versionType=commit" in query_params, (
            "CRITICAL: Completed PRs must use commit ID, not branch name (which may be deleted)"
        )

        assert (
            "versionDescriptor.version=b57ff98707abffe28e017b27d3dc06de50488bee"
            in query_params
        ), (
            "CRITICAL: Must use merge commit ID from lastMergeCommit to fetch files "
            "after source branch deletion"
        )

        # Must NOT use branch name for completed PRs
        assert "baldini/add_provider_selection_response" not in query_params, (
            "Should NOT try to fetch from source branch for completed PRs (branch may be deleted)"
        )

        # And: Content retrieval succeeds using merge commit
        assert result.success is True, (
            "Completed PR content retrieval should succeed using merge commit"
        )
        assert len(result.files) == 1, "Should retrieve files from merge commit"
        assert "ProviderSelectionResponse" in result.files[0].content

        # And: No errors even though source branch is deleted
        assert len(result.error_files) == 0, (
            "CRITICAL FIX VERIFICATION: Files should not fail when using merge commit "
            "for completed PRs, even if source branch is deleted"
        )
