"""
BDD Tests for Azure DevOps PR Comment Posting

Tests the ability to post comments and replies to PRs in Azure DevOps.
"""

import json
from datetime import datetime
from unittest.mock import Mock, patch

import pytest


class TestAzureDevOpsPRCommentPosting:
    """
    BDD Test: Post new comment thread to a pull request
    
    Given a pull request that needs feedback or updates
    When I want to add a comment to the PR
    Then I should be able to create a new comment thread
    And the comment should appear in the PR
    
    Context:
    - Comments are organized in threads in Azure DevOps
    - Each thread can have multiple comments (replies)
    - New threads start with parentCommentId = 0
    - commentType = 1 for text comments
    - Thread status can be "active", "fixed", "closed", etc.
    
    Use cases:
    - AI agents providing feedback on code changes
    - Automated tools posting analysis results
    - Developers adding comments programmatically
    """
    
    def test_post_new_comment_thread_to_pr(self):
        """
        Scenario: Post a new top-level comment thread to PR
        
        Given a pull request in Azure DevOps
        And I have established PR context
        When I post a new comment with text content
        Then the comment should be created as a new thread
        And the thread should have status "active"
        And the API should return the created thread details
        
        Implementation notes:
        - Uses az rest with POST method
        - Endpoint: .../pullRequests/{pr_id}/threads?api-version=7.0
        - Body includes comments array with parentCommentId=0
        - Returns created thread with thread ID
        """
        # Given: A PR context
        mock_pr_context = {
            "organization": "microsoft",
            "project": "Universal Store",
            "repository": "Commerce.PaymentsDataPlatform",
            "pr_id": 14469941,
            "pr_url": "https://microsoft.visualstudio.com/Universal%20Store/_git/Commerce.PaymentsDataPlatform/pullrequest/14469941",
        }
        
        # Mock project and repo GUID lookups
        mock_project_guid = "e8efa521-db8e-4531-9cd8-6923807c7e83"
        mock_repo_guid = "0e4e93c3-d007-477e-860b-1d95d7be89a1"
        
        # Mock successful comment creation response
        mock_thread_response = {
            "id": 12345,
            "status": "active",
            "threadContext": None,
            "comments": [
                {
                    "id": 1,
                    "parentCommentId": 0,
                    "author": {
                        "displayName": "Jack Pines",
                        "uniqueName": "v-pinesjack@microsoft.com"
                    },
                    "content": "This looks good! Nice work on the refactoring.",
                    "publishedDate": datetime.now().isoformat(),
                    "commentType": "text"
                }
            ],
            "properties": {}
        }
        
        with (
            patch("pdp_dev_mcp.tools.common.azure_devops_pr_comments.get_repository_context"),
            patch("pdp_dev_mcp.tools.common.azure_devops_pr_comments.get_project_identifier", return_value=mock_project_guid),
            patch("subprocess.run") as mock_subprocess
        ):
            # Mock subprocess calls
            mock_subprocess.side_effect = [
                Mock(returncode=0, stdout=json.dumps({"id": mock_repo_guid, "project": {"id": mock_project_guid}})),  # Repo info
                Mock(returncode=0, stdout=json.dumps(mock_thread_response)),  # Comment creation
            ]
            
            # When: Posting a new comment
            from pdp_dev_mcp.tools.common.azure_devops_pr_comments import azure_devops_post_pr_comment
            from pdp_dev_mcp.tools.common.azure_devops_common import AzureDevOpsPRContext
            
            pr_context = AzureDevOpsPRContext(
                pr_url=mock_pr_context["pr_url"],
                organization=mock_pr_context["organization"],
                project=mock_pr_context["project"],
                repository=mock_pr_context["repository"],
                pr_id=mock_pr_context["pr_id"],
                source="url",
            )
            
            result = azure_devops_post_pr_comment(
                pr_context=pr_context,
                comment_text="This looks good! Nice work on the refactoring.",
                thread_status="active"
            )
            
            # Then: Comment should be created successfully
            assert result["success"], f"Expected success. Got error: {result.get('error')}"
            assert result["thread_id"] == 12345, f"Expected thread_id 12345, got {result.get('thread_id')}"
            assert result["comment_id"] == 1, f"Expected comment_id 1, got {result.get('comment_id')}"
            assert result["thread_status"] == "active"
            
            # And: Should have called az rest with correct parameters
            calls = mock_subprocess.call_args_list
            post_call = calls[1]  # Second call is the POST (first is repo info)
            args = post_call[0][0]
            
            assert "az" in args
            assert "rest" in args
            assert "--method" in args
            assert "POST" in args
            assert "--uri" in args
            assert f"pullRequests/{mock_pr_context['pr_id']}/threads" in " ".join(args)
            assert "--resource" in args
            assert "499b84ac-1321-427f-aa17-267ca6975798" in args
            assert "--body" in args


