"""Test PR URL parsing functionality for AI agents assisting developers."""

from pdp_dev_mcp.tools.common.enhanced_repository_discovery import (
    parse_azure_devops_pr_url,
)


class TestAIAgentsCanParseAzureDevOpsPRUrls:
    """
    AI agents need to parse Azure DevOps PR URLs to provide
    accurate code review assistance across different URL formats.
    """

    def test_ai_agents_can_parse_modern_azure_devops_pr_urls_for_developer_assistance(
        self,
    ):
        """
        As an AI agent helping developers with code review
        When I receive a modern dev.azure.com PR URL
        Then I extract organization, project, repository, and PR ID
        so I can access the correct Azure DevOps context for the developer
        """
        # Given: An AI agent receives a modern Azure DevOps PR URL
        pr_url = "https://dev.azure.com/msazure/One/_git/CFS-Payments-DataPlatform-PMT/pullrequest/13483931"

        # When: AI agent parses the URL to assist developer
        org, project, repository, pr_id = parse_azure_devops_pr_url(pr_url)

        # Then: All URL components are correctly extracted for Azure DevOps operations
        assert org == "msazure", (
            f"Expected organization 'msazure' but got '{org}' - AI agent cannot locate correct Azure DevOps org from URL: {pr_url}"
        )
        assert project == "One", (
            f"Expected project 'One' but got '{project}' - AI agent cannot access correct project from URL: {pr_url}"
        )
        assert repository == "CFS-Payments-DataPlatform-PMT", (
            f"Expected repository 'CFS-Payments-DataPlatform-PMT' but got '{repository}' - AI agent cannot identify repository from URL: {pr_url}"
        )
        assert pr_id == "13483931", (
            f"Expected PR ID '13483931' but got '{pr_id}' - AI agent cannot reference correct PR from URL: {pr_url}"
        )

    def test_ai_agents_can_parse_legacy_azure_devops_pr_urls_for_backward_compatibility(
        self,
    ):
        """
        As an AI agent working with legacy Azure DevOps instances
        When I receive a legacy .visualstudio.com PR URL
        Then I extract all required components correctly
        so I can assist developers with older repositories
        """
        # Given: An AI agent receives a legacy Azure DevOps PR URL
        pr_url = "https://microsoft.visualstudio.com/DefaultCollection/PaymentsDataPlatform/_git/Commerce.PaymentsDataPlatform/pullrequest/123456"

        # When: AI agent parses the legacy URL format
        org, project, repository, pr_id = parse_azure_devops_pr_url(pr_url)

        # Then: Legacy URL components are correctly extracted for developer assistance
        assert org == "microsoft", (
            f"Expected organization 'microsoft' but got '{org}' - AI agent cannot identify legacy org from URL: {pr_url}"
        )
        assert project == "PaymentsDataPlatform", (
            f"Expected project 'PaymentsDataPlatform' but got '{project}' - AI agent cannot access legacy project from URL: {pr_url}"
        )
        assert repository == "Commerce.PaymentsDataPlatform", (
            f"Expected repository 'Commerce.PaymentsDataPlatform' but got '{repository}' - AI agent cannot identify legacy repository from URL: {pr_url}"
        )
        assert pr_id == "123456", (
            f"Expected PR ID '123456' but got '{pr_id}' - AI agent cannot reference legacy PR from URL: {pr_url}"
        )

    def test_ai_agents_can_parse_repository_urls_without_pr_for_general_operations(
        self,
    ):
        """
        As an AI agent helping with repository operations
        When I receive a git repository URL without a PR reference
        Then I extract repository information and indicate no PR ID
        so I can assist developers with general repository tasks beyond code review
        """
        # Given: An AI agent receives a repository URL without PR reference
        git_url = "https://dev.azure.com/msazure/One/_git/CFS-Payments-DataPlatform-PMT"

        # When: AI agent parses the repository URL for developer assistance
        org, project, repository, pr_id = parse_azure_devops_pr_url(git_url)

        # Then: Repository components are extracted with empty PR ID for general operations
        assert org == "msazure", (
            f"Expected organization 'msazure' but got '{org}' - AI agent cannot identify org from repo URL: {git_url}"
        )
        assert project == "One", (
            f"Expected project 'One' but got '{project}' - AI agent cannot access project from repo URL: {git_url}"
        )
        assert repository == "CFS-Payments-DataPlatform-PMT", (
            f"Expected repository 'CFS-Payments-DataPlatform-PMT' but got '{repository}' - AI agent cannot identify repository from repo URL: {git_url}"
        )
        assert pr_id == "", (
            f"Expected empty PR ID for repository URL but got '{pr_id}' - AI agent incorrectly detected PR from repo URL: {git_url}"
        )

    def test_ai_agents_can_parse_legacy_repository_urls_for_general_operations(self):
        """
        As an AI agent working with legacy Azure DevOps instances
        When I receive a legacy git repository URL without PR reference
        Then I extract repository information correctly
        so I can assist developers with legacy repository operations
        """
        # Given: An AI agent receives a legacy repository URL without PR reference
        git_url = "https://microsoft.visualstudio.com/DefaultCollection/PaymentsDataPlatform/_git/Commerce.PaymentsDataPlatform"

        # When: AI agent parses the legacy repository URL for developer assistance
        org, project, repository, pr_id = parse_azure_devops_pr_url(git_url)

        # Then: Legacy repository components are extracted with empty PR ID
        assert org == "microsoft", (
            f"Expected organization 'microsoft' but got '{org}' - AI agent cannot identify legacy org from repo URL: {git_url}"
        )
        assert project == "PaymentsDataPlatform", (
            f"Expected project 'PaymentsDataPlatform' but got '{project}' - AI agent cannot access legacy project from repo URL: {git_url}"
        )
        assert repository == "Commerce.PaymentsDataPlatform", (
            f"Expected repository 'Commerce.PaymentsDataPlatform' but got '{repository}' - AI agent cannot identify legacy repository from repo URL: {git_url}"
        )
        assert pr_id == "", (
            f"Expected empty PR ID for repository URL but got '{pr_id}' - AI agent incorrectly detected PR from legacy repo URL: {git_url}"
        )

    def test_ai_agents_can_parse_git_urls_with_git_suffix_for_flexibility(self):
        """
        As an AI agent handling various repository URL formats
        When I receive a git URL with .git suffix
        Then I extract repository information correctly
        so I can assist developers regardless of URL format variations
        """
        # Given: An AI agent receives a git URL with .git suffix
        git_url = (
            "https://dev.azure.com/msazure/One/_git/CFS-Payments-DataPlatform-PMT.git"
        )

        # When: AI agent parses the URL with .git suffix
        org, project, repository, pr_id = parse_azure_devops_pr_url(git_url)

        # Then: Repository components are extracted correctly ignoring .git suffix
        assert org == "msazure", (
            f"Expected organization 'msazure' but got '{org}' - AI agent cannot identify org from .git URL: {git_url}"
        )
        assert project == "One", (
            f"Expected project 'One' but got '{project}' - AI agent cannot access project from .git URL: {git_url}"
        )
        assert repository == "CFS-Payments-DataPlatform-PMT", (
            f"Expected repository 'CFS-Payments-DataPlatform-PMT' but got '{repository}' - AI agent cannot identify repository from .git URL: {git_url}"
        )
        assert pr_id == "", (
            f"Expected empty PR ID for .git URL but got '{pr_id}' - AI agent incorrectly detected PR from .git URL: {git_url}"
        )

    def test_ai_agents_can_parse_urls_with_encoded_spaces_for_proper_decoding(self):
        """
        As an AI agent handling URL-encoded project names
        When I receive a URL with URL-encoded spaces in project name
        Then I decode the spaces correctly
        so I can provide accurate project information to developers
        """
        # Given: An AI agent receives a URL with URL-encoded spaces
        pr_url = (
            "https://dev.azure.com/contoso/My%20Project/_git/MyRepo/pullrequest/789"
        )

        # When: AI agent parses the URL with encoded spaces
        org, project, repository, pr_id = parse_azure_devops_pr_url(pr_url)

        # Then: URL-encoded spaces are correctly decoded for developer use
        assert org == "contoso", (
            f"Expected organization 'contoso' but got '{org}' - AI agent cannot identify org from encoded URL: {pr_url}"
        )
        assert project == "My Project", (  # Should decode %20 to space
            f"Expected project 'My Project' but got '{project}' - AI agent failed to decode URL-encoded spaces from: {pr_url}"
        )
        assert repository == "MyRepo", (
            f"Expected repository 'MyRepo' but got '{repository}' - AI agent cannot identify repository from encoded URL: {pr_url}"
        )
        assert pr_id == "789", (
            f"Expected PR ID '789' but got '{pr_id}' - AI agent cannot reference PR from encoded URL: {pr_url}"
        )

    def test_ai_agents_can_parse_real_world_pr_urls_for_production_scenarios(self):
        """
        As an AI agent working with real production URLs
        When I receive actual PR URLs from developer workflows
        Then I extract all components correctly
        so I can provide reliable assistance with real-world scenarios
        """
        # Given: An AI agent receives a real-world PR URL from production use
        pr_url1 = "https://dev.azure.com/msazure/One/_git/CFS-Payments-DataPlatform-PMT/pullrequest/13483931"

        # When: AI agent parses the real-world URL
        org1, project1, repository1, pr_id1 = parse_azure_devops_pr_url(pr_url1)

        # Then: Real-world URL components are extracted correctly for developer assistance
        assert org1 == "msazure", (
            f"Expected organization 'msazure' but got '{org1}' - AI agent cannot identify org from real-world URL: {pr_url1}"
        )
        assert project1 == "One", (
            f"Expected project 'One' but got '{project1}' - AI agent cannot access project from real-world URL: {pr_url1}"
        )
        assert repository1 == "CFS-Payments-DataPlatform-PMT", (
            f"Expected repository 'CFS-Payments-DataPlatform-PMT' but got '{repository1}' - AI agent cannot identify repository from real-world URL: {pr_url1}"
        )
        assert pr_id1 == "13483931", (
            f"Expected PR ID '13483931' but got '{pr_id1}' - AI agent cannot reference PR from real-world URL: {pr_url1}"
        )

    def test_ai_agents_handle_invalid_urls_gracefully_for_error_recovery(self):
        """
        As an AI agent receiving potentially invalid URLs
        When I receive a non-Azure DevOps URL
        Then I return empty values gracefully
        so I can inform developers about unsupported URL formats
        """
        # Given: An AI agent receives an invalid non-Azure DevOps URL
        invalid_url = "https://github.com/user/repo/pull/123"

        # When: AI agent attempts to parse the invalid URL
        org, project, repository, pr_id = parse_azure_devops_pr_url(invalid_url)

        # Then: Empty values are returned for unsupported URLs
        assert org == "", (
            f"Expected empty organization but got '{org}' - AI agent should return empty for invalid URL: {invalid_url}"
        )
        assert project == "", (
            f"Expected empty project but got '{project}' - AI agent should return empty for invalid URL: {invalid_url}"
        )
        assert repository == "", (
            f"Expected empty repository but got '{repository}' - AI agent should return empty for invalid URL: {invalid_url}"
        )
        assert pr_id == "", (
            f"Expected empty PR ID but got '{pr_id}' - AI agent should return empty for invalid URL: {invalid_url}"
        )

    def test_ai_agents_handle_empty_urls_gracefully_for_robust_operation(self):
        """
        As an AI agent receiving potentially empty input
        When I receive an empty URL string
        Then I return empty values gracefully
        so I can handle edge cases without crashing and inform developers appropriately
        """
        # Given: An AI agent receives an empty URL string
        empty_url = ""

        # When: AI agent attempts to parse the empty URL
        org, project, repository, pr_id = parse_azure_devops_pr_url(empty_url)

        # Then: Empty values are returned for empty input
        assert org == "", (
            f"Expected empty organization but got '{org}' - AI agent should handle empty URL gracefully"
        )
        assert project == "", (
            f"Expected empty project but got '{project}' - AI agent should handle empty URL gracefully"
        )
        assert repository == "", (
            f"Expected empty repository but got '{repository}' - AI agent should handle empty URL gracefully"
        )
        assert pr_id == "", (
            f"Expected empty PR ID but got '{pr_id}' - AI agent should handle empty URL gracefully"
        )

    def test_ai_agents_can_parse_modern_visualstudio_pr_urls_with_encoded_spaces(self):
        """
        As an AI agent working with modern visualstudio.com URLs
        When I receive a modern format visualstudio.com PR URL with URL-encoded spaces
        Then I extract all components correctly including decoding spaces
        so I can provide accurate assistance with modern visualstudio.com repositories
        """
        # Given: An AI agent receives a modern visualstudio.com PR URL with encoded spaces
        pr_url = "https://microsoft.visualstudio.com/Universal%20Store/_git/Commerce.PaymentsDataPlatform/pullrequest/13903594"

        # When: AI agent parses the modern visualstudio.com URL
        org, project, repository, pr_id = parse_azure_devops_pr_url(pr_url)

        # Then: All URL components are correctly extracted with decoded spaces
        assert org == "microsoft", (
            f"Expected organization 'microsoft' but got '{org}' - AI agent cannot identify org from modern visualstudio.com URL: {pr_url}"
        )
        assert project == "Universal Store", (
            f"Expected project 'Universal Store' but got '{project}' - AI agent failed to decode URL-encoded spaces in modern visualstudio.com URL: {pr_url}"
        )
        assert repository == "Commerce.PaymentsDataPlatform", (
            f"Expected repository 'Commerce.PaymentsDataPlatform' but got '{repository}' - AI agent cannot identify repository from modern visualstudio.com URL: {pr_url}"
        )
        assert pr_id == "13903594", (
            f"Expected PR ID '13903594' but got '{pr_id}' - AI agent cannot reference PR from modern visualstudio.com URL: {pr_url}"
        )
