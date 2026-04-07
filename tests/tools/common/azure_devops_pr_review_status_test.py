"""
BDD tests for Azure DevOps PR Review Status functionality.

Tests focus on user stories and business value - helping developers and DevOps
engineers understand the true review status of pull requests, including which
approvals have been invalidated by subsequent commits.

Follows the project's BDD testing standards for clear, maintainable tests.
"""

from unittest.mock import Mock, patch
import json
from datetime import datetime, timedelta

from pdp_dev_mcp.tools.common.azure_devops_pr_review import (
    azure_devops_get_pr_review_status,
)


class TestDeveloperPRReviewStatusWorkflow:
    """
    Developers need accurate PR review status information to understand
    what actions are required before merging, especially when approvals
    have been invalidated by subsequent commits.
    """

    def test_developer_sees_invalidated_approvals_after_new_commit(self):
        """
        As a developer
        When I push a new commit after reviewers have approved
        Then I can see which approvals were invalidated and need reapproval
        
        This is the core scenario: branch policies require approvals "since last commit",
        so all approvals given before the latest commit become invalid.
        """
        # Given: A PR with 2 approvals, then a new commit pushed after
        now = datetime.now()
        approval_time = now - timedelta(hours=2)  # Approved 2 hours ago
        commit_time = now - timedelta(hours=1)    # New commit 1 hour ago
        
        mock_repo_context = {
            "success": True,
            "organization": "microsoft",
            "project": "Universal Store",
            "repository": "Commerce.PaymentsDataPlatform",
            "org_url": "https://dev.azure.com/microsoft",
        }
        
        mock_pr_details = {
            "pullRequestId": 14446184,
            "title": "Test PR with invalidated approvals",
            "status": "active",
            "createdBy": {"displayName": "Test Developer"},
            "creationDate": (now - timedelta(days=1)).isoformat(),
            "repository": {
                "name": "Commerce.PaymentsDataPlatform",
                "project": {"name": "Universal Store"}
            },
            "reviewers": [
                {
                    "id": "approver1-id",
                    "displayName": "Approver One",
                    "uniqueName": "approver1@microsoft.com",
                    "vote": 10,  # Approved
                    "votedFor": [{"date": approval_time.isoformat()}]
                },
                {
                    "id": "approver2-id",
                    "displayName": "Approver Two", 
                    "uniqueName": "approver2@microsoft.com",
                    "vote": 10,  # Approved
                    "votedFor": [{"date": approval_time.isoformat()}]
                },
                {
                    "id": "pending-id",
                    "displayName": "Pending Reviewer",
                    "uniqueName": "pending@microsoft.com",
                    "vote": 0,  # No vote yet
                    "votedFor": []
                }
            ],
            "commits": [
                {"commitId": "abc123", "author": {"date": commit_time.isoformat()}},
            ]
        }
        
        # Mock commits response from REST API
        mock_commits_response = {
            "value": [
                {
                    "commitId": "abc123",
                    "committer": {"date": commit_time.isoformat()},
                    "author": {"date": commit_time.isoformat()}
                }
            ]
        }
        
        # Mock properties response with stale approvals
        mock_properties_response = {
            "value": {
                "OneReviewPolicyPilot": {
                    "$value": json.dumps({
                        "OwnerPaths": [{
                            "OwnerVotes": [
                                {"Id": "approver1-id", "ApprovalState": "Stale"},
                                {"Id": "approver2-id", "ApprovalState": "Stale"}
                            ]
                        }]
                    })
                }
            }
        }
        
        with (
            patch("pdp_dev_mcp.tools.common.azure_devops_pr_review.get_repository_context", return_value=mock_repo_context),
            patch("subprocess.run") as mock_subprocess
        ):
            # Mock responses for multiple subprocess calls:
            # 1. PR details call (az repos pr show)
            # 2. Commit history call (az rest)
            # 3. Properties call (az rest)
            mock_subprocess.side_effect = [
                Mock(returncode=0, stdout=json.dumps(mock_pr_details)),  # PR details
                Mock(returncode=0, stdout=json.dumps(mock_commits_response)),  # Commits
                Mock(returncode=0, stdout=json.dumps(mock_properties_response)),  # Properties
            ]
            
            # When: Developer checks PR review status
            result = azure_devops_get_pr_review_status(
                pr_id=14446184,
                working_directory="/test/repo/path"
            )
            
            # Then: The system correctly identifies invalidated approvals
            assert result["success"], "PR status retrieval should succeed"
            
            # And: Shows 2 invalidated approvers
            invalidated_approvers = result["approval_status"]["invalidated_approvers"]
            assert len(invalidated_approvers) == 2, (
                f"Expected 2 invalidated approvers after new commit, got {len(invalidated_approvers)}"
            )
            
            # And: Shows names of who needs to reapprove
            invalidated_names = [r["name"] for r in invalidated_approvers]
            assert "Approver One" in invalidated_names
            assert "Approver Two" in invalidated_names
            
            # And: Indicates 2 more approvals are needed (policy requires 2 since last commit)
            assert result["approval_status"]["needs_approvals_count"] == 2, (
                "Should need 2 approvals since both were invalidated by commit"
            )
            
            # And: Summary clearly states the situation
            summary = result["summary"]
            assert "invalidated" in summary.lower(), (
                "Summary should mention invalidated approvals"
            )

    def test_developer_sees_blocking_rejection(self):
        """
        As a developer
        When a reviewer rejects my PR
        Then I can clearly see who rejected it and why I can't merge
        
        Rejections (vote=-10) are blocking - the PR cannot be completed
        until the rejection is resolved (reviewer changes to approve or waits).
        """
        # Given: A PR with one approval but one rejection
        now = datetime.now()
        
        mock_repo_context = {
            "success": True,
            "organization": "microsoft",
            "project": "Universal Store",
            "repository": "Commerce.PaymentsDataPlatform",
            "org_url": "https://dev.azure.com/microsoft",
        }
        
        mock_pr_details = {
            "pullRequestId": 14389303,
            "title": "Test PR with rejection",
            "status": "active",
            "reviewers": [
                {
                    "displayName": "Approving Reviewer",
                    "uniqueName": "approver@microsoft.com",
                    "vote": 10,  # Approved
                    "votedFor": [{"date": now.isoformat()}]
                },
                {
                    "displayName": "Rejecting Reviewer",
                    "uniqueName": "rejector@microsoft.com",
                    "vote": -10,  # Rejected - this is blocking!
                    "votedFor": [{"date": now.isoformat()}]
                }
            ],
            "commits": []
        }
        
        with (
            patch("pdp_dev_mcp.tools.common.azure_devops_pr_review.get_repository_context", return_value=mock_repo_context),
            patch("subprocess.run") as mock_subprocess
        ):
            mock_subprocess.return_value = Mock(
                returncode=0,
                stdout=json.dumps(mock_pr_details)
            )
            
            # When: Developer checks PR status
            result = azure_devops_get_pr_review_status(
                pr_id=14389303,
                working_directory="/test/repo/path"
            )
            
            # Then: System shows rejection is blocking
            assert result["success"]
            assert result["approval_status"]["has_rejection"], (
                "Should indicate PR has blocking rejection"
            )
            
            # And: Shows who rejected
            rejecting_reviewers = result["approval_status"]["rejecting_reviewers"]
            assert len(rejecting_reviewers) == 1
            assert rejecting_reviewers[0]["name"] == "Rejecting Reviewer"
            assert rejecting_reviewers[0]["vote"] == -10
            
            # And: Summary clearly indicates blocking status
            summary = result["summary"]
            assert "reject" in summary.lower(), (
                "Summary should mention rejection"
            )
            assert "cannot merge" in summary.lower() or "blocked" in summary.lower(), (
                "Summary should indicate PR is blocked"
            )

    def test_developer_sees_waiting_for_author_status(self):
        """
        As a developer
        When reviewers mark "Waiting for Author" (vote=-5)
        Then I can see that I need to address feedback before they'll approve
        
        "Waiting for Author" is not blocking like rejection, but indicates
        the reviewer expects changes before giving approval.
        """
        # Given: A PR with "Waiting for Author" votes
        now = datetime.now()
        
        mock_repo_context = {
            "success": True,
            "organization": "microsoft",
            "project": "Universal Store",
            "repository": "Commerce.PaymentsDataPlatform",
            "org_url": "https://dev.azure.com/microsoft",
        }
        
        mock_pr_details = {
            "pullRequestId": 14388031,
            "title": "Test PR waiting for author",
            "status": "active",
            "reviewers": [
                {
                    "displayName": "Reviewer One",
                    "uniqueName": "reviewer1@microsoft.com",
                    "vote": -5,  # Waiting for author
                    "votedFor": [{"date": now.isoformat()}]
                },
                {
                    "displayName": "Reviewer Two",
                    "uniqueName": "reviewer2@microsoft.com",
                    "vote": -5,  # Waiting for author
                    "votedFor": [{"date": now.isoformat()}]
                }
            ],
            "commits": []
        }
        
        with (
            patch("pdp_dev_mcp.tools.common.azure_devops_pr_review.get_repository_context", return_value=mock_repo_context),
            patch("subprocess.run") as mock_subprocess
        ):
            mock_subprocess.return_value = Mock(
                returncode=0,
                stdout=json.dumps(mock_pr_details)
            )
            
            # When: Developer checks PR status
            result = azure_devops_get_pr_review_status(
                pr_id=14388031,
                working_directory="/test/repo/path"
            )
            
            # Then: System shows waiting status
            assert result["success"]
            
            waiting_reviewers = result["approval_status"]["waiting_reviewers"]
            assert len(waiting_reviewers) == 2, (
                f"Expected 2 waiting reviewers, got {len(waiting_reviewers)}"
            )
            
            # And: Shows who is waiting
            waiting_names = [r["name"] for r in waiting_reviewers]
            assert "Reviewer One" in waiting_names
            assert "Reviewer Two" in waiting_names
            
            # And: Summary indicates author action needed
            summary = result["summary"]
            assert "waiting" in summary.lower(), (
                "Summary should mention waiting for author"
            )

    def test_developer_sees_pr_ready_to_merge(self):
        """
        As a developer
        When my PR has enough valid approvals and no blockers
        Then I can see that it's ready to merge
        
        This is the success case: 2+ approvals since last commit,
        no rejections, no conflicts.
        """
        # Given: A PR with 2 valid approvals after latest commit
        now = datetime.now()
        commit_time = now - timedelta(hours=2)
        approval_time = now - timedelta(hours=1)  # Approved AFTER commit
        
        mock_repo_context = {
            "success": True,
            "organization": "microsoft",
            "project": "Universal Store",
            "repository": "Commerce.PaymentsDataPlatform",
            "org_url": "https://dev.azure.com/microsoft",
        }
        
        mock_pr_details = {
            "pullRequestId": 14364739,
            "title": "Test PR ready to merge",
            "status": "active",
            "reviewers": [
                {
                    "displayName": "Approver One",
                    "uniqueName": "approver1@microsoft.com",
                    "vote": 10,
                    "votedFor": [{"date": approval_time.isoformat()}]
                },
                {
                    "displayName": "Approver Two",
                    "uniqueName": "approver2@microsoft.com",
                    "vote": 10,
                    "votedFor": [{"date": approval_time.isoformat()}]
                }
            ],
            "commits": [
                {"commitId": "abc123", "author": {"date": commit_time.isoformat()}},
            ]
        }
        
        with (
            patch("pdp_dev_mcp.tools.common.azure_devops_pr_review.get_repository_context", return_value=mock_repo_context),
            patch("subprocess.run") as mock_subprocess
        ):
            mock_subprocess.return_value = Mock(
                returncode=0,
                stdout=json.dumps(mock_pr_details)
            )
            
            # When: Developer checks PR status
            result = azure_devops_get_pr_review_status(
                pr_id=14364739,
                working_directory="/test/repo/path"
            )
            
            # Then: System shows PR is ready
            assert result["success"]
            assert result["approval_status"]["is_approved"], (
                "PR with 2 valid approvals should be marked as approved"
            )
            assert result["approval_status"]["needs_approvals_count"] == 0, (
                "PR should need 0 more approvals"
            )
            
            # And: Shows valid approvers
            valid_approvers = result["approval_status"]["valid_approvers"]
            assert len(valid_approvers) == 2
            
            # And: No invalidated approvals
            assert len(result["approval_status"]["invalidated_approvers"]) == 0
            
            # And: Summary indicates ready to merge
            summary = result["summary"]
            assert "ready" in summary.lower() or "approved" in summary.lower(), (
                "Summary should indicate PR is ready to merge"
            )