class TestAzureDevOpsPRCommentReplies:
    """
    BDD Test: Reply to existing comment thread
    
    Given an existing comment thread on a PR
    When I want to reply to that thread
    Then I should be able to add a reply comment
    And the reply should be nested under the parent thread
    
    Context:
    - Replies use the threads/{thread_id}/comments endpoint
    - parentCommentId references the comment being replied to
    - Thread ID must exist in the PR
    
    Use cases:
    - AI agents responding to feedback
    - Developers clarifying questions
    - Automated tools updating status
    """
    
    def test_reply_to_existing_comment_thread(self):
        """
        Scenario: Reply to an existing comment thread
        
        Given a pull request with an existing comment thread
        And I have the thread ID
        When I post a reply to that thread
        Then the reply should be added to the thread
        And the reply should reference the parent comment
        
        Implementation notes:
        - Uses az rest with POST method
        - Endpoint: .../pullRequests/{pr_id}/threads/{thread_id}/comments?api-version=7.0
        - Body includes content and parentCommentId
        - Returns created comment details
        """
        # Given: A PR context and existing thread
        mock_pr_context = {
            "organization": "microsoft",
            "project": "Universal Store",
            "repository": "Commerce.PaymentsDataPlatform",
            "pr_id": 14469941,
            "pr_url": "https://microsoft.visualstudio.com/Universal%20Store/_git/Commerce.PaymentsDataPlatform/pullrequest/14469941",
        }
        
        existing_thread_id = 12345
        parent_comment_id = 1
        
        # Mock project and repo GUID lookups
        mock_project_guid = "e8efa521-db8e-4531-9cd8-6923807c7e83"
        mock_repo_guid = "0e4e93c3-d007-477e-860b-1d95d7be89a1"
        
        # Mock successful reply response
        mock_reply_response = {
            "id": 2,
            "parentCommentId": parent_comment_id,
            "author": {
                "displayName": "Jack Pines",
                "uniqueName": "v-pinesjack@microsoft.com"
            },
            "content": "Thanks for the feedback! I've addressed your concerns.",
            "publishedDate": datetime.now().isoformat(),
            "commentType": "text"
        }
        
        with (
            patch("pdp_dev_mcp.tools.common.azure_devops_pr_comments.get_repository_context"),
            patch("pdp_dev_mcp.tools.common.azure_devops_pr_comments.get_project_identifier", return_value=mock_project_guid),
            patch("subprocess.run") as mock_subprocess
        ):
            # Mock subprocess calls
            mock_subprocess.side_effect = [
                Mock(returncode=0, stdout=json.dumps({"id": mock_repo_guid, "project": {"id": mock_project_guid}})),  # Repo info
                Mock(returncode=0, stdout=json.dumps(mock_reply_response)),  # Reply creation
            ]
            
            # When: Posting a reply
            from pdp_dev_mcp.tools.common.azure_devops_pr_comments import azure_devops_reply_to_pr_comment
            from pdp_dev_mcp.tools.common.azure_devops_common import AzureDevOpsPRContext
            
            pr_context = AzureDevOpsPRContext(
                pr_url=mock_pr_context["pr_url"],
                organization=mock_pr_context["organization"],
                project=mock_pr_context["project"],
                repository=mock_pr_context["repository"],
                pr_id=mock_pr_context["pr_id"],
                source="url",
            )
            
            result = azure_devops_reply_to_pr_comment(
                pr_context=pr_context,
                thread_id=existing_thread_id,
                comment_text="Thanks for the feedback! I've addressed your concerns.",
                parent_comment_id=parent_comment_id
            )
            
            # Then: Reply should be created successfully
            assert result["success"], f"Expected success. Got error: {result.get('error')}"
            assert result["comment_id"] == 2, f"Expected comment_id 2, got {result.get('comment_id')}"
            assert result["parent_comment_id"] == parent_comment_id
            assert result["thread_id"] == existing_thread_id
            
            # And: Should have called az rest with correct parameters
            calls = mock_subprocess.call_args_list
            post_call = calls[1]  # Second call is the POST (first is repo info)
            args = post_call[0][0]
            
            assert "az" in args
            assert "rest" in args
            assert "--method" in args
            assert "POST" in args
            assert "--uri" in args
            assert f"threads/{existing_thread_id}/comments" in " ".join(args)
            assert "--resource" in args
            assert "499b84ac-1321-427f-aa17-267ca6975798" in args
            assert "--body" in args
