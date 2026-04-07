"""
Tests for AI-enabling code analysis tools.

Tests focus on what AI agents can accomplish when provided with flexible
analysis frameworks rather than rigid prescriptive patterns.
"""

import json
import pytest
from unittest.mock import patch, Mock

from pdp_dev_mcp.tools.code_review.ai_enabling_analysis import (
    get_code_analysis_context,
    CodeAnalysisContext,
    AnalysisGuidelines,
    DomainContext,
    QualityCategories,
)


# Test utilities for black-box I/O mocking
def create_mock_iterations_response(iteration_id=1):
    """Create mock Azure DevOps iterations API response."""
    import json
    from unittest.mock import Mock

    return Mock(
        returncode=0, stdout=json.dumps({"value": [{"id": iteration_id}]}), stderr=""
    )


def create_mock_changes_response(file_paths):
    """Create mock Azure DevOps changes API response with file paths."""
    import json
    from unittest.mock import Mock

    return Mock(
        returncode=0,
        stdout=json.dumps(
            {
                "changeEntries": [
                    {"item": {"path": f"/{path}"}, "changeType": "edit"}
                    for path in file_paths
                ]
            }
        ),
        stderr="",
    )


def create_mock_pr_details_response(title="Test PR", description="Test description"):
    """Create mock PR details response."""
    import json
    from unittest.mock import Mock

    return Mock(
        returncode=0,
        stdout=json.dumps(
            {
                "title": title,
                "description": description,
                "createdBy": {"displayName": "Test User"},
            }
        ),
        stderr="",
    )


# Standard test PR parameters
TEST_PR_ID = 13844374
TEST_ORG = "msazure"
TEST_PROJECT = "One"
TEST_REPO = "Commerce.PaymentsDataPlatform"