class TestDevOpsEngineerPRReviewStatusWorkflow:
    """
    DevOps engineers need batch PR status information to monitor
    team velocity and identify PRs that need attention.
    """

    def test_engineer_gets_status_for_multiple_prs(self):
        """
        As a DevOps engineer
        When I want to monitor team PRs
        Then I can get status for multiple PRs in one call
        
        This supports the use case from the feature request: creating
        a Teams message summarizing all active PRs.
        """
        # Given: Multiple PRs with different states
        mock_repo_context = {
            "success": True,
            "organization": "microsoft",
            "project": "Universal Store",
            "repository": "Commerce.PaymentsDataPlatform",
            "org_url": "https://dev.azure.com/microsoft",
        }
        
        # This test will verify that the tool can be called multiple times
        # efficiently (we'll implement batch support in Phase 4 if needed)
        
        with (
            patch("pdp_dev_mcp.tools.common.azure_devops_pr_review.get_repository_context", return_value=mock_repo_context),
            patch("subprocess.run") as mock_subprocess
        ):
            # Track state for which PR we're currently processing
            current_pr_id = [None]
            call_sequence = [0]  # Track position in 4-call sequence (PR, token, commits, properties)
            
            def mock_pr_call(*args, **kwargs):
                cmd = args[0] if args else []
                cmd_str = " ".join(cmd) if isinstance(cmd, list) else str(cmd)
                
                # Detect which type of call this is
                if "az repos pr show" in cmd_str or "pullrequest" in cmd_str.lower():
                    # This is a PR details call - determine which PR
                    if "14446184" in cmd_str:
                        current_pr_id[0] = 14446184
                        call_sequence[0] = 1  # Next will be token
                        return Mock(returncode=0, stdout=json.dumps({
                            "pullRequestId": 14446184,
                            "title": "PR with invalidated approvals",
                            "status": "active",
                            "createdBy": {"displayName": "Developer One"},
                            "creationDate": "2025-01-01T00:00:00Z",
                            "repository": {"webUrl": "https://dev.azure.com/microsoft/project/_git/repo", "name": "repo", "project": {"name": "project"}},
                            "reviewers": []
                        }))
                    elif "14389303" in cmd_str:
                        current_pr_id[0] = 14389303
                        call_sequence[0] = 1  # Next will be token
                        return Mock(returncode=0, stdout=json.dumps({
                            "pullRequestId": 14389303,
                            "title": "PR with rejection",
                            "status": "active",
                            "createdBy": {"displayName": "Developer Two"},
                            "creationDate": "2025-01-01T00:00:00Z",
                            "repository": {"webUrl": "https://dev.azure.com/microsoft/project/_git/repo", "name": "repo", "project": {"name": "project"}},
                            "reviewers": []
                        }))
                elif "az" in cmd_str and "rest" in cmd_str and "/commits" in cmd_str:
                    # Commits call (az rest)
                    call_sequence[0] = 2  # Next will be properties
                    return Mock(returncode=0, stdout=json.dumps({"value": []}))
                elif "az" in cmd_str and "rest" in cmd_str and "/properties" in cmd_str:
                    # Properties call (az rest)
                    call_sequence[0] = 0  # Next will be new PR
                    return Mock(returncode=0, stdout=json.dumps({"value": {}}))
                
                return Mock(returncode=1, stdout="{}")
            
            mock_subprocess.side_effect = mock_pr_call
            
            # When: Engineer checks status for multiple PRs
            pr_statuses = []
            for pr_id in [14446184, 14389303]:
                result = azure_devops_get_pr_review_status(
                    pr_id=pr_id,
                    working_directory="/test/repo/path"
                )
                pr_statuses.append(result)
            
            # Then: Got status for all PRs
            assert len(pr_statuses) == 2
            for i, status in enumerate(pr_statuses):
                if not status["success"]:
                    print(f"PR {i} failed: {status.get('error', 'Unknown error')}")
            assert all(status["success"] for status in pr_statuses), (
                f"All PR status retrievals should succeed. Errors: {[s.get('error') for s in pr_statuses if not s['success']]}"
            )

    def test_engineer_handles_api_errors_gracefully(self):
        """
        As a DevOps engineer
        When Azure DevOps API calls fail for some PRs
        Then I get clear error information without breaking the workflow
        
        This ensures resilience when monitoring many PRs.
        """
        # Given: A scenario where API calls might fail
        mock_repo_context = {
            "success": True,
            "organization": "microsoft",
            "project": "Universal Store",
            "repository": "Commerce.PaymentsDataPlatform",
            "org_url": "https://dev.azure.com/microsoft",
        }
        
        with (
            patch("pdp_dev_mcp.tools.common.azure_devops_pr_review.get_repository_context", return_value=mock_repo_context),
            patch("subprocess.run") as mock_subprocess
        ):
            # Mock API failure
            mock_subprocess.return_value = Mock(
                returncode=1,
                stderr="PR not found or access denied"
            )
            
            # When: Engineer tries to get status for non-existent/inaccessible PR
            result = azure_devops_get_pr_review_status(
                pr_id=99999999,
                working_directory="/test/repo/path"
            )
            
            # Then: Returns clear error without throwing exception
            assert not result["success"], (
                "Should indicate failure for inaccessible PR"
            )
            assert "error" in result, (
                "Should include error information"
            )
            assert result["error"], (
                "Error message should not be empty"
            )


