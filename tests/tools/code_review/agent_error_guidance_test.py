"""Test AI agent-specific error handling and guidance."""

from unittest.mock import Mock, patch
from pdp_dev_mcp.tools.code_review.ai_comment_posting import (
    post_ai_generated_comments,
    create_ai_comment,
    CommentType,
    CommentSeverity,
)


class TestAIAgentsCanReceiveErrorGuidanceForTroubleshooting:
    """Test that AI agents can receive comprehensive error guidance for troubleshooting Azure DevOps operations."""

    @patch("subprocess.run")
    def test_ai_agents_can_get_authentication_error_guidance_to_resolve_login_issues(
        self, mock_subprocess
    ):
        """As an AI agent helping developers with Azure DevOps operations,
        When I encounter authentication errors,
        Then I should receive clear guidance on resolving login issues,
        So I can help the developer troubleshoot Azure CLI authentication problems."""
        
        # Given: AI agent creates a comment to post
        comment = create_ai_comment(
            comment_id="auth_test",
            title="Test Comment",
            content="Test authentication error handling",
            comment_type=CommentType.GENERAL,
            severity=CommentSeverity.INFO,
        )
        
        # When: Authentication errors occur during API operations
        auth_errors = [
            "authentication failed",
            "Unauthorized access - 401", 
            "AUTHENTICATION_ERROR: Token expired",
        ]
        
        for error_message in auth_errors:
            mock_subprocess.return_value = Mock(returncode=1, stderr=error_message)
            
            result = post_ai_generated_comments(
                org="test-org",
                project="test-project", 
                repository="test-repo",
                pr_id=123,
                comments=[comment],
                dry_run=False
            )
            
            # Then: Error guidance includes authentication troubleshooting steps
            assert result.failed_posts > 0
            assert len(result.failures) > 0
            failure = result.failures[0]
            guidance = failure.get("agent_guidance", "")
            assert "az account show" in guidance  # Core troubleshooting step

    @patch("subprocess.run")
    def test_ai_agents_can_get_permission_error_guidance_to_resolve_access_issues(self, mock_subprocess):
        """As an AI agent helping developers with Azure DevOps PR operations,
        When I encounter permission errors,
        Then I should receive specific guidance on resolving access issues,
        So I can help the developer understand and fix Azure DevOps permissions problems."""
        
        # Given: AI agent creates a comment to post  
        comment = create_ai_comment(
            comment_id="perm_test",
            title="Test Comment",
            content="Test permission error handling",
            comment_type=CommentType.GENERAL,
            severity=CommentSeverity.INFO,
        )
        
        # When: Permission errors occur during API operations
        perm_errors = [
            "Forbidden - 403",
            "Access forbidden to resource", 
            "FORBIDDEN: insufficient permissions",
        ]
        
        for error_message in perm_errors:
            mock_subprocess.return_value = Mock(returncode=1, stderr=error_message)
            
            result = post_ai_generated_comments(
                org="test-org",
                project="test-project",
                repository="test-repo", 
                pr_id=123,
                comments=[comment],
                dry_run=False
            )
            
            # Then: Error guidance includes permission troubleshooting steps
            assert result.failed_posts > 0
            assert len(result.failures) > 0
            failure = result.failures[0]
            guidance = failure.get("agent_guidance", "")
            assert "permissions" in guidance.lower()  # Core issue identification

    @patch("subprocess.run")
    def test_ai_agents_can_get_not_found_error_guidance_to_resolve_resource_issues(
        self, mock_subprocess
    ):
        """As an AI agent helping developers with Azure DevOps resource access,
        When I encounter resource not found errors,
        Then I should receive clear guidance on identifying missing resources,
        So I can help the developer understand and resolve repository or PR access problems."""
        
        # Given: AI agent creates a comment to post
        comment = create_ai_comment(
            comment_id="test",
            title="Test Comment", 
            content="Test resource not found handling",
            comment_type=CommentType.GENERAL,
            severity=CommentSeverity.INFO,
        )
        
        # When: Resource not found errors occur during API operations
        not_found_errors = [
            "Resource not found - 404",
            "PR not found",
            "Repository does not exist",
        ]

        for error_message in not_found_errors:
            mock_subprocess.return_value = Mock(returncode=1, stderr=error_message)
            
            result = post_ai_generated_comments(
                org="test-org",
                project="test-project",
                repository="test-repo",
                pr_id=123,
                comments=[comment],
                dry_run=False
            )
            
            # Then: Error guidance includes resource troubleshooting steps
            assert result.failed_posts > 0
            assert len(result.failures) > 0
            failure = result.failures[0]
            guidance = failure.get("agent_guidance", "")
            assert "repository" in guidance.lower() or "project" in guidance.lower() or "exists" in guidance.lower()

    @patch("subprocess.run")
    def test_ai_agents_can_get_connectivity_error_guidance_to_resolve_network_issues(
        self, mock_subprocess
    ):
        """As an AI agent helping developers with Azure DevOps API operations,
        When I encounter network connectivity errors,
        Then I should receive comprehensive guidance on diagnosing connection problems,
        So I can help the developer troubleshoot network connectivity and Azure service availability."""
        
        # Given: AI agent creates a comment to post
        comment = create_ai_comment(
            comment_id="test", 
            title="Test Comment",
            content="Test connectivity error handling",
            comment_type=CommentType.GENERAL,
            severity=CommentSeverity.INFO,
        )
        
        # When: Connectivity errors occur during API operations
        conn_errors = [
            "Connection timeout occurred",
            "ConnectionError: Failed to reach server",
            "Network timeout after 30 seconds",
        ]

        for error_message in conn_errors:
            mock_subprocess.return_value = Mock(returncode=1, stderr=error_message)
            
            result = post_ai_generated_comments(
                org="test-org",
                project="test-project",
                repository="test-repo",
                pr_id=123,
                comments=[comment],
                dry_run=False
            )
            
            # Then: Error guidance includes connectivity troubleshooting steps
            assert result.failed_posts > 0
            assert len(result.failures) > 0
            failure = result.failures[0]
            guidance = failure.get("agent_guidance", "")
            assert len(guidance) > 0  # Some guidance provided for connectivity issues

    @patch("subprocess.run")
    def test_ai_agents_can_get_rate_limit_error_guidance_to_resolve_throttling_issues(
        self, mock_subprocess
    ):
        """As an AI agent helping developers with Azure DevOps API operations,
        When I encounter rate limiting errors,
        Then I should receive specific guidance on handling API throttling,
        So I can help the developer implement proper rate limiting strategies and batch processing."""
        
        # Given: AI agent creates a comment to post
        comment = create_ai_comment(
            comment_id="test",
            title="Test Comment",
            content="Test rate limit error handling", 
            comment_type=CommentType.GENERAL,
            severity=CommentSeverity.INFO,
        )
        
        # When: Rate limit errors occur during API operations
        rate_errors = [
            "Rate limit exceeded - 429",
            "Too many requests - rate limit hit",
            "API rate limit reached",
        ]

        for error_message in rate_errors:
            mock_subprocess.return_value = Mock(returncode=1, stderr=error_message)
            
            result = post_ai_generated_comments(
                org="test-org",
                project="test-project", 
                repository="test-repo",
                pr_id=123,
                comments=[comment],
                dry_run=False
            )
            
            # Then: Error guidance includes rate limiting troubleshooting steps
            assert result.failed_posts > 0
            assert len(result.failures) > 0
            failure = result.failures[0]
            guidance = failure.get("agent_guidance", "")
            assert len(guidance) > 0  # Some guidance provided for rate limiting

    @patch("subprocess.run")
    def test_ai_agents_can_get_json_decode_error_guidance_to_resolve_parsing_issues(
        self, mock_subprocess
    ):
        """As an AI agent helping developers with Azure DevOps API responses,
        When I encounter JSON parsing errors,
        Then I should receive clear guidance on handling malformed API responses,
        So I can help the developer diagnose and resolve Azure DevOps API response format issues."""
        
        # Given: AI agent creates a comment to post
        comment = create_ai_comment(
            comment_id="test",
            title="Test Comment",
            content="Test JSON decode error handling",
            comment_type=CommentType.GENERAL,
            severity=CommentSeverity.INFO,
        )
        
        # When: JSON decode errors occur during API operations
        json_errors = [
            "JSON decode error: invalid format",
            "Failed to decode JSON response",
            "JSONDecodeError: Expecting value",
        ]

        for error_message in json_errors:
            mock_subprocess.return_value = Mock(returncode=1, stderr=error_message)
            
            result = post_ai_generated_comments(
                org="test-org",
                project="test-project",
                repository="test-repo",
                pr_id=123,
                comments=[comment],
                dry_run=False
            )
            
            # Then: Error guidance includes JSON parsing troubleshooting steps
            assert result.failed_posts > 0
            assert len(result.failures) > 0
            failure = result.failures[0]
            guidance = failure.get("agent_guidance", "")
            assert len(guidance) > 0  # Some guidance provided for JSON issues

    @patch("subprocess.run")
    def test_ai_agents_can_get_azure_cli_error_guidance_to_resolve_tooling_issues(self, mock_subprocess):
        """As an AI agent helping developers with Azure CLI integration,
        When I encounter Azure CLI specific errors,
        Then I should receive detailed guidance on resolving CLI tooling problems,
        So I can help the developer diagnose and fix Azure CLI installation and configuration issues."""
        
        # Given: AI agent creates a comment to post
        comment = create_ai_comment(
            comment_id="test",
            title="Test Comment",
            content="Test Azure CLI error handling",
            comment_type=CommentType.GENERAL,
            severity=CommentSeverity.INFO,
        )
        
        # When: Azure CLI errors occur during API operations
        cli_errors = [
            "Azure CLI not found",
            "az command failed",
            "Azure CLI authentication required",
        ]

        for error_message in cli_errors:
            mock_subprocess.return_value = Mock(returncode=1, stderr=error_message)
            
            result = post_ai_generated_comments(
                org="test-org",
                project="test-project",
                repository="test-repo",
                pr_id=123,
                comments=[comment],
                dry_run=False
            )
            
            # Then: Error guidance includes Azure CLI troubleshooting steps
            assert result.failed_posts > 0
            assert len(result.failures) > 0
            failure = result.failures[0]
            guidance = failure.get("agent_guidance", "")
            assert "Azure CLI" in guidance or "az" in guidance  # CLI-specific guidance

    @patch("subprocess.run")
    def test_ai_agents_can_get_general_error_guidance_to_resolve_unknown_issues(self, mock_subprocess):
        """As an AI agent helping developers with Azure DevOps operations,
        When I encounter unknown or general errors,
        Then I should receive comprehensive fallback guidance for troubleshooting,
        So I can help the developer systematically diagnose and resolve unexpected Azure DevOps problems."""
        
        # Given: AI agent creates a comment to post
        comment = create_ai_comment(
            comment_id="test",
            title="Test Comment",
            content="Test general error handling",
            comment_type=CommentType.GENERAL,
            severity=CommentSeverity.INFO,
        )
        
        # When: General errors occur during API operations
        general_errors = [
            "Unexpected database error",
            "Unknown system failure",
            "Internal server error - 500",
        ]

        for error_message in general_errors:
            mock_subprocess.return_value = Mock(returncode=1, stderr=error_message)
            
            result = post_ai_generated_comments(
                org="test-org",
                project="test-project",
                repository="test-repo",
                pr_id=123,
                comments=[comment],
                dry_run=False
            )
            
            # Then: Error guidance includes general troubleshooting steps
            assert result.failed_posts > 0
            assert len(result.failures) > 0
            failure = result.failures[0]
            guidance = failure.get("agent_guidance", "")
            assert len(guidance) > 0  # Some guidance provided for general errors

    @patch("subprocess.run")
    def test_ai_agents_receive_structured_error_guidance_for_comprehensive_troubleshooting(
        self, mock_subprocess
    ):
        """As an AI agent helping developers with Azure DevOps troubleshooting,
        When I request error guidance for any type of error,
        Then I should receive well-structured guidance following agent-friendly patterns,
        So I can provide comprehensive and actionable troubleshooting assistance to developers."""
        
        # Given: AI agent creates a comment to post
        comment = create_ai_comment(
            comment_id="test",
            title="Test Comment",
            content="Test structured error guidance",
            comment_type=CommentType.GENERAL,
            severity=CommentSeverity.INFO,
        )
        
        # When: Any error occurs during API operations (using authentication as example)
        mock_subprocess.return_value = Mock(returncode=1, stderr="authentication failed")
        
        result = post_ai_generated_comments(
            org="test-org",
            project="test-project",
            repository="test-repo",
            pr_id=123,
            comments=[comment],
            dry_run=False
        )
        
        # Then: Error guidance is structured and comprehensive
        assert result.failed_posts > 0
        assert len(result.failures) > 0
        failure = result.failures[0]
        assert "agent_guidance" in failure
        guidance = failure["agent_guidance"]
        
        # Should provide actionable guidance
        assert isinstance(guidance, str)
        assert len(guidance) > 10  # Meaningful guidance provided
        assert any(
            keyword in guidance.lower()
            for keyword in ["verify", "check", "ensure", "account", "show"]
        )