class TestAIAgentsCanPerformFlexibleCodeAnalysis:
    """Test what AI agents can accomplish with enabling frameworks rather than prescriptive constraints."""

    def test_ai_agents_can_receive_comprehensive_analysis_guidelines_for_payment_code_review(
        self,
    ) -> None:
        """
        As an AI agent assisting with code review
        When I need to analyze payment processing code changes
        Then I receive comprehensive analysis guidelines that enable flexible reasoning
        """
        # Given: A PR with payment processing changes requiring domain expertise
        mock_files = {
            "src/databricks/silver/payment_transactions.py": {},
            "src/databricks/gold/chargeback_processor.py": {},
        }

        # When: AI agent requests analysis guidelines
        with patch("subprocess.run") as mock_run:
            # Mock Azure DevOps API calls (I/O layer)
            file_paths = list(mock_files.keys())
            mock_run.side_effect = [
                create_mock_iterations_response(),  # iterations call
                create_mock_changes_response(file_paths),  # changes call
                create_mock_pr_details_response(),  # PR details (may not be called in all tests)
            ]

            result = get_code_analysis_context(
                pr_id=TEST_PR_ID,
                org=TEST_ORG,
                project=TEST_PROJECT,
                repository=TEST_REPO,
            )

            # Then: API was called to fetch files
            # subprocess.run was called for API requests
            assert mock_run.call_count >= 2  # At least iterations + changes

            # And: AI receives comprehensive analysis framework enabling flexible reasoning
            assert isinstance(result, CodeAnalysisContext)

            # And: Guidelines provide analytical framework without constraining reasoning
            guidelines = result.analysis_guidelines
            assert isinstance(guidelines, AnalysisGuidelines)
            assert "quality, performance" in guidelines.objective
            assert "business logic" in guidelines.objective
            assert "flexible AI reasoning" in guidelines.objective
            assert "payment processing" in guidelines.domain_focus.lower()
            assert "flexible reasoning" in guidelines.approach.lower()

            # And: Domain context enables payment-specific expertise
            domain = result.domain_context
            assert isinstance(domain, DomainContext)
            assert "PCI DSS" in str(domain.compliance_requirements)
            assert "Spark DataFrame optimization" in str(domain.performance_patterns)
            assert "Chargeback and refund processing" in str(domain.business_logic)
            assert "Credential and certificate management" in str(
                domain.security_patterns
            )

            # And: Quality categories provide structure while allowing novel classifications
            categories = result.quality_categories
            assert isinstance(categories, QualityCategories)
            assert "performance" in categories.standard_categories
            assert "security" in categories.standard_categories
            assert "domain-specific" in categories.standard_categories
            assert categories.allow_novel_categories is True
            assert "AI can propose new categories" in categories.novel_category_guidance

            # And: Analysis framework explains how to organize findings for downstream tools
            assert "organize your analysis findings" in result.output_guidance.lower()
            assert "azure devops comment threading" in result.output_guidance.lower()

    def test_ai_agents_can_adapt_analysis_context_for_different_code_types(
        self,
    ) -> None:
        """
        As an AI agent analyzing different types of code
        When I encounter Spark, API, or database code
        Then I receive context-specific guidance that adapts to the technology stack
        """
        # Given: A PR with mixed technology stack changes
        mock_files = {
            "src/databricks/transformations/spark_processor.py": {},
            "src/api/payment_endpoints.py": {},
        }

        # When: AI agent requests analysis for mixed technology stack
        with patch("subprocess.run") as mock_run:
            # Mock Azure DevOps API calls (I/O layer)
            file_paths = list(mock_files.keys())
            mock_run.side_effect = [
                create_mock_iterations_response(),  # iterations call
                create_mock_changes_response(file_paths),  # changes call
                create_mock_pr_details_response(),  # PR details (may not be called in all tests)
            ]

            result = get_code_analysis_context(
                pr_id=TEST_PR_ID,
                org=TEST_ORG,
                project=TEST_PROJECT,
                repository=TEST_REPO,
            )

            # Then: Context adapts to include technology-specific guidance
            guidelines = result.analysis_guidelines
            assert "data_processing" in guidelines.technology_focus.lower()

            # And: Domain context includes data processing patterns
            domain = result.domain_context
            assert len(domain.technology_patterns) > 0

    def test_ai_agents_can_detect_database_and_frontend_technologies(
        self,
    ) -> None:
        """
        As an AI agent analyzing different code types
        When I encounter database and frontend files
        Then I receive appropriate technology-specific guidance
        """
        # Given: A PR with database and frontend files
        mock_files = {
            "src/queries/payment_lookup.sql": {},
            "src/data/database_migrations.py": {},
            "src/ui/payment_form.js": {},
            "src/frontend/checkout.tsx": {},
        }

        # When: AI agent requests analysis context
        with patch("subprocess.run") as mock_run:
            # Mock Azure DevOps API calls (I/O layer)
            file_paths = list(mock_files.keys())
            mock_run.side_effect = [
                create_mock_iterations_response(),  # iterations call
                create_mock_changes_response(file_paths),  # changes call
                create_mock_pr_details_response(),  # PR details (may not be called in all tests)
            ]

            result = get_code_analysis_context(
                pr_id=TEST_PR_ID,
                org=TEST_ORG,
                project=TEST_PROJECT,
                repository=TEST_REPO,
            )

            # Then: Technology-specific patterns are detected
            guidelines = result.analysis_guidelines
            assert (
                "database" in guidelines.technology_focus.lower()
                or "frontend" in guidelines.technology_focus.lower()
            )

            # And: Technology patterns include database or frontend guidance
            domain = result.domain_context
            assert len(domain.technology_patterns) > 0

    def test_ai_agents_can_handle_comprehensive_analysis_depth(
        self,
    ) -> None:
        """
        As an AI agent conducting thorough code reviews
        When I request comprehensive analysis depth
        Then I receive extended focus areas and detailed context
        """
        # Given: A PR requiring comprehensive analysis
        mock_files = {
            "src/core/payment_engine.py": {},
            "src/api/transactions.py": {},
        }

        # When: AI agent requests comprehensive analysis
        with patch("subprocess.run") as mock_run:
            # Mock Azure DevOps API calls (I/O layer)
            file_paths = list(mock_files.keys())
            mock_run.side_effect = [
                create_mock_iterations_response(),  # iterations call
                create_mock_changes_response(file_paths),  # changes call
                create_mock_pr_details_response(),  # PR details (may not be called in all tests)
            ]

            result = get_code_analysis_context(
                pr_id=TEST_PR_ID,
                org=TEST_ORG,
                project=TEST_PROJECT,
                repository=TEST_REPO,
                depth="comprehensive",
            )

            # Then: Comprehensive focus areas are provided
            guidelines = result.analysis_guidelines
            assert (
                len(guidelines.focus_areas) > 5
            )  # Comprehensive mode has more focus areas
            assert (
                "documentation" in str(guidelines.focus_areas).lower()
                or "testing" in str(guidelines.focus_areas).lower()
            )

    def test_ai_agents_can_detect_utility_files_as_simple_changes(
        self,
    ) -> None:
        """
        As an AI agent optimizing analysis effort
        When I encounter utility or helper files
        Then I recognize them as simple changes with reduced complexity
        """
        # Given: A PR with utility files
        mock_files = {
            "src/utils/payment_helpers.py": {},
        }

        # When: AI agent requests analysis
        with patch("subprocess.run") as mock_run:
            # Mock Azure DevOps API calls (I/O layer)
            file_paths = list(mock_files.keys())
            mock_run.side_effect = [
                create_mock_iterations_response(),  # iterations call
                create_mock_changes_response(file_paths),  # changes call
                create_mock_pr_details_response(),  # PR details (may not be called in all tests)
            ]

            result = get_code_analysis_context(
                pr_id=TEST_PR_ID,
                org=TEST_ORG,
                project=TEST_PROJECT,
                repository=TEST_REPO,
            )

            # Then: Complexity is recognized as low
            domain = result.domain_context
            assert domain.complexity_level == "low"

    def test_ai_agents_can_detect_actual_technology_patterns_without_mocking(
        self,
    ) -> None:
        """
        As an AI agent detecting technology patterns
        When I analyze files with clear technology indicators
        Then I correctly identify Spark, API, and database technologies
        """
        # Given: A PR with clear technology patterns
        mock_files = {
            "src/databricks/spark_processor.py": {},
            "src/api/endpoints/payment_service.py": {},
            "src/database/queries.sql": {},
        }

        # When: AI agent requests analysis
        with patch("subprocess.run") as mock_run:
            # Mock Azure DevOps API calls (I/O layer)
            file_paths = list(mock_files.keys())
            mock_run.side_effect = [
                create_mock_iterations_response(),  # iterations call
                create_mock_changes_response(file_paths),  # changes call
                create_mock_pr_details_response(),  # PR details (may not be called in all tests)
            ]

            result = get_code_analysis_context(
                pr_id=TEST_PR_ID,
                org=TEST_ORG,
                project=TEST_PROJECT,
                repository=TEST_REPO,
            )

            # Then: Multiple technologies are detected
            guidelines = result.analysis_guidelines
            tech_focus = guidelines.technology_focus.lower()
            assert "data_processing" in tech_focus
            assert "database" in tech_focus

            # And: Technology patterns include multiple domains
            domain = result.domain_context
            assert len(domain.technology_patterns) > 5

    def test_ai_agents_can_detect_complex_changes_vs_simple_changes(
        self,
    ) -> None:
        """
        As an AI agent assessing change complexity
        When I encounter multi-file changes
        Then I recognize them as medium complexity requiring standard analysis depth
        """
        # Given: A PR with multiple files
        mock_files = {
            "src/core/processor.py": {},
            "src/api/handlers.py": {},
            "src/models/transaction.py": {},
        }

        # When: AI agent requests analysis
        with patch("subprocess.run") as mock_run:
            # Mock Azure DevOps API calls (I/O layer)
            file_paths = list(mock_files.keys())
            mock_run.side_effect = [
                create_mock_iterations_response(),  # iterations call
                create_mock_changes_response(file_paths),  # changes call
                create_mock_pr_details_response(),  # PR details (may not be called in all tests)
            ]

            result = get_code_analysis_context(
                pr_id=TEST_PR_ID,
                org=TEST_ORG,
                project=TEST_PROJECT,
                repository=TEST_REPO,
            )

            # Then: Complexity is recognized as medium
            domain = result.domain_context
            assert domain.complexity_level == "medium"

    def test_ai_agents_can_detect_infrastructure_as_code_patterns(
        self,
    ) -> None:
        """
        As an AI agent analyzing infrastructure changes
        When I encounter IaC files (Bicep, ARM, Terraform)
        Then I receive infrastructure-specific analysis context
        """
        # Given: A PR with IaC files
        mock_files = {
            "deployment/main.bicep": {},
            "infrastructure/resources.json": {},
        }

        # When: AI agent requests analysis
        with patch("subprocess.run") as mock_run:
            # Mock Azure DevOps API calls (I/O layer)
            file_paths = list(mock_files.keys())
            mock_run.side_effect = [
                create_mock_iterations_response(),  # iterations call
                create_mock_changes_response(file_paths),  # changes call
                create_mock_pr_details_response(),  # PR details (may not be called in all tests)
            ]

            result = get_code_analysis_context(
                pr_id=TEST_PR_ID,
                org=TEST_ORG,
                project=TEST_PROJECT,
                repository=TEST_REPO,
            )

            # Then: Infrastructure technology is detected
            guidelines = result.analysis_guidelines
            assert "infrastructure" in guidelines.technology_focus.lower()

            # And: Infrastructure patterns are included
            domain = result.domain_context
            patterns_str = str(domain.technology_patterns).lower()
            assert "infrastructure" in patterns_str or "deployment" in patterns_str

    def test_ai_agents_receive_security_context_for_vulnerability_analysis(
        self,
    ) -> None:
        """
        As an AI agent performing security analysis
        When I analyze any code
        Then I receive comprehensive security patterns and compliance requirements
        """
        # Given: A PR that requires security analysis
        mock_files = {
            "src/auth/authentication.py": {},
        }

        # When: AI agent requests analysis
        with patch("subprocess.run") as mock_run:
            # Mock Azure DevOps API calls (I/O layer)
            file_paths = list(mock_files.keys())
            mock_run.side_effect = [
                create_mock_iterations_response(),  # iterations call
                create_mock_changes_response(file_paths),  # changes call
                create_mock_pr_details_response(),  # PR details (may not be called in all tests)
            ]

            result = get_code_analysis_context(
                pr_id=TEST_PR_ID,
                org=TEST_ORG,
                project=TEST_PROJECT,
                repository=TEST_REPO,
            )

            # Then: Security patterns are provided
            domain = result.domain_context
            assert len(domain.security_patterns) > 0
            assert any(
                "credential" in pattern.lower() or "authentication" in pattern.lower()
                for pattern in domain.security_patterns
            )

    def test_ai_agents_receive_minimal_context_for_simple_analysis_requests(
        self,
    ) -> None:
        """
        As an AI agent optimizing analysis efficiency
        When I request minimal analysis depth
        Then I receive focused context without extended focus areas
        """
        # Given: A simple PR
        mock_files = {
            "src/config.py": {},
        }

        # When: AI agent requests minimal analysis
        with patch("subprocess.run") as mock_run:
            # Mock Azure DevOps API calls (I/O layer)
            file_paths = list(mock_files.keys())
            mock_run.side_effect = [
                create_mock_iterations_response(),  # iterations call
                create_mock_changes_response(file_paths),  # changes call
                create_mock_pr_details_response(),  # PR details (may not be called in all tests)
            ]

            result = get_code_analysis_context(
                pr_id=TEST_PR_ID,
                org=TEST_ORG,
                project=TEST_PROJECT,
                repository=TEST_REPO,
                depth="minimal",
            )

            # Then: Focus areas are minimal
            guidelines = result.analysis_guidelines
            assert (
                len(guidelines.focus_areas) <= 3
            )  # Minimal mode has fewer focus areas

    def test_ai_agents_can_use_pr_metadata_to_enhance_analysis_context(
        self,
    ) -> None:
        """
        As an AI agent using PR metadata
        When PR details are available
        Then I receive enhanced context with PR title and description in guidelines
        """
        # Given: A PR with metadata available from Azure DevOps API
        mock_file_paths = ["src/payment.py"]

        # Mock the Azure CLI response (I/O boundary)
        mock_pr_data = {
            "pullRequestId": TEST_PR_ID,
            "title": "Add payment validation",
            "description": "This PR adds comprehensive validation for payment processing",
            "status": "active",
        }

        # When: AI agent requests analysis with PR metadata available
        with patch("subprocess.run") as mock_subprocess:
            # Mock subprocess.run to return Azure DevOps API responses at I/O boundary
            mock_subprocess.side_effect = [
                create_mock_iterations_response(),  # iterations call
                create_mock_changes_response(mock_file_paths),  # changes call
                Mock(returncode=0, stdout=json.dumps(mock_pr_data)),  # PR details
            ]

            result = get_code_analysis_context(
                pr_id=TEST_PR_ID,
                org=TEST_ORG,
                project=TEST_PROJECT,
                repository=TEST_REPO,
            )

            # Then: PR metadata is incorporated into guidelines
            guidelines = result.analysis_guidelines
            assert "Add payment validation" in guidelines.objective