class TestPRReviewStatusEdgeCases:
    """
    Edge cases and boundary conditions for PR review status detection.
    """

    def test_handles_pr_with_no_reviewers(self):
        """
        As a developer
        When my PR has no reviewers assigned yet
        Then I can see that it needs reviewers
        """
        # Given: A PR with no reviewers
        mock_repo_context = {
            "success": True,
            "organization": "microsoft",
            "project": "Universal Store",
            "repository": "Commerce.PaymentsDataPlatform",
            "org_url": "https://dev.azure.com/microsoft",
        }
        
        mock_pr_details = {
            "pullRequestId": 12345,
            "title": "PR with no reviewers",
            "status": "active",
            "reviewers": [],  # No reviewers at all
            "commits": []
        }
        
        with (
            patch("pdp_dev_mcp.tools.common.azure_devops_pr_review.get_repository_context", return_value=mock_repo_context),
            patch("subprocess.run") as mock_subprocess
        ):
            mock_subprocess.return_value = Mock(
                returncode=0,
                stdout=json.dumps(mock_pr_details)
            )
            
            # When: Checking PR status
            result = azure_devops_get_pr_review_status(
                pr_id=12345,
                working_directory="/test/repo/path"
            )
            
            # Then: Shows needs reviewers
            assert result["success"]
            assert result["approval_status"]["needs_approvals_count"] >= 2, (
                "PR should need at least 2 approvals"
            )
            assert len(result["approval_status"]["valid_approvers"]) == 0

    def test_handles_pr_with_only_approved_with_suggestions(self):
        """
        As a developer
        When reviewers approve with suggestions (vote=5)
        Then I can see these count as valid approvals
        
        Vote=5 is "Approved with suggestions" - counts toward approval
        requirement but indicates non-blocking feedback.
        """
        # Given: A PR with "Approved with suggestions" votes
        now = datetime.now()
        
        mock_repo_context = {
            "success": True,
            "organization": "microsoft",
            "project": "Universal Store",
            "repository": "Commerce.PaymentsDataPlatform",
            "org_url": "https://dev.azure.com/microsoft",
        }
        
        mock_pr_details = {
            "pullRequestId": 12345,
            "title": "PR approved with suggestions",
            "status": "active",
            "reviewers": [
                {
                    "displayName": "Reviewer One",
                    "uniqueName": "reviewer1@microsoft.com",
                    "vote": 5,  # Approved with suggestions
                    "votedFor": [{"date": now.isoformat()}]
                },
                {
                    "displayName": "Reviewer Two",
                    "uniqueName": "reviewer2@microsoft.com",
                    "vote": 5,  # Approved with suggestions
                    "votedFor": [{"date": now.isoformat()}]
                }
            ],
            "commits": []
        }
        
        with (
            patch("pdp_dev_mcp.tools.common.azure_devops_pr_review.get_repository_context", return_value=mock_repo_context),
            patch("subprocess.run") as mock_subprocess
        ):
            mock_subprocess.return_value = Mock(
                returncode=0,
                stdout=json.dumps(mock_pr_details)
            )
            
            # When: Checking PR status
            result = azure_devops_get_pr_review_status(
                pr_id=12345,
                working_directory="/test/repo/path"
            )
            
            # Then: These count as valid approvals
            assert result["success"]
            valid_approvers = result["approval_status"]["valid_approvers"]
            assert len(valid_approvers) == 2, (
                "Approved with suggestions (vote=5) should count as valid approval"
            )

    def test_handles_missing_vote_timestamps(self):
        """
        As a developer
        When vote timestamp data is missing from API response
        Then the system gracefully degrades and shows votes without timeline info
        
        This handles the error case mentioned in the feature request.
        """
        # Given: PR data with missing timestamp information
        mock_repo_context = {
            "success": True,
            "organization": "microsoft",
            "project": "Universal Store",
            "repository": "Commerce.PaymentsDataPlatform",
            "org_url": "https://dev.azure.com/microsoft",
        }
        
        mock_pr_details = {
            "pullRequestId": 12345,
            "title": "PR with missing timestamps",
            "status": "active",
            "reviewers": [
                {
                    "displayName": "Reviewer",
                    "uniqueName": "reviewer@microsoft.com",
                    "vote": 10,
                    # Missing votedFor field entirely
                }
            ],
            "commits": []
        }
        
        with (
            patch("pdp_dev_mcp.tools.common.azure_devops_pr_review.get_repository_context", return_value=mock_repo_context),
            patch("subprocess.run") as mock_subprocess
        ):
            mock_subprocess.return_value = Mock(
                returncode=0,
                stdout=json.dumps(mock_pr_details)
            )
            
            # When: Checking PR status
            result = azure_devops_get_pr_review_status(
                pr_id=12345,
                working_directory="/test/repo/path"
            )
            
            # Then: Should succeed with degraded information
            assert result["success"], (
                "Should succeed even with missing timestamp data"
            )
            
            # And: Shows the vote but with unknown invalidation status
            valid_approvers = result["approval_status"]["valid_approvers"]
            # At least one approver should be present
            assert len(valid_approvers) > 0, (
                "Should show approver even without timestamp data"
            )
            
            # And: Should indicate in summary that timeline info is limited
            # (The tool should handle gracefully without crashing)

    def test_handles_multiple_vote_changes_by_same_reviewer(self):
        """
        As a developer
        When a reviewer changes their vote multiple times
        Then the system uses the most recent vote status
        
        This tests that we correctly handle vote history when reviewers
        change from approve to reject or vice versa.
        """
        # Given: A PR where a reviewer changed their vote
        now = datetime.now()
        first_vote_time = now - timedelta(hours=3)
        second_vote_time = now - timedelta(hours=1)
        
        mock_repo_context = {
            "success": True,
            "organization": "microsoft",
            "project": "Universal Store",
            "repository": "Commerce.PaymentsDataPlatform",
            "org_url": "https://dev.azure.com/microsoft",
        }
        
        mock_pr_details = {
            "pullRequestId": 12345,
            "title": "PR with vote changes",
            "status": "active",
            "reviewers": [
                {
                    "displayName": "Reviewer",
                    "uniqueName": "reviewer@microsoft.com",
                    "vote": 10,  # Current vote is approval
                    "votedFor": [
                        {"date": first_vote_time.isoformat()},
                        {"date": second_vote_time.isoformat()}
                    ]
                }
            ],
            "commits": []
        }
        
        with (
            patch("pdp_dev_mcp.tools.common.azure_devops_pr_review.get_repository_context", return_value=mock_repo_context),
            patch("subprocess.run") as mock_subprocess
        ):
            mock_subprocess.return_value = Mock(
                returncode=0,
                stdout=json.dumps(mock_pr_details)
            )
            
            # When: Checking PR status
            result = azure_devops_get_pr_review_status(
                pr_id=12345,
                working_directory="/test/repo/path"
            )
            
            # Then: Uses the most recent vote (approval)
            assert result["success"]
            valid_approvers = result["approval_status"]["valid_approvers"]
            assert len(valid_approvers) == 1
            assert valid_approvers[0]["vote"] == 10

    def test_handles_vote_at_exact_same_time_as_commit(self):
        """
        As a developer
        When a vote is given at the exact same timestamp as a commit
        Then the system applies consistent tie-breaking logic
        
        Edge case: vote and commit timestamps match exactly.
        Conservative approach: consider vote before commit as invalidated.
        """
        # Given: Vote and commit at same exact time
        now = datetime.now()
        exact_time = now - timedelta(hours=1)
        
        mock_repo_context = {
            "success": True,
            "organization": "microsoft",
            "project": "Universal Store",
            "repository": "Commerce.PaymentsDataPlatform",
            "org_url": "https://dev.azure.com/microsoft",
        }
        
        mock_pr_details = {
            "pullRequestId": 12345,
            "title": "PR with simultaneous vote and commit",
            "status": "active",
            "repository": {
                "name": "Commerce.PaymentsDataPlatform",
                "project": {"name": "Universal Store"}
            },
            "reviewers": [
                {
                    "id": "reviewer-id",
                    "displayName": "Reviewer",
                    "uniqueName": "reviewer@microsoft.com",
                    "vote": 10,
                    "votedFor": [{"date": exact_time.isoformat()}]
                }
            ],
        }
        
        # Mock commits response from REST API
        mock_commits_response = {
            "value": [
                {
                    "commitId": "abc123",
                    "committer": {"date": exact_time.isoformat()},
                    "author": {"date": exact_time.isoformat()}
                }
            ]
        }
        
        # Mock properties response with stale approval (vote at same time as commit)
        mock_properties_response = {
            "value": {
                "OneReviewPolicyPilot": {
                    "$value": json.dumps({
                        "OwnerPaths": [{
                            "OwnerVotes": [
                                {"Id": "reviewer-id", "ApprovalState": "Stale"}
                            ]
                        }]
                    })
                }
            }
        }
        
        with (
            patch("pdp_dev_mcp.tools.common.azure_devops_pr_review.get_repository_context", return_value=mock_repo_context),
            patch("subprocess.run") as mock_subprocess
        ):
            mock_subprocess.side_effect = [
                Mock(returncode=0, stdout=json.dumps(mock_pr_details)),  # PR details
                Mock(returncode=0, stdout=json.dumps(mock_commits_response)),  # Commits
                Mock(returncode=0, stdout=json.dumps(mock_properties_response)),  # Properties
            ]
            
            # When: Checking PR status
            result = azure_devops_get_pr_review_status(
                pr_id=12345,
                working_directory="/test/repo/path"
            )
            
            # Then: Conservative approach - treat as invalidated
            assert result["success"]
            invalidated_approvers = result["approval_status"]["invalidated_approvers"]
            assert len(invalidated_approvers) == 1, (
                "Vote at same time as commit should be treated as invalidated (conservative)"
            )


