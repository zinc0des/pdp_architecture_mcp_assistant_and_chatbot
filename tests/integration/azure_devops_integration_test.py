"""
Azure DevOps workflow integration tests.

Tests focus on real Azure DevOps API integration - ensuring workflow tools work together
with live data and catch repository scoping, authentication, and API compatibility issues
that unit tests with mocks cannot detect.

These tests require:
- Active Azure DevOps authentication (az login)
- Access to Commerce.PaymentsDataPlatform repository
- Network connectivity to dev.azure.com

Run with: pytest tests/azure_devops_integration_test.py -m integration
"""

import pytest

from pdp_dev_mcp.tools.common.azure_devops_repository import (
    azure_devops_repository_discovery,
    azure_devops_workflow_setup,
)
from pdp_dev_mcp.tools.common.azure_devops_pr_comments import (
    azure_devops_pr_comment_analysis,
)


@pytest.mark.integration
class TestAIAgentsCanHelpDevelopersWithCompleteAzureDevOpsWorkflows:
    """
    Integration tests that verify AI agents can help developers execute complete Azure DevOps workflows
    with real API data, ensuring tools work together seamlessly in production environments.

    These tests verify AI agents can help developers:
    - Discover and navigate repository contexts consistently across tools
    - Analyze PR feedback and implement reviewer suggestions effectively
    - Handle real-world edge cases and authentication issues gracefully
    - Execute end-to-end workflows that combine multiple Azure DevOps operations
    """

    def test_ai_agents_can_help_developers_discover_and_maintain_consistent_repository_context(
        self,
    ) -> None:
        """
        Verify AI agents help developers by maintaining consistent repository context across workflow tools.

        This test ensures AI agents help developers avoid the common bug where workflow tools
        operate on different repository scopes, leading to confusing and incorrect results.
        """
        # Step 1: Discover repository context
        discovery_result = azure_devops_repository_discovery()

        assert discovery_result["success"], (
            f"Repository discovery should succeed in Azure DevOps environment: {discovery_result.get('error', 'Unknown error')}"
        )

        discovered_repo = discovery_result["repository"]
        discovered_org = discovery_result["organization"]
        discovered_project = discovery_result["project"]

        # Step 2: Run workflow setup using discovered context
        setup_result = azure_devops_workflow_setup()

        assert setup_result["success"], (
            f"Workflow setup should succeed with discovered context: {setup_result.get('error', 'Unknown error')}"
        )

        # Step 3: Verify consistent repository context
        setup_repo = setup_result["repository_context"]["repository"]
        setup_org = setup_result["repository_context"]["organization"]
        setup_project = setup_result["repository_context"]["project"]

        assert discovered_repo == setup_repo, (
            f"Repository discovery ({discovered_repo}) and workflow setup ({setup_repo}) must use same repository"
        )
        assert discovered_org == setup_org, (
            f"Repository discovery ({discovered_org}) and workflow setup ({setup_org}) must use same organization"
        )
        assert discovered_project == setup_project, (
            f"Repository discovery ({discovered_project}) and workflow setup ({setup_project}) must use same project"
        )

    def test_ai_agents_can_help_developers_analyze_prs_with_compatible_tool_integration(
        self,
    ) -> None:
        """
        Verify AI agents help developers by ensuring PR analysis tools work together seamlessly.

        This test ensures AI agents help developers avoid the workflow breaking bug where
        PR listing and PR analysis tools operate on incompatible PR scopes.
        """
        # Step 1: Get PR list from workflow setup
        setup_result = azure_devops_workflow_setup()

        assert setup_result["success"], (
            f"Workflow setup should succeed to test PR compatibility: {setup_result.get('error', 'Unknown error')}"
        )

        pr_overview = setup_result["pr_overview"]
        assert pr_overview["total_prs"] > 0, (
            "Workflow setup should return at least one PR to test compatibility"
        )

        # Step 2: Test that first PR from setup can be analyzed
        first_pr = pr_overview["recent_prs"][0]
        pr_id = first_pr["id"]

        # Step 3: Verify PR comment analysis works with PR from workflow setup
        analysis_result = azure_devops_pr_comment_analysis(
            pr_id=pr_id, save_to_file=False
        )

        assert analysis_result["success"], (
            f"PR comment analysis should succeed for PR {pr_id} returned by workflow setup: {analysis_result.get('error', 'Unknown error')}"
        )

        # Step 4: Verify repository context consistency
        setup_context = setup_result["repository_context"]
        analysis_context = analysis_result["repository_context"]

        assert setup_context["repository"] == analysis_context["repository"], (
            f"Workflow setup repository ({setup_context['repository']}) must match analysis repository ({analysis_context['repository']})"
        )
        assert setup_context["organization"] == analysis_context["organization"], (
            f"Workflow setup organization ({setup_context['organization']}) must match analysis organization ({analysis_context['organization']})"
        )
        assert setup_context["project"] == analysis_context["project"], (
            f"Workflow setup project ({setup_context['project']}) must match analysis project ({analysis_context['project']})"
        )

    def test_ai_agents_can_help_developers_resolve_pr_feedback_with_actionable_thread_data(
        self,
    ) -> None:
        """
        Verify AI agents help developers by providing actionable thread data for PR comment resolution.

        This test ensures AI agents help developers complete the feedback loop: analyze PR comments
        and then resolve them after implementing the suggestions.
        """
        # Step 1: Get a PR with potential comments
        setup_result = azure_devops_workflow_setup()
        assert setup_result["success"], (
            "Workflow setup must succeed for resolution testing"
        )

        pr_overview = setup_result["pr_overview"]
        if pr_overview["total_prs"] == 0:
            pytest.skip("No PRs available for testing comment resolution workflow")

        # Step 2: Analyze PR comments to get thread structure
        first_pr = pr_overview["recent_prs"][0]
        pr_id = first_pr["id"]

        analysis_result = azure_devops_pr_comment_analysis(
            pr_id=pr_id, save_to_file=False
        )
        assert analysis_result["success"], f"PR analysis must succeed for PR {pr_id}"

        # Step 3: Verify analysis provides data needed for resolution
        comment_summary = analysis_result["comment_summary"]

        # The analysis should provide clear metrics for resolution decisions
        assert "total_threads" in comment_summary, (
            "Comment analysis must provide total thread count for resolution tool"
        )
        assert "active_threads" in comment_summary, (
            "Comment analysis must provide active thread count for resolution tool"
        )
        assert "resolution_ready" in analysis_result, (
            "Comment analysis must provide resolution readiness indicator"
        )

        # Step 4: Verify REST API details are provided for resolution tool
        assert "rest_api_details" in analysis_result, (
            "Comment analysis must provide REST API details for resolution tool"
        )
        rest_details = analysis_result["rest_api_details"]
        assert "repo_guid" in rest_details, (
            "Comment analysis must provide repository GUID for resolution API calls"
        )
        assert "project_guid" in rest_details, (
            "Comment analysis must provide project GUID for resolution API calls"
        )

    @pytest.mark.slow
    def test_ai_agents_can_help_developers_execute_complete_azure_devops_workflows_end_to_end(
        self,
    ) -> None:
        """
        Verify AI agents help developers execute complete Azure DevOps workflows from start to finish.

        This test ensures AI agents help developers with realistic end-to-end workflows:
        repository discovery → workflow setup → PR analysis → consistent data across all steps.

        Marked as slow since it makes multiple Azure DevOps API calls.
        """
        # Step 1: Repository discovery
        discovery_result = azure_devops_repository_discovery()
        assert discovery_result["success"], (
            "Repository discovery must succeed for complete workflow"
        )

        # Step 2: Workflow setup
        setup_result = azure_devops_workflow_setup()
        assert setup_result["success"], (
            "Workflow setup must succeed for complete workflow"
        )

        # Step 3: PR analysis (if PRs available)
        pr_overview = setup_result["pr_overview"]
        if pr_overview["total_prs"] > 0:
            first_pr = pr_overview["recent_prs"][0]
            pr_id = first_pr["id"]

            analysis_result = azure_devops_pr_comment_analysis(
                pr_id=pr_id, save_to_file=False
            )
            assert analysis_result["success"], (
                f"PR analysis must succeed for complete workflow (PR {pr_id})"
            )

            # Verify data consistency across all workflow steps
            discovery_repo = discovery_result["repository"]
            setup_repo = setup_result["repository_context"]["repository"]
            analysis_repo = analysis_result["repository_context"]["repository"]

            assert discovery_repo == setup_repo == analysis_repo, (
                f"Repository context must be consistent across workflow: "
                f"discovery={discovery_repo}, setup={setup_repo}, analysis={analysis_repo}"
            )

        # Step 4: Verify workflow provides actionable next steps
        assert "next_steps" in setup_result, (
            "Complete workflow must provide actionable next steps for AI agents"
        )
        next_steps = setup_result["next_steps"]
        assert len(next_steps) > 0, (
            "Workflow must provide at least one actionable next step"
        )