class TestAIAgentsHandleComplexAnalysisScenarios:
    """Test AI agents handling complex multi-dimensional analysis scenarios."""

    def test_ai_agents_adapt_analysis_depth_for_complex_multi_technology_changes(self):
        """
        As an AI agent analyzing complex multi-technology PRs
        When I encounter changes across Spark, APIs, and infrastructure
        Then I receive comprehensive context covering all technology domains
        """
        # Given: A complex PR with multiple technologies
        mock_files = {
            "src/databricks/silver/processor.py": {},
            "src/api/payment_endpoints.py": {},
            "deployment/main.bicep": {},
            "src/database/migrations/001.sql": {},
        }

        # When: AI agent requests comprehensive analysis
        with patch("subprocess.run") as mock_run:
            # Mock Azure DevOps API calls (I/O layer)
            file_paths = list(mock_files.keys())
            mock_run.side_effect = [
                create_mock_iterations_response(),  # iterations call
                create_mock_changes_response(file_paths),  # changes call
                create_mock_pr_details_response(),  # PR details (may not be called in all tests)
            ]

            result = get_code_analysis_context(
                pr_id=TEST_PR_ID,
                org=TEST_ORG,
                project=TEST_PROJECT,
                repository=TEST_REPO,
                depth="comprehensive",
            )

            # Then: Multiple technologies are detected
            guidelines = result.analysis_guidelines
            tech_focus = guidelines.technology_focus.lower()
            assert "data_processing" in tech_focus
            assert "infrastructure" in tech_focus
            assert "database" in tech_focus

            # And: Comprehensive analysis depth is applied
            assert len(guidelines.focus_areas) > 5