class TestPRReviewStatusNetworkAndAPIErrors:
    """
    Test error handling for network failures, API errors, and malformed data.
    Critical for agentic tools to have actionable error messages.
    """

    def test_handles_network_timeout_gracefully(self):
        """
        As a DevOps engineer using agentic tools
        When Azure DevOps API calls timeout
        Then I get a clear error message indicating the timeout
        
        This ensures the AI agent can report the issue clearly to users.
        """
        # Given: A network timeout scenario
        mock_repo_context = {
            "success": True,
            "organization": "microsoft",
            "project": "Universal Store",
            "repository": "Commerce.PaymentsDataPlatform",
            "org_url": "https://dev.azure.com/microsoft",
        }
        
        with (
            patch("pdp_dev_mcp.tools.common.azure_devops_pr_review.get_repository_context", return_value=mock_repo_context),
            patch("subprocess.run") as mock_subprocess
        ):
            # Simulate timeout
            import subprocess
            mock_subprocess.side_effect = subprocess.TimeoutExpired(
                cmd=["az", "repos", "pr", "show"],
                timeout=30
            )
            
            # When: Trying to get PR status
            result = azure_devops_get_pr_review_status(
                pr_id=12345,
                working_directory="/test/repo/path"
            )
            
            # Then: Returns clear error about timeout
            assert not result["success"]
            assert "error" in result
            assert "timeout" in result["error"].lower(), (
                f"Error should mention timeout. Got: {result['error']}"
            )

    def test_handles_invalid_json_response_from_api(self):
        """
        As a DevOps engineer
        When Azure DevOps API returns malformed JSON
        Then I get a clear error about the parsing failure
        
        This helps diagnose API issues or Azure CLI problems.
        """
        # Given: API returns invalid JSON
        mock_repo_context = {
            "success": True,
            "organization": "microsoft",
            "project": "Universal Store",
            "repository": "Commerce.PaymentsDataPlatform",
            "org_url": "https://dev.azure.com/microsoft",
        }
        
        with (
            patch("pdp_dev_mcp.tools.common.azure_devops_pr_review.get_repository_context", return_value=mock_repo_context),
            patch("subprocess.run") as mock_subprocess
        ):
            # Return malformed JSON
            mock_subprocess.return_value = Mock(
                returncode=0,
                stdout="{ invalid json: this won't parse }"
            )
            
            # When: Trying to get PR status
            result = azure_devops_get_pr_review_status(
                pr_id=12345,
                working_directory="/test/repo/path"
            )
            
            # Then: Returns clear parsing error
            assert not result["success"]
            assert "error" in result
            assert "json" in result["error"].lower() or "parse" in result["error"].lower(), (
                f"Error should mention JSON parsing issue. Got: {result['error']}"
            )

    def test_handles_pr_not_found_error(self):
        """
        As a developer
        When I check status for a PR that doesn't exist
        Then I get a clear message that the PR wasn't found
        
        Common scenario: PR was deleted or ID is wrong.
        """
        # Given: API returns PR not found error
        mock_repo_context = {
            "success": True,
            "organization": "microsoft",
            "project": "Universal Store",
            "repository": "Commerce.PaymentsDataPlatform",
            "org_url": "https://dev.azure.com/microsoft",
        }
        
        with (
            patch("pdp_dev_mcp.tools.common.azure_devops_pr_review.get_repository_context", return_value=mock_repo_context),
            patch("subprocess.run") as mock_subprocess
        ):
            # Return error from Azure CLI
            mock_subprocess.return_value = Mock(
                returncode=1,
                stderr="TF401180: The requested pull request was not found."
            )
            
            # When: Trying to get status for non-existent PR
            result = azure_devops_get_pr_review_status(
                pr_id=99999999,
                working_directory="/test/repo/path"
            )
            
            # Then: Returns clear "not found" error
            assert not result["success"]
            assert "error" in result
            assert "not found" in result["error"].lower(), (
                f"Error should indicate PR not found. Got: {result['error']}"
            )

    def test_handles_permission_denied_error(self):
        """
        As a developer
        When I don't have permission to view a PR
        Then I get a clear permission error message
        
        This helps users understand access control issues.
        """
        # Given: API returns permission error
        mock_repo_context = {
            "success": True,
            "organization": "microsoft",
            "project": "Universal Store",
            "repository": "Commerce.PaymentsDataPlatform",
            "org_url": "https://dev.azure.com/microsoft",
        }
        
        with (
            patch("pdp_dev_mcp.tools.common.azure_devops_pr_review.get_repository_context", return_value=mock_repo_context),
            patch("subprocess.run") as mock_subprocess
        ):
            mock_subprocess.return_value = Mock(
                returncode=1,
                stderr="TF401019: The Git repository with name or identifier Commerce.PaymentsDataPlatform does not exist or you do not have permissions for the operation you are attempting."
            )
            
            # When: Trying to access restricted PR
            result = azure_devops_get_pr_review_status(
                pr_id=12345,
                working_directory="/test/repo/path"
            )
            
            # Then: Returns clear permission error
            assert not result["success"]
            assert "error" in result
            assert "permission" in result["error"].lower() or "access" in result["error"].lower(), (
                f"Error should mention permission issue. Got: {result['error']}"
            )

    def test_handles_missing_required_fields_in_api_response(self):
        """
        As a DevOps engineer
        When API response is missing required fields
        Then I get a clear error about what's missing
        
        This helps diagnose incomplete API responses or version mismatches.
        """
        # Given: API response missing required fields
        mock_repo_context = {
            "success": True,
            "organization": "microsoft",
            "project": "Universal Store",
            "repository": "Commerce.PaymentsDataPlatform",
            "org_url": "https://dev.azure.com/microsoft",
        }
        
        # Missing pullRequestId field
        mock_pr_details = {
            "title": "Test PR",
            "status": "active",
            # Missing pullRequestId!
            "reviewers": []
        }
        
        with (
            patch("pdp_dev_mcp.tools.common.azure_devops_pr_review.get_repository_context", return_value=mock_repo_context),
            patch("subprocess.run") as mock_subprocess
        ):
            mock_subprocess.return_value = Mock(
                returncode=0,
                stdout=json.dumps(mock_pr_details)
            )
            
            # When: Trying to process incomplete response
            result = azure_devops_get_pr_review_status(
                pr_id=12345,
                working_directory="/test/repo/path"
            )
            
            # Then: Returns clear error about missing field
            assert not result["success"]
            assert "error" in result
            # Error should be specific about what's wrong

    def test_handles_repository_context_failure(self):
        """
        As a developer
        When repository context discovery fails
        Then I get clear guidance on how to fix it
        
        Common scenario: not in a git repo or remote not configured.
        """
        # Given: Repository context fails
        mock_failed_context = {
            "success": False,
            "error": "Not a git repository",
            "suggestion": "Run this command in a git repository with Azure DevOps remote"
        }
        
        with patch("pdp_dev_mcp.tools.common.azure_devops_pr_review.get_repository_context", return_value=mock_failed_context):
            # When: Trying to get PR status without valid context
            result = azure_devops_get_pr_review_status(
                pr_id=12345,
                working_directory="/not/a/repo"
            )
            
            # Then: Returns clear context error with guidance
            assert not result["success"]
            assert "error" in result
            assert "repository" in result["error"].lower(), (
                f"Error should mention repository context. Got: {result['error']}"
            )
            assert "suggestion" in result or "how to fix" in str(result).lower(), (
                "Should provide guidance on fixing the issue"
            )