@pytest.mark.integration
class TestAIAgentsCanHelpDevelopersHandleRealWorldAzureDevOpsEdgeCases:
    """
    Integration tests that verify AI agents help developers handle real-world edge cases
    and challenging scenarios that only occur with live Azure DevOps data.
    """

    def test_ai_agents_can_help_developers_work_with_repositories_that_have_no_active_prs(
        self,
    ) -> None:
        """
        Verify AI agents help developers work effectively even when repositories have no active PRs.
        """
        setup_result = azure_devops_workflow_setup()
        assert setup_result["success"], "Workflow setup should succeed even with no PRs"

        # Even with no PRs, workflow should provide valid structure
        pr_overview = setup_result["pr_overview"]
        assert "total_prs" in pr_overview, (
            "PR overview must include total count even if zero"
        )
        assert "recent_prs" in pr_overview, (
            "PR overview must include recent PRs list even if empty"
        )
        assert isinstance(pr_overview["recent_prs"], list), "Recent PRs must be a list"

    def test_ai_agents_can_help_developers_analyze_prs_that_have_no_comment_threads(
        self,
    ) -> None:
        """
        Verify AI agents help developers handle PR analysis gracefully even for PRs with no comments.
        """
        # Get any available PR
        setup_result = azure_devops_workflow_setup()
        if setup_result["pr_overview"]["total_prs"] == 0:
            pytest.skip("No PRs available for testing comment analysis edge cases")

        first_pr = setup_result["pr_overview"]["recent_prs"][0]
        pr_id = first_pr["id"]

        analysis_result = azure_devops_pr_comment_analysis(
            pr_id=pr_id, save_to_file=False
        )
        assert analysis_result["success"], (
            f"Analysis should succeed even for PR {pr_id} without comments"
        )

        # Analysis should handle zero comments gracefully
        comment_summary = analysis_result["comment_summary"]
        assert comment_summary["total_threads"] >= 0, (
            "Total threads must be non-negative"
        )
        assert comment_summary["active_threads"] >= 0, (
            "Active threads must be non-negative"
        )
        assert "resolution_ready" in analysis_result, (
            "Resolution ready status must be provided"
        )

    def test_ai_agents_can_help_developers_understand_authentication_issues_with_helpful_error_messages(
        self,
    ) -> None:
        """
        Verify AI agents help developers understand and resolve authentication issues quickly.

        This test temporarily disrupts Azure CLI authentication to verify AI agents provide
        helpful error messages that guide developers to solutions.

        Note: This test disrupts authentication temporarily, but restores it afterward.
        """
        import os
        import tempfile
        import shutil
        import time

        # Save current environment state
        original_azure_config_dir = os.environ.get("AZURE_CONFIG_DIR")
        original_azure_extension_dir = os.environ.get("AZURE_EXTENSION_DIR")

        temp_dir = None
        try:
            # Create temporary directory that will not contain valid Azure CLI config
            temp_dir = tempfile.mkdtemp()

            # Redirect Azure CLI to use temporary directory (no valid auth)
            os.environ["AZURE_CONFIG_DIR"] = temp_dir
            os.environ["AZURE_EXTENSION_DIR"] = temp_dir

            # Test workflow setup with broken authentication (this uses Azure CLI)
            setup_result = azure_devops_workflow_setup()

            # Should fail gracefully with meaningful error
            assert not setup_result["success"], (
                f"Workflow setup should fail with broken authentication: {setup_result}"
            )
            assert "error" in setup_result, "Failed setup should include error message"

            # Error should provide actionable guidance
            error_msg = setup_result["error"].lower()
            # Check for common Azure CLI authentication error indicators
            auth_indicators = [
                "please run 'az login'",
                "not logged in",
                "authentication",
                "login",
                "credential",
                "az login",
                "sign in",
                "sign-in",
                "unauthorized",
                "authentication failed",
                "access denied",
            ]

            has_auth_guidance = any(
                indicator in error_msg for indicator in auth_indicators
            )
            assert has_auth_guidance, (
                f"Error should provide authentication guidance. Got: {setup_result['error']}"
            )

        finally:
            # Restore original environment
            if original_azure_config_dir:
                os.environ["AZURE_CONFIG_DIR"] = original_azure_config_dir
            elif "AZURE_CONFIG_DIR" in os.environ:
                del os.environ["AZURE_CONFIG_DIR"]

            if original_azure_extension_dir:
                os.environ["AZURE_EXTENSION_DIR"] = original_azure_extension_dir
            elif "AZURE_EXTENSION_DIR" in os.environ:
                del os.environ["AZURE_EXTENSION_DIR"]

            # Clean up temporary directory with retry logic
            if temp_dir and os.path.exists(temp_dir):
                try:
                    # Give Azure CLI processes time to finish
                    time.sleep(0.1)
                    shutil.rmtree(temp_dir, ignore_errors=True)
                except (OSError, PermissionError):
                    # If cleanup fails, let the OS handle it eventually
                    pass

    def test_ai_agents_can_achieve_real_azure_devops_integration_success_for_production_workflows(
        self,
    ):
        """
        As a developer
        When I use Azure DevOps MCP tools with the actual Commerce.PaymentsDataPlatform repository
        Then all operations work correctly with the real "Universal Store" project

        This is an integration test that validates the URL encoding fixes work
        with the actual Azure DevOps environment.
        """
        import os

        # Given: Real repository directory
        real_repo_dir = "/Users/jackpines/src/Microsoft/Commerce.PaymentsDataPlatform"
        if not os.path.exists(real_repo_dir):
            pytest.skip(f"Real repository not available at {real_repo_dir}")

        # When: Running workflow setup on real repository
        result = azure_devops_workflow_setup(working_directory=real_repo_dir)

        # Then: Setup succeeds with real Azure DevOps integration
        assert result["success"] is True, (
            f"Real Azure DevOps integration should work. Error: {result.get('error', 'No error')}"
        )
        assert result["repository_context"]["project"] == "Universal Store", (
            f"Should correctly identify project as 'Universal Store'. "
            f"Got: '{result['repository_context']['project']}'"
        )
        assert result["workflow_ready"] is True, (
            "Azure CLI should be successfully configured for project with spaces"
        )


# Configuration for pytest integration test runner
def pytest_configure(config):
    """Configure pytest markers for integration tests."""
    config.addinivalue_line(
        "markers",
        "integration: mark test as integration test requiring live Azure DevOps access",
    )
    config.addinivalue_line(
        "markers", "slow: mark test as slow integration test making multiple API calls"
    )