class TestAIAgentsCanAutomaticallyFetchPRFiles:
    """Test the critical auto-fetch workflow that enables AI code review."""

    def test_ai_agents_can_automatically_fetch_pr_files_when_given_pr_context(
        self,
    ):
        """
        As an AI agent starting a code review workflow
        When I provide PR context (org/project/repository/pr_id)
        Then the tool automatically fetches the changed files from Azure DevOps API
        So I don't need to manually provide file lists
        """
        # Given: A PR with changed files in Azure DevOps
        mock_files = {
            "src/payment_processor.py": {"changeType": "edit"},
            "src/models/transaction.py": {"changeType": "add"},
            "tests/test_processor.py": {"changeType": "edit"},
        }

        # When: AI agent requests analysis context with only PR parameters
        with patch("subprocess.run") as mock_run:
            # Mock Azure DevOps API calls (I/O layer)
            file_paths = list(mock_files.keys())
            mock_run.side_effect = [
                create_mock_iterations_response(),  # iterations call
                create_mock_changes_response(file_paths),  # changes call
                create_mock_pr_details_response(),  # PR details (may not be called in all tests)
            ]

            result = get_code_analysis_context(
                pr_id=TEST_PR_ID,
                org=TEST_ORG,
                project=TEST_PROJECT,
                repository=TEST_REPO,
            )

            # Then: The tool fetched files from Azure DevOps API
            # subprocess.run was called for API requests
            assert mock_run.call_count >= 2  # At least iterations + changes

            # And: The result includes the fetched files
            assert len(result.files) == 3
            assert "src/payment_processor.py" in result.files
            assert "src/models/transaction.py" in result.files
            assert "tests/test_processor.py" in result.files

    def test_ai_agents_can_start_code_review_workflow_with_only_pr_url_info(
        self,
    ):
        """
        As an AI agent given a PR URL by a developer
        When I extract org/project/repository/pr_id from the URL
        Then I can immediately start the code review workflow by calling get_code_analysis_context
        So developers have a seamless single-step workflow
        """
        # Given: A developer provides a PR URL (we extract the components)
        # URL would be: https://dev.azure.com/{TEST_ORG}/{TEST_PROJECT}/_git/{TEST_REPO}/pullrequest/{TEST_PR_ID}

        # And: The PR has changed files
        mock_files = {
            "src/core/engine.py": {},
            "src/api/handlers.py": {},
        }

        # When: AI agent extracts URL components and requests analysis
        with patch("subprocess.run") as mock_run:
            # Mock Azure DevOps API calls (I/O layer)
            file_paths = list(mock_files.keys())
            mock_run.side_effect = [
                create_mock_iterations_response(),  # iterations call
                create_mock_changes_response(file_paths),  # changes call
                create_mock_pr_details_response(),  # PR details (may not be called in all tests)
            ]

            result = get_code_analysis_context(
                pr_id=TEST_PR_ID,
                org=TEST_ORG,
                project=TEST_PROJECT,
                repository=TEST_REPO,
            )

            # Then: The workflow completes successfully in a single call
            assert len(result.files) == 2
            assert result.pr_id == TEST_PR_ID

            # And: Analysis context is ready for code review
            assert isinstance(result.analysis_guidelines, AnalysisGuidelines)
            assert isinstance(result.domain_context, DomainContext)

    def test_ai_agents_get_empty_list_when_auto_fetch_fails_gracefully(
        self,
    ):
        """
        As an AI agent handling API failures gracefully
        When the Azure DevOps API call to fetch files fails
        Then I receive an empty file list instead of a crash
        So the workflow can continue with whatever information is available
        """
        # Given: Azure DevOps API is unavailable or returns an error

        # When: AI agent requests analysis and API fails at I/O boundary
        with patch("subprocess.run") as mock_subprocess:
            # Mock subprocess.run to fail (simulating Azure CLI failure)
            mock_subprocess.side_effect = Exception("API unavailable")

            result = get_code_analysis_context(
                pr_id=TEST_PR_ID,
                org=TEST_ORG,
                project=TEST_PROJECT,
                repository=TEST_REPO,
            )

            # Then: Empty list is returned gracefully
            assert result.files == []

            # And: Other analysis context is still provided
            assert isinstance(result.analysis_guidelines, AnalysisGuidelines)
            assert isinstance(result.domain_context, DomainContext)