class TestPRReviewStatusComplexScenarios:
    """
    Test complex real-world scenarios that combine multiple conditions.
    """

    def test_handles_mix_of_valid_and_invalidated_approvals(self):
        """
        As a developer
        When my PR has some approvals before a commit and some after
        Then I can see exactly which are valid and which need reapproval
        
        Real scenario: 2 approvals, then commit, then 1 more approval.
        """
        # Given: Mixed approval timeline
        now = datetime.now()
        early_approval_time = now - timedelta(hours=4)
        commit_time = now - timedelta(hours=2)
        late_approval_time = now - timedelta(hours=1)
        
        mock_repo_context = {
            "success": True,
            "organization": "microsoft",
            "project": "Universal Store",
            "repository": "Commerce.PaymentsDataPlatform",
            "org_url": "https://dev.azure.com/microsoft",
        }
        
        mock_pr_details = {
            "pullRequestId": 12345,
            "title": "PR with mixed approvals",
            "status": "active",
            "repository": {
                "name": "Commerce.PaymentsDataPlatform",
                "project": {"name": "Universal Store"}
            },
            "reviewers": [
                {
                    "id": "early1-id",
                    "displayName": "Early Approver One",
                    "uniqueName": "early1@microsoft.com",
                    "vote": 10,
                    "votedFor": [{"date": early_approval_time.isoformat()}]
                },
                {
                    "id": "early2-id",
                    "displayName": "Early Approver Two",
                    "uniqueName": "early2@microsoft.com",
                    "vote": 10,
                    "votedFor": [{"date": early_approval_time.isoformat()}]
                },
                {
                    "id": "late-id",
                    "displayName": "Late Approver",
                    "uniqueName": "late@microsoft.com",
                    "vote": 10,
                    "votedFor": [{"date": late_approval_time.isoformat()}]
                }
            ],
        }
        
        # Mock commits response from REST API
        mock_commits_response = {
            "value": [
                {
                    "commitId": "abc123",
                    "committer": {"date": commit_time.isoformat()},
                    "author": {"date": commit_time.isoformat()}
                }
            ]
        }
        
        # Mock properties response - early approvals are stale, late approval is valid
        mock_properties_response = {
            "value": {
                "OneReviewPolicyPilot": {
                    "$value": json.dumps({
                        "OwnerPaths": [{
                            "OwnerVotes": [
                                {"Id": "early1-id", "ApprovalState": "Stale"},
                                {"Id": "early2-id", "ApprovalState": "Stale"},
                                {"Id": "late-id", "ApprovalState": "Valid"}
                            ]
                        }]
                    })
                }
            }
        }
        
        with (
            patch("pdp_dev_mcp.tools.common.azure_devops_pr_review.get_repository_context", return_value=mock_repo_context),
            patch("subprocess.run") as mock_subprocess
        ):
            mock_subprocess.side_effect = [
                Mock(returncode=0, stdout=json.dumps(mock_pr_details)),  # PR details
                Mock(returncode=0, stdout=json.dumps(mock_commits_response)),  # Commits
                Mock(returncode=0, stdout=json.dumps(mock_properties_response)),  # Properties
            ]
            
            # When: Checking PR status
            result = azure_devops_get_pr_review_status(
                pr_id=12345,
                working_directory="/test/repo/path"
            )
            
            # Then: Correctly identifies valid vs invalidated
            assert result["success"]
            
            valid_approvers = result["approval_status"]["valid_approvers"]
            assert len(valid_approvers) == 1, (
                f"Should have 1 valid approval (after commit). Got {len(valid_approvers)}"
            )
            assert valid_approvers[0]["name"] == "Late Approver"
            
            invalidated_approvers = result["approval_status"]["invalidated_approvers"]
            assert len(invalidated_approvers) == 2, (
                f"Should have 2 invalidated approvals (before commit). Got {len(invalidated_approvers)}"
            )
            
            # And: Needs 1 more approval
            assert result["approval_status"]["needs_approvals_count"] == 1, (
                "Should need 1 more approval to reach 2 total since last commit"
            )

    def test_handles_pr_with_rejection_and_waiting_and_approvals(self):
        """
        As a developer
        When my PR has a mix of rejection, waiting, and approvals
        Then I get a clear summary of all statuses
        
        Complex scenario showing all vote types at once.
        """
        # Given: PR with all vote types
        now = datetime.now()
        
        mock_repo_context = {
            "success": True,
            "organization": "microsoft",
            "project": "Universal Store",
            "repository": "Commerce.PaymentsDataPlatform",
            "org_url": "https://dev.azure.com/microsoft",
        }
        
        mock_pr_details = {
            "pullRequestId": 12345,
            "title": "PR with mixed vote types",
            "status": "active",
            "reviewers": [
                {
                    "displayName": "Approver",
                    "uniqueName": "approver@microsoft.com",
                    "vote": 10,
                    "votedFor": [{"date": now.isoformat()}]
                },
                {
                    "displayName": "Rejector",
                    "uniqueName": "rejector@microsoft.com",
                    "vote": -10,
                    "votedFor": [{"date": now.isoformat()}]
                },
                {
                    "displayName": "Waiter",
                    "uniqueName": "waiter@microsoft.com",
                    "vote": -5,
                    "votedFor": [{"date": now.isoformat()}]
                },
                {
                    "displayName": "Pending",
                    "uniqueName": "pending@microsoft.com",
                    "vote": 0,
                    "votedFor": []
                }
            ],
            "commits": []
        }
        
        with (
            patch("pdp_dev_mcp.tools.common.azure_devops_pr_review.get_repository_context", return_value=mock_repo_context),
            patch("subprocess.run") as mock_subprocess
        ):
            mock_subprocess.return_value = Mock(
                returncode=0,
                stdout=json.dumps(mock_pr_details)
            )
            
            # When: Checking PR status
            result = azure_devops_get_pr_review_status(
                pr_id=12345,
                working_directory="/test/repo/path"
            )
            
            # Then: Shows all vote types correctly
            assert result["success"]
            
            assert len(result["approval_status"]["valid_approvers"]) == 1
            assert len(result["approval_status"]["rejecting_reviewers"]) == 1
            assert len(result["approval_status"]["waiting_reviewers"]) == 1
            assert len(result["approval_status"]["pending_reviewers"]) == 1
            
            # And: Shows it's blocked by rejection
            assert result["approval_status"]["has_rejection"]
            
            # And: Summary mentions the blocking state
            summary = result["summary"]
            assert "blocked" in summary.lower() or "reject" in summary.lower()

    def test_team_approvals_dont_count_toward_approval_policy(self):
        """
        As a developer
        When a PR has approvals from teams/distribution lists
        Then those approvals should not count toward the required individual approvals
        
        Background:
        Teams and distribution lists are automatically added to PRs for notification purposes.
        Their "approvals" are automatic/inherited and don't represent actual code review.
        Branch policies require individual human approvers, not team memberships.
        
        Real scenario: PR #14330186 in PaymentsJournal repo had:
        - PayReconDevs team: voted 10 (auto-approval)
        - Payments Data Platform Dev team: voted 10 (auto-approval)  
        - Michael Baldini: voted 10 (individual approval)
        
        Policy requires 2 individual approvals, but tool incorrectly counted it as 3 approvals
        and marked PR as "ready to merge" when it still needs 1 more individual reviewer.
        """
        # Given: A PR with 1 individual approval and 2 team approvals
        now = datetime.now()
        
        mock_repo_context = {
            "success": True,
            "organization": "msazure",
            "project": "One",
            "repository": "CFS-Payments-DataPlatform-PaymentsJournal",
            "org_url": "https://dev.azure.com/msazure",
        }
        
        mock_pr_details = {
            "pullRequestId": 14330186,
            "title": "Add Country_ISO_Short field (WI 35451529)",
            "status": "active",
            "createdBy": {"displayName": "Jack Pines"},
            "creationDate": (now - timedelta(days=5)).isoformat(),
            "repository": {
                "name": "CFS-Payments-DataPlatform-PaymentsJournal",
                "project": {"name": "One"}
            },
            "reviewers": [
                {
                    "id": "team1-id",
                    "displayName": "[TEAM FOUNDATION]\\PayReconDevs",
                    "uniqueName": "vstfs:///Framework/IdentityDomain/41b4f3ee-c651-4a14-9847-b7cbb5315b80\\PayReconDevs",
                    "vote": 10,  # Team approval (automatic)
                    "isContainer": True,  # This marks it as a team/group
                    "votedFor": [{"date": (now - timedelta(days=4)).isoformat()}]
                },
                {
                    "id": "individual1-id",
                    "displayName": "Michael Baldini",
                    "uniqueName": "mbaldini@microsoft.com",
                    "vote": 10,  # Individual approval
                    "isContainer": False,
                    "votedFor": [{"date": (now - timedelta(days=3)).isoformat()}]
                },
                {
                    "id": "team2-id",
                    "displayName": "[TEAM FOUNDATION]\\Payments Data Platform Dev",
                    "uniqueName": "vstfs:///Framework/IdentityDomain/41b4f3ee-c651-4a14-9847-b7cbb5315b80\\Payments Data Platform Dev",
                    "vote": 10,  # Team approval (automatic)
                    "isContainer": True,  # This marks it as a team/group
                    "votedFor": [{"date": (now - timedelta(days=2)).isoformat()}]
                },
                {
                    "id": "individual2-id",
                    "displayName": "Dean Jordaan",
                    "uniqueName": "deanj@microsoft.com",
                    "vote": 0,  # Pending individual reviewer
                    "isContainer": False,
                    "votedFor": []
                }
            ],
            "commits": []
        }
        
        with (
            patch("pdp_dev_mcp.tools.common.azure_devops_pr_review.get_repository_context", return_value=mock_repo_context),
            patch("subprocess.run") as mock_subprocess
        ):
            mock_subprocess.return_value = Mock(
                returncode=0,
                stdout=json.dumps(mock_pr_details)
            )
            
            # When: Checking PR review status
            result = azure_devops_get_pr_review_status(
                pr_id=14330186,
                working_directory="/test/repo/path"
            )
            
            # Then: The system correctly counts only individual approvals
            assert result["success"], "PR status retrieval should succeed"
            
            # And: valid_approvers list still includes teams (for informational purposes)
            # but the approval count logic filters them out
            valid_approvers = result["approval_status"]["valid_approvers"]
            assert len(valid_approvers) == 3, (
                f"valid_approvers should include all approvals (teams + individuals) for information. "
                f"Got {len(valid_approvers)}"
            )
            
            # And: Can identify which are teams vs individuals
            team_approvers = [a for a in valid_approvers if a.get("is_container", False)]
            individual_approvers = [a for a in valid_approvers if not a.get("is_container", False)]
            
            assert len(team_approvers) == 2, (
                f"Expected 2 team approvers. Got: {[a['name'] for a in team_approvers]}"
            )
            assert len(individual_approvers) == 1, (
                f"Expected 1 individual approver. Got: {[a['name'] for a in individual_approvers]}"
            )
            
            # And: The individual approver is Michael Baldini
            assert individual_approvers[0]["name"] == "Michael Baldini", (
                "The only individual approver should be Michael Baldini"
            )
            
            # And: Needs 1 more approval (policy requires 2 individual approvals)
            needs_approvals = result["approval_status"]["needs_approvals_count"]
            assert needs_approvals == 1, (
                f"Policy requires 2 individual approvals, has 1, should need 1 more. "
                f"Got needs_approvals_count={needs_approvals}"
            )
            
            # And: Not marked as approved/ready to merge
            assert not result["approval_status"]["is_approved"], (
                "PR should not be marked as approved when still needing individual reviews"
            )
            
            # And: Summary correctly indicates more approvals needed
            summary = result["summary"]
            assert "Needs 1 approval" in summary, (
                f"Summary should indicate 1 more approval needed. Got: {summary}"
            )
            
            # And: Summary should NOT say "Ready to merge"
            assert "ready to merge" not in summary.lower(), (
                f"PR should not be marked as ready when needing more approvals. Got: {summary}"
            )
    def test_pr_needing_approvals_after_team_filtering_should_flag_for_reminders(self):
        """
        As a developer
        When a PR has everyone voted but needs more individual approvals (after filtering teams)
        Then the PR should be flagged as needing attention even with no "pending" reviewers
        
        Background:
        This is the real scenario from PR #14330186 - it has:
        - Team approvals (PayReconDevs, Payments Data Platform Dev) 
        - 1 individual approval (Michael Baldini)
        - Policy requires 2 individual approvals
        - Everyone assigned has voted (vote != 0)
        - Has active comment thread
        
        The reminder tool currently only flags PRs with pending reviewers (vote == 0),
        but it should also flag PRs that need more approvals even when everyone has voted.
        
        This test documents the expected behavior for future enhancement.
        """
        # Given: A PR where everyone has voted but still needs more individual approvals
        now = datetime.now()
        
        mock_repo_context = {
            "success": True,
            "organization": "msazure",
            "project": "One",
            "repository": "CFS-Payments-DataPlatform-PaymentsJournal",
            "org_url": "https://dev.azure.com/msazure",
        }
        
        mock_pr_details = {
            "pullRequestId": 14330186,
            "title": "Add Country_ISO_Short field (WI 35451529)",
            "status": "active",
            "createdBy": {"displayName": "Jack Pines"},
            "creationDate": (now - timedelta(days=5)).isoformat(),
            "repository": {
                "name": "CFS-Payments-DataPlatform-PaymentsJournal",
                "project": {"name": "One"}
            },
            "reviewers": [
                {
                    "id": "team1-id",
                    "displayName": "[TEAM FOUNDATION]\\PayReconDevs",
                    "uniqueName": "vstfs:///Framework/IdentityDomain/41b4f3ee-c651-4a14-9847-b7cbb5315b80\\PayReconDevs",
                    "vote": 10,  # Team approval
                    "isContainer": True,
                    "votedFor": [{"date": (now - timedelta(days=4)).isoformat()}]
                },
                {
                    "id": "individual1-id",
                    "displayName": "Michael Baldini",
                    "uniqueName": "mbaldini@microsoft.com",
                    "vote": 10,  # Individual approval  
                    "isContainer": False,
                    "votedFor": [{"date": (now - timedelta(days=3)).isoformat()}]
                },
                {
                    "id": "team2-id",
                    "displayName": "[TEAM FOUNDATION]\\Payments Data Platform Dev",
                    "uniqueName": "vstfs:///Framework/IdentityDomain/41b4f3ee-c651-4a14-9847-b7cbb5315b80\\Payments Data Platform Dev",
                    "vote": 10,  # Team approval
                    "isContainer": True,
                    "votedFor": [{"date": (now - timedelta(days=2)).isoformat()}]
                },
                # NOTE: No pending reviewers (vote == 0) - everyone has voted
            ],
            "commits": []
        }
        
        with (
            patch("pdp_dev_mcp.tools.common.azure_devops_pr_review.get_repository_context", return_value=mock_repo_context),
            patch("subprocess.run") as mock_subprocess
        ):
            mock_subprocess.return_value = Mock(
                returncode=0,
                stdout=json.dumps(mock_pr_details)
            )
            
            # When: Checking PR review status
            result = azure_devops_get_pr_review_status(
                pr_id=14330186,
                working_directory="/test/repo/path"
            )
            
            # Then: PR should NOT be approved (needs 1 more individual approval)
            assert not result["approval_status"]["is_approved"], (
                "PR should not be approved when needing more individual approvals"
            )
            
            # And: Should need 1 more approval
            assert result["approval_status"]["needs_approvals_count"] == 1, (
                f"Should need 1 more approval. Got: {result['approval_status']['needs_approvals_count']}"
            )
            
            # And: Should have no pending reviewers (everyone has voted)
            pending_reviewers = result["approval_status"]["pending_reviewers"]
            assert len(pending_reviewers) == 0, (
                f"Should have no pending reviewers (everyone voted). Got {len(pending_reviewers)}: "
                f"{[r['name'] for r in pending_reviewers]}"
            )
            
            # And: Summary should indicate need for more approvals
            summary = result["summary"]
            assert "Needs 1 approval" in summary, (
                f"Summary should indicate need for more approvals. Got: {summary}"
            )
            
            # NOTE: This PR should be flagged for reminders despite having no "pending" reviewers
            # Future enhancement: Reminder tool should detect this scenario
            # Current behavior: Reminder tool only flags PRs with pending_reviewers (vote == 0)
            # Desired behavior: Also flag PRs with needs_approvals_count > 0

    def test_pr_with_no_individual_reviewers_joined_yet_needs_team_members_to_participate(self):
        """
        As a developer
        When a PR has teams added but no individual developers have joined to review
        Then the PR should be flagged as needing attention to get team members to participate
        
        Background:
        Real workflow pattern:
        - PR is created
        - Teams are automatically added as reviewers (notification only)
        - Teams do NOT actually approve - individual members must join and approve
        - Policy requires 2 individual developer approvals
        - If no individuals have joined yet, needs_approvals_count = 2
        - But there are no "pending reviewers" (vote == 0) to remind
        
        This is the MOST CRITICAL scenario the reminder tool currently misses:
        Fresh PRs waiting for team members to notice and join.
        """
        # Given: A PR where only teams are added, no individuals have joined yet
        now = datetime.now()
        
        mock_repo_context = {
            "success": True,
            "organization": "microsoft",
            "project": "Universal Store",
            "repository": "Commerce.PaymentsDataPlatform",
            "org_url": "https://dev.azure.com/microsoft",
        }
        
        mock_pr_details = {
            "pullRequestId": 88888,
            "title": "Fresh PR awaiting team member participation",
            "status": "active",
            "createdBy": {"displayName": "New Developer"},
            "creationDate": (now - timedelta(hours=6)).isoformat(),
            "repository": {
                "name": "Commerce.PaymentsDataPlatform",
                "project": {"name": "Universal Store"}
            },
            "reviewers": [
                # Teams are added automatically but don't count as approvers
                # Individual team members need to JOIN the PR and approve
                {
                    "id": "team1-id",
                    "displayName": "[TEAM FOUNDATION]\\Payments Data Platform Dev",
                    "uniqueName": "vstfs:///Framework/IdentityDomain/team1",
                    "vote": 0,  # Team hasn't "voted" - individuals must join
                    "isContainer": True,
                    "isRequired": True,
                    "votedFor": []
                },
                # NO individual developers have joined yet!
                # This is the critical gap - PR needs visibility but no pending_reviewers exist
            ],
            "commits": []
        }
        
        with (
            patch("pdp_dev_mcp.tools.common.azure_devops_pr_review.get_repository_context", return_value=mock_repo_context),
            patch("subprocess.run") as mock_subprocess
        ):
            mock_subprocess.return_value = Mock(
                returncode=0,
                stdout=json.dumps(mock_pr_details)
            )
            
            # When: Checking PR review status
            result = azure_devops_get_pr_review_status(
                pr_id=88888,
                working_directory="/test/repo/path"
            )
            
            # Then: PR should NOT be approved (needs 2 individual approvals)
            assert not result["approval_status"]["is_approved"], (
                "PR with no individual approvals should NOT be approved"
            )
            
            # And: Should need 2 individual approvals (has none)
            assert result["approval_status"]["needs_approvals_count"] == 2, (
                f"Should need 2 individual approvals. "
                f"Got: {result['approval_status']['needs_approvals_count']}"
            )
            
            # And: Should have 0 valid individual approvers
            valid_approvers = result["approval_status"]["valid_approvers"]
            individual_approvers = [a for a in valid_approvers if not a.get("is_container", False)]
            assert len(individual_approvers) == 0, (
                f"Should have 0 individual approvers (no one joined yet). "
                f"Got: {[a['name'] for a in individual_approvers]}"
            )
            
            # And: Pending reviewers will only show the team (if vote==0), not individuals
            pending_reviewers = result["approval_status"]["pending_reviewers"]
            # The team itself might show as "pending" but that doesn't help - we need individuals!
            
            # And: Summary should indicate need for 2 approvals
            summary = result["summary"]
            assert "Needs 2 approval" in summary, (
                f"Summary should indicate need for 2 approvals. Got: {summary}"
            )
            

class TestAzureDevOpsPRReminderToolGaps:
    """
    Test scenarios where the PR reminder tool misses PRs that need attention.
    
    These tests document gaps in azure_devops_send_pr_review_reminders()
    which only flags PRs with pending_reviewers (vote==0), missing:
    1. Fresh PRs with only teams added (no individuals joined yet)
    2. PRs where everyone voted but still need more approvals after new commits
    """

    def test_reminder_tool_flags_fresh_pr_with_only_teams_no_individuals(self):
        """
        As a developer using the PR reminder tool
        When I have a fresh PR with only teams added as reviewers
        And no individual developers have joined to review yet
        Then the reminder tool should flag this PR as needing attention
        So I know to proactively reach out to team members
        
        Background:
        Real team workflow:
        - Developer creates PR, teams auto-added
        - Policy requires 2 individual approvals
        - No individuals have joined yet (needs_approvals_count = 2)
        - Team "reviewers" have vote=0 but they're containers, not real pending reviewers
        - Current reminder tool filters out teams, sees 0 pending reviewers, skips PR
        
        Expected: Reminder tool should flag PRs where needs_approvals_count > 0
        """
        # Given: A fresh PR with only teams added
        now = datetime.now()
        
        mock_repo_context = {
            "success": True,
            "organization": "microsoft",
            "project": "Universal Store",
            "repository": "Commerce.PaymentsDataPlatform",
            "org_url": "https://dev.azure.com/microsoft",
        }
        
        # Mock PR list response (1 active PR created by current user today)
        mock_pr_list = [
            {
                "pullRequestId": 99999,
                "title": "Fresh PR awaiting team member participation",
                "status": "active",
                "createdBy": {"displayName": "Current Developer"},
                "creationDate": now.isoformat(),
            }
        ]
        
        # Mock PR detail response (only teams, no individuals)
        mock_pr_detail = {
            "pullRequestId": 99999,
            "title": "Fresh PR awaiting team member participation",
            "status": "active",
            "createdBy": {"displayName": "Current Developer"},
            "creationDate": now.isoformat(),
            "repository": {
                "name": "Commerce.PaymentsDataPlatform",
                "project": {"name": "Universal Store"}
            },
            "mergeStatus": "succeeded",
            "reviewers": [
                {
                    "id": "team-id",
                    "displayName": "[TEAM FOUNDATION]\\Payments Data Platform Dev",
                    "uniqueName": "vstfs:///Framework/IdentityDomain/team",
                    "vote": 0,
                    "isContainer": True,
                    "isRequired": True,
                }
            ],
            "commits": []
        }
        
        with (
            patch("pdp_dev_mcp.tools.common.azure_devops_pr_review.get_repository_context", return_value=mock_repo_context),
            patch("pdp_dev_mcp.tools.common.azure_devops_pr_review.get_project_identifier", return_value="project-guid"),
            patch("subprocess.run") as mock_subprocess
        ):
            # Mock subprocess calls in order: current user, pr list, pr detail
            mock_subprocess.side_effect = [
                Mock(returncode=0, stdout="current.user@microsoft.com"),  # az account show
                Mock(returncode=0, stdout=json.dumps(mock_pr_list)),  # az repos pr list
                Mock(returncode=0, stdout=json.dumps(mock_pr_detail)),  # az repos pr show
            ]
            
            # When: Running the reminder tool
            from pdp_dev_mcp.tools.common.azure_devops_pr_review import azure_devops_send_pr_review_reminders
            result = azure_devops_send_pr_review_reminders(
                max_days_old=30,
                current_user_only=True,
                working_directory="/test/repo/path",
                save_analysis=False
            )
            
            # Then: Tool should successfully analyze
            assert result["success"], f"Expected success. Got error: {result.get('error')}"
            
            # And: Should flag this PR as needing reminders (not skip it)
            summary = result.get("summary", {})
            assert summary.get("prs_needing_reminders", 0) >= 1, (
                f"Expected at least 1 PR needing reminders (fresh PR with no individuals). "
                f"Got {summary.get('prs_needing_reminders', 0)} PRs flagged. "
                f"Full result: {result}"
            )
            
            # And: Should include this specific PR in the flagged list
            flagged_prs = result.get("pending_prs", [])
            pr_99999 = next((pr for pr in flagged_prs if pr.get("pr_id") == 99999), None)
            assert pr_99999 is not None, (
                f"Expected PR 99999 to be flagged for reminders. "
                f"Flagged PRs: {[pr.get('pr_id') for pr in flagged_prs]}"
            )

    def test_reminder_tool_flags_pr_needing_more_approvals_after_invalidation(self):
        """
        As a developer using the PR reminder tool
        When my PR had approvals but they were invalidated by new commits
        And all reviewers already voted (no vote==0 pending reviewers)
        Then the reminder tool should flag this PR as needing attention
        So I know to re-engage reviewers for fresh approvals
        
        Background:
        This is the exact scenario from PR #14330186:
        - Had 2 team approvals (teams auto-approve, don't count)
        - Had 1 individual approval
        - New commit pushed
        - Individual approval invalidated
        - Everyone has voted (approve=10, no vote=0)
        - Policy needs 2 individual approvals, only have 0 valid
        - needs_approvals_count = 2
        - Current reminder tool sees no pending reviewers, skips PR
        
        Expected: Reminder tool should flag PRs where needs_approvals_count > 0
        """
        # Given: A PR with invalidated approvals after new commit
        now = datetime.now()
        commit_time = now - timedelta(hours=1)
        old_approval_time = now - timedelta(hours=2)
        
        mock_repo_context = {
            "success": True,
            "organization": "msazure",
            "project": "One",
            "repository": "CFS-Payments-DataPlatform-PaymentsJournal",
            "org_url": "https://dev.azure.com/msazure",
        }
        
        # Mock PR list response
        mock_pr_list = [
            {
                "pullRequestId": 14330186,
                "title": "PR with invalidated approvals",
                "status": "active",
                "createdBy": {"displayName": "Current Developer"},
                "creationDate": (now - timedelta(days=2)).isoformat(),
            }
        ]
        
        # Mock PR detail response (approvals before last commit)
        mock_pr_detail = {
            "pullRequestId": 14330186,
            "title": "PR with invalidated approvals",
            "status": "active",
            "createdBy": {"displayName": "Current Developer"},
            "creationDate": (now - timedelta(days=2)).isoformat(),
            "repository": {
                "name": "CFS-Payments-DataPlatform-PaymentsJournal",
                "project": {"name": "One"}
            },
            "mergeStatus": "succeeded",
            "reviewers": [
                # Teams that auto-approved (don't count)
                {
                    "id": "team1",
                    "displayName": "[TEAM FOUNDATION]\\PayReconDevs",
                    "vote": 10,
                    "isContainer": True,
                    "votedFor": [{"date": old_approval_time.isoformat()}]
                },
                {
                    "id": "team2",
                    "displayName": "[TEAM FOUNDATION]\\Payments Data Platform Dev",
                    "vote": 10,
                    "isContainer": True,
                    "votedFor": [{"date": old_approval_time.isoformat()}]
                },
                # Individual who approved BEFORE last commit (invalidated)
                {
                    "id": "user1",
                    "displayName": "Reviewer One",
                    "uniqueName": "reviewer1@microsoft.com",
                    "vote": 10,
                    "isContainer": False,
                    "isRequired": True,
                    "votedFor": [{"date": old_approval_time.isoformat()}]
                }
            ],
            "commits": [
                {"committer": {"date": commit_time.isoformat()}}
            ]
        }
        
        with (
            patch("pdp_dev_mcp.tools.common.azure_devops_pr_review.get_repository_context", return_value=mock_repo_context),
            patch("pdp_dev_mcp.tools.common.azure_devops_pr_review.get_project_identifier", return_value="project-guid"),
            patch("subprocess.run") as mock_subprocess
        ):
            # Mock subprocess calls
            mock_subprocess.side_effect = [
                Mock(returncode=0, stdout="current.user@microsoft.com"),  # az account show
                Mock(returncode=0, stdout=json.dumps(mock_pr_list)),  # az repos pr list
                Mock(returncode=0, stdout=json.dumps(mock_pr_detail)),  # az repos pr show
            ]
            
            # When: Running the reminder tool
            from pdp_dev_mcp.tools.common.azure_devops_pr_review import azure_devops_send_pr_review_reminders
            result = azure_devops_send_pr_review_reminders(
                max_days_old=30,
                current_user_only=True,
                working_directory="/test/repo/path",
                save_analysis=False
            )
            
            # Then: Tool should successfully analyze
            assert result["success"], f"Expected success. Got error: {result.get('error')}"
            
            # And: Should flag this PR as needing reminders
            summary = result.get("summary", {})
            assert summary.get("prs_needing_reminders", 0) >= 1, (
                f"Expected at least 1 PR needing reminders (PR with invalidated approvals). "
                f"Got {summary.get('prs_needing_reminders', 0)} PRs flagged. "
                f"Full result: {result}"
            )
            
            # And: Should include PR #14330186 in the flagged list
            flagged_prs = result.get("pending_prs", [])
            pr_14330186 = next((pr for pr in flagged_prs if pr.get("pr_id") == 14330186), None)
            assert pr_14330186 is not None, (
                f"Expected PR #14330186 to be flagged for reminders. "
                f"Flagged PRs: {[pr.get('pr_id') for pr in flagged_prs]}"
            )

    def test_reminder_tool_should_skip_draft_prs(self):
        """
        As a developer using the PR reminder tool
        When I have draft PRs that are not ready for review
        Then the reminder tool should skip them and not flag for reminders
        So I don't get bothered about PRs I'm still working on
        
        Background:
        Draft PRs are work-in-progress and explicitly marked as not ready for review.
        It doesn't make sense to remind reviewers about draft PRs since the author
        hasn't indicated they're ready for feedback yet.
        """
        # Given: A draft PR and a regular PR
        now = datetime.now()
        
        mock_repo_context = {
            "success": True,
            "organization": "microsoft",
            "project": "Universal Store",
            "repository": "Commerce.PaymentsDataPlatform",
            "org_url": "https://dev.azure.com/microsoft",
        }
        
        # Mock PR list response (1 draft, 1 regular)
        mock_pr_list = [
            {
                "pullRequestId": 11111,
                "title": "Draft PR - still working on it",
                "status": "active",
                "isDraft": True,  # This is a draft
                "createdBy": {"displayName": "Current Developer"},
                "creationDate": now.isoformat(),
            },
            {
                "pullRequestId": 22222,
                "title": "Regular PR ready for review",
                "status": "active",
                "isDraft": False,  # This is ready for review
                "createdBy": {"displayName": "Current Developer"},
                "creationDate": now.isoformat(),
            }
        ]
        
        # Mock PR detail responses
        mock_draft_pr_detail = {
            "pullRequestId": 11111,
            "title": "Draft PR - still working on it",
            "status": "active",
            "isDraft": True,
            "createdBy": {"displayName": "Current Developer"},
            "creationDate": now.isoformat(),
            "repository": {
                "name": "Commerce.PaymentsDataPlatform",
                "project": {"name": "Universal Store"}
            },
            "mergeStatus": "succeeded",
            "reviewers": [
                {
                    "id": "reviewer1",
                    "displayName": "Reviewer One",
                    "uniqueName": "reviewer1@microsoft.com",
                    "vote": 0,
                    "isContainer": False,
                    "isRequired": True,
                }
            ],
            "commits": []
        }
        
        mock_regular_pr_detail = {
            "pullRequestId": 22222,
            "title": "Regular PR ready for review",
            "status": "active",
            "isDraft": False,
            "createdBy": {"displayName": "Current Developer"},
            "creationDate": now.isoformat(),
            "repository": {
                "name": "Commerce.PaymentsDataPlatform",
                "project": {"name": "Universal Store"}
            },
            "mergeStatus": "succeeded",
            "reviewers": [
                {
                    "id": "reviewer2",
                    "displayName": "Reviewer Two",
                    "uniqueName": "reviewer2@microsoft.com",
                    "vote": 0,
                    "isContainer": False,
                    "isRequired": True,
                }
            ],
            "commits": []
        }
        
        with (
            patch("pdp_dev_mcp.tools.common.azure_devops_pr_review.get_repository_context", return_value=mock_repo_context),
            patch("pdp_dev_mcp.tools.common.azure_devops_pr_review.get_project_identifier", return_value="project-guid"),
            patch("subprocess.run") as mock_subprocess
        ):
            # Mock subprocess calls: current user, pr list, pr detail (draft), pr detail (regular)
            mock_subprocess.side_effect = [
                Mock(returncode=0, stdout="current.user@microsoft.com"),  # az account show
                Mock(returncode=0, stdout=json.dumps(mock_pr_list)),  # az repos pr list
                Mock(returncode=0, stdout=json.dumps(mock_draft_pr_detail)),  # az repos pr show (draft)
                Mock(returncode=0, stdout=json.dumps(mock_regular_pr_detail)),  # az repos pr show (regular)
            ]
            
            # When: Running the reminder tool
            from pdp_dev_mcp.tools.common.azure_devops_pr_review import azure_devops_send_pr_review_reminders
            result = azure_devops_send_pr_review_reminders(
                max_days_old=30,
                current_user_only=True,
                working_directory="/test/repo/path",
                save_analysis=False
            )
            
            # Then: Tool should successfully analyze
            assert result["success"], f"Expected success. Got error: {result.get('error')}"
            
            # And: Should flag only the regular PR, not the draft
            summary = result.get("summary", {})
            assert summary.get("prs_needing_reminders", 0) == 1, (
                f"Expected exactly 1 PR needing reminders (not the draft). "
                f"Got {summary.get('prs_needing_reminders', 0)} PRs flagged."
            )
            
            # And: Should include only the regular PR in the flagged list
            flagged_prs = result.get("pending_prs", [])
            assert len(flagged_prs) == 1, (
                f"Expected 1 flagged PR. Got {len(flagged_prs)}"
            )
            
            pr_22222 = next((pr for pr in flagged_prs if pr.get("pr_id") == 22222), None)
            assert pr_22222 is not None, (
                f"Expected regular PR 22222 to be flagged. "
                f"Flagged PRs: {[pr.get('pr_id') for pr in flagged_prs]}"
            )
            
            # And: Draft PR should NOT be in the list
            pr_11111 = next((pr for pr in flagged_prs if pr.get("pr_id") == 11111), None)
            assert pr_11111 is None, (
                f"Expected draft PR 11111 to be skipped, but it was flagged!"
            )

    def test_reminder_tool_should_skip_prs_waiting_for_author(self):
        """
        As a developer using the PR reminder tool
        When I have PRs with active comment threads requiring my attention
        Then the reminder tool should skip them and not send reminders
        So I don't ask reviewers for attention when I need to address comments first
        
        Background:
        Active comment threads (thread.status = "active") indicate unresolved feedback.
        Comments can come from reviewers OR non-reviewers (e.g., team members providing input).
        Non-reviewer comments don't technically block merge, but best practice is to address
        all active comments before prompting for more reviews. Once author resolves comments,
        the thread status changes and PR becomes eligible for review reminders again.
        
        Real-world example: PR #14330186 has active comment from non-reviewer that needs
        author attention before proceeding with review reminders.
        """
        # Given: A PR with active comment threads and a regular PR
        now = datetime.now()
        
        mock_repo_context = {
            "success": True,
            "organization": "microsoft",
            "project": "Universal Store",
            "repository": "Commerce.PaymentsDataPlatform",
            "org_url": "https://dev.azure.com/microsoft",
        }
        
        # Mock PR list response
        mock_pr_list = [
            {
                "pullRequestId": 33333,
                "title": "PR with active comment threads",
                "status": "active",
                "isDraft": False,
                "createdBy": {"displayName": "Current Developer"},
                "creationDate": now.isoformat(),
            },
            {
                "pullRequestId": 44444,
                "title": "PR ready for review",
                "status": "active",
                "isDraft": False,
                "createdBy": {"displayName": "Current Developer"},
                "creationDate": now.isoformat(),
            }
        ]
        
        # Mock PR detail responses
        mock_pr_with_comments_detail = {
            "pullRequestId": 33333,
            "title": "PR with active comment threads",
            "status": "active",
            "isDraft": False,
            "createdBy": {"displayName": "Current Developer"},
            "creationDate": now.isoformat(),
            "repository": {
                "name": "Commerce.PaymentsDataPlatform",
                "project": {"name": "Universal Store"}
            },
            "mergeStatus": "succeeded",
            "reviewers": [
                {
                    "id": "reviewer1",
                    "displayName": "Team Member",
                    "uniqueName": "team.member@microsoft.com",
                    "vote": 0,  # No vote yet, just left comments
                    "isContainer": False,
                    "isRequired": False,
                }
            ],
            "threads": [
                {
                    "id": 1,
                    "status": "active",  # Active comment thread
                    "comments": [
                        {
                            "author": {"displayName": "Team Member"},
                            "content": "Please address this feedback"
                        }
                    ]
                }
            ],
            "commits": []
        }
        
        mock_ready_pr_detail = {
            "pullRequestId": 44444,
            "title": "PR ready for review",
            "status": "active",
            "isDraft": False,
            "createdBy": {"displayName": "Current Developer"},
            "creationDate": now.isoformat(),
            "repository": {
                "name": "Commerce.PaymentsDataPlatform",
                "project": {"name": "Universal Store"}
            },
            "mergeStatus": "succeeded",
            "reviewers": [
                {
                    "id": "reviewer2",
                    "displayName": "Reviewer Two",
                    "uniqueName": "reviewer2@microsoft.com",
                    "vote": 0,
                    "isContainer": False,
                    "isRequired": True,
                }
            ],
            "threads": [],  # No active comment threads
            "commits": []
        }
        
        with (
            patch("pdp_dev_mcp.tools.common.azure_devops_pr_review.get_repository_context", return_value=mock_repo_context),
            patch("pdp_dev_mcp.tools.common.azure_devops_pr_review.get_project_identifier", return_value="project-guid"),
            patch("subprocess.run") as mock_subprocess
        ):
            # Mock subprocess calls
            mock_subprocess.side_effect = [
                Mock(returncode=0, stdout="current.user@microsoft.com"),  # az account show
                Mock(returncode=0, stdout=json.dumps(mock_pr_list)),  # az repos pr list
                Mock(returncode=0, stdout=json.dumps(mock_pr_with_comments_detail)),  # az repos pr show (with comments)
                Mock(returncode=0, stdout=json.dumps(mock_ready_pr_detail)),  # az repos pr show (ready)
            ]
            
            # When: Running the reminder tool
            from pdp_dev_mcp.tools.common.azure_devops_pr_review import azure_devops_send_pr_review_reminders
            result = azure_devops_send_pr_review_reminders(
                max_days_old=30,
                current_user_only=True,
                working_directory="/test/repo/path",
                save_analysis=False
            )
            
            # Then: Tool should successfully analyze
            assert result["success"], f"Expected success. Got error: {result.get('error')}"
            
            # And: Should flag only the ready PR, not the one with active comments
            summary = result.get("summary", {})
            assert summary.get("prs_needing_reminders", 0) == 1, (
                f"Expected exactly 1 PR needing reminders (not the one with active comments). "
                f"Got {summary.get('prs_needing_reminders', 0)} PRs flagged."
            )
            
            # And: Should include only the ready PR in the flagged list
            flagged_prs = result.get("pending_prs", [])
            assert len(flagged_prs) == 1, (
                f"Expected 1 flagged PR. Got {len(flagged_prs)}"
            )
            
            pr_44444 = next((pr for pr in flagged_prs if pr.get("pr_id") == 44444), None)
            assert pr_44444 is not None, (
                f"Expected ready PR 44444 to be flagged. "
                f"Flagged PRs: {[pr.get('pr_id') for pr in flagged_prs]}"
            )
            
            # And: PR with active comments should NOT be in the list
            pr_33333 = next((pr for pr in flagged_prs if pr.get("pr_id") == 33333), None)
            assert pr_33333 is None, (
                f"Expected PR 33333 with active comments to be skipped, but it was flagged!"
            )