class TestAIAgentsCanUseModernContextBasedAPIs:
    """
    Test that AI agents can use the modern context-first API approach
    for get_code_analysis_context, matching the pattern used by other tools.
    """

    def test_ai_agents_can_get_analysis_context_using_pr_url_for_convenience(self):
        """
        As an AI agent given a PR URL by a developer
        When I call get_code_analysis_context with just the pr_url parameter
        Then I receive complete analysis context without manually parsing the URL
        So I have a streamlined single-step workflow
        """
        # Given: A developer provides a PR URL
        pr_url = f"https://dev.azure.com/{TEST_ORG}/{TEST_PROJECT}/_git/{TEST_REPO}/pullrequest/{TEST_PR_ID}"

        # And: The PR has changed files
        mock_files = {"src/core/engine.py": {}, "src/api/handlers.py": {}}

        # When: AI agent requests analysis using just the URL
        with patch("subprocess.run") as mock_run:
            # Mock the Azure DevOps API call that fetches files
            mock_run.return_value = Mock(
                returncode=0, stdout=json.dumps({"changeEntries": []})
            )

            with patch(
                "pdp_dev_mcp.tools.code_review.ai_comment_posting._get_pr_diff_files"
            ) as mock_get_files:
                mock_get_files.return_value = mock_files

                result = get_code_analysis_context(pr_url=pr_url, depth="standard")

                # Then: Analysis context is returned successfully
                assert isinstance(result, CodeAnalysisContext)
                assert result.pr_id == TEST_PR_ID
                assert len(result.files) == 2
                assert "src/core/engine.py" in result.files
                assert "src/api/handlers.py" in result.files

                # And: API was called with correctly parsed parameters
                mock_get_files.assert_called_once_with(
                    TEST_ORG, TEST_PROJECT, TEST_REPO, TEST_PR_ID
                )

    def test_ai_agents_can_get_analysis_context_using_pr_context_object_for_consistency(
        self,
    ):
        """
        As an AI agent using the context-first pattern
        When I establish context once and reuse it across multiple tools
        Then I can pass the same context to get_code_analysis_context
        So I have consistent behavior across all PR analysis tools
        """
        # Given: An established PR context (from azure_devops_establish_pr_context)
        from pdp_dev_mcp.tools.common.azure_devops_common import (
            AzureDevOpsPRContext,
        )

        pr_context = AzureDevOpsPRContext(
            pr_url=f"https://dev.azure.com/{TEST_ORG}/{TEST_PROJECT}/_git/{TEST_REPO}/pullrequest/{TEST_PR_ID}",
            organization=TEST_ORG,
            project=TEST_PROJECT,
            repository=TEST_REPO,
            pr_id=TEST_PR_ID,
            source="url",
        )

        # And: The PR has changed files
        mock_files = {"src/payments/processor.py": {}}

        # When: AI agent requests analysis using the context object
        with patch(
            "pdp_dev_mcp.tools.code_review.ai_comment_posting._get_pr_diff_files"
        ) as mock_get_files:
            mock_get_files.return_value = mock_files

            result = get_code_analysis_context(pr_context=pr_context)

            # Then: Analysis context is returned with context-extracted parameters
            assert isinstance(result, CodeAnalysisContext)
            assert result.pr_id == TEST_PR_ID
            assert len(result.files) == 1
            assert "src/payments/processor.py" in result.files

            # And: API was called with parameters from the context object
            mock_get_files.assert_called_once_with(
                TEST_ORG, TEST_PROJECT, TEST_REPO, TEST_PR_ID
            )

    def test_ai_agents_can_still_use_legacy_individual_parameters_for_backward_compatibility(
        self,
    ):
        """
        As an AI agent or existing code using the old API
        When I call get_code_analysis_context with individual parameters
        Then the function still works exactly as before
        So backward compatibility is maintained
        """
        # Given: Individual parameters in the legacy style
        mock_files = {"src/legacy/module.py": {}}

        # When: AI agent uses legacy parameter style
        with patch(
            "pdp_dev_mcp.tools.code_review.ai_comment_posting._get_pr_diff_files"
        ) as mock_get_files:
            mock_get_files.return_value = mock_files

            result = get_code_analysis_context(
                pr_id=TEST_PR_ID,
                org=TEST_ORG,
                project=TEST_PROJECT,
                repository=TEST_REPO,
            )

            # Then: Function works as before
            assert isinstance(result, CodeAnalysisContext)
            assert result.pr_id == TEST_PR_ID
            assert len(result.files) == 1

    def test_ai_agents_receive_clear_error_when_missing_required_parameters(self):
        """
        As an AI agent making an invalid API call
        When I call get_code_analysis_context without sufficient parameters
        Then I receive a clear error message explaining what's needed
        So I can correct my tool usage
        """
        # Given: No parameters provided

        # When: AI agent calls without required parameters
        # Then: Clear error is raised
        with pytest.raises(ValueError) as exc_info:
            get_code_analysis_context()

        assert "Must provide either" in str(exc_info.value)
        assert "pr_context" in str(exc_info.value)
        assert "pr_url" in str(exc_info.value)
        assert "pr_id, org, project, and repository" in str(exc_info.value)

    def test_ai_agents_can_use_modern_visualstudio_url_format_for_direct_analysis(
        self,
    ):
        """
        As an AI agent working with modern visualstudio.com URLs
        When I provide a PR URL in the modern visualstudio.com format with URL-encoded spaces
        Then the function correctly parses and uses it
        So I can work with all Azure DevOps URL formats
        """
        # Given: A modern visualstudio.com PR URL with encoded spaces
        pr_url = "https://microsoft.visualstudio.com/Universal%20Store/_git/Commerce.PaymentsDataPlatform/pullrequest/13903594"

        # And: The PR has changed files
        mock_files = {"src/payments/universal_store.py": {}}

        # When: AI agent requests analysis using the modern visualstudio.com URL
        with patch(
            "pdp_dev_mcp.tools.code_review.ai_comment_posting._get_pr_diff_files"
        ) as mock_get_files:
            mock_get_files.return_value = mock_files

            result = get_code_analysis_context(pr_url=pr_url)

            # Then: URL is correctly parsed and analysis succeeds
            assert isinstance(result, CodeAnalysisContext)
            assert result.pr_id == 13903594
            assert len(result.files) == 1

            # And: API was called with correctly decoded parameters
            mock_get_files.assert_called_once_with(
                "microsoft",
                "Universal Store",
                "Commerce.PaymentsDataPlatform",
                13903594,
            )
